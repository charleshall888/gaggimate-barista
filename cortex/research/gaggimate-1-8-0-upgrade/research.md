# Research: Gaggimate Firmware v1.7.3 → v1.8.0 Upgrade

**Date**: 2026-04-18
**Upstream release**: https://github.com/jniebuhr/gaggimate/releases/tag/v1.8.0 (published 2026-04-01)
**Scope**: Full audit of every integration touchpoint between our barista agent (MCP tools, skills, knowledge files, profile schema, data formats) and Gaggimate firmware 1.8.0.

**Post–critical-review revision**: this artifact has been hardened after four parallel adversarial reviewers + Opus synthesis flagged a factual error about `vf` location, a wrong file citation for the DDSA algorithm, optimistic sizing across all DRs, and a verification-first reordering of the work.

## Research Questions

1. **What did 1.8.0 change in firmware that our agent layer depends on?**
   → Mostly client-side (web UI analyzer, DDSA algorithm, profile list UI). On-device data contracts are **mostly stable**: profile JSON unchanged, shot binary format unchanged (SHOT_LOG_VERSION still 5), HTTP endpoints unchanged (additive fields only), BLE UUIDs unchanged. ⚠️ **Stability comes with a blind spot**: same version byte + no version gating means any subtle firmware-internal semantic shift (float precision, phase-transition semantics, sidecar coupling) cannot be detected from the record itself.

2. **Did MCP tool response shapes change?**
   → No known breaking changes. Additive: `rssi` field in `/api/status`, `/api/scales/list`, `/api/scales/info`. **Semantic shift**: `evt:status.bt` now reflects selected profile's volumetric-target presence rather than the settings flag (trap for future consumers). **Unverified risk**: `manage_shot_notes` (via `req:shot:notes:set`) may now write to a location the native Note Editor does not read, or vice-versa. Verification is front-line, not a decomp chore — `/feedback` runs on every rated shot.

3. **Did the profile JSON schema change?**
   → **No.** `parseProfile`/`writeProfile` in `src/display/models/profile.h` are unchanged. All fields identical. Our 13 stored profiles in `coffees/*/` are fully compatible.

4. **What new DDSA / phase-stop telemetry does firmware expose?**
   → **None from firmware.** All DDSA logic lives client-side in `web/src/pages/ShotAnalyzer/services/AnalyzerService.js` (~1007 lines; `calculateShotMetrics` alone ~700 lines, 12 support functions). Computed from existing sample stream + `phaseTransitions[]`. The English doc at `docs/PhaseEndStop_Algorithm_English.md` is ~44 lines and omits many numerical constants; the JS source is the real spec.

5. **Does `list_recent_shots` behave differently under capacity-based history?**
   → Same response shape, same `/api/history/index.bin` format. Retention policy shifted: `MAX_HISTORY_ENTRIES = 100` **removed**, replaced by `MIN_FREE_SPACE_BYTES = 500 KB` floor. Our default `limit=10` is unaffected in the common case. **Unverified**: ordering invariant (newest-first?) and purge-order invariant (FIFO by age?) under space pressure. Also: capacity purge now also deletes the companion `.json` sidecar — potential grind-map orphaning if notes moved to sidecar.

6. **Native shot analyzer + note editor overlap with `/diagnose` and `/feedback` — per-feature recommendation?**
   → See Decision Records. The native analyzer UI (deep-link, phase-stop overlay, `vf` plot, exit-reason classification, note editor, chart image export) is arguably now the **canonical diagnosis surface** — a URL deep-link + chart-image-to-vision-Claude inverts the effort model of "port the algorithm to Python."

7. **What knowledge-file / skill / CLAUDE.md updates does 1.8.0 warrant?**
   → See Decomposition Candidates. Sizing upgraded from XS to S per MEMORY.md's single-source-of-truth architecture (propagates across CLAUDE.md + knowledge/ + knowledge/reference/ + skills/ + MEMORY.md).

## Firmware 1.8.0 Change Summary

