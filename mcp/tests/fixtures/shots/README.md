# Shot regression fixtures

This directory is the checked-in regression surface for the shot-analysis pipeline. Each `.slog` is a real binary shot captured from the Gaggimate device; the sibling `.golden.json` is the output of `transform_shot_for_ai(parse_binary_shot(bytes, id))` at the time of capture. `test_shot_regression.py` parametrizes over every `.slog` and asserts exact equality against the golden — any drift in the parser or transformer surfaces as a failing assertion.

## Fixtures

### 249.slog — healthy bloom-slide (archetype a)

- **Profile**: Tropical Bloom [AI] — 5-phase bloom profile (Gentle Fill → Bloom → Ramp → Peak Hold → Tropical Slide).
- **Shot metrics**: 44.8 s, 49.6 g final weight, rating 4★.
- **Rationale**: The ticket's named candidate (Shot 170, Typica Anaerobic 5★ bloom slide) was evicted by the 1.8.0 free-space purge before capture; 249 is the nearest-surviving dialed-in bloom-slide shot on the device.

### 246.slog — diverse alternate (archetype b)

- **Profile**: Adaptive v2 — 6-phase adaptive/lever-simulation profile (Prefill → Fill → Compressing → Dripping → Pressurize → Extraction).
- **Shot metrics**: 25.9 s, 37.8 g final weight, rating 3★.
- **Rationale**: No pre-bloom-era decline-profile shot survived the 1.8.0 eviction (the Chelchele decline-era shots referenced in session memory are long-gone). 246 is labeled as a **diverse alternate** per the ticket's substitution rule — Adaptive v2 is a structurally different profile family from Tropical Bloom, exercising different phase-transition and compliance-metric code paths than 249.

### 247.slog — BT-scale-artifact candidate (archetype c)

- **Profile**: Tropical Bloom [AI] (same as 249), truncated.
- **Shot metrics**: 20.8 s, **`final_weight_g=None`**, last sample has `weight_g=0.0` while `flow_ml_s=6.6` (scale read zero while flow continued). Unrated.
- **Rationale**: No shots in the current inventory carry the transformer's explicit `unstable_weight` / `weight_anomalies` surface, so this is labeled as a **BT-artifact candidate**, not a confirmed-flagged artifact shot. The scale-read-zero-under-positive-flow pattern is the kind of anomaly the harness is meant to preserve for future transformer changes that may surface these cases more explicitly.

## Weight-flow hygiene behavior

The `FlowSummary` aggregates `peak_weight_flow_g_s`, `avg_weight_flow_g_s`, and `time_to_first_nonzero_weight_flow_s` are computed under the Unified Hygiene Rule: a sample qualifies when `vf` is present, `|vf| < 20.0` (strict-less-than the firmware int16/FLOW_SCALE=100 clamp sentinel), and `pf > 0.0` (pump actually flowing). Each fixture exercises a different slice of this rule.

- **246 (healthy, complete)**: enough samples satisfy the base hygiene rule to produce non-null aggregates — a straightforward positive-signal case. The regenerated `peak_weight_flow_g_s`, `avg_weight_flow_g_s`, and `time_to_first_nonzero_weight_flow_s` are all non-null and `time_to_first_nonzero_weight_flow_s >= time_to_first_drip_s` (drip precedes or coincides with the first clean weight-flow reading — the expected physical ordering).
- **247 (pathological / BT-artifact candidate)**: the Unified Hygiene Rule rejects so many samples that both `peak_weight_flow_g_s` and `time_to_first_nonzero_weight_flow_s` regenerate to `null`, and `avg_weight_flow_g_s` is `0.0`. Two filters do the rejection work: (a) the `pf > 0` guard eliminates pre-pump tare samples (positive `vf` and `v` readings before the pump starts); (b) the `abs(vf) < 20.0` strict-less-than clamp filter eliminates firmware int16 clamp-sentinel samples. Both filters are necessary — the clamp filter fires first on sentinel samples and the `pf > 0` guard handles different samples (pre-pump positive-`vf` spikes below the clamp bound). The net result is that 247 exercises the rejection paths but leaves no non-null survivors — it discriminates against under-filtering bugs but cannot verify correctness of non-null survivor values.
- **249 (healthy bloom-slide, multi-phase)**: most brew-phase samples pass the Unified Hygiene Rule and produce non-null aggregates. The `avg_weight_flow_g_s` aggregate does NOT apply an extra `vf > 0` filter on top of the base rule, so brew-phase negative-`vf` samples would be retained as honest scale drift during extraction. This committed fixture does not contain any such samples in practice — its negative-`vf` samples all sit in the pre-brew region and are filtered out by the brew-phase + `pf > 0` gates. A future fixture with genuine brew-phase scale drift would exercise the retained-negatives code path; 249 does not.

