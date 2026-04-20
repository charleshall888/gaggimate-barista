# Plan: shot-fixture-regression-harness

## Overview

Purely additive harness in the `mcp/` package: a stdlib-only deep-equality walker + its unit tests, a `gaggimate_mcp.tools.refresh_fixtures` CLI with default/`--fetch` modes (inline HTTP — no modification of `api/http.py`), three `.slog` + `.golden.json` fixture pairs captured from device history after an explicit feasibility pre-flight, a parametrized pytest that asserts exact equality against goldens, a fixtures README, and a private-repo archive copy. The harness touches zero existing files in the main repo.

## Tasks

### Task 1: Deep-equality walker module
- **Files**: `mcp/tests/shot_fixture_walker.py` (new)
- **What**: Provide a stdlib-only recursive comparator that asserts exact equality on nested dict/list structures, surfacing up to 10 mismatches with full field paths on failure. Consumed by Task 4's regression test.
- **Depends on**: none
- **Complexity**: simple
- **Context**:
  - Public API: `compare(expected, actual, max_mismatches: int = 10) -> list[Mismatch]` returning an empty list on full match, or up to N `Mismatch` instances. A sibling `assert_equal(expected, actual, max_mismatches: int = 10) -> None` wrapper raises `AssertionError` with a formatted multi-line message when the list is non-empty.
  - `Mismatch` dataclass fields: `path: str`, `kind: Literal["value", "type", "length", "extra_key", "missing_key"]`, `expected: object`, `actual: object`.
  - Module-level sentinel: `_MISSING = object()`. Used in `Mismatch.expected` (for `"extra_key"`) or `Mismatch.actual` (for `"missing_key"`) to signal absence distinctly from `None`.
  - **Path notation**: dict keys joined with `.` (e.g., `summary.avg_pressure_bar`); list indices as `[N]` (e.g., `phases[1].samples[12].weight_flow_g_s`). Root path is empty string `""`.
  - **Traversal order (pinned)**: depth-first. For dicts: iterate keys in `sorted(expected.keys())` order, recurse into each; then iterate extra keys from actual in `sorted(actual.keys() - expected.keys())` order and emit `"extra_key"` for each. For lists: iterate in index order (0..N-1).
  - **Type-equality rules (pinned)**:
    - `isinstance(x, bool)` check comes **before** `isinstance(x, (int, float))` on both sides — `True == 1` is a `"type"` mismatch.
    - `None` is a first-class value; `None == None` matches, `None == 0` is `"type"`, `None == _MISSING` is NOT equal (handled via `"extra_key"`/`"missing_key"` kinds, not `"type"`).
    - Container-category mismatch: if one side is `dict` and the other is `list` (or any `isinstance` category diff), emit `"type"` mismatch at the current path; do NOT recurse.
  - **List length rule (pinned, short-circuit)**: if `len(expected) != len(actual)`, emit ONE `"length"` mismatch at the list's path with `expected=len(expected)`, `actual=len(actual)`, and do NOT walk per-element. Rationale: positional drift (one element inserted mid-list) would otherwise cascade into `N - index` value mismatches and drown the actual signal at the `max_mismatches=10` cap.
  - **Float rule (pinned)**: use `==` only. No tolerance. Transformer pre-rounds all numeric output to 1 d.p. (summary stats) or 2 d.p. (RMSE/compliance); any float tolerance < 0.01 is a phantom guard and 0.01 would hide real regressions.
  - **Recursion cutoff (pinned)**: the walker returns immediately when the mismatch list length reaches `max_mismatches`. Do not finish the current container; callers that need a complete picture can pass a higher `max_mismatches` value.
  - **Invariants assumed about transformer output (not enforced by the walker)**: output is NaN-free (RMSE uses `None` for insufficient-sample cases per `transformers/shot.py:285-287`; other float sinks are `round()` of non-NaN inputs), tuple-free (TypedDict fields are typed as `list`), and free of `-0.0` (all outputs are positive quantities — pressures, flow rates, durations, bar-seconds). If any of these are violated in the future, the regression test will surface the drift but the failure message may be counterintuitive (`NaN != NaN` → `"value"` mismatch; `-0.0 == 0.0` under `==` but their JSON `repr` differs, which would fail Task 8c byte-stability with a `diff` that looks clean to the walker). Document this in the README.
  - **Formatted failure message**: one line per mismatch. Examples:
    - Value: `phases[1].samples[12].weight_flow_g_s: expected 2.14, got 2.09`
    - Type: `summary.rmse_bar: expected float, got NoneType`
    - Length: `phases[1].samples: expected length 200, got length 201`
    - Extra key: `extra key in actual: summary.debug_flag`
    - Missing key: `missing key in actual: summary.rmse_bar`
  - LOC budget: target 50–80 lines for the walker itself. Stdlib only. No `dataclasses.asdict`, no `typing.get_type_hints` runtime lookup.
