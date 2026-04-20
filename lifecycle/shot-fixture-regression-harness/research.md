# Research: Shot-fixture regression harness

## Epic Reference

Ticket 016 is a child of epic 013 (Gaggimate firmware 1.7.3 → 1.8.0 upgrade adaptation). The epic's research artifact at `research/gaggimate-1-8-0-upgrade/research.md` flagged this harness as the missing safety net behind tickets 015 (weight-flow surfacing), 018 (DDSA algorithm port), and 021 (BLE-precision drift investigation) — all three risk silent regression on historical-shot diagnosis if the transformer is modified without fixture-based validation. This research scopes strictly to the harness; cross-ticket concerns live in the epic artifact.

---

## Codebase Analysis

### Files that will be created or modified

- **`mcp/tests/fixtures/shots/`** (new directory) — location for `.slog` fixture inputs + `.golden.json` outputs + README.
- **`mcp/tests/fixtures/shots/<shot_id>.slog`** × ≥3 — binary fixture files copied from device via the existing HTTP path (`/api/history/{padded_id}.slog`).
- **`mcp/tests/fixtures/shots/<shot_id>.golden.json`** × ≥3 — checked-in golden output of `transform_shot_for_ai(parse_binary_shot(...))`.
- **`mcp/tests/fixtures/shots/README.md`** (new) — fixture provenance, rationale, regeneration procedure.
- **`mcp/tests/test_shot_regression.py`** (new, per AC) — pytest that runs the parser + transformer on each fixture and asserts deep equality against the golden, with 1e-6 float tolerance.
- **`mcp/src/gaggimate_mcp/tools/refresh_fixtures.py`** (new, optional) — CLI entry point for regenerating goldens: `python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>`. The tools namespace exists but is currently empty (only `__init__.py`).

### Relevant existing patterns

- **Pipeline entry points**:
  - `mcp/src/gaggimate_mcp/parsers/shot.py:127` — `parse_binary_shot(data: bytes, shot_id: str) -> ShotData`
  - `mcp/src/gaggimate_mcp/transformers/shot.py:449` — `transform_shot_for_ai(shot: ShotData) -> TransformedShot`
  - `mcp/src/gaggimate_mcp/api/http.py:103` — `fetch_shot(shot_id)` performs HTTP fetch → parse, used by `analyze_shot` in `server.py:458`.
- **Output types**: `TransformedSample`, `ShotSummary`, `TransformedShot` are **TypedDict** (not Pydantic) — declared in `transformers/shot.py:14-97`. This matters because TypedDict serializes via stdlib `json.dumps` directly.
- **Rounding convention**: all numeric outputs are explicitly pre-rounded — `round(x * 10) / 10` (1 d.p. for summary stats) or `round(x, 2)` (2 d.p. for RMSE/compliance). See `transformers/shot.py:239, 250, 285-287, 296-299`. This is the core reason deep-equality goldens are viable: the transformer does not leak raw float drift into its output.
- **Existing tests**: `mcp/tests/test_parsers_shot.py` and `test_transformers_shot.py` build inputs in-memory via `struct.pack` — there is no file-based fixture precedent. Tests use direct `==` equality on pre-rounded floats; no `pytest.approx` or `math.isclose` in use today. No `conftest.py`.

### Integration points and dependencies

- **Full call chain** for the harness: `<shot_id>.slog bytes → parse_binary_shot → ShotData → transform_shot_for_ai → TransformedShot (TypedDict) → json.dumps`. The harness bypasses the HTTP fetch layer entirely and reads bytes from disk.
- **`list_recent_shots` and `analyze_shot`** reach the same transformer via the HTTP path — replacing bytes from disk vs bytes from HTTP is the only substitution needed for offline fixture runs.
- **No pytest fixtures shared across tests today** — the new test file can be self-contained or introduce a minimal `conftest.py` scoped to `mcp/tests/fixtures/shots/`.

### Non-determinism findings (critical for 1e-6 tolerance)

