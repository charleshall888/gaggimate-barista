# Review: operationalize-rpm-as-an-extraction-variable

## Stage 1: Spec Compliance

### Requirement R1: DF64V.md gains a skill-consumable "RPM as a dial-in lever" note
- **Expected**: New `## RPM as a dial-in lever` subsection after `## Motor Speed (RPM)`, covering narrow triggers, the timer-anchored uncontested re-dial fact with NO printed directional rule, and the contested + own-data hedge. Heading count = 1; "shot timer" present; contested/McKeon ≥ 1; no un-hedged directional body claim.
- **Actual**: `knowledge/grinders/DF64V.md` L46–60. `grep -c "## RPM as a dial-in lever"` = 1 (heading). `grep -ci "shot timer"` = 1; `grep -ci "contested\|McKeon"` = 7. L48 states triggers ("never the opening move", "never a channeling fix"). L50 anchors on the shot timer and explicitly refuses a printed direction ("No printed 'raise RPM → go finer' rule lives here on purpose; the timer decides"). L52–58 carry the McKeon-coarser / Hoffmann-null / vendor-unproven / own-data hedge. Bare-string count of "RPM as a dial-in lever" (3) reflects the heading plus two cross-references (L42, L103) — the cross-references are R2's required reconciliation, not stray directional claims; the operative heading-scoped count is 1.
- **Verdict**: PASS
- **Notes**: Agent-reasoned hedge audit re-run (below) confirms no bare directional body/clarity assertion survives in the file, including the reworded L42 region.

### Requirement R2: DF64V.md body↔RPM associations (former L85 and L42) reconciled to one hedged voice
- **Expected**: Old "Manage body via higher dose or slightly higher RPM" line gone (count 0); remaining body mentions each co-occur with a hedge or cross-reference to the dial-in-lever note.
- **Actual**: `grep -c "Manage body via higher dose or slightly higher RPM"` = 0. The former L85 is replaced by the hedged Burr Character "Practical implication" (L103) which cross-references the dial-in-lever note and the McKeon-coarser/Hoffmann-null evidence. The former L42 Motor Speed line now reads (L42) "the link between RPM and cup body is contested, not a settled dial" and routes the reader to the new note. Full per-line hedge audit (see Hedge Audit section) shows every body/clarity line is hedged, anti-claim, or the hedge framing itself.
- **Verdict**: PASS

### Requirement R3: `_NOTATION.md` gains RPM logging rules
- **Expected**: A `## …RPM` section after Core Principle / before Epoch Binding, plus a summary-table row; states integer/grinder-config-not-chirp/not-epoch-bound/blank-for-fixed/never-infer/independent-column. `grep -ci "RPM"` ≥ 4; `## .*RPM` heading present; summary row present.
- **Actual**: `knowledge/grinders/_NOTATION.md` L21–31 (`## Motor Speed (RPM) — A Separate, Non-Chirp Coordinate`, correctly positioned after Core Principle L7–17, before Epoch Binding L33). States plain-integer, grinder-config-not-chirp, NOT epoch-bound, blank-for-fixed, never-infer, independent-column. Summary-table row added at L112. `grep -ci "RPM"` = 7 (≥ 4); `grep -ci "## .*RPM"` = 1. Explicitly additive ("additive to … not a redefinition").
- **Verdict**: PASS

### Requirement R4: `grind-map.example.md` synced to the live 13-column RPM schema
- **Expected**: `RPM` at position 7 in header/separator/sample (sample value 1100), plus the legend line; header and separator pipe counts equal.
- **Actual**: `grep -c "| Grind | RPM | Profile |"` = 1; `grep -c "variable-speed grinder RPM as an integer"` = 1; sample row L9 carries `1100` at position 7; legend L13 mirrors the live file. Header L7 and separator L8 both have 14 pipes (equal).
- **Verdict**: PASS