- **Verification**: interactive/session-dependent — this file is exercised by Task 2's unit tests; no meaningful standalone check exists until Task 2 runs.
- **Status**: [x] complete

### Task 2: Walker unit tests
- **Files**: `mcp/tests/test_shot_fixture_walker.py` (new)
- **What**: Cover every pinned branch of the walker's contract so regressions in the comparator itself are caught before they mask regressions in the transformer.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**:
  - Test cases required (each is a discrete `def test_*()`):
    - (i) Identical nested structures → empty mismatch list.
    - (ii) Single scalar-value mismatch at a nested path (e.g., `phases[1].samples[12].weight_flow_g_s: 2.14 → 2.09`) → exactly one `"value"` Mismatch with the correct `[N]` / `.key` path. **This is the core drift-detection proof.**
    - (iii) The `True == 1` / `False == 0` trap → `"type"` mismatch, not silent pass.
    - (iv) Extra key in actual → `"extra_key"` Mismatch with `expected is _MISSING` and `actual` equal to the value found at that key.
    - (v) Missing key in actual → `"missing_key"` Mismatch with `expected` equal to the value from expected and `actual is _MISSING`.
    - (vi) List length mismatch (e.g., `expected=[1,2,3]`, `actual=[1,2,3,4]`) → exactly one `"length"` Mismatch at the list's path with `expected=3, actual=4`. Per-element walk does NOT occur — assert that (e.g., no secondary mismatches emitted even if index-3 element would match nothing).
    - (vii) `None` vs `None` → equal; `None` vs `0` → `"type"` mismatch; `None` vs `_MISSING` handled via `"missing_key"`/`"extra_key"` per (iv)/(v), not `"type"`.
    - (viii) Deeply nested mismatch path formatting: verify path string equals `phases[1].samples[12].weight_flow_g_s` for a drift at that location.
    - (ix) Collect-through-N=10 with mid-recursion cutoff: inject a tree with 15 separable mismatches (e.g., 15 dict keys all with wrong values under a single top-level key), assert `len(compare(..., max_mismatches=10)) == 10`. Pin the specific 10 returned by construction (since traversal order is now deterministic under sorted keys) and assert their paths — this catches accidental reordering in a future refactor.
    - (x) Container-category mismatch (e.g., `expected={"a": 1}`, `actual=[1]`) → one `"type"` mismatch at the parent path; NO recursion into either side.
  - Follows existing test style in `mcp/tests/test_transformers_shot.py` (pytest `def test_*()` functions, direct `==` assertions on `Mismatch` fields, no fixtures or parametrize unless natural).
- **Verification**: `cd mcp && pytest tests/test_shot_fixture_walker.py -v` — pass if exit 0 and all ten cases pass.
- **Status**: [x] complete

