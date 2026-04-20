# Review: shot-fixture-regression-harness

## Stage 1: Spec Compliance

### Requirement 1: Fixture directory and binaries
- **Expected**: `mcp/tests/fixtures/shots/` contains at least three `.slog` files checked into the main repo. `ls mcp/tests/fixtures/shots/*.slog | wc -l` returns ≥ 3.
- **Actual**: Directory exists at `mcp/tests/fixtures/shots/`. Three `.slog` files present: `246.slog`, `247.slog`, `249.slog`. Verified: count = 3.
- **Verdict**: PASS

### Requirement 2: Golden JSON outputs (full surface)
- **Expected**: Alongside each `.slog`, a `<shot_id>.golden.json` containing the complete `TransformedShot` output. Acceptance script returns `True`.
- **Actual**: `246.golden.json`, `247.golden.json`, `249.golden.json` all present alongside their `.slog` siblings. Acceptance script executed and returned `True`.
- **Verdict**: PASS

### Requirement 3: Golden byte-stability across contributors
- **Expected**: Goldens written with `json.dumps(transformed, sort_keys=True, indent=2)` + trailing newline, UTF-8. Regenerating twice back-to-back produces byte-identical files.
- **Actual**: `_write_golden` in `refresh_fixtures.py` uses `json.dumps(transformed, sort_keys=True, indent=2, ensure_ascii=False)` + `"\n"`, `encoding="utf-8"`. `ensure_ascii=False` is an acceptable extension (only affects non-ASCII chars in transformer output, which is pre-rounded numeric data; cannot weaken byte-stability). Two back-to-back runs on shot 249 produced identical output (`diff` exited 0).
- **Verdict**: PASS
- **Notes**: `ensure_ascii=False` is not in the spec's acceptance literal but does not violate it — spec says byte-stability, not a precise kwarg set. The README documents the exact parameters used, so contributors know what to replicate.

### Requirement 4: Regression pytest file
- **Expected**: `mcp/tests/test_shot_regression.py` parametrizes over every `.slog`, runs `parse_binary_shot` then `transform_shot_for_ai`, loads sibling golden, asserts exact deep equality with no float tolerance. `pytest mcp/tests/test_shot_regression.py` exits 0 on clean checkout.
- **Actual**: File exists. Parametrizes over `FIXTURE_DIR.glob("*.slog")` with sorted order, uses `slog_path.stem.zfill(6)` as the shot ID. Missing golden triggers `pytest.fail` with the refresh CLI command. No `try/except` around the transformer call. Calls `assert_equal(expected, transformed, max_mismatches=10)`. Confirmed: 3 tests pass.
- **Verdict**: PASS

### Requirement 5: Custom deep-equality helper with field-path failure messages
- **Expected**: Project-local stdlib-only walker with: list-index path tracking, `isinstance(x, bool)` before numeric checks, distinct messages for type/extra key/missing key mismatch, collect up to N=10 differences before raising. Walker has unit tests covering each case. Running `pytest mcp/tests/test_shot_fixture_walker.py` exits 0.
- **Actual**: `shot_fixture_walker.py` implements all pinned contract branches. Bool guard fires before the `None` and container checks. List length short-circuits without per-element walk. `_MISSING` sentinel used for extra/missing keys. `compare()` collects up to `max_mismatches`. `assert_equal()` raises `AssertionError` with a formatted multi-line message. 12 tests in `test_shot_fixture_walker.py` all pass.
- **Verdict**: PASS
- **Notes**: The spec says 10 pinned test cases (plan.md items i–x); the implementation delivers 12 by splitting test_none_and_none_equal_none_vs_zero_is_type (which covers both `None==None` and `None vs 0` and a missing-key baseline in one function) and adding `test_assert_equal_raises_on_mismatch` + `test_assert_equal_silent_on_match` as bonus wrapper tests. All 10 pinned cases are covered. The two bonus wrapper tests are additive and correct.

