"""Drift-detection guard for ``ANALYZER_JS_VERSION`` vs vendored harness JS.

If a future firmware re-sync bumps ``ANALYZER_JS_VERSION`` without re-vendoring
``analyzer-service.<version>.js`` / ``parse-binary-shot.<version>.js`` (or vice
versa), this test fails loudly. See "Re-syncing shot-analyzer on firmware
upgrades" runbook in ``mcp/README.md``.
"""

from pathlib import Path

from gaggimate_mcp.analysis.shot_analyzer import ANALYZER_JS_VERSION

HARNESS_DIR = Path(__file__).parent / "fixtures" / "shots" / "harness"


def test_analyzer_service_js_filename_matches_version() -> None:
    matches = list(HARNESS_DIR.glob("analyzer-service.*.js"))
    assert matches, (
        f"No analyzer-service.*.js files found in {HARNESS_DIR}. "
        "Re-vendor the harness JS for the current firmware version."
    )
    for path in matches:
        assert ANALYZER_JS_VERSION in path.name, (
            f"Vendored harness file {path.name} does not contain "
            f"ANALYZER_JS_VERSION={ANALYZER_JS_VERSION!r}. Either bump the "
            "constant or re-vendor the JS so they agree."
        )


def test_parse_binary_shot_js_filename_matches_version() -> None:
    matches = list(HARNESS_DIR.glob("parse-binary-shot.*.js"))
    assert matches, (
        f"No parse-binary-shot.*.js files found in {HARNESS_DIR}. "
        "Re-vendor the harness JS for the current firmware version."
    )
    for path in matches:
        assert ANALYZER_JS_VERSION in path.name, (
            f"Vendored harness file {path.name} does not contain "
            f"ANALYZER_JS_VERSION={ANALYZER_JS_VERSION!r}. Either bump the "
            "constant or re-vendor the JS so they agree."
        )