### Task 3: Refresh CLI module
- **Files**: `mcp/src/gaggimate_mcp/tools/refresh_fixtures.py` (new) — ONLY this file. Do NOT modify `mcp/src/gaggimate_mcp/api/http.py`.
- **What**: Implement the default + `--fetch` workflows for (re)generating fixture pairs. Uses inline `aiohttp` in fetch mode to preserve the spec's "purely additive" scope. Sets the convention for the currently-empty `gaggimate_mcp.tools` namespace.
- **Depends on**: none
- **Complexity**: simple
- **Context**:
  - Entry point: synchronous `main(argv: list[str]) -> int` with `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`.
  - Argparse surface: one positional `shot_id: str`, one flag `--fetch` (store_true). No other flags.
  - Fixture directory resolved relative to the repo root: `mcp/tests/fixtures/shots/`. Resolution strategy: walk up from `__file__` to locate the `mcp/` directory, then append `tests/fixtures/shots/`. Create the directory if missing.
  - **Default mode** (no `--fetch`): read `{fixture_dir}/{shot_id}.slog`. If absent, print error to stderr pointing to `--fetch` and return 1. If present: `data = path.read_bytes(); shot = parse_binary_shot(data, shot_id.zfill(6)); transformed = transform_shot_for_ai(shot)`. Write `{fixture_dir}/{shot_id}.golden.json` per the byte-stable writer below.
  - **Fetch mode** (`--fetch`): obtain raw `.slog` bytes from the device via inline `aiohttp.GET`. Do NOT extract a helper in `api/http.py`; do NOT call `GaggimateHTTPClient.fetch_shot` (it pre-parses). The inline implementation must faithfully duplicate the following five behaviors from `api/http.py:103-156`:
    1. `padded_id = shot_id.zfill(6)` — canonical-ID normalization.
    2. URL construction: `url = f"{protocol}://{host}/api/history/{padded_id}.slog"` where `protocol = "https" if config.use_https else "http"` and `host, use_https` come from `GaggimateConfig()` (import from `gaggimate_mcp.config`).
    3. Timeout: `aiohttp.ClientTimeout(total=5.0)`.
    4. HTTP 404 → print `Error: shot {shot_id} not found on device.` and return 1.
    5. `aiohttp.ClientError` → print `Error: device unreachable: {exc}` and return 1.
    Non-200 non-404 status → print `Error: HTTP {status}: {reason}` and return 1.
  - Wrap the async `aiohttp` call via `asyncio.run(_fetch_bytes(shot_id))` inside `main`; do not make `main` async. The `_fetch_bytes` coroutine is a 10–15 line private helper in the same module.
  - After successful byte retrieval: write bytes to `{fixture_dir}/{shot_id}.slog` (overwriting), then parse + transform + write golden as in default mode.
  - **Byte-stable golden writer**: `body = json.dumps(transformed, sort_keys=True, indent=2, ensure_ascii=False); path.write_text(body + "\n", encoding="utf-8")`. The trailing newline and UTF-8 encoding are load-bearing for R3 byte-stability.
  - Error reporting: any failure prints a concise one-line message to stderr (`print(..., file=sys.stderr)`) and returns non-zero. No tracebacks escape `main`.
  - Additional error cases:
    - Default mode, `.slog` missing: `Error: mcp/tests/fixtures/shots/{shot_id}.slog not found. Use --fetch to capture from device.` → exit 1.
    - Parse/transform exception: propagate the exception message as `Error: failed to process {shot_id}: {exc}` → exit 1.
  - Imports available: `parse_binary_shot` from `gaggimate_mcp.parsers.shot`, `transform_shot_for_ai` from `gaggimate_mcp.transformers.shot`, `GaggimateConfig` from `gaggimate_mcp.config`, `aiohttp` directly.
- **Verification**: `cd mcp && python -m gaggimate_mcp.tools.refresh_fixtures --help` — pass if exit 0 and the help text lists the `shot_id` positional and `--fetch` flag.
- **Status**: [x] complete