### On-device data contracts (what MCP sees)
- **Profile JSON**: unchanged.
- **Binary `.slog` shot log**: unchanged. Version still 5, header 512 B, sample 26 B, `phaseTransitions[12]`.
- **`/api/history/index.bin` layout**: unchanged.
- **HTTP endpoint set**: unchanged. Additive field `rssi` in `/api/status` and `/api/scales/*`.
- **WebSocket**: `req:history:rebuild` is now asynchronous. New event `evt:history-rebuild-progress` with `{status: scanning|started|processing|completed|error, total, current}`.
- **BLE characteristic UUIDs**: unchanged. Wire-format precision changed: numeric payloads are now serialized via `std::to_string` default (6 digits) instead of `snprintf("%.Nf", …)`. Float parsers (`atof`, `parseFloat`) are unaffected; regex-based exact-digit parsers would break. **Unresolved**: does firmware round-trip these strings through `atof` into `.slog` storage, causing least-significant-bit drift in our parsed float output?
- **`evt:status.bt` semantics**: now reflects `profile.isVolumetric()` rather than `settings.isVolumetricTarget()`.
- **Shot history retention**: fixed 100-entry cap → 500 KB free-space floor. Ordering + purge-order invariants unverified.

### New ambient capabilities (not consumed today)
- **mDNS service advertisement** (`_gaggimate._tcp.local` + `_http._tcp.local`, port 80, TXT `version=<git-tag>` and `type=espresso_machine`). `.local` resolution already uses mDNS under the hood.
- **Per-sample weight-flow field** (`vf`) — ⚠️ **already present in our parser** (`parsers/shot.py` line 33: `'VF': 8`). Not surfaced through the transformer.
- **Sidecar shot-notes JSON** (beside `.slog`) with fields `rating`, `beanType`, `grindSetting`, `doseIn`, `doseOut`, `ratio`. Native note editor reads/writes this file.

### Client-side additions (not firmware data)
- **DDSA / PhaseEndStop algorithm** in `AnalyzerService.js` — per-phase exit-reason classification (`weight | volumetric | pressure | flow | pumped | time`), auto-delay estimation (4s linear regression per phase + cross-phase accumulation), "delay review hint" output.
- **Shot analyzer UI** — deep-link shot view (`http://{host}/analyze/{shot_id}`), chart with phase-stop overlays, chart video/picture export.
- **Note editor** — dedicated UI for the sidecar notes file.
- **Profile list** — search, tabs (filters `utility: true` profiles), correctly-indexed volumetric-target display fix (PR 603).

### Stability / internal fixes (device-internal but can affect shot envelope)
- BLE buffer over-read, race conditions, spurious boot loops, controller-waiting state.
- Webserver stability.
- Standby timeout honours 0 value — if user relied on auto-standby between shots, thermal envelope shifts.
- Runtime WiFi-disconnect reconnect.

## Codebase Analysis — Integration Touchpoints

### MCP tools (`mcp/src/gaggimate_mcp/server.py`)

| Tool | Transport | Current dependency | 1.8.0 status |
|------|-----------|-------------------|--------------|
| `manage_profile` | WebSocket `req:profiles:list/load/save/delete` | Pydantic schema (`models/profile.py`) enforces fields | ✅ compatible (no schema drift) |
| `list_recent_shots` | HTTP GET `/api/history/index.bin` (binary parse) | Index entry layout | ✅ compatible (format unchanged); ⚠️ retention ordering invariant unverified |
| `analyze_shot` | HTTP GET `/api/history/{id}.slog` (binary parse, `parsers/shot.py`) | `SHOT_LOG_VERSION=5`, FIELD_BITS mappings, scaling factors | ✅ compatible; parser already reads `vf`; transformer does not surface it |
| `manage_shot_notes` | WebSocket `req:shot:notes:set` | Rating, notes, balance_taste | ⚠️ **front-line risk**: may now write to location native Note Editor does not read, or vice-versa. `/feedback` runs after every rated shot — must verify before claiming upgrade is safe |
| `diagnose_connection` | ping, HTTP probe, DNS/mDNS `.local` lookup | Hostname `gaggimate.local` | ✅ compatible; `.local` resolution already uses mDNS under the hood |

No version gating is present in either the client or the binary parser.

### Profile schema references

Canonical schema lives in `knowledge/GAGGIMATE_PROFILE_CREATION_GUIDE.md`. Pydantic enforcement in `mcp/src/gaggimate_mcp/models/profile.py`. Both match firmware v1.8.0 — **no updates required**.

### Shot data / telemetry references

- Parser: `mcp/src/gaggimate_mcp/parsers/shot.py` — FIELD_BITS (including `'VF': 8`), scale factors unchanged.
- Transformer: `mcp/src/gaggimate_mcp/transformers/shot.py` — exposes `TransformedSample` with `flow_ml_s` (pump flow) but **does not surface `vf` (weight flow)** even though the parser reads it.
- Compliance metrics: unchanged.
- **No regression fixtures.** Every change to TransformedSample, FlowSummary, or `/diagnose` output risks silent regression on historical shots (the shot IDs named in MEMORY.md for PERC Ethiopia, Chrome Yellow, La Papaya etc.).

