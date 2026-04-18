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

The user's Gaggimate was upgraded from 1.7.3 to 1.8.0. A full audit of every integration touchpoint found the upgrade is **technically low-risk** (profile JSON unchanged, shot binary format unchanged, HTTP endpoints unchanged) but exposes several adaptation opportunities and one front-line verification blocker:

- `manage_shot_notes` may now persist to a sidecar `.json` rather than the path our WebSocket request wrote to in 1.7.3. `/feedback` runs after every rated shot — must verify before claiming the upgrade is safe.
- Per-sample weight flow (`vf`) is emitted in shot data; our parser already reads it but the transformer does not surface it.
- A full DDSA / PhaseEndStop classification algorithm is available in the device's web analyzer; porting it gives `/diagnose` autonomous exit-reason output.
- Several documentation traps (shot-history retention shift, `evt:status.bt` semantic flip, new `rssi` fields) need propagation through CLAUDE.md + knowledge files.

## Scope

- P0 verification: confirm `manage_shot_notes` still round-trips with native note editor
- Transformer upgrade: surface `weight_flow_g_s` per sample
- Regression harness: checked-in fixture shots + golden transformer output (prerequisite for all parser/transformer changes)
- Documentation: retention shift, `evt:status.bt` trap, `rssi` fields, DDSA in native UI, `vf` surfacing
- DDSA port: port `calculateShotMetrics` + support functions from `AnalyzerService.js` v1.8.0 to Python for autonomous exit-reason output in `/diagnose`
- Shot-notes alignment: extend `manage_shot_notes` with `dose_in_g`, `dose_out_g`, `grind_setting`, `bean_type`
- Deep-link: add `http://{host}/analyze/{shot_id}` line to `/diagnose` output as a complement
- Verification spikes: mixed-era shot compatibility, retention ordering invariants, BLE-precision round-trip drift

## Explicitly out of scope (dropped during critical review)

- mDNS service-browse discovery in MCP (DR-3 dropped — `.local` already resolves; own DR argued against)
- Profile `utility: true` tagging (zero extraction value)

## Children

- 014: Round-trip verify `manage_shot_notes` on 1.8.0
- 015: Surface `weight_flow_g_s` in `TransformedSample` + `FlowSummary`
- 016: Shot-fixture regression harness
- 017: Documentation pass for 1.8.0 semantics
- 018: Port DDSA / PhaseEndStop algorithm into `/diagnose`
- 019: Extend `manage_shot_notes` with native note fields
- 020: Add deep-link to `/analyze/{shot_id}` in `/diagnose` output
- 021: Post-upgrade behavior verification spike
- 022: BLE-precision round-trip drift investigation
