"""Regression test for ``transform_shot_for_ai``.

Parametrized over every ``.slog`` file in ``tests/fixtures/shots/``. Each case
parses the binary, runs the transformer, and asserts exact equality against
the sibling ``.golden.json``. Goldens are regenerated via
``python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>``.
"""

import json
from pathlib import Path

import pytest

from gaggimate_mcp.parsers.shot import parse_binary_shot
from gaggimate_mcp.transformers.shot import transform_shot_for_ai

from tests.shot_fixture_walker import assert_equal


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "shots"


@pytest.mark.parametrize(
    "slog_path",
    sorted(FIXTURE_DIR.glob("*.slog")) if FIXTURE_DIR.exists() else [],
    ids=lambda p: p.stem,
)
def test_transform_matches_golden(slog_path: Path) -> None:
    golden_path = slog_path.with_suffix(".golden.json")
    if not golden_path.exists():
        pytest.fail(
            f"Missing golden: {golden_path} — regenerate via "
            f"'python -m gaggimate_mcp.tools.refresh_fixtures {slog_path.stem}'."
        )

    data = slog_path.read_bytes()
    shot = parse_binary_shot(data, slog_path.stem.zfill(6))
    transformed = transform_shot_for_ai(shot)

    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    assert_equal(expected, transformed, max_mismatches=10)