Audit of `parsers/shot.py` and `transformers/shot.py`:

- **No `random`, no `datetime.now()`, no hash-dependent iteration, no threading.** Timestamps are read from the `.slog` header as Unix ints and passed through unchanged.
- **Dict insertion order is stable** — TypedDict + Python 3.13 (project requires `>=3.13` per `mcp/pyproject.toml:9`) guarantees insertion-order preservation.
- **All floats are pre-rounded** before assignment to output fields. The only floating-point computations that escape direct rounding are `sqrt()` in the RMSE calculation (`transformers/shot.py:239`) and accumulation loops in `calculate_total_volume` (`transformers/shot.py:99-116`); both are consumed by a `round(..., 2)` or `round(x*10)/10` sink immediately.
- **Consequence**: byte-stable goldens are achievable. `json.dumps(transformed, sort_keys=True, indent=2)` produces deterministic output. The 1e-6 tolerance in the AC is insurance against pathological cross-platform `sqrt()` ULP drift, not a required capability under current transformer code.

### `gaggimate_mcp.tools/` namespace convention

`mcp/src/gaggimate_mcp/tools/__init__.py` exists but is empty. No existing CLI-style modules. A new `refresh_fixtures.py` would be the first occupant. Recommended shape: plain `main(shot_id: str)` synchronous function (device fetch can reuse the async `http.fetch_shot` but the fixture write step is sync), invoked via `python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>`. No argparse needed for a 1-arg script; `sys.argv[1]` is fine.

### Sibling ticket impact on golden schema

- **Ticket 015 (weight-flow surfacing)** adds three fields per the ticket body: `weight_flow_g_s` to `TransformedSample`, plus `peak_weight_flow_g_s`, `avg_weight_flow_g_s`, `time_to_first_nonzero_weight_flow_s` to `FlowSummary`. 015's own AC states: "fixture-based test asserts transformer output matches golden values for all three added fields on each of 016's fixture shots. No 'manual validation acceptable' escape hatch." **015 therefore expects per-sample TransformedSample goldens.**
- **Ticket 018 (DDSA port)** does not modify `TransformedShot` output. It produces a separate `PhaseExitReason` stream tested against reference-JS JSON sidecars (`.reference-js.json`) captured during 016 OR 018. Per 018's AC: "For each of 016's fixture shots, a reference-js JSON exists alongside (captured via the prerequisite above)." Whether 016 captures those sidecars or 018 does is an open scope question.
- **Ticket 021** needs a pre-upgrade (firmware 1.7.3) shot paired against a post-upgrade (1.8.0) shot of the same coffee/grind/dose for BLE-precision drift comparison. User upgraded ~2026-04-01. Capacity-based retention (500KB floor) may have already evicted pre-upgrade `.slog` files; 021's body acknowledges this and documents the "unanswerable" outcome. **Implication for 016**: if any pre-upgrade shot survives, candidate (b) should probably be that shot, not just "a decline-profile-era shot."

### CI-adjacent findings

No `.github/workflows/`, no `Makefile`, no `tox.ini`, no `pre-commit-config.yaml`, no custom git hooks, no pytest config in `pyproject.toml`. The harness is a **local developer verification tool** only, not a CI gate. Per AC: flag CI wiring as follow-up in the epic.

### Sidecar JSON (firmware 1.8.0 context)

The current parser and transformer do not read or write `.json` sidecar files. Sidecars are a 1.8.0 native-UI feature (`rating`, `beanType`, `grindSetting`, `doseIn`, `doseOut`, `ratio`) and out of scope for 016 — they belong to ticket 014 (manage_shot_notes alignment).

---

## Web Research

### Snapshot-testing library comparison

