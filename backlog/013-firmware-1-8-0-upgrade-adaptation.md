---
id: "013"
title: "Gaggimate firmware 1.8.0 upgrade adaptation"
status: open
priority: high
type: epic
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
---

# Gaggimate firmware 1.8.0 upgrade adaptation

Adapt our barista agent system (MCP tools, skills, knowledge files) to Gaggimate firmware v1.8.0 and consume its new capabilities where they deliver agent value.

## Motivation

The user's Gaggimate was upgraded from 1.7.3 to 1.8.0. A full audit of every integration touchpoint found the upgrade is **technically low-risk** (profile JSON unchanged, shot binary format unchanged, HTTP endpoints unchanged) but exposes several adaptation opportunities and one critical verification blocker:

- `manage_shot_notes` may now persist to a sidecar `.json` rather than the path our WebSocket request wrote to in 1.7.3. `/feedback` runs after every rated shot — must verify before claiming the upgrade is safe.
- Per-sample weight flow (`vf`) is emitted in shot data; our parser already reads it but the transformer does not surface it.
- A full DDSA / PhaseEndStop classification algorithm is available in the device's web analyzer; porting it gives `/diagnose` autonomous exit-reason output.
- Several semantic traps (the `evt:status.bt` flip, shot-history retention shift) need to be documented so future contributors don't inherit them silently.

## Scope

- `manage_shot_notes` verified to round-trip with native editor on 1.8.0, then extended with native sidecar fields (014)
- Transformer upgrade: surface `weight_flow_g_s` per sample (015)
- Regression harness: checked-in fixture shots + golden transformer output (016) — prerequisite for 015, 018, 021
- DDSA port: port `calculateShotMetrics` + support functions from `AnalyzerService.js` v1.8.0 to Python for autonomous exit-reason output in `/diagnose`; includes deep-link to native analyzer UI in `/diagnose` output (018)
- Documentation: `evt:status.bt` semantic flip + retention shift (017)
- Post-upgrade drift investigation: mixed-era compatibility + retention ordering + BLE precision (021)

## Explicitly out of scope (dropped during critical review)

- mDNS service-browse discovery in MCP (DR-3 dropped — `.local` already resolves; own DR argued against)
- Profile `utility: true` tagging (zero extraction value)

## Epic acceptance criteria

- All children closed.
- `mcp/tests/test_shot_regression.py` passes against 016's fixtures.
- `mcp/tests/test_phase_end_stop_parity.py` passes with DDSA port matching reference JS output within tolerance (018).
- 021 investigation outcome recorded in verification-notes.md; if drift detected, follow-up tickets spawned and epic reassessed before close.

## Children (post-critical-review consolidation — 6, not 9)

- **014** (critical): Align manage_shot_notes with 1.8.0 native sidecar schema — verification is first AC, alignment is second
- **015** (medium): Surface weight_flow_g_s in TransformedSample + FlowSummary — blocked by 016
- **016** (high): Shot-fixture regression harness — blocks 015, 018, 021
- **017** (medium): Document evt:status.bt semantic flip + retention shift
- **018** (medium): Port DDSA / PhaseEndStop algorithm into /diagnose — includes deep-link; blocked by 016
- **021** (high): Post-upgrade drift investigation — mixed-era + retention + BLE precision; blocked by 016

### Consolidations applied during critical review

- Original 014 (verification) + 019 (field alignment) → single 014 (same file, §3 same-file merge rule)
- Original 020 (deep-link) → folded into 018 (same /diagnose output)
- Original 022 (BLE precision) → folded into 021 question (c) (same mechanical activity)
- Original 017 bundled 7 doc topics → narrowed to 2 cross-cutting semantic traps; `vf` doc moved into 015, DDSA doc moved into 018