### Requirement R5: `_TEMPLATE.md` documents the RPM-section gating convention for forkers
- **Expected**: One-line note that a grinder is variable-speed (RPM behavior enabled) when its file has a `## Motor Speed (RPM)` section; fixed-speed grinders omit it. No `**Speed:**` data field.
- **Actual**: `knowledge/grinders/_TEMPLATE.md` L63 inside the Espresso Operating Point placement comment: "Variable-speed gating: a grinder is treated as variable-speed (RPM behavior enabled across the skills) when its file includes a `## Motor Speed (RPM)` section; fixed-speed grinders omit it." `grep -ci "Motor Speed (RPM)\|RPM behavior\|variable-speed"` = 1. No `**Speed:**` field added (Non-Requirement respected).
- **Verdict**: PASS

### Requirement R6: `user-setup` gains a current "Operating RPM" field (the home for current RPM)
- **Expected**: `Operating RPM` field added to `user-setup.example.md` with documented integer parse rule; meaningful only for variable-speed; blank/absent for fixed-speed; create-if-absent contract documented.
- **Actual**: `user-setup.example.md` adds an `Operating RPM` row to the Equipment table (L12, blank — the example grinder is the fixed-speed Encore ESP) and a Notes bullet (L57) documenting the integer parse rule, the variable-speed-only meaning, the distinction from the grind-map historical stamp, and the create-if-absent contract. `grep -ci "Operating RPM"` = 2; `grep -ci "variable-speed"` = 1 co-occurring with the documentation.
- **Verdict**: PASS

### Requirement R7: Variable-speed gating rule — pinned to the literal section heading
- **Expected**: Gate keyed on the literal `## Motor Speed (RPM)` quick-tier heading; `/new-coffee` and `/feedback` each restate the gate inline with a discriminating OFF/fallback clause (`fixed-speed`, `never error`); signal present in DF64V.md (=1), absent in SETTE_270.md (=0).
- **Actual**: `grep -c "## Motor Speed (RPM)"` = 1 (DF64V.md) / 0 (SETTE_270.md). `/new-coffee` SKILL.md L72 (Step 4 SYNTHESIZE) restates the gate keyed on the literal heading with the OFF clause "this is a **fixed-speed** path — omit the RPM row entirely and **never error**." `/feedback` SKILL.md L72 (top of Step 3 ANALYZE) restates it: "RPM behavior is **ON** iff … contains a section whose heading is exactly `## Motor Speed (RPM)` … → the grinder is **fixed-speed**: RPM behavior is **OFF** … **never error**." `fixed-speed`/`never error` counts ≥ 1 in both files, sitting inside the gate blocks (confirmed by reading). Fixture trace (verification-trace.md §3.1, §3.2): DF64V → ON, Sette → OFF.
- **Verdict**: PASS
- **Notes**: Exactly ONE gate restatement in feedback — the "RPM behavior is" ON/OFF logic appears once (L72). The other contract-restatement sentence (L29) is the pre-existing Conditionally-Load grinder resolution, not a duplicate gate. Task-7/Task-8 surfaces do not collide.

### Requirement R8: `/new-coffee` recommends a starting RPM (variable-speed only) as a runtime placeholder
- **Expected**: Conditional `RPM` row in the Recommended Starting Parameters table, gated ON; runtime placeholder (no literal numbers); `RPM_RECOMMENDATION` claim in SELF_CHECK `<claims>` block.
- **Actual**: `/new-coffee` SKILL.md L235 adds `| RPM | [placeholder] | [variable-speed only] |` to the output table, with the conditional-emission note at L260. `grep -c "| RPM |"` = 2 (row + note); `grep -Ec "\b(1000|1100|1200|1400)\b"` = 0 (placeholder, no literals). SELF_CHECK.md L25 carries one `RPM_RECOMMENDATION` claim inside the `<claims>` block (L13–28); `grep -c "RPM_RECOMMENDATION"` = 1. Fixture trace: DF64V → row rendered, Sette → omitted.
- **Verdict**: PASS

