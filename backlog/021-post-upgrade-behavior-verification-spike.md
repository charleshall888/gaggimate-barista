---
id: "021"
title: "Post-upgrade drift investigation: mixed-era, retention ordering, BLE precision"
status: open
priority: high
type: spike
parent: "013"
blocked-by: ["016"]
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
---

# Post-upgrade drift investigation: mixed-era, retention ordering, BLE precision

## What this delivers

Empirical determination of three behavioral invariants that, if violated, would invalidate the fixture-based regression harness (016) and every historical-shot comparison the agent does: (a) mixed-era shot compatibility, (b) shot-history ordering/purge invariants, (c) BLE-precision float drift across the 1.7.3/1.8.0 boundary.

## Why high priority (elevated from low during critical review)

All three sub-questions test whether our foundation is intact. If any returns "drift detected," the consequences compound:

- Mixed-era drift means `/diagnose` silently gives different answers comparing a new shot to a pre-upgrade shot vs. a post-upgrade shot — and 016's fixtures need version-gating to remain valid.
- Retention-ordering drift means `/feedback`'s implicit "last N shots at this grind" heuristic could pull non-sequential samples.
- BLE-precision drift means every cross-era numerical comparison (`/diagnose` comparing to historical shots, `/feedback` trend analysis, compliance metrics) is corrupted at sub-LSB levels — small enough to pass tolerance but large enough to shift interpretation.

Priority should reflect blast radius if the answer is "drift exists," not likelihood.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decomposition Candidates #5, #6, and #7 (mixed-era, retention, BLE precision) consolidated here because all three require the same activity — pull pre-upgrade and post-upgrade shots, diff transformed fields.

## Three questions to answer

### (a) Mixed-era shot compatibility

`SHOT_LOG_VERSION` is still 5 in 1.8.0 and no version gating exists in the parser. If firmware introduced subtle internal semantic shifts (float precision round-trip through BLE serialization, phase-transition sample semantics, sidecar coupling) while keeping the version byte fixed, our parser has no way to distinguish a 1.7.3 shot from a 1.8.0 shot.

- Pull one `.slog` logged before upgrade and one logged after, same coffee family if possible.
- Run both through parser + transformer pipeline.
- Diff transformed outputs field-by-field. Document any systematic cross-era delta.

### (b) Retention ordering + purge-order invariants

`MAX_HISTORY_ENTRIES = 100` was removed; `MIN_FREE_SPACE_BYTES = 500 * 1024` now gates retention.

- Query `/api/history/index.bin` and verify entry order matches expectation (likely newest-first — confirm).
- Do not require artificial space-pressure simulation. Observe purge-order passively if eviction happens during the investigation window; otherwise document "no eviction observed during this window" as a legitimate terminal state.

### (c) BLE-precision round-trip drift (formerly ticket 022)

Firmware 1.8.0 changed BLE wire-format precision (`snprintf("%.Nf", …)` → `std::to_string` with 6-digit default). If firmware round-trips BLE strings through `atof` before writing to `.slog`, parsed floats may drift in least-significant bits.

- Using a pre-upgrade fixture shot and a post-upgrade shot (see fixture-availability note below), compare raw parser outputs field-by-field (`cp`, `fl`, `v`, `tf`, `pf`, etc.).
- Look for systematic bias or precision shift. Quantify magnitude (e.g. "mean delta of 0.0003 bar on `cp` across all samples"). No threshold to meet — the question is whether ANY systematic drift exists.

## ⚠️ Pre-upgrade fixture availability

The user upgraded approximately 2026-04-01 (~17 days before this ticket was written). 1.8.0 retention is capacity-based rather than count-based, so pre-upgrade `.slog` files may already be evicted. Investigate at implementation time:

- If pre-upgrade shots still exist on device, pull them directly.
- If evicted, check whether the private data repo (via `.data-repo-path`) preserves any historical `.slog` files. The storage path is under `{private_repo}/mcp-data/` per CLAUDE.md's Data Architecture section.
- If neither is available, question (a) and question (c) become unanswerable. Document this outcome explicitly in verification-notes.md — the honest result is "no pre-upgrade fixture available; drift check deferred until one is captured retroactively or next firmware upgrade."

## Acceptance criteria

- Findings captured in `research/gaggimate-1-8-0-upgrade/verification-notes.md` (using the format template established by ticket 014).
- For each of the three questions: a section with (question restated, method used, raw comparison data or observation, conclusion: "drift detected"/"no drift"/"unable to test").
- If any question returns "drift detected," spawn a follow-up ticket for parser version-gating or fixture re-curation. The follow-up's scope depends on the drift class; this ticket is investigation-only.

## Dependencies

- 016 (fixture harness) — hard block. Provides the reference point against which post-upgrade shots are compared, and provides the checked-in golden output for regression reference.

## Supersedes

- Old ticket 022 (BLE-precision round-trip investigation) — merged here as question (c).
