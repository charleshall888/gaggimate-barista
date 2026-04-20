"""Tests for save_shot_notes read-modify-write merge logic and tool-layer
bean_type propagation.

Covers Task 1 (RMW merge + wire-type stringification + defensive parsing +
no-op short-circuit + existing-string preservation) and Task 2 (bean_type
propagation through manage_shot_notes to both the WS transport and the
local ratings.json backup).

These tests deliberately avoid network: GaggimateWebSocketClient is
instantiated with a stub config, then `get_shot_notes` and `_send_request`
are replaced with AsyncMocks per-test. The captured call's kwargs["notes"]
dict is the contract under test.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from gaggimate_mcp.api.websocket import GaggimateWebSocketClient
from gaggimate_mcp.config import GaggimateConfig
from gaggimate_mcp.storage.ratings import RatingStorage


def _make_client() -> GaggimateWebSocketClient:
    """Build a WS client with a minimal config (no network access in tests)."""
    config = GaggimateConfig(gaggimate_host="test.local")
    return GaggimateWebSocketClient(config)


@pytest.mark.asyncio
async def test_rmw_preserves_existing_fields():
    """Existing fields not touched by the caller must survive the merge."""
    client = _make_client()
    existing = {"id": "246", "rating": 3, "balanceTaste": "bitter"}
    client.get_shot_notes = AsyncMock(return_value=existing)
    client._send_request = AsyncMock(return_value={"msg": "ok"})

    await client.save_shot_notes(shot_id="246", notes="hi")

    assert client._send_request.call_count == 1
    sent_notes = client._send_request.call_args.kwargs["notes"]
    assert sent_notes["id"] == "246"
    assert sent_notes["rating"] == 3
    assert sent_notes["balanceTaste"] == "bitter"
    assert sent_notes["notes"] == "hi"


@pytest.mark.asyncio
async def test_empty_sidecar_stringifies_dose_and_ratio():
    """Empty sidecar + caller doses → wire payload has stringified dose/ratio."""
    client = _make_client()
    client.get_shot_notes = AsyncMock(return_value=None)
    client._send_request = AsyncMock(return_value={"msg": "ok"})

    await client.save_shot_notes(
        shot_id="246",
        rating=5,
        dose_in=22.0,
        dose_out=55.0,
        bean_type="X",
    )

    assert client._send_request.call_count == 1
    sent_notes = client._send_request.call_args.kwargs["notes"]
    assert sent_notes["id"] == "246"
    assert sent_notes["rating"] == 5
    # Dose and ratio fields MUST be strings — firmware reads doseOut with
    # .is<String>() and silently zeros the index volume column otherwise.
    assert sent_notes["doseIn"] == "22.0"
    assert isinstance(sent_notes["doseIn"], str)
    assert sent_notes["doseOut"] == "55.0"
    assert isinstance(sent_notes["doseOut"], str)
    assert sent_notes["ratio"] == "2.5"
    assert isinstance(sent_notes["ratio"], str)
    assert sent_notes["beanType"] == "X"


@pytest.mark.asyncio
async def test_defensive_non_dict_existing():
    """Non-dict get_shot_notes return → treated as empty, no exception."""
    client = _make_client()
    client.get_shot_notes = AsyncMock(return_value="oops")
    client._send_request = AsyncMock(return_value={"msg": "ok"})

    # Should not raise.
    await client.save_shot_notes(shot_id="246", rating=3)

    assert client._send_request.call_count == 1
    sent_notes = client._send_request.call_args.kwargs["notes"]
    # Empty-merge semantics: only id (synthesized) + rating from the caller.
    assert sent_notes["id"] == "246"
    assert sent_notes["rating"] == 3


@pytest.mark.asyncio
async def test_noop_short_circuit():
    """Caller value identical to existing → skip WS save entirely."""
    client = _make_client()
    existing = {"id": "246", "rating": 3}
    client.get_shot_notes = AsyncMock(return_value=existing)
    client._send_request = AsyncMock(return_value={"msg": "ok"})

    await client.save_shot_notes(shot_id="246", rating=3)

    # get_shot_notes is mocked separately so it does NOT increment
    # _send_request.call_count. Exact 0 is the contract: the merged payload
    # equals the existing dict so no wire write occurs.
    assert client._send_request.call_count == 0


@pytest.mark.asyncio
async def test_existing_dose_strings_preserved():
    """String dose values from the native editor must survive untouched."""
    client = _make_client()
    existing = {"id": "246", "doseIn": "18.0"}
    client.get_shot_notes = AsyncMock(return_value=existing)
    client._send_request = AsyncMock(return_value={"msg": "ok"})

    # Caller passes notes only — no dose fields. doseIn must be unchanged.
    await client.save_shot_notes(shot_id="246", notes="hi")

    assert client._send_request.call_count == 1
    sent_notes = client._send_request.call_args.kwargs["notes"]
    # Byte-for-byte preservation: not float-coerced, not stripped.
    assert sent_notes["doseIn"] == "18.0"
    assert isinstance(sent_notes["doseIn"], str)


@pytest.mark.asyncio
async def test_tool_passes_bean_type_to_both_sinks(tmp_path, monkeypatch):
    """manage_shot_notes propagates bean_type to local backup and WS transport."""
    # Redirect RatingStorage to a temp dir so we don't touch the real
    # ratings.json. GaggimateConfig's `storage_path` env is GAGGIMATE_STORAGE_PATH.
    monkeypatch.setenv("GAGGIMATE_STORAGE_PATH", str(tmp_path))

    # Re-import the server module so its module-level rating_storage picks up
    # the new env. importlib.reload is the standard pattern but `import` of
    # a fresh sub-module via importlib gives us a clean instance.
    import importlib

    import gaggimate_mcp.server as server
    importlib.reload(server)

    # --- (a) sync_to_device=False: only local backup is written ---
    # @mcp.tool() registers the function with the FastMCP instance but
    # leaves the original function callable directly — call it as a normal
    # async function rather than going through the MCP transport.
    manage = server.manage_shot_notes

    result_json = await manage(
        shot_id="999",
        bean_type="TEST-BEAN",
        sync_to_device=False,
    )
    result = json.loads(result_json)
    assert result["success"] is True

    # The ratings.json file should now have the "000999" entry with bean_type.
    ratings_file = tmp_path / "ratings.json"
    assert ratings_file.exists(), f"expected ratings.json at {ratings_file}"
    on_disk = json.loads(ratings_file.read_text())
    assert "000999" in on_disk, f"expected key '000999' in {list(on_disk.keys())}"
    assert on_disk["000999"]["bean_type"] == "TEST-BEAN"

    # --- (b) sync_to_device=True with mocked ws_client.save_shot_notes ---
    # Patch save_shot_notes on the module-level ws_client so we can assert
    # bean_type is forwarded as a kwarg to the transport layer.
    with patch.object(
        server.ws_client, "save_shot_notes", new_callable=AsyncMock
    ) as mock_save:
        mock_save.return_value = {"msg": "ok"}
        result_json = await manage(
            shot_id="999",
            bean_type="TEST-BEAN",
            sync_to_device=True,
        )
        result = json.loads(result_json)
        assert result["success"] is True
        assert mock_save.call_count == 1
        # bean_type must be passed through as a kwarg.
        assert mock_save.call_args.kwargs.get("bean_type") == "TEST-BEAN"
