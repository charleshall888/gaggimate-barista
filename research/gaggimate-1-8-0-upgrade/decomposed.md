# Decomposition: gaggimate-1-8-0-upgrade

## Epic
- **Backlog ID**: 013
- **Title**: Gaggimate firmware 1.8.0 upgrade adaptation

## Work Items (post-critical-review)

| ID | Title | Priority | Size | Depends On |
|----|-------|----------|------|------------|
| 014 | Align manage_shot_notes with 1.8.0 native sidecar schema | critical | S-M | — |
| 015 | Surface weight_flow_g_s in TransformedSample + FlowSummary | medium | XS | 016 |
| 016 | Shot-fixture regression harness | high | S | — |
| 017 | Document evt:status.bt semantic flip + retention shift | medium | XS | — |
| 018 | Port DDSA algorithm into /diagnose (includes deep-link) | medium | L | 016 |
| 021 | Post-upgrade drift investigation (mixed-era + retention + BLE) | high | S | 016 |

## Suggested Implementation Order

1. **014 and 016 in parallel, starting immediately.** 014 is critical-priority and is a blocker for claiming the upgrade is safe. 016 unblocks 015, 018, and 021.
2. **Once 016 lands**: 015 can ship (XS, fast win) and 018 can start (L). 021 can start its investigation in parallel with 018.
3. **017 can land anytime** — it has no dependencies and is a small cross-cutting docs change.

## Consolidations Applied During Critical Review

The initial decomposition produced 9 children. Adversarial review (4 parallel reviewers + Opus synthesis) identified structural over-decomposition. The consolidations below reduced the count to 6 while eliminating several inverted-dependency and hidden-work problems.

### Merge: old 014 + old 019 → new 014

Both modified `mcp/src/gaggimate_mcp/server.py`. Splitting a 10-minute verification step into its own XS ticket gated an S-M feature ticket behind a backlog handoff. Per decompose skill §3 (same-file S-sized items consolidate). Verification is now the first AC of 014, alignment is the second.

### Merge: old 020 → new 018

Old 020 was a 3-line AC about adding a URL to `/diagnose` output. Ticket 018 already modifies `/diagnose` output substantially (DDSA exit-reason integration). Splitting them created an artificial PR boundary.

### Merge: old 022 → new 021 question (c)

Both required pulling pre-upgrade and post-upgrade shots from the device and diffing transformed fields. Same mechanical activity, different analytical lens. 022's own dependency chain already cited 021 explicitly.

### Narrow: old 017 from 7 topics to 2

Earlier draft of 017 bundled 7 documentation topics. Five of them document capabilities produced by other tickets (`vf` surfacing from 015, DDSA availability from 018, etc.). Docs-as-standalone-ticket is a deferral antipattern — docs would either ship before backing code (false claims) or get permanently deprioritized. New 017 retains only the two cross-cutting semantic traps that aren't tied to any code change: the `evt:status.bt` semantic flip and the retention shift.

### Priority recalibration

- **014 → critical** (from high). `/feedback` runs on every rated shot; silent corruption is blocker-tier. The schema's `critical` tier was previously unused across the repo; this is the first legitimate use.
- **015 → medium** (from high). Additive nice-to-have; nothing regresses if slipped. Earlier `high` was effort-calibrated ("XS and valuable") rather than blast-radius-calibrated.
- **021 → high** (from low). If drift is detected on any of its three sub-questions, 016's fixtures are invalid and every historical-shot diagnosis is unreliable. Priority should reflect consequence-if-wrong, not likelihood.

### AC hardening

- Added concrete `verification-notes.md` format to 014 and 021 (previously a fabricated-convention reference).
- Removed 015's self-contradicting "interim step is acceptable" escape hatch; it now hard-blocks on 016.
- Added `1e-3` tolerance spec to 018's bit-compatibility check.
- Added explicit JS-output-capture prerequisite discussion to 018 (previously hidden tooling work).
- Scoped 016's fixture sourcing to specific shot_ids (Shot 170 from MEMORY.md, decline-profile candidate) rather than "find something representative."
- Flagged pre-upgrade fixture-availability challenge in 021 with explicit fallback (private data repo history, or honestly declaring the test unrunnable).
- Removed judgment-word ACs ("terse", "where fits", "sensible position", "if possible", "similar profile/conditions").

## Dropped (confirmed out of scope)

- mDNS discovery (original DR-3) — own recommendation was against; `.local` already resolves.
- Profile `utility: true` tagging — zero extraction value.
- Pre-603 volumetric-index bug check — already resolved in the research artifact itself.

## User-chosen directions (applied during research-phase critical review)

- **DR-1 direction**: user chose full algorithm port (L effort) over deep-link/vision-Claude path (XS). Preference for agent autonomy even at higher effort + maintenance cost. Saved to memory as a feedback signal.
- **DR-2 scope**: user chose verify + pursue full field alignment rather than verify-only YAGNI.

## Created Files

Currently active:
- `backlog/013-firmware-1-8-0-upgrade-adaptation.md` — Gaggimate firmware 1.8.0 upgrade adaptation (epic)
- `backlog/014-verify-manage-shot-notes-1-8-0.md` — Align manage_shot_notes with 1.8.0 native sidecar schema
- `backlog/015-surface-weight-flow-in-transformer.md` — Surface weight_flow_g_s in TransformedSample + FlowSummary
- `backlog/016-shot-fixture-regression-harness.md` — Shot-fixture regression harness
- `backlog/017-documentation-pass-1-8-0-semantics.md` — Document evt:status.bt semantic flip + retention shift
- `backlog/018-port-ddsa-algorithm-to-diagnose.md` — Port DDSA algorithm into /diagnose (includes deep-link)
- `backlog/021-post-upgrade-behavior-verification-spike.md` — Post-upgrade drift investigation

Archived as superseded during critical review:
- `backlog/archive/019-extend-manage-shot-notes-fields.md` — merged into 014
- `backlog/archive/020-deep-link-analyzer-in-diagnose.md` — merged into 018
- `backlog/archive/022-ble-precision-round-trip-investigation.md` — merged into 021

## Epic AC

- All 6 children closed.
- `mcp/tests/test_shot_regression.py` passes against 016's fixtures.
- `mcp/tests/test_phase_end_stop_parity.py` passes with DDSA port matching reference JS output within `1e-3` tolerance (018).
- 021 investigation outcome recorded in `verification-notes.md`; if drift is detected on any sub-question, follow-up tickets are spawned and the epic is reassessed before closing.