## Diversity summary

The three fixtures span **2 distinct profile types** (Tropical Bloom + Adaptive v2) and **3 structurally distinct archetypes** (healthy 5-phase bloom extraction, 6-phase adaptive/lever extraction, and a truncated bloom shot with a scale anomaly).

**Floor relaxation note**: The ticket's diversity floor (ii) asks for 2+ distinct coffee origins OR meaningfully different dose/grind across fixtures. The device shots 245–249 carry empty `bean_type`/`dose_in`/`dose_out` sidecar fields (the active-coffee annotations were not back-filled before capture), and sidecars for older shots were purged with the binary bodies under the 1.8.0 free-space floor. This constraint is therefore **documented as relaxed for this fixture cohort** — the profile-type and archetype diversity above is the operative diversity signal. If future fixture refreshes land on annotated shots, this note should be tightened.

## Running the test

```
cd mcp && pytest tests/test_shot_regression.py
```

## Refreshing goldens

### Default mode (transformer changed, `.slog` already captured)

```
python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>
```

Regenerates `<shot_id>.golden.json` from the existing `<shot_id>.slog` bytes. No device required. Review the resulting git diff manually — the pre-rounding invariant means any non-intentional numeric diff is a real regression worth inspecting.

### `--fetch` mode (capturing a new fixture or replacing the binary)

```
python -m gaggimate_mcp.tools.refresh_fixtures <shot_id> --fetch
```

Requires `GAGGIMATE_HOST` to resolve. Fetches the `.slog` from the device, writes both `<shot_id>.slog` and `<shot_id>.golden.json`.

## Exact-equality contract + pre-rounding invariant

The regression test uses exact `==` on every field in the transformed output. This is sound only because the transformer pre-rounds all numeric output to 1 decimal place (summary stats) or 2 decimal places (RMSE / compliance metrics). Any future change that introduces un-rounded floats will trip this harness — that is intentional. If a reviewer is tempted to add a float tolerance to `assert_equal`, they should first confirm whether the rounding invariant was relaxed in the transformer; reach for the tolerance only if the answer is yes.

## Walker contract surprises

The deep-equality walker (`shot_fixture_walker.py`) assumes three invariants about transformer output that it does **not** enforce:

- **NaN-free**: the walker uses `==` on floats; `float("nan") != float("nan")` would surface as a `"value"` mismatch in the regression failure message. The transformer currently emits `None` (not NaN) for insufficient-sample RMSE cases.
- **Tuple-free**: TypedDict fields are all typed as `list`. If the transformer starts emitting a tuple where a list was before, the walker will raise a container-category `"type"` mismatch.
- **`-0.0`-free**: `-0.0 == 0.0` under Python `==` so the walker would not flag a sign-zero drift, but `json.dumps(-0.0)` yields `"-0.0"` and `json.dumps(0.0)` yields `"0.0"` — byte-stability (below) catches sign-zero cases the walker misses.

If any of these invariants are violated in the future, the regression failure message may be counterintuitive. The walker unit tests (`test_shot_fixture_walker.py`) cover the NaN-comparison surface; byte-stability catches `-0.0`.

## Byte-stability convention

Goldens are written by `refresh_fixtures` as:

```python
body = json.dumps(transformed, sort_keys=True, indent=2, ensure_ascii=False)
path.write_text(body + "\n", encoding="utf-8")
```

The `sort_keys=True`, `indent=2`, trailing-newline, and UTF-8 encoding are all load-bearing for reproducible diffs. **Do not reformat goldens with other tools** (jq, prettier, IDE auto-format) — any reformatting will break byte-stability on the next refresh and produce spurious diffs that drown the real ones.

## Python minor-version note

Contributors refreshing goldens should use a Python minor version consistent with the existing goldens — nominally **Python 3.13.x** (per `mcp/pyproject.toml`'s `requires-python = ">=3.13"`). Cross-minor-version `repr(float)` differences are rare but possible and would break byte-stability even when the transformer output is semantically identical. No programmatic pre-flight check is enforced; this is an honor-system convention.

## Archive

Each `.slog` in this directory is also archived at `{private-data-repo}/mcp-data/shot-archive/<shot_id>.slog` as eviction insurance — the main-repo copies are authoritative for the regression tests; the archive copies are the recovery surface if the main-repo files are ever corrupted or the device history is wiped before a fresh capture.

If `.data-repo-path` is absent at the project root when fixtures are captured or refreshed, the archive step is skipped silently and this section does not apply.