| Library | State (early 2026) | Refresh mechanism | Float handling | Fit for this use case |
|---------|-------------------|-------------------|----------------|----------------------|
| **syrupy** | v5.1.0 Jan 2026, active | `pytest --snapshot-update` | `path_type` matchers replace volatile fields with type tokens — NOT per-field tolerance | Best ergonomics; `JSONSnapshotExtension` gives `.json` output files; adds dev-dep |
| **pytest-regressions** | Active (ESSS) | `--force-regen` / `force_regen=True` | `data_regression(round_digits=N)` — single uniform rounding only; `num_regression` has real atol/rtol but is flat-dict only | Fit if one global tolerance works; YAML default, JSON needs plumbing |
| **pytest-snapshot** | **Abandoned** (no release in 12+ mo) | — | — | Do not adopt |
| **inline-snapshot** | Active | `--inline-snapshot=fix` | — | Wrong shape — for inline values in test source, not for ~50 KB JSON |

**Net finding**: no library gives per-field float tolerance on nested dict/JSON data natively. The cleanest alternative to hand-curated goldens is a ~30-line recursive deep-equality walker (a standard pattern cited in Haskell tasty-golden community docs as the right escape hatch), which the codebase can own directly.

### Float tolerance patterns for nested structures

- `pytest.approx` — scalar/list/flat-dict only, no recursive walk.
- `math.isclose` — scalar only.
- `DeepDiff(significant_digits=N, math_epsilon=EPSILON)` — recursive but single global tolerance.
- `recursive-diff` PyPI package — purpose-built for nested-structure diffs with per-field `rtol`/`atol`; exists specifically to solve this problem.
- **Hand-rolled ~30-LOC walker** — recurse through dict/list, match strings/ints/bools with `==`, match floats with `math.isclose(rel_tol=..., abs_tol=...)`, optionally consult a field-name→tolerance map. Most flexible; no external dep.

### JSON/dict determinism gotchas