### Requirement R9: `/feedback` reads the current Operating RPM and stamps it into the grind-map row
- **Expected**: When gate ON, read Operating RPM from user-setup and use it as the row value; session-stated RPM overrides (triggers R11); prompt once if unknown, write blank if still unknown, never infer; gated to variable-speed.
- **Actual**: `/feedback` SKILL.md L66 (Step 2 COLLECT): "When the gate is ON, read the current `Operating RPM` from `user-setup.md` … and carry it forward as the RPM value for the grind-map row in Step 4b. If the user states a different RPM this session, that stated value overrides … (and triggers the mid-bag re-dial guard). If the gate is ON but Operating RPM is unknown, prompt for it once (light) and, if still unknown, leave it blank — never infer. When the gate is OFF … do not read or prompt for RPM." `grep -ci "Operating RPM\|current RPM"` = 5. Fixture trace: DF64V (1100 set) → 1100 stamped; Sette → no read, blank cell.
- **Verdict**: PASS

### Requirement R10: `/feedback` grind-map writer emits 13 fields with RPM at position 7
- **Expected**: Writer changed from "12 fields" to "13 fields in order: Coffee, Roast, Process, Origin, Days Off Roast, Grind, RPM, Profile, Ratio, Temp, Rating, Date, Puck Screen?"; RPM cell names both branches (integer / blank, never infer); back-compat note column counts updated.
- **Actual**: `grep -c "12 fields"` = 0; `grep -c "Grind, RPM, Profile"` = 1. L154: "these 13 fields in order: `Coffee, Roast, Process, Origin, Days Off Roast, Grind, RPM, Profile, Ratio, Temp, Rating, Date, Puck Screen?`" (RPM at position 7). RPM-cell sub-step L156–158 names both branches: variable-speed gate-ON → plain integer (with blank if unknown after one prompt); fixed-speed/unresolved/contract-fallback → blank; "never infer." Back-compat note L162 updated: "Old 12-column (or shorter) rows … only the newly appended row is 13-column."
- **Verdict**: PASS
- **Notes**: This is the load-bearing correctness fix flagged by the plan — the writer is now aligned to the live 13-col header. A misaligned-row guard (L153) was additionally authored: scan the live file for any data row whose column count ≠ 13 and flag it (no auto-backfill), satisfying the spec Edge.

