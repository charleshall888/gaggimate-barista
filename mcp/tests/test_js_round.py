"""Unit tests for ``js_round`` — the JS ``Math.round`` semantic match.

Python's built-in ``round`` uses banker's rounding (0.5 → 0, 2.5 → 2),
which would produce off-by-one errors versus AnalyzerService.js. These
five canonical cases lock in JS ``Math.round`` rounds-toward-+∞ behavior.
"""

from gaggimate_mcp.analysis.shot_analyzer import js_round


def test_js_round_matches_js_math_round() -> None:
    assert js_round(0.5) == 1
    assert js_round(-0.5) == 0
    assert js_round(2.5) == 3
    assert js_round(-2.5) == -2
    assert js_round(24.5) == 25