### Skill behavior depending on firmware

| Skill | Firmware dependencies | 1.8.0 impact |
|-------|----------------------|--------------|
| `/gaggimate-profiles` | Profile schema | None; all valid |
| `/diagnose` | Binary `.slog` parsing, phase markers, compliance metrics, weight artifact detection | None breaking; native analyzer UI now arguably the canonical surface for visual diagnosis |
| `/feedback` | `manage_shot_notes` WS endpoint | ⚠️ front-line verification needed |
| `/new-coffee` | Profile create via `manage_profile` | None |
| `/consult` | Knowledge files only | None |

## Per-feature Recommendations (decision anchors)

| 1.8.0 feature | Overlap with agent | Recommendation |
|---------------|-------------------|----------------|
| Native Shot Analyzer UI (deep-link `/analyze/{shot_id}`) | `/diagnose` | **Link + vision-Claude**: add a deep-link line to `/diagnose` output; user pastes chart export image into conversation for vision-Claude to read. XS effort; leverages native rendering instead of porting 1000 lines of algorithm. |
| DDSA / Phase-stop / Exit reasons | `/diagnose` | **Defer the full port.** Options in DR-1 — open strategic question. |
| Note editor (native sidecar JSON) | `/feedback` + coffees/ | **Verify first.** Round-trip test is P0 — do NOT defer. Field alignment feature is separate and likely YAGNI for single user. |
| Capacity-based shot history | `list_recent_shots` | **Verify ordering invariants** + doc the shift. |
| Chart image/video export | `/diagnose` | **Integrate**: user pastes chart image → vision-Claude reads it. No special tooling. |
| mDNS `_gaggimate._tcp` | `diagnose_connection`, host config | **Not recommended**. `.local` already resolves via mDNS. Own DR argued against. |
| Auto-delay logic / exit-reason improvements | `/diagnose` | Subsumed by DR-1 strategic question. |
| `evt:status.bt` semantic change | — | **Documentation trap.** Not read today, but flip is a pitfall for future connection-surface extensions. Add prominent note to CLAUDE.md + devnotes. |
| Per-sample `vf` / weight_flow | `analyze_shot`, `/diagnose` | **Surface through transformer** (parser already reads it). Trivial code change, XS. |
| Profile `utility: true` tag | — | **Not recommended**. Cosmetic UI organization; zero extraction value. |
| BLE precision change | — | **Investigate** whether BLE→.slog round-trip causes parsed float drift. Regression-fixture-prerequisite. |
| Async `req:history:rebuild` + progress event | none today | **No action.** |
| `rssi` field | none today | **No action.** |

## Decision Records

### DR-1 (revised): How to consume 1.8.0's DDSA / exit-reason capability
- **Context**: 1.8.0 computes per-phase exit reasons and auto-delay estimation entirely in the browser at `web/src/pages/ShotAnalyzer/services/AnalyzerService.js`. `calculateShotMetrics` is ~700 lines in a 1007-line file; it depends on a 4s weight regression (`getRegressionWeightRate`), phase anchor detection, tolerance constants (`LAST_PHASE_OVERSHOOT_MAX_G=4g`, `LAST_PHASE_UNDERSHOOT_MIN_G/MAX_G=2/6g`, `LAST_PHASE_ESTIMATED_DELAY_MAX_MS=4000ms`), and scale-lost-permanently flag propagation. The English doc (44 lines) omits these. Without consumption, our `/diagnose` output is strictly less informative than the device UI, but the device UI is always one click away.
- **Options considered**:
  - (a) Full algorithm port to Python (L effort — not M as originally estimated; ~700 lines of dense logic; recurring maintenance tax on every firmware release; no test fixtures).
  - (b) **Deep-link + vision-Claude**: add `http://{host}/analyze/{shot_id}` link to `/diagnose` output; user pastes chart export image into conversation for vision-Claude to read phase overlays, vf/pump-flow divergence, exit reasons directly. XS effort; leverages native rendering.
  - (c) Do nothing; current `/diagnose` output continues unchanged.
- **Recommendation**: **(a) Full algorithm port** — user-chosen direction. Agent autonomy valued over the lower-cost deep-link path. (b) remains a complementary nice-to-have the user can adopt informally; (c) acceptable only if (a) stalls.
- **Trade-offs**: L effort + recurring maintenance tax on each firmware release (must re-port any algorithm changes and re-validate against reference). Mitigation: check in fixture shots + golden outputs, cite firmware version of the algorithm source, schedule re-sync on each upstream minor release.