### Task 4: Regression test file
- **Files**: `mcp/tests/test_shot_regression.py` (new)
- **What**: Parametrize over every `.slog` file in `mcp/tests/fixtures/shots/` and assert that `transform_shot_for_ai(parse_binary_shot(bytes, id))` matches the sibling `.golden.json` via the Task 1 walker.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**:
  - Fixture directory path: resolve via `pathlib.Path(__file__).parent / "fixtures" / "shots"`.
  - Parametrize: `@pytest.mark.parametrize("slog_path", sorted(FIXTURE_DIR.glob("*.slog")), ids=lambda p: p.stem)`. If the directory is empty or absent, the parametrize list is empty and pytest emits no tests — this is intentional per spec Edge Cases.
  - Test body shape:
    1. Read `.slog` bytes and the companion golden path `slog_path.with_suffix(".golden.json")`.
    2. If the golden is missing: `pytest.fail(f"Missing golden: {golden_path} — regenerate via 'python -m gaggimate_mcp.tools.refresh_fixtures {slog_path.stem}'.")`.
    3. Call `parse_binary_shot(bytes, slog_path.stem.zfill(6))` then `transform_shot_for_ai(shot)`.
    4. Load the golden: `expected = json.loads(golden_path.read_text(encoding="utf-8"))`.
    5. Call `assert_equal(expected, transformed, max_mismatches=10)` from the walker. The assertion failure message handles all field-path reporting.
  - No `try`/`except` around the transformer call — exceptions propagate as-is.
  - No golden-refresh logic in this test file. Refresh is owned exclusively by Task 3's CLI.
- **Verification**: `cd mcp && pytest tests/test_shot_regression.py --collect-only` — pass if exit 0 (collection succeeds regardless of fixture count; functional verification lands in Task 8 after fixtures exist).
- **Status**: [x] complete