### Requirement 6: Refresh CLI with two modes
- **Expected**: Module at `mcp/src/gaggimate_mcp/tools/refresh_fixtures.py`. Default mode regenerates golden from committed `.slog`; errors clearly if `.slog` absent. Fetch mode fetches from device, overwrites `.slog`, regenerates golden; errors on 404 or connection failure. Both modes write goldens per R3 byte-stability.
- **Actual**: Module exists. Default mode: checks `slog_path.exists()`, prints clear error to stderr pointing to `--fetch`, returns 1. Fetch mode: inline `aiohttp.GET` with `padded_id.zfill(6)`, `protocol = "https" if config.use_https else "http"`, `aiohttp.ClientTimeout(total=5.0)`, 404 prints `Error: shot {shot_id} not found on device.`, `aiohttp.ClientError` caught and printed. `asyncio.run(_fetch_bytes(...))` called inside synchronous `main`. Byte-stable writer confirmed. Both acceptance cases (a) and (b) verified: clean exit on committed `.slog`, exit 1 + message on missing `missing_id_xyz`.
- **Verdict**: PASS
- **Notes**: The timeout exception block also catches `asyncio.TimeoutError` separately (added in commit 82f6eb9's "refresh_fixtures now catches asyncio.TimeoutError under the device-unreachable path"). This is a correct hardening — Python 3.11+ `asyncio.TimeoutError` is a subclass of `TimeoutError`, not `aiohttp.ClientError`. The `_TIMEOUT_EXC` tuple with the `py<3.11` fallback is sound.

### Requirement 7: Fixtures README
- **Expected**: `mcp/tests/fixtures/shots/README.md` documents for each fixture: origin shot_id, profile name, coffee (if known), archetype slot, rationale, substitution note. Also covers (a) test invocation, (b) both refresh workflows, (c) exact-equality contract + pre-rounding invariant, (d) byte-stability convention, (e) Python minor-version note.
- **Actual**: README exists. Per-fixture subsections present for 249, 246, 247 with all required fields. (a) Test invocation `cd mcp && pytest tests/test_shot_regression.py` present. (b) Both refresh modes documented with commands and use-case descriptions. (c) Exact-equality contract + pre-rounding invariant section present. (d) Byte-stability convention section present with the exact `json.dumps` call. (e) Python minor-version note (Python 3.13.x) present. Diversity summary section present. Archive section present. Walker contract surprises section present (bonus, additive).
- **Verdict**: PASS

### Requirement 8: Fixture selection — pragmatic with diversity floor
- **Expected**: Three archetype slots: (a) healthy bloom-slide, (b) decline/diverse alternate, (c) BT-artifact or diverse alternate if none available. Diversity floor: 2+ distinct profile types AND 2+ distinct coffee origins (or same-origin with meaningful dose/grind diversity). Minimum count ≥ 3. Private-repo archive byte-identical copy for each `.slog`.
- **Actual**: Three fixtures selected. 249 = healthy bloom-slide (archetype a, Shot 170 evicted — documented substitution). 246 = Adaptive v2 diverse alternate (archetype b — no decline shot survived 1.8.0 eviction, documented). 247 = BT-artifact candidate (archetype c label — weight=0 under positive flow, transformer does not emit explicit flag so labeled "candidate", documented). Profile-type diversity: Tropical Bloom (5-phase bloom) vs Adaptive v2 (6-phase adaptive/lever) = 2 distinct types. Coffee-origin diversity: floor (ii) explicitly relaxed by user per Task 5a feasibility gate — all device shots 245–249 have empty `bean_type`/`dose_in`/`dose_out` sidecars due to 1.8.0 eviction. README documents the relaxation explicitly in the Diversity summary section. Archive: all three `.slog` files byte-identical to `{private-data-repo}/mcp-data/shot-archive/` copies — verified via `filecmp.cmp` (returned `True`). `.data-repo-path` present at project root; archive step was executed.
- **Verdict**: PARTIAL
- **Notes**: The floor (i) profile-type diversity is satisfied (Tropical Bloom + Adaptive v2). Floor (ii) coffee-origin/dose-grind diversity is not satisfied and was explicitly relaxed with user authorization and documented in the README. This is the documented escalation path from the spec itself (R8 says "the implementer notes the skip in the README" — in this case, the full relaxation rationale is documented). Rated PARTIAL rather than PASS because the letter of R8's diversity floor is not met, even though the escalation and documentation are fully compliant with the spec's process. This is an expected, accepted gap with no action required.

### Requirement 9: CI follow-up note in PR description
- **Expected**: PR description includes a short "Follow-up" note recommending `mcp/tests/test_shot_regression.py` and `mcp/tests/test_shot_fixture_walker.py` be gated once CI is added. Acceptance is session-dependent: no grep-able artifact required.
- **Actual**: No GitHub PR was created — commits went directly to main branch. No `gh pr create` invocation found in session artifacts. The spec's acceptance criterion is "session-dependent: the PR description carries the follow-up note. No grep-able artifact file required." The CI follow-up intent is documented in the research artifact and plan.md, but not in a formal PR description field. The backlog item `016-shot-fixture-regression-harness.md` itself carries the original note "if none exists, note that in the epic and flag as a follow-up" in its acceptance criteria.
- **Verdict**: PARTIAL
- **Notes**: Since there is no PR object, the delivery vehicle for the CI follow-up note is absent. The intent is reflected in `lifecycle/shot-fixture-regression-harness/research.md` ("No CI wiring in this ticket: flag as follow-up in the epic, per AC") and `plan.md` Scope Boundaries ("The PR description carries a follow-up note"), but neither is a PR description in the sense R9 requires. This gap is acknowledged: the spec itself calls the acceptance "session-dependent" with no required grep-able artifact — a pragmatic concession that the CI note is informational only and its absence does not affect the harness's functional correctness.

## Requirements Drift

**State**: none
**Findings**:
- None
**Update needed**: None

## Stage 2: Code Quality

- **Naming conventions**: Consistent throughout. `shot_fixture_walker.py` (no `test_` prefix so pytest skips collection), `test_shot_fixture_walker.py`, `test_shot_regression.py`, `refresh_fixtures.py` all follow the project's `snake_case` conventions. `_MISSING`, `_walk`, `_write_golden`, `_fetch_bytes`, `_resolve_fixture_dir` are correctly prefixed as private. `gaggimate_mcp.tools` namespace convention is set by `refresh_fixtures.py` as the first occupant — synchronous `main(argv: list[str]) -> int` entry point, `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`, argparse for flags, async via `asyncio.run(...)`. This matches the spec's Technical Constraints exactly.

- **Error handling**: All failure paths in `refresh_fixtures.py` print to stderr and return a non-zero integer — no exceptions escape `main`. The `aiohttp.ClientError` catch is correct and covers connection failures. The `_TIMEOUT_EXC` tuple correctly handles both Python 3.10 (`asyncio.TimeoutError` only) and 3.11+ (`TimeoutError` added as superclass). The `try/except Exception` around parse/transform is appropriately broad for a CLI tool — surfaces the message without a traceback. In the regression test, no `try/except` wraps the transformer call, so exceptions propagate cleanly per spec.

- **Test coverage**: All 10 plan.md pinned test cases present in `test_shot_fixture_walker.py`. The two bonus tests (`test_assert_equal_raises_on_mismatch`, `test_assert_equal_silent_on_match`) exercise the `assert_equal` wrapper separately from `compare`, which is correct since `assert_equal` is a distinct public API. Walker LOC (113 lines including docstring, imports, and all helpers) is slightly above the 50–80 LOC budget from plan.md but the extra lines are the `_format_mismatch` and `assert_equal` helpers — additive value, not bloat. Regression test covers 3 fixtures with distinct profiles and structural properties.

- **Pattern consistency**: `refresh_fixtures.py` correctly follows the inline-aiohttp pattern from plan.md Task 3 veto surface rather than modifying `api/http.py`. The five behaviors from `api/http.py:103-156` are faithfully duplicated: `zfill(6)`, URL construction from `GaggimateConfig`, 5s timeout, 404 handling, `ClientError` wrapping. The `_resolve_fixture_dir` walker (walking up from `__file__` to find the `mcp/` directory) is robust for both installed and editable installs. The `fixture_dir.mkdir(parents=True, exist_ok=True)` guard in `main` is correct — creates the directory if missing without erroring on subsequent runs. No existing files in `mcp/` were modified, consistent with the spec's "purely additive" scope.

## Verdict

```json
{"verdict": "APPROVED", "cycle": 1, "issues": ["R8 coffee-origin diversity floor not met (user-authorized relaxation, documented in README)", "R9 CI follow-up note not in a PR description (no PR created; intent captured in lifecycle artifacts only)"], "requirements_drift": "none"}
```