### DR-2 (revised): `manage_shot_notes` alignment — split into two tickets
- **Context**: 1.8.0 introduces a sidecar `.json` file next to each `.slog` with `rating`, `beanType`, `grindSetting`, `doseIn`, `doseOut`, `ratio`. Native note editor reads/writes this file. Our `manage_shot_notes` currently sends `{rating, notes, balance_taste}` via `req:shot:notes:set`. It is unknown whether the WebSocket endpoint now writes to the sidecar, writes elsewhere, or has become a no-op.
- **Two decisions, not one**:
  1. **(P0) Verification**: write via MCP → read via native editor → write via native editor → read via MCP. Needs one real shot and ~10 minutes. This is **not a decomp chore** — it's the upgrade's biggest unknown and `/feedback` runs on every rated shot.
  2. **(Deferred) Field alignment**: extend `manage_shot_notes` to round-trip `dose_in_g`, `dose_out_g`, `grind_setting`, `bean_type`. For a single-user tool, this is likely YAGNI unless the verification reveals that the native editor is the user's preferred entry point.
- **Recommendation**: do decision #1 immediately (P0). Pursue decision #2 (field alignment) after verification — user-chosen direction. Target: extend `manage_shot_notes` with `dose_in_g`, `dose_out_g`, `grind_setting`, `bean_type` so native editor edits interoperate with agent edits. Implementation path depends on what verification reveals (WS endpoint still authoritative → extend WS message; sidecar now authoritative → write sidecar directly).
- **Trade-offs**: Verification is ~10 minutes. Field alignment is S-to-M depending on persistence path.

### DR-3: mDNS discovery for MCP connection — **DROPPED**
- **Status**: removed from backlog. Own prior recommendation was (b) keep fixed hostname; `.local` already resolves via mDNS at OS level; python-zeroconf is not trivial cross-platform (Linux needs avahi, Windows needs Bonjour); no multi-machine use case exists.
- **Preserved for reference only**, not a ticket.

### DR-4 (revised): Surface `weight_flow_g_s` in `TransformedSample`
- **Context correction**: the prior "Resolved" note claiming `vf` is not in `.slog` was **factually wrong**. `parsers/shot.py` line 33 maps `'VF': 8` and line 64 defines a `FieldDef`. Our parser already reads it. The firmware's `shot_log_format.h` sample bit layout includes it (the schema-diff agent's "byte-identical" claim meant "no change in 1.8.0," not "VF is absent"). The work is **just transformer surfacing** — the parser is ready.
- **Options**:
  - (a) Surface as `weight_flow_g_s` in `TransformedSample`; add summary aggregation (avg, peak, time-to-first-weight-flow) to `FlowSummary`.
  - (b) Skip; prefer chart-image path (see DR-1 option b) where divergence between pump flow and weight flow is a visual glance.
- **Recommendation**: **(a) is XS**, worth doing regardless — the field is right there and does not depend on hardware verification. Per-sample value can be useful even when chart is the primary diagnosis modality (e.g., reporting peak weight-flow as a metric).
- **Trade-offs**: XS code change; minor `/diagnose` interpretation extension. Risk: no fixture test — change should be validated against a known historical shot.

## Feasibility Assessment

| Approach | Effort | Risks | Prerequisites |
|----------|--------|-------|---------------|
| DR-1 option (a) — full DDSA port | **L** (revised from M) | Algorithm drift on future firmware; numerical-parity with 700 lines of JS source; no regression fixtures | Read `AnalyzerService.js` in full; decide on tolerance-constant handling |
| DR-1 option (b) — deep-link + vision-Claude | **XS** | Requires chart screenshot from user (light friction) | None |
| DR-2 #1 verification (P0) | **XS** (~10 min + 1 shot) | None | One real shot |
| DR-2 #2 field alignment (deferred) | S–M (after verification) | Unknown persistence path until #1 completes | DR-2 #1 |
| DR-3 mDNS discovery | **DROPPED** | — | — |
| DR-4 weight-flow surfacing | **XS** (revised from S) | No regression fixtures; manual validation against historical shot | None — parser already reads `vf` |
| Docs & knowledge updates | **S** (revised from XS) | Cross-file propagation per single-source-of-truth architecture (CLAUDE.md + knowledge/ + knowledge/reference/ + skills/ + MEMORY.md) | — |
| BLE-precision round-trip investigation | **S** | None — investigation only | Shot fixture harness (build a minimum one, see below) |
| Shot-fixture regression harness (net-new chore) | **S** | None — prevents regressions from every other ticket | — |
| Mixed-era shot-history behavior check | **XS** | Investigation only | — |
| Retention ↔ sidecar coupling check | **XS** | Investigation only | Follows DR-2 #1 |