### Requirement R11: `/feedback` mid-bag RPM-change re-dial guard (compares against user-setup, no history parser)
- **Expected**: On a stated RPM ≠ user-setup Operating RPM (variable-speed only), warn + re-anchor (re-dial grind to restore shot time, don't carry old chirp+N marks) AND update/create user-setup Operating RPM via the data-repo path even on an unrated shot; single user-setup read, no grind-map history scan.
- **Actual**: `/feedback` SKILL.md L109–115 (ANALYZE). L111 explicitly "a single read — do NOT scan prior grind-map rows." Two actions: (1) L112 warn + re-anchor on the shot timer, route the why to `DF64V.md`, don't carry the old `chirp + N marks` forward; (2) L113 update-or-create the Operating RPM field, "creating the row if it is absent," and "must reach the Step 4e `.data-repo-path` commit/push **even when no rating is recorded**." L115: stated RPM matching the current value (or no RPM stated) → do nothing. Fixture trace: delta → warn+update; same/none → silent; fixed-speed → guard OFF.
- **Verdict**: PASS

### Requirement R12: `/feedback` offers RPM only as experiment-aware guidance, never a standing lever
- **Expected**: Adjustment-hierarchy block contains zero "RPM"; experiment-triggered RPM branch exists elsewhere and routes to DF64V.md; routine sour/bitter/fast/slow diagnosis never volunteers RPM.
- **Actual**: The adjustment-hierarchy block (L76–81: Grind → Yield/Ratio → Temperature → Pressure/Profile → Puck prep) contains zero "RPM" (block-scoped `grep -c "RPM"` = 0). The experiment branch (L119–121) is a separate sub-section that fires only on an explicit body/clarity experiment, gives hedged guidance, and routes to `knowledge/grinders/DF64V.md` rather than restating numbers; it states "Do NOT volunteer RPM as a fix during routine sour/bitter/fast/slow diagnosis." `grep -c "DF64V.md"` = 2. Fixture trace: routine "too sour" → no RPM; explicit experiment → hedged routed guidance.
- **Verdict**: PASS

### Requirement R13: `/diagnose` is RPM-aware as investigation context (minimal; not a gate)
- **Expected**: CORRELATE uses a known RPM (from grind-map row or stated) as advisory context routed to DF64V.md/DF64V_REFERENCE.md, with an explicit "no RPM known → unchanged" fallback; no out-of-range alarm, no grinder-resolution surgery.
- **Actual**: `/diagnose` SKILL.md L145 (§3 CORRELATE): "If the RPM used for the shot is known — from the shot's `grind-map.md` row or a value the user states — fold it into the correlation narrative as contextual input. A logged RPM is self-identifying … so no grinder-resolution or out-of-range gating is needed." Examples defer interpretation to `DF64V.md`/`DF64V_REFERENCE.md`. Explicit fallback: "If no RPM is known for the shot, behave exactly as today — skip this context and run the correlation unchanged." `grep -ci "RPM"` ≥ 1 in CORRELATE; `grep -Ec "\b(1000|1100|1200|1400)\b"` = 0. Fixture trace: known RPM → context; no RPM → unchanged.
- **Verdict**: PASS

### Requirement R14: `/consult` routes RPM questions to the active grinder reference
- **Expected**: `rpm`, `motor speed`, `grind speed` added to the grind/grinder routing-keyword row (the row also containing finer/coarser/grind setting).
- **Actual**: `/consult` SKILL.md L28: "| grind, grinder, finer, coarser, grind setting, rpm, motor speed, grind speed | Active grinder reference … → `knowledge/grinders/` | …". `grep -n "rpm"` and `grep -n "grind setting"` both report line 28 (same row). No new routing machinery, no number literals.
- **Verdict**: PASS

### Requirement R15: No hardcoded RPM numbers in skills (single source of truth)
- **Expected**: `grep -rEc "\b(1000|1100|1200|1400)\b"` = 0 across all four skill files; numbers live only in DF64V.md / user-setup.
- **Actual**: All four skill files return 0 (consult, new-coffee, diagnose, feedback). Verified directly. RPM numbers appear only in `knowledge/grinders/DF64V.md` (their SSOT) and the `grind-map.example.md`/`user-setup` data files.
- **Verdict**: PASS

### Edge cases (spec)
- **Fixed-speed (Sette) active**: PASS — gate OFF everywhere (no prompts, blank RPM cell, no RPM row, Operating RPM unused, /diagnose unchanged). Verified by the SETTE_270.md gate-signal = 0 and each skill's OFF clause.
- **Variable-speed, Operating RPM not yet set**: PASS — `/new-coffee` falls back to the DF64V reference default (L72/L260); `/feedback` prompts once and writes blank if still unknown, never infers (L66, L157).
- **RPM changed mid-bag**: PASS — R11 guard (L109–115) warns + re-anchors and updates/creates user-setup Operating RPM.
- **Grinder unconfigured / user-setup unreadable / no map match**: PASS — gate OFF, never error (each gate restatement carries the contract fallback + `never error`).
- **Pre-existing pre-fix grind-map row (column count ≠ 13)**: PASS — misaligned-row guard (L153) flags, no auto-backfill.
- **Stale RPM in /diagnose after grinder switch**: PASS — known RPM used as advisory context for the shot; no RPM → unchanged; no RPM facts asserted beyond DF64V framing.
- **Markdown parse caveat**: N/A by design — no positional grind-map parser is built; current RPM comes from the user-setup single read.

### Headless Verification Protocol
- **Discriminating structural greps**: PASS — independently re-run. R15 global scan = 0 (all four skills); R7 discriminator = 1 (DF64V) / 0 (SETTE_270); RPM_RECOMMENDATION = 1 inside `<claims>`; R12 hierarchy-block RPM = 0; all Phase-1 greps hold.
- **Agent-reasoned hedge audit (Task 1d)**: PASS — re-run over `DF64V.md`. Every body/clarity mention (L39, L42, L48, L50, L52, L54, L55, L56, L58, L97, L99, L101, L103) is either the hedge framing itself, an explicit anti-claim ("do not assume a direction", "No printed 'raise RPM → go finer' rule lives here on purpose"), or co-occurs in-sentence with a contested/vendor/McKeon/Hoffmann/null/unproven/plausible hedge. No bare directional "(more) RPM → (more/fuller) body/clarity" assertion survives anywhere, including the reworded L42 region and the former L85 (now gone, replaced by the hedged L103). The new note anchors on the shot timer and refuses a printed re-dial direction.
- **Agent-reasoned behavioral trace (two input states)**: PASS — verification-trace.md records, for each traced skill, State-A (ON) and State-B (OFF) branches with verbatim quotes of the governing gate/writer/output lines; the quotes match the committed skill text. Mid-bag delta-only and routine-"too sour"-no-RPM behaviors hold against the quoted lines.

## Requirements Drift
**State**: none
**Findings**:
- None
**Update needed**: None

(`cortex/requirements/project.md` is an unconfigured template — all sections are TODO placeholders — and no area docs matched the lifecycle tag `df64v-ssp-migration`. The drift baseline is therefore effectively empty. Every change in the implementation traces directly to a spec requirement (R1–R15), the spec's Edge cases, or the Headless Verification Protocol; nothing introduces behavior surprising relative to the spec. Per the review instructions, drift defaults to none.)

## Stage 2: Code Quality
- **Naming conventions**: Consistent with existing patterns. The new `## RPM as a dial-in lever` heading matches the file's `## `-section style; the `## Motor Speed (RPM) — A Separate, Non-Chirp Coordinate` notation heading mirrors `_NOTATION.md`'s descriptive-heading convention; the summary-table row uses the existing `| Concept | Rule |` format. The `Operating RPM` field follows the Equipment-table + Notes-bullet pattern established for the Puck Screen field. The conditional `| RPM | [placeholder] | [variable-speed only] |` row matches the existing `| Temperature | X°C | … |` and `| Grind | XY | … |` runtime-placeholder rows.
- **Error handling**: Robust. Every gate/OFF/fallback clause inherits the Active Grinder contract's attempt-then-fallback discipline and explicitly carries `never error`. All OFF paths (fixed-speed, no match, no resolved file, contract fallback, unreadable user-setup) degrade to inert RPM behavior (no prompts, blank cell, no row). The "never infer" rule is stated at every write point. The misaligned-row guard flags rather than mutating, and the mid-bag write reaches the commit path even on an unrated shot.
- **Test coverage**: The plan's two-part Headless Verification Protocol was actually executed and holds against the real files. I independently re-ran every runnable grep AC (Phase 1 and Phase 2) and confirmed the counts; the agent-reasoned hedge audit and behavioral trace in verification-trace.md are accurate against the committed skill/knowledge text (governing lines quoted match the files). The verification correctly used only ugrep-safe fixed-string / simple-alternation greps and did not attempt the rejected complex-regex form.
- **Pattern consistency**: New sections follow existing conventions. The feedback gate pre-check is structurally analogous to the existing Puck-Screen gated pre-check; the grind-map writer RPM-cell sub-step parallels the Puck Screen? cell rule; the experiment-triggered RPM branch is cleanly separated from the adjustment hierarchy (zero collision between Task-7 and Task-8 surfaces; exactly one gate restatement). The `grind-map.example.md` schema sync matches the live file byte-for-byte (header + legend).

## Verdict
```json
{"verdict": "APPROVED", "cycle": 1, "issues": [], "requirements_drift": "none"}
```
