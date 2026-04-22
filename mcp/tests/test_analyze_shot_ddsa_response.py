"""End-to-end ``analyze_shot`` MCP response shape test (Task 12 / spec R17).

Mocks ``http_client.fetch_shot`` and ``ws_client.load_profile`` to return real
fixture data (parsed ``247.slog`` and ``247.profile.json``) so the test
exercises the full DDSA wiring inside ``analyze_shot`` without touching the
network. Asserts the response carries the three new top-level keys
(``phase_exits``, ``auto_delay``, ``analyzer_url``), that ``auto_delay`` is
JSON-clean (``int`` or ``None``, never ``NaN``/``Infinity``/``float``), that
each ``phase_exits[*]`` carries the contract keys, and that ``analyzer_url``
is constructed from the pre-normalization ``shot_id`` parameter (leading
zeros stripped; non-numeric IDs preserved verbatim).

A degradation case mocks ``ws_client.load_profile`` to raise; asserts every
``phase_exits[*]`` collapses to ``exit_reason_type="unknown"`` with
``unavailable_reason="profile_unavailable"``, and the deep-link still
renders.

Field-naming note: the normal-path ``classify_phase_exits`` emits ``number``
(``str``, mirroring JS ``Object.keys()`` output) for the phase identifier;
the degraded path also emits ``phase_number`` (``int``). This test asserts
``number`` on the normal path and the same key set on the degraded path,
locking in what the implementation actually emits today (per T11/T8b
reconciliation note).
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from gaggimate_mcp.parsers.shot import parse_binary_shot


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "shots"
ANALYZER_URL_RE = r"^http://[^/]+/analyze/[^/]+$"


def _load_fixture_shot():
    """Parse the 247.slog fixture into a ShotData object."""
    slog_path = FIXTURE_DIR / "247.slog"
    return parse_binary_shot(slog_path.read_bytes(), "000247")


def _load_fixture_profile() -> dict:
    """Load the 247.profile.json fixture into a dict."""
    profile_path = FIXTURE_DIR / "247.profile.json"
    return json.loads(profile_path.read_text(encoding="utf-8"))


def _reload_server():
    """Re-import the server module so module-level singletons rebuild fresh."""
    import importlib

    import gaggimate_mcp.server as server

    importlib.reload(server)
    return server


async def _invoke_analyze_shot(
    *,
    shot_id: str,
    profile_loader: AsyncMock,
):
    """Invoke ``analyze_shot`` against mocked transport layers and return the parsed JSON dict."""
    server = _reload_server()

    shot_data = _load_fixture_shot()

    with patch.object(
        server.http_client, "fetch_shot", new_callable=AsyncMock
    ) as mock_fetch, patch.object(
        server.ws_client, "load_profile", new=profile_loader
    ):
        mock_fetch.return_value = shot_data
        raw = await server.analyze_shot(shot_id=shot_id)

    return raw, json.loads(raw)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "shot_id,expected_url_tail",
    [
        ("247", "/analyze/247"),
        ("00247", "/analyze/247"),
        ("abc", "/analyze/abc"),
    ],
)
async def test_analyze_shot_response_shape(
    shot_id: str, expected_url_tail: str
) -> None:
    """Normal path: response carries the three new keys with correct types/format."""
    profile_loader = AsyncMock(return_value=_load_fixture_profile())
    raw, response = await _invoke_analyze_shot(
        shot_id=shot_id, profile_loader=profile_loader
    )

    # Top-level success contract still intact.
    assert response["success"] is True

    # (a) all three new keys present.
    assert "phase_exits" in response
    assert "auto_delay" in response
    assert "analyzer_url" in response

    # (b) auto_delay.delay_ms is int or None — never float, NaN, Infinity.
    auto_delay = response["auto_delay"]
    assert isinstance(auto_delay, dict)
    assert "delay_ms" in auto_delay
    delay_ms = auto_delay["delay_ms"]
    if delay_ms is not None:
        assert isinstance(delay_ms, int) and not isinstance(delay_ms, bool), (
            f"auto_delay.delay_ms must be int (not float/bool), got {type(delay_ms).__name__}"
        )
    # JSON sanity: serialized form must not contain NaN/Infinity tokens.
    assert "NaN" not in raw
    assert "Infinity" not in raw
    # And the response must round-trip with allow_nan=False (catches float NaNs
    # buried in nested dicts/lists that the substring check would miss).
    json.dumps(response, allow_nan=False)

    # (c) every phase_exits entry has the contract keys. The normal-path
    # implementation emits the JS-mirrored ``number`` (str) field for the phase
    # identifier; ``phase_number`` is degraded-path-only (per T8b/T11 drift).
    phase_exits = response["phase_exits"]
    assert isinstance(phase_exits, list)
    assert len(phase_exits) >= 1
    for entry in phase_exits:
        assert "exit_reason_type" in entry
        assert "unavailable_reason" in entry
        # Normal path: JS-mirrored ``number`` key is the phase identifier.
        assert "number" in entry
        # Normal path means a real profile was found; unavailable_reason must
        # be None for every classified phase.
        assert entry["unavailable_reason"] is None

    # (d) + (e) analyzer_url shape.
    analyzer_url = response["analyzer_url"]
    assert isinstance(analyzer_url, str)
    # General shape: http://<host>/analyze/<tail>.
    import re

    assert re.match(ANALYZER_URL_RE, analyzer_url), (
        f"analyzer_url did not match {ANALYZER_URL_RE}: {analyzer_url}"
    )
    assert analyzer_url.endswith(expected_url_tail), (
        f"analyzer_url tail mismatch: expected end {expected_url_tail}, got {analyzer_url}"
    )


@pytest.mark.asyncio
async def test_analyze_shot_numeric_id_matches_strict_regex() -> None:
    """A purely numeric shot_id produces a URL matching ``/analyze/\\d+$``."""
    import re

    profile_loader = AsyncMock(return_value=_load_fixture_profile())
    _, response = await _invoke_analyze_shot(
        shot_id="247", profile_loader=profile_loader
    )

    # Spec R17(d): on a numeric-shot-id fixture, the URL matches the strict
    # numeric regex ``^http://[^/]+/analyze/\d+$``.
    strict = r"^http://[^/]+/analyze/\d+$"
    assert re.match(strict, response["analyzer_url"]), response["analyzer_url"]


@pytest.mark.asyncio
async def test_analyze_shot_profile_unavailable_degradation() -> None:
    """``ws_client.load_profile`` raises → degraded ``profile_unavailable`` payload."""
    # AsyncMock with side_effect=Exception(...) — invoking the mock raises.
    profile_loader = AsyncMock(side_effect=Exception("WS unreachable"))
    raw, response = await _invoke_analyze_shot(
        shot_id="247", profile_loader=profile_loader
    )

    assert response["success"] is True

    # phase_exits is a non-empty list (one entry per observed shot phase).
    phase_exits = response["phase_exits"]
    assert isinstance(phase_exits, list)
    assert len(phase_exits) >= 1
    for entry in phase_exits:
        assert entry["exit_reason_type"] == "unknown"
        assert entry["unavailable_reason"] == "profile_unavailable"
        # Degraded path emits BOTH ``number`` (str) and ``phase_number``
        # (int) — assert both so future churn on either spelling fails loudly.
        assert "number" in entry
        assert "phase_number" in entry

    # auto_delay collapses to the documented degraded shape.
    assert response["auto_delay"] == {
        "delay_ms": None,
        "auto": False,
        "unavailable_reason": "profile_unavailable",
    }

    # analyzer_url still renders.
    import re

    assert re.match(ANALYZER_URL_RE, response["analyzer_url"]), response["analyzer_url"]

    # JSON sanity even on the degraded path.
    assert "NaN" not in raw
    assert "Infinity" not in raw
    json.dumps(response, allow_nan=False)