## Decision Records (updated)

Summary of revised DR dispositions:

- DR-1: **proceed — full algorithm port** (user-chosen; L effort, recurring maintenance tax accepted for agent autonomy).
- DR-2: **verification P0 + field alignment** (user-chosen; both #1 and #2 pursued).
- DR-3: **dropped**.
- DR-4: **proceed** — XS transformer change.

## Open Questions

1. **Does `req:shot:notes:set` persist somewhere the native Note Editor reads?** Must be answered by hardware round-trip (DR-2 #1). Blocker for claiming the upgrade is safe.
2. **Does the native Note Editor expose `balance_taste`?** Defer to DR-2 #2 if we ever pursue field alignment.
3. **Does the firmware round-trip BLE-precision strings through `atof` into `.slog` storage?** If yes, parsed floats may drift in least-significant bits across the 1.7.3/1.8.0 boundary. Answered by comparing a pre-upgrade and post-upgrade fixture shot at identical grind/dose — see regression harness ticket.
4. **Is `/api/history/index.bin` ordering (newest-first?) and purge-order (FIFO by age?) preserved under the capacity-based retention policy?** Answerable by inspecting firmware source or observing behavior on a space-constrained device.
5. **When capacity purge evicts a `.slog`, does it also evict the sidecar `.json`?** Confirmed yes by the schema-diff agent. Implication: any grind-map reference to an old shot_id may orphan silently.

### Resolved during review

- ~~Is our profile generator ever emitting volumetric targets at index > 0?~~ **No.** All 13 profiles place volumetric as the sole target in the final phase's `targets[]`. PR 603 irrelevant. (Removed as backlog ticket.)
- ~~mDNS TXT `version` string format?~~ `BUILD_GIT_VERSION` — git tag or `git describe`. Irrelevant since mDNS work is dropped.

### Previously-resolved, now corrected

- ~~Is per-sample `vf` stored in `.slog`?~~ **Yes — our parser already reads it.** The earlier "no" conclusion was wrong; `parsers/shot.py` line 33 maps `'VF': 8`. DR-4 is therefore XS (transformer surfacing only).

## Decomposition Candidates (post-review)

Organized by priority, not by DR.

### P0 — blocker, do immediately
1. **Round-trip verify `manage_shot_notes` on 1.8.0** (XS, from DR-2 #1) — write via MCP, read via native editor, and vice-versa. Output: confirmation or diagnosis of breakage.

### P1 — low-effort wins
2. **Surface `weight_flow_g_s` in `TransformedSample` + `FlowSummary`** (XS, from DR-4). Parser already reads `vf`.
3. **Shot-fixture regression harness** (S, chosen before major transformer changes) — checked-in representative shot + golden transformer output. Prerequisite for DR-1 port and BLE-precision investigation.
4. **Documentation pass**: shot-history retention shift, DDSA availability in device UI, `evt:status.bt` semantic flip trap, `rssi` additive fields, `vf` now surfaced. (S, updated from XS per single-source-of-truth propagation.)

### P2 — chosen features
5. **Port DDSA / PhaseEndStop algorithm into `/diagnose`** (L, from DR-1 option a). Port `calculateShotMetrics` + 12 support functions from `AnalyzerService.js` v1.8.0 to Python; validate against checked-in fixture shots; cite firmware version; schedule re-sync on upstream minor releases. Blocked by fixture harness.
6. **Add deep-link to `/analyze/{shot_id}` in `/diagnose` output** (XS complement to DR-1). Low-cost enhancement: even with algorithm port, the chart UI remains useful for user inspection.
7. **Extend `manage_shot_notes` with native note fields** (S–M, from DR-2 #2). Add `dose_in_g`, `dose_out_g`, `grind_setting`, `bean_type` parameters; persistence path determined by P0 verification outcome.

### P3 — verification & risk reduction
8. **Mixed-era shot-history behavior check**: pull one 1.7.3 shot and one 1.8.0 shot, compare transformed outputs for drift. (XS investigation.)
9. **Retention ordering + purge-order invariants**: confirm newest-first index ordering and FIFO purges under space pressure. (XS investigation.)
10. **BLE-precision round-trip drift investigation**: determine whether parsed floats diverge across firmware versions. (S, requires fixture harness.)

### Dropped
- mDNS discovery (DR-3) — own recommendation against.
- Profile `utility: true` tagging — zero extraction value.
- Pre-603 volumetric-index bug check — already resolved in this artifact.
