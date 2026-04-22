# Gaggimate MCP — Maintainer Notes

Operational documentation for maintainers working on the Gaggimate MCP server. The Python module `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py` (a Python port of the device-side `AnalyzerService.js`) needs periodic re-syncing whenever upstream gaggimate firmware bumps the analyzer logic; this README captures that workflow plus the fixture-capture procedure used by the parity test.

For per-fixture context (which `.slog` exercises which extraction archetype, byte-stability conventions for `.golden.json`, etc.), see `mcp/tests/fixtures/shots/README.md` — this file deliberately does not duplicate that content.

## Prerequisites

The Node harness under `mcp/tests/fixtures/shots/harness/` regenerates the `.reference-js.json` sidecars consumed by the Python parity test (`mcp/tests/test_phase_end_stop_parity.py`). It requires a local Node.js install.

- **Node.js ≥ 20.17.0** — the version pinned in `mcp/tests/fixtures/shots/harness/package.json` under `engines.node`. The minimum is set by ESM auto-reparse behavior introduced in 20.17; older Node fails with `SyntaxError: Unexpected token 'export'` when it tries to load the vendored `analyzer-service.*.js` and `parse-binary-shot.*.js` files as CommonJS.
- **macOS**: `brew install node@22` (Homebrew) or `nvm install 22` (if you already use nvm).
- **Linux**: `nvm install 22` is the most portable path. Distro packages also work — Debian/Ubuntu users can run `apt install nodejs npm`, but check `node --version` because some distro repos ship older 18.x or 20.x point releases.

> `package.json` declares `"engines": {"node": ">=20.17.0"}` but `engines` is **advisory** in npm — npm prints a warning when the constraint is unmet but does not refuse to run. Self-check with `node --version` before running the harness; if you see the `Unexpected token 'export'` error above, your Node is too old.

The MCP server runtime itself (Python 3.13+, `uv`) does not depend on Node — Node is only needed when capturing or refreshing fixtures.

## Re-syncing shot-analyzer on firmware upgrades

When upstream gaggimate releases a new firmware tag (e.g. `v1.9.0`) and you need to bring the Python port back into parity, follow these steps in order:

1. **Check out the gaggimate repo at the new tag** — clone or `git fetch && git checkout v1.9.0` in your local copy. You'll be diffing two source files out of it: `web/src/pages/ShotAnalyzer/services/AnalyzerService.js` and `web/src/pages/ShotHistory/parseBinaryShot.js`.
2. **Update `ANALYZER_JS_VERSION`** in `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py` (and the module docstring's `Port of AnalyzerService.js lines 208–1006 @ gaggimate v1.8.0` line-range citation if the new tag's line numbers shifted). The constant value is what the version-consistency test (step 6) cross-checks against the vendored filenames.
3. **Diff and re-vendor the JS sources.** Compare the two upstream files against `mcp/tests/fixtures/shots/harness/analyzer-service.v1.8.0.js` and `mcp/tests/fixtures/shots/harness/parse-binary-shot.v1.8.0.js`; copy the new versions over with the new version embedded in the filename (e.g. `analyzer-service.v1.9.0.js`, `parse-binary-shot.v1.9.0.js`). Delete the previous-version files in the same commit. Update the `import` statements at the top of `capture.js` to point at the new filenames.
4. **Update `HARNESS_SETTINGS` in `capture.js`** if the gaggimate web UI defaults at `web/src/pages/ShotAnalyzer/index.jsx:111-112` changed between versions. The committed defaults (`scaleDelayMs: 200`, `sensorDelayMs: 200`, `isAutoAdjusted: true`) are baseline-pinned for parity — different settings produce different exit classifications, so any drift in the upstream defaults must be mirrored here.
5. **Regenerate every reference-JS sidecar** with `node mcp/tests/fixtures/shots/harness/capture.js --all` from the repo root. This rewrites `<shot_id>.reference-js.json` for every `.slog` in `mcp/tests/fixtures/shots/`. Review the resulting git diff — non-trivial diffs are expected on a real algorithm change but should be inspected for plausibility before committing.
6. **Run the parity test** with `uv run pytest mcp/tests/test_phase_end_stop_parity.py`. Fix any newly-surfaced port deltas in `shot_analyzer.py` until the test passes. If a genuinely-divergent float field needs a per-field tolerance entry, add it with an inline comment citing the JS source line or commit per the discipline rule in `lifecycle/port-ddsa-phaseendstop-algorithm-into-diagnose/spec.md` (R11).
7. **Run the version-consistency test** with `uv run pytest mcp/tests/test_analyzer_version_consistency.py`. This catches leftover version-mismatch artifacts (vendored JS filename containing `v1.8.0` while `ANALYZER_JS_VERSION` says `v1.9.0`, or vice versa) before the PR opens.