### Task 5a: Fixture feasibility pre-flight
- **Files**: none (inventory and selection analysis; outputs working notes for Task 5b and Task 6)
- **What**: Before any fetch, enumerate available shot sources and verify the diversity floor is meetable. Escalate to the user with a specific decision surface if it is not, rather than silently relaxing the floor or fabricating diversity during capture.
- **Depends on**: [3]
- **Complexity**: complex
- **Context**:
  - **Source A — device history**: call the MCP tool `list_recent_shots` with `limit=40` to enumerate the current device shot pool. For each candidate, note: `shot_id`, profile name, coffee metadata (may be `None` if the sidecar was purged by 1.8.0's free-space floor — see CLAUDE.md "Firmware 1.8.0 semantic traps"), presence of weight anomalies in the transformer output (`unstable_weight` flag or `weight_anomalies` list).
  - **Source B — private-repo archive**: if `.data-repo-path` exists at the project root, list `{private-data-repo}/mcp-data/shot-archive/*.slog`. This is expected to be empty on the first run of this ticket (the archive is populated by Task 7), but it may contain fixtures from a prior partial run or manual archive.
  - **Archetype slot targets (spec R8)**:
    - (a) Healthy bloom-slide — target Shot 170 (Choco Coffee Hacienda La Papaya Typica Anaerobic, 5★ balanced, currently dialed-in per session memory). If evicted, substitute the nearest dialed-in bloom-slide shot.
    - (b) Pre-bloom-era / decline-profile shot — search for any shot using a decline profile (no bloom phase, higher peak pressure). Session memory notes PERC Ethiopia Chelchele at 14E on an old declining-pressure profile; this is unlikely to have survived eviction given ~4 subsequent coffees, but check before concluding.
    - (c) BT-scale-artifact shot — scan transformer outputs for `unstable_weight` or `weight_anomalies`. If none exist, OMIT rather than substitute a healthy shot labeled as (c); select a "diverse alternate" (different profile family or coffee origin from (a) and (b)) and plan to label it as "diverse alternate" in the README.
  - **Diversity floor (mandatory, spec R8)**: the three selected fixtures must jointly satisfy (i) 2+ distinct profile types, (ii) 2+ distinct coffee origins OR same origin with meaningfully different dose/grind, (iii) count ≥ 3.
  - **Feasibility gate**: after inventory, verify the floor is satisfiable across the union of Source A + Source B. If NO combination of three available shots satisfies all three floor constraints, STOP. Surface to the user:
    - What was found (brief table: candidate count by profile type, by origin).
    - Which floor constraint cannot be met and why (e.g., "only 1 profile type available on device; sidecars for shots older than 2026-03-15 appear purged so coffee-origin metadata is unknown for 12 of 14 candidates").
    - Three explicit options to choose from: (A) relax the diversity floor for this ticket, document the relaxation in the README, proceed; (B) pull a fresh shot on a different profile/coffee to meet the floor (contradicts spec R8's no-hardware-session rule — requires user authorization); (C) defer the ticket until inventory is richer.
    - Do NOT proceed to Task 5b without an explicit user decision.
  - **On feasibility pass**: record the selected 3 shot_ids + archetype assignments + rationale for each (including any substitution or omission vs the ticket's named candidates) in working notes. These notes are the input to Task 5b's fetches and Task 6's README sections.
  - **No hardware sessions** (spec R8): do not ask the user to pull a fresh shot, run an old profile, or induce BT artifacts as part of pre-flight — only as an option surfaced IF feasibility fails.
- **Verification**: session-dependent — the output is a selection decision (three shot_ids + rationale) or an escalation prompt. No grep-able artifact is produced; verification is that Task 5b has a concrete list of IDs to fetch OR the user has chosen to defer/relax/authorize-hardware-session per the feasibility-gate options.
- **Status**: [x] complete — selected 249 (healthy bloom-slide), 246 (adaptive diverse alternate), 247 (BT-artifact: weight=0 with positive flow); user relaxed (ii) origin/dose-grind floor given sidecar-metadata absence.

### Task 5b: Capture selected fixtures
- **Files**: `mcp/tests/fixtures/shots/<id_a>.slog`, `mcp/tests/fixtures/shots/<id_a>.golden.json`, `mcp/tests/fixtures/shots/<id_b>.slog`, `mcp/tests/fixtures/shots/<id_b>.golden.json`, `mcp/tests/fixtures/shots/<id_c>.slog`, `mcp/tests/fixtures/shots/<id_c>.golden.json` (six files, new; IDs determined by Task 5a)
- **What**: Run `refresh_fixtures --fetch <id>` for each selected ID from Task 5a to produce the `.slog` + `.golden.json` pairs.
- **Depends on**: [5a]
- **Complexity**: simple
- **Context**:
  - Device connectivity required. `GAGGIMATE_HOST` must resolve.
  - For each of the three shot_ids recorded in Task 5a's working notes: run `cd mcp && python -m gaggimate_mcp.tools.refresh_fixtures <id> --fetch`. Confirm each command exits 0 and produces both files.
  - If any shot_id is drawn from Source B (private-repo archive) rather than Source A (device history): copy the `.slog` from `{private-data-repo}/mcp-data/shot-archive/<id>.slog` to `mcp/tests/fixtures/shots/<id>.slog`, then run `refresh_fixtures <id>` (default mode, no `--fetch`) to generate the golden from the archive bytes.
  - Do NOT induce BT artifacts, run old profiles, or pull new shots unless the user explicitly authorized hardware sessions via the Task 5a feasibility gate.
- **Verification**:
  (a) `ls mcp/tests/fixtures/shots/*.slog | wc -l` returns ≥ 3 — pass if ≥ 3.
  (b) `python -c "import pathlib; p=pathlib.Path('mcp/tests/fixtures/shots'); print(all((p/(s.stem+'.golden.json')).exists() for s in p.glob('*.slog')))"` prints `True` — pass if output is `True`.
- **Status**: [x] complete

### Task 6: Fixtures README
- **Files**: `mcp/tests/fixtures/shots/README.md` (new)
- **What**: Document per-fixture provenance, the diversity summary, test invocation, both refresh workflows, the exact-equality contract, byte-stability convention, the walker's pinned contract, and the Python minor-version note.
- **Depends on**: [5b]
- **Complexity**: simple
- **Context**:
  - Required sections (spec R7 items (a)–(e) plus R8 per-fixture detail, plus walker contract surfaced from Task 1):
    - Header: one-paragraph purpose statement — this is the checked-in regression surface for the shot-analysis pipeline.
    - **Fixtures**: one subsection per fixture. Include: origin `shot_id`, profile name, coffee name (from session memory / user-setup if known), archetype slot (bloom-slide / decline / BT-artifact / diverse alternate), rationale for this specific shot, substitution or omission note if different from the ticket's named candidates.
    - **Diversity summary**: one sentence confirming the profile-type distribution and coffee-origin distribution across the three fixtures. If the floor was relaxed per Task 5a's feasibility-gate escalation, document the relaxation and the user's rationale here explicitly.
    - **Running the test**: exact command `cd mcp && pytest tests/test_shot_regression.py`.
    - **Refreshing goldens** — two sub-sections:
      - Default (for transformer changes): `python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>`. Use this when the transformer changes and goldens need to be regenerated from the existing `.slog` bytes. No device required. Review the resulting `.golden.json` diff manually — the pre-rounding invariant means any non-intentional diff is a real regression.
      - `--fetch` (for re-capture): `python -m gaggimate_mcp.tools.refresh_fixtures <shot_id> --fetch`. Use this to initially capture a fixture or replace a `.slog` whose contents need to change. Requires device connectivity.
    - **Exact-equality contract + pre-rounding invariant**: the regression test uses exact `==` on every field. This is sound only because the transformer pre-rounds all numeric output to 1 d.p. (summary stats) or 2 d.p. (RMSE/compliance). Any future change that introduces un-rounded floats will trip this harness — that is intentional, and the reviewer should confirm the rounding invariant before adding a tolerance.
    - **Walker contract surprises**: note the three invariants assumed but not enforced — NaN-free output, tuple-free output, `-0.0`-free output. If a future transformer change violates any of these, the regression failure message may be counterintuitive (`nan != nan` surfaces as a `"value"` mismatch; `-0.0 == 0.0` under `==` but their JSON `repr` differs, which can fail byte-stability while the walker passes). Task 8c (byte-stability) catches the sign-zero case; the walker unit tests catch the NaN case.
    - **Byte-stability convention**: goldens are written as `json.dumps(transformed, sort_keys=True, indent=2)` plus a trailing newline, UTF-8 encoded. Do not reformat goldens with other tools (jq, prettier, IDE auto-format) — any reformatting will break byte-stability.
    - **Python minor-version note**: contributors refreshing goldens should use a Python minor version consistent with the existing goldens (nominally 3.13.x) to avoid cross-version `repr(float)` differences that would break byte-stability even when transformer output is semantically identical.
    - **Archive note**: each `.slog` is also archived at `{private-data-repo}/mcp-data/shot-archive/<shot_id>.slog` as eviction insurance. If `.data-repo-path` was absent when the fixtures were captured, this section says so instead.
- **Verification**:
  (a) `test -f mcp/tests/fixtures/shots/README.md` — pass if exit 0.
  (b) `grep -c 'refresh_fixtures' mcp/tests/fixtures/shots/README.md` — pass if count ≥ 2 (both refresh workflows referenced).
- **Status**: [x] complete

### Task 7: Archive fixtures to private data repo
- **Files**: `{private-data-repo}/mcp-data/shot-archive/<id_a>.slog`, `{private-data-repo}/mcp-data/shot-archive/<id_b>.slog`, `{private-data-repo}/mcp-data/shot-archive/<id_c>.slog` (three files, new external); the main-repo `.slog` files are NOT modified.
- **What**: Copy each committed `.slog` to the private data repo's `mcp-data/shot-archive/` directory as eviction insurance, and commit + push per the CLAUDE.md auto-commit policy.
- **Depends on**: [5b]
- **Complexity**: simple
- **Context**:
  - Read `.data-repo-path` at the project root.
    - If absent: skip the copy entirely. Surface the skip to the user and to the Task 6 README.
    - If present: its contents are the absolute path to the private data repo root.
  - Create `{private-repo}/mcp-data/shot-archive/` if it does not exist.
  - For each `.slog` in `mcp/tests/fixtures/shots/`: copy byte-for-byte to `{private-repo}/mcp-data/shot-archive/<same-name>.slog` (overwrite if present).
  - Auto-commit policy (CLAUDE.md): use separate `Bash` calls, no `cd`, no chaining. Use `--git-dir={private_repo}/.git --work-tree={private_repo}` on every git invocation.
    - `git --git-dir={repo}/.git --work-tree={repo} add mcp-data/shot-archive/*.slog`
    - `git --git-dir={repo}/.git --work-tree={repo} commit -m "Archive shot fixtures for mcp regression harness"`
    - `git --git-dir={repo}/.git --work-tree={repo} push`
  - If `git push` fails: inform the user with the CLAUDE.md message: `Private repo push failed — changes saved locally. Run git push manually in {private_repo_path} when credentials are available.` Do not fail the task.
- **Verification**:
  (a) If `.data-repo-path` exists: `python -c "import pathlib, filecmp; main=pathlib.Path('mcp/tests/fixtures/shots'); archive=pathlib.Path(open('.data-repo-path').read().strip())/'mcp-data/shot-archive'; print(all(filecmp.cmp(main/s.name, archive/s.name, shallow=False) for s in main.glob('*.slog')))"` prints `True` — pass if `True`.
  (b) If `.data-repo-path` does not exist: verify the Task 6 README contains the `.data-repo-path absent` archive note — `grep -c 'archive' mcp/tests/fixtures/shots/README.md` ≥ 1.
- **Status**: [x] complete

### Task 8: End-to-end verification
- **Files**: none (verification-only; no code changes)
- **What**: Confirm the full harness passes and the byte-stability contract holds on real fixtures.
- **Depends on**: [2, 4, 5b, 6, 7]
- **Complexity**: simple
- **Context**:
  - The drift-detection property of the walker is proved hermetically by Task 2 case (ii) + (viii) + (ix) — no production-code mutation is needed at this stage.
- **Verification**:
  (a) `cd mcp && pytest tests/test_shot_fixture_walker.py` — pass if exit 0.
  (b) `cd mcp && pytest tests/test_shot_regression.py` — pass if exit 0 and at least 3 tests collected and passed.
  (c) Byte-stability on a committed fixture: pick any committed shot_id; `cd mcp && python -m gaggimate_mcp.tools.refresh_fixtures <id>; cp tests/fixtures/shots/<id>.golden.json /tmp/a.json; python -m gaggimate_mcp.tools.refresh_fixtures <id>; diff /tmp/a.json tests/fixtures/shots/<id>.golden.json` — pass if `diff` exits 0.
- **Status**: [x] complete — 12 walker tests pass, 3 regression tests pass, byte-stability diff clean on 249.

## Verification Strategy

Full harness works end-to-end when Task 8's three checks all pass:

1. Walker unit tests pass independently (Task 8a) — the comparator's pinned contract holds, including the drift-detection property (case ii), the path-formatting property (case viii), and the count-cutoff property (case ix).
2. Regression test passes against all committed fixtures (Task 8b) — the transformer's current output matches the goldens.
3. Goldens are byte-stable across back-to-back refresh runs (Task 8c) — contributors on the same Python minor version will produce identical diffs.

Additional passive verification:
- `.data-repo-path`-gated archive copies exist at `{private-repo}/mcp-data/shot-archive/` (Task 7 verification).
- README documents both refresh modes, the exact-equality contract, the pre-rounding invariant, walker contract surprises (NaN / sign-zero / tuple), byte-stability, and the Python minor-version note (Task 6 verification).

## Veto Surface

- **Walker module location**: `mcp/tests/shot_fixture_walker.py` (no `test_` prefix so pytest does not collect it as a test). Alternatives considered: `mcp/tests/_walker.py` or promotion to `mcp/src/gaggimate_mcp/testing/`. Current placement keeps the helper scoped to `tests/`.
- **Task 3 HTTP path pinned to inline-aiohttp**: originally let the implementer choose between inline and refactoring `GaggimateHTTPClient.fetch_shot` to extract a `fetch_shot_bytes` helper. Pinned to inline to honor the spec's "purely additive" commitment and avoid pulling existing-file regression-test scope into this ticket. If you prefer the refactor path (cleaner long-term, but adds behavior-preservation acceptance criteria), say so before implementation begins.
- **Fixture count at exactly 3**: the spec sets the minimum at ≥ 3, and research recommends exactly 3 to minimize refresh churn for ticket 015. If you want broader coverage (e.g., 4–5 fixtures to add more exit-reason diversity for 018), speak up.
- **Drift-detection proof moved from Task 8 to Task 2**: originally Task 8 included a step (8d) that injected `+ 0.01` into the transformer to verify the harness catches drift. Removed because (i) the property is already proved hermetically by Task 2 case (ii) + (viii), and (ii) mutating production code and relying on prose-only revert is operationally fragile (sandbox interruption, auto-commit collision, formatter hooks). If you want the end-to-end drift-injection check back, the safer approach is a separate one-off test fixture that feeds a deliberately-drifted golden through the regression test and asserts the walker complains — without touching the transformer.
- **Task 5 split into 5a (feasibility pre-flight) and 5b (capture)**: originally a single task. Split because the diversity floor (2+ profiles, 2+ origins) may be un-meetable given recent bloom-slide-exclusive dialing and 1.8.0's sidecar purging on capacity eviction. 5a now has an explicit escalation path if feasibility fails. If you would rather have the implementer silently relax the floor and proceed, say so.

## Scope Boundaries

Excluded from this feature (mirrors spec Non-Requirements):

- **No new dev dependencies.** No `syrupy`, `pytest-regressions`, `DeepDiff`, `recursive-diff`, or `numpy.testing`. The walker is hand-rolled.
- **No JS-reference sidecars.** Ticket 018 owns that capture mechanism entirely.
- **No `manage_shot_notes` testing.** Ticket 014's scope.
- **No CI pipeline creation.** The PR description carries a follow-up note; no `.github/workflows/`, `Makefile`, `tox.ini`, pre-commit, or git hooks are added.
- **No snapshot library or `--snapshot-update` flag.** Refresh is always explicit via the CLI module.
- **No replacement of `test_parsers_shot.py` / `test_transformers_shot.py`.** They continue to cover synthetic in-memory inputs; this harness adds real-data coverage alongside.
- **No hardware sessions by default.** No running old profiles, no inducing BT artifacts, no pulling new shots to satisfy an archetype — unless the user explicitly authorizes via the Task 5a feasibility-gate escalation.
- **No fixture eviction/rotation policy.** Once committed, fixtures stay until intentionally replaced.
- **No attempt to preserve pre-upgrade (1.7.3) shots for ticket 021.** Firmware wipes shot history on upgrade; 021's BLE-precision sub-question is definitionally unanswerable from device data.
- **No float tolerance in the regression test.** Exact equality only, guarded by the pre-rounding invariant.
- **No modification of any existing file in the main repo.** Specifically: parser, transformer, `server.py`, existing tests, AND `api/http.py` are all untouched. The spec's Changes to Existing Behavior says "No existing parser, transformer, `server.py`, or test file is modified"; this plan extends that to `api/http.py` by pinning Task 3 to inline-aiohttp (see Veto Surface).
- **No Python minor-version enforcement.** The README advises contributors to use a consistent Python minor (nominally 3.13.x); no programmatic pre-flight check is added. If cross-version drift becomes a recurring friction point, that would be a follow-up ticket.
- **No drift-injection into production code at verification time.** The drift-detection property is proved hermetically in the walker unit tests (Task 2).