- Dict insertion order is stable since Python 3.7 — safe to rely on.
- `json.dumps(..., sort_keys=True)` is **the canonical recommendation for regression tests** — the stdlib `json` docs explicitly say so.
- Pydantic v2 `model_dump_json()` is not documented as deterministic across versions (Pydantic issue #7424 open as of 2026-03). **Not relevant here** — our outputs are stdlib TypedDicts, not Pydantic models.
- Sets/frozensets serialize in arbitrary order — convert to sorted lists before dumping. **Not relevant here** — no sets in `TransformedShot`.
- `repr(0.1)` is stable within a Python major version but cross-version risk is non-zero; for byte-stable serialization across Python versions, use explicit-precision format (`f"{x:.6g}"`). The 1e-6 tolerance in the AC sidesteps this concern entirely.

### Golden-file testing anti-patterns (must-read for harness design)

- **"Guru Checks Output" rubber-stamping** (Randy Coulman, 2016): snapshot tests only catch that *something* changed; they don't validate correctness. If refresh is too easy and diffs are too large, developers stop reading diffs. **Mitigations**: (a) keep fixtures small and readable, (b) pair snapshot equality with a few targeted explicit assertions on load-bearing fields, (c) treat every golden refresh as a code-review surface requiring manual inspection.
- **Non-determinism leaks** — the usual suspects: timestamps, UUIDs, hash-randomized iteration, float repr. Already audited out of this codebase; `PYTHONHASHSEED` not a concern.

### Binary fixtures in git

~150 KB total across 3 `.slog` files is firmly in the "commit directly to git" zone. Git LFS overhead is only justified >1 MB individual files or >500 MB binary weight total. Base64-in-source is an anti-pattern above 1 KB. Fetching at test time introduces flakiness. **Recommendation: commit directly, no LFS.**

### Key references

- syrupy docs: https://syrupy-project.github.io/syrupy/
- Randy Coulman on snapshot anti-patterns: https://randycoulman.com/blog/2016/09/06/snapshot-testing-use-with-care/
- Roman Cheplyaka's "Introduction to golden testing": https://ro-che.info/articles/2017-12-04-golden-tests
- `recursive-diff` PyPI: https://pypi.org/project/recursive-diff/

---

## Requirements & Constraints

### From epic research (gaggimate-1-8-0-upgrade/research.md)

- Line 84: "No regression fixtures. Every change to TransformedSample, FlowSummary, or /diagnose output risks silent regression on historical shots."
- Line 157: "Shot-fixture regression harness (net-new chore) — S effort. Blocks 015, 018, 021."
- Line 196: "Shot-fixture regression harness (S, chosen before major transformer changes) — checked-in representative shot + golden transformer output. Prerequisite for DR-1 port and BLE-precision investigation."

### From sibling tickets (as de facto requirements)

**Ticket 015 hard-blocks on 016.** 015 will add `weight_flow_g_s` to `TransformedSample` + three aggregate fields to `FlowSummary`, and its AC says the regression test "asserts transformer output matches golden values for all three added fields on each of 016's fixture shots. No 'manual validation acceptable' escape hatch."

**Ticket 018 hard-blocks on 016.** 018 will port DDSA to Python and test against reference-JS JSON for each of 016's fixture shots, with `1e-3` float tolerance on gram/second/millisecond values. 018's output stream is *separate* from `TransformedShot` — it's a `PhaseExitReason` stream. Implication: 018 does not force golden-JSON refresh in 016's files. It does, however, expect fixture shots chosen to exercise different exit-reason types (`weight | volumetric | pressure | flow | pumped | time`).

**Ticket 021 hard-blocks on 016** (for BLE-precision sub-question only). 021 needs a matched pair of pre-upgrade (1.7.3) and post-upgrade (1.8.0) shots at identical grind/dose. User upgraded ~2026-04-01; 021 acknowledges capacity-based retention may have evicted pre-upgrade data and the sub-question becomes unanswerable in that case.

**Ticket 014 (sidecar notes alignment)** does not block on 016 and does not require fixture data. 016 does not need to support shot-notes testing.

### Project-level constraints

- Python `>=3.13` (`mcp/pyproject.toml:9`).
- Dev deps: pytest, pytest-asyncio, pytest-cov only. No other test libraries currently. Adding syrupy or `recursive-diff` would be a policy change, however small.
- No CI. Harness is a local developer tool; the developer is the review gate.
- Data-repo split: `coffees/`, `grind-map.md`, `user-setup.md` are symlinked into a private data repo. `.slog` fixture binaries are **not** data-repo data — they are test infrastructure and belong in the main repo at `mcp/tests/fixtures/shots/`.

### Scope exclusions (what the harness does NOT do)

- Not a general mocking framework; only replaces the HTTP-fetched bytes with disk bytes for the parser.
- Not a CI pipeline; not a pre-commit hook. (AC says: flag CI wiring as follow-up.)
- Does not test `manage_shot_notes` round-trip (that's 014).
- Does not capture reference-JS JSON for DDSA parity (that's 018's concern; see open question below).
- Does not replace the synthetic-input unit tests already in `test_parsers_shot.py` / `test_transformers_shot.py` — it complements them by adding real-data regression coverage.

---

## Tradeoffs & Alternatives

### A. Hand-curated golden JSON (ticket's prescribed approach)

- **Effort**: S (~120–180 LOC): a ~60 LOC test file + ~40 LOC refresh script + ~30 LOC tolerance-aware deep-equals helper + fixtures README.
- **Refresh burden on 015's field additions**: 3 golden files fully rewritten. Diff is mechanical; the reviewer must confirm each diff *is* the intended new field and not silent drift elsewhere. ~15 min of human attention per refresh event.
- **Coverage**: highest — every field in `TransformedSample`, `ShotSummary`, per-phase aggregates, derived values.
- **Determinism risk**: low. Transformer is pre-rounded; dict order is stable in 3.13.
- **Failure readability**: **poor** without a custom assertion helper that prints the offending field path; a bare `assert dict_a == dict_b` on nested structures is unreadable at N=25 samples × 4 phases.
- **Portability**: works anywhere. Pure stdlib.

### B. Snapshot library (syrupy / pytest-regressions)

- **Effort**: S–M (+ dev-dep). Tests shrink to `assert result == snapshot`. Refresh is `pytest --snapshot-update` / `--force-regen`.
- **Refresh burden**: marginally better than A — one command regenerates all snapshots. Reviewer cost unchanged.
- **Float tolerance**: the real sticking point. Syrupy doesn't do per-field tolerance natively (path_type matchers replace values with type tokens — coarser than tolerance). pytest-regressions `num_regression` has real `atol`/`rtol` but only for flat dicts / numpy arrays, not for our nested `phases[*].samples[*]` shape.
- **At N=3 fixtures, the library win is modest** and the dev-dep cost is real (currently zero third-party test libraries beyond pytest+asyncio+cov).

### C. Field-level contract tests (no deep-equality)

- **Effort**: S (~80–100 LOC). No goldens.
- **Refresh burden**: **near-zero** when fields are added — new invariants stack alongside old ones without rewrites.
- **Coverage**: **dangerous gap.** Misses silent drift in untested fields or within tested ranges (e.g., `avg_pressure_bar: 8.0 → 7.7` slips past `5 <= avg_pressure_bar <= 10`). The epic research named this exact failure mode ("silent drift in historical-shot diagnosis") as the thing to prevent. Contract tests catch catastrophic regressions, not silent ones.

### D. Synthetic fixture generation (no binary `.slog`)

- **Effort**: XS (~60 LOC), and is arguably already covered by existing unit tests.
- **Coverage**: **dealbreaker** — skips the parser entirely, missing real-world data edge cases (BT-scale 0g dropouts, trailing artifacts, incomplete shots) and any future parser regression from firmware changes. Wrong-shaped for a 1.8.0 upgrade epic where parser behavior may shift.

### Hybrid: narrow deep-equality

Golden covers **ShotSummary + per-phase aggregates** only; TransformedSample arrays tested via field-level invariants in the same test file.

- **Motivation**: `/diagnose` reads summaries and aggregates, not individual samples. Diagnostic drift shows up there. Per-sample values being off by 0.01 bar does not affect diagnosis; a 0.3 bar shift in `avg_pressure_bar` does.
- **Refresh burden reduction**: 015's three new `TransformedSample` fields wouldn't touch existing goldens — just add three new invariants.
- **Strong tension with 015's AC**: 015 explicitly says "golden values for all three added fields on each of 016's fixture shots" — with `weight_flow_g_s` being a per-sample `TransformedSample` field. Narrow deep-equality would require 015 to introduce its own golden surface for those fields, fragmenting the harness. Unless 015's AC is renegotiated at that time, the hybrid undermines 015's expected interface. **→ open question for Spec.**

### Recommendation

**Approach A (hand-curated deep-equality goldens), with these specifics:**

1. **Golden scope**: full `TransformedShot` output (TransformedSample + ShotSummary + ComplianceMetrics + derived fields) — matches 015's AC and the ticket's stated contract. The "narrow hybrid" reduces refresh churn but breaks the interface 015 expects; not worth the savings at N=3.
2. **Deep-equality helper**: ~30 LOC recursive walker with a single `abs_tol=1e-6` on all floats and exact equality on strings/ints/bools. Prints offending field path + expected/actual/delta on failure.
3. **Byte-stable goldens on write**: `json.dumps(transformed, sort_keys=True, indent=2)`. Rely on transformer's pre-rounding; no custom float encoder needed.
4. **Refresh mechanism**: a small `gaggimate_mcp.tools.refresh_fixtures` module (~40 LOC). The tools namespace is empty today; being first is fine. Invocation: `python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>`. The script fetches from device via existing `http.fetch_shot`, runs the transformer, writes `.slog` + `.golden.json`. One command, no arg parsing cruft.
5. **Fixture count**: exactly 3 (the AC minimum). More fixtures mean more refresh surface for 015; prefer concentrated diversity.
6. **Fixture selection for exit-reason diversity**: nudge the three fixtures toward *different* exit reasons (one volumetric, one time-based, one weight-based if available) to give 018 useful coverage. Do not over-engineer — if a clean diversity set isn't available, fall back to the ticket's archetype split (healthy bloom-slide / decline / BT-artifact).
7. **No snapshot library**: zero new dev dependencies.
8. **No CI wiring in this ticket**: flag as follow-up in the epic, per AC.

---

## Open Questions

1. **Golden surface scope (the A vs hybrid tension).** 015's AC expects golden-validated per-sample fields (`weight_flow_g_s`). The tradeoffs analysis suggests a narrow surface (summary-only) would reduce churn, but would break 015's expected interface. **Recommendation is to honor 015's AC and use the full surface (Approach A)** — this is the default unless the user wants 015's AC renegotiated preemptively. Defer ratification to Spec.

2. **DDSA reference-JS sidecars — 016 or 018 responsibility?** 018's AC says reference-JS sidecars exist "for each of 016's fixture shots, captured via the prerequisite above" — the "prerequisite" is ambiguous. Capturing reference-JS requires running the 1.8.0 web UI's DDSA implementation against each fixture and exporting the output — an act 016 can do but doesn't strictly need to. **Deferred**: recommend 018 captures its own reference-JS sidecars when it runs, since the capture depends on a running web UI session and 018 is the tier that cares. 016 only ensures fixture `.slog` files exercise varied exit reasons.

3. **Pre-upgrade fixture availability for 021.** User upgraded ~2026-04-01 (~18 days ago relative to 2026-04-19). Capacity-based retention (500 KB floor) may or may not have evicted pre-upgrade shots. **Deferred to Spec**: during implementation, check whether any pre-upgrade `.slog` survives in device history. If yes, candidate (b) should be that shot (satisfying both 021's needs and the "decline-era" archetype in the original ticket). If not, document in fixtures README that 021's BLE-precision sub-question cannot be answered with checked-in fixtures, matching 021's own acknowledgment of this risk.

4. **Refresh trigger UX.** Three options: dedicated CLI (`python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>`), env var (`UPDATE_GOLDENS=1 pytest mcp/tests/test_shot_regression.py`), or purely manual README steps. **Recommendation: CLI script.** It's ~40 LOC, matches the ticket's suggested invocation, and makes "regenerate + review diff" the default path rather than a pytest-flag dance. Env var is fragile (easy to forget in CI-less setups); README-only is the "vague document how" the AC explicitly rejects. Defer final call to Spec.

5. **Custom failure-message helper.** Research strongly recommends a ~25 LOC custom assertion helper that prints `phases[1].samples[12].weight_flow_g_s: expected 2.14, got 2.09, delta 0.05 > tolerance 1e-6` on failure. The ticket AC doesn't call this out explicitly. **Deferred to Spec**: recommend adding to the AC since bare `assert a == b` on nested TransformedShot produces unreadable failure output at N=25 samples × 4 phases.

6. **Fixture selection priority when archetypes conflict with exit-reason diversity.** The ticket's archetypes (healthy bloom-slide / decline / BT-artifact) and 018's exit-reason diversity needs (volumetric / time / weight / pressure) may not all fit in three shots. **Deferred to Spec**: ask user to rank priorities — if a shot can satisfy both (e.g., a volumetric-stop bloom-slide shot at Shot 170), great; if not, the archetype split wins by default because that's what the AC enumerates.

7. **JSON formatting for goldens: `sort_keys=True` or insertion-order?** Current transformer uses TypedDict with stable insertion order, so `sort_keys=True` and insertion-order both produce stable output today. `sort_keys=True` is strictly safer (canonical stdlib recommendation for regression tests) and produces more readable diffs when fields are added in the middle of a struct. **Recommendation: `sort_keys=True, indent=2`.** Defer to Spec for ratification.