Commit the version-bump constant, the renamed vendored JS files, and the regenerated `.reference-js.json` sidecars together in one cohesive change so reviewers can correlate the algorithmic delta against the parity-output delta.

## Adding a new fixture

To extend the regression and parity coverage with a new shot:

1. **Drop the new `<shot_id>.slog`** into `mcp/tests/fixtures/shots/`. The shot ID matches the device-assigned ID; the `.slog` is the raw binary you'd otherwise pull via `refresh_fixtures --fetch`.
2. **Regenerate the golden** with `python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>`. This produces `<shot_id>.golden.json` from the binary, exercising the full transformer pipeline that `test_shot_regression.py` covers. (See `mcp/tests/fixtures/shots/README.md` for context on the byte-stability convention this golden adheres to.)
3. **Capture the companion `<shot_id>.profile.json`** by fetching the device profile that produced the shot. With the device online, run `manage_profile(action="get", profile_id=...)` (the profile ID lives in the parsed shot's `profile_id` field) and save the returned JSON verbatim — do not reformat or re-serialize it. The profile sidecar is the second input the parity test feeds to `classify_phase_exits` / `estimate_auto_delay`.
4. **Capture the reference-JS sidecar** with `node mcp/tests/fixtures/shots/harness/capture.js <shot_id>` (single-shot mode). This produces `<shot_id>.reference-js.json` — the canonical-serialized output of the vendored `calculateShotMetrics` against the new `.slog` + `.profile.json` inputs.
5. **Confirm both suites pass** with `uv run pytest`. The regression test (`test_shot_regression.py`) picks up the new `.golden.json`; the parity test (`test_phase_end_stop_parity.py`) auto-parametrizes over the new `.slog` and asserts Python-vs-JS parity against the new sidecar.

**Contributors without Node installed**: skip step 4. Open a draft PR with just the `.slog`, `.profile.json`, and `.golden.json` and tag a maintainer in the description; the maintainer regenerates the `.reference-js.json` locally and pushes it to your branch. The parity test will fail-loudly on missing sidecars (with a message naming the missing path and pointing back at this section) until the maintainer's commit lands — that's expected.

## Known coverage gaps

The committed fixtures (246, 247, 249) span two profile types and three structural archetypes (see `mcp/tests/fixtures/shots/README.md`), but several extraction-mode and degradation scenarios remain uncovered. These are **not gating** for the initial port — they are documented here so future fixture captures can target them deliberately.

- **Flow-target-only Turbo profiles** — none of the three committed fixtures exercise a phase that uses a flow target as its sole stop condition. Turbo-style profiles (coarse grind, short dwell, flow-stop) would exercise the flow-classification branch of `classify_phase_exits` in isolation and shake out any pressure/duration cross-talk in the algorithm.
- **Pure power-target profiles** — fixture 249 is suspected to contain a power-target phase, but no committed fixture covers a profile that is *exclusively* power-targeted across all phases. DDSA classifies power-target exits as `duration` (no quantitative stop target exists in the JS), and a pure-power fixture would confirm that fallback fires consistently across multi-phase profiles.
- **Decaf and dark-roast bean profiles** — all three fixtures are light-medium roast naturals/bloom-slide extractions. Decaf porosity and dark-roast solubility produce visibly different pressure-flow signatures; coverage here would catch parity drift in the auto-delay estimator's edge handling for atypical curves.
- **Cross-era fixtures (mixed pre-1.8.0 + post-1.8.0)** — every committed `.slog` was captured under firmware 1.8.0. A cross-era cohort would exercise the `evt:status.bt` semantic-flip and `MIN_FREE_SPACE_BYTES` retention-shift edge cases (documented in the project root `CLAUDE.md` under "Firmware 1.8.0 semantic traps") and confirm the port is robust to mixed-vintage shot data.
- **Scale-lost-mid-shot scenario** — the JS source propagates a sticky "scale lost permanently" flag across four check sites and two fallback paths (lines 407, 447, 545, 624, 691-692, 804). The port implements all six explicitly, but no committed fixture forces the propagation path to fire mid-extraction. A synthetic or curated capture where the BT scale drops out partway through the brew phase would close this gap.
