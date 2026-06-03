# Research: Operationalize RPM as a first-class extraction variable across the dialing skills (DF64V variable-speed)

> Lifecycle: `operationalize-rpm-as-an-extraction-variable` · tier: complex · criticality: high
> Mode: codebase + synthesis grounding (NOT a web-research spike — 025 owns the RPM science, established contested/null).
> Fan-out: 7-agent core wave (Codebase, Web, Requirements & Constraints, Active-Grinder Gating, Knowledge-Synthesis Grounding, grind-map Data Format, Tradeoffs) + 1 adversarial pass.

## Codebase Analysis

**Real paths (the ticket body's `skills/` is wrong — that dir does not exist):**
- Skills: `.claude/skills/{new-coffee,feedback,diagnose,consult}/SKILL.md` (+ `new-coffee/references/SELF_CHECK.md`, `diagnose/references/{DIAGNOSTIC_TREES,TELEMETRY_PATTERNS}.md`).
- **NO `plugins/cortex-core/` mirror exists in this repo, and no pre-commit hook.** The "edit canonical, mirrors regenerate via pre-commit" line in CLAUDE.md/ticket is cortex-core boilerplate that does **not** apply here. `.claude/skills/` is the sole canonical source — edit those directly, nothing to propagate.

**Where RPM wiring lands (file:section):**
- `new-coffee/SKILL.md` — Step 4 SYNTHESIZE (~L62-72: add RPM to the build list, gated to variable-speed); **Step 4b SELF_CHECK `<claims>` block (~L79-99): an `RPM_RECOMMENDATION` claim must be added or RPM is the one starting parameter that escapes the critic/arbiter check**; Output "Recommended Starting Parameters" table (~L229-236: add `| RPM | ~1000–1100 | … |` row, conditional). Grinder resolution already restated at `new-coffee:58`.
- `feedback/SKILL.md` — Conditionally-Load table (L29-30); Step 2 GATHER table (L48-56: optional RPM capture); Step 3 ANALYZE adjustment hierarchy (L66-103: any RPM lever slots *below* grind/ratio/temp/pressure/puck-prep + the mid-bag re-dial guard); **Step 4b grind-map write (L133-140) — the load-bearing fix**; Step 4c `manage_shot_notes` (RPM is not an MCP param — out of scope unless folded into `notes`); Step 4e Private Repo Commit (L159-168, unchanged — RPM rides existing path).
- `diagnose/SKILL.md` — Step 3 CORRELATE (L139-154). **Diagnose has NO grinder-resolution step today** (it only reads `user-setup.md` for Active Coffee); adding RPM requires inserting contract resolution it lacks. (See Open Questions — scope challenged.)
- `consult/SKILL.md` — Step 1 routing table (L23-38; grind/grinder row at L28); Step 1b RESOLVE Active Grinder Reference (L44-50); Step 5 deep-tier row (L85). RPM theory Qs already route to `DF64V_REFERENCE.md` via the existing cascade — **cheapest, lowest-risk touch-point (one keyword-row edit).**

**Patterns to mirror:**
- **Active Grinder contract** canonical sentence (CLAUDE.md rule 7) is restated verbatim at `new-coffee:58`, `feedback:29`, `consult:48`. Copy it wherever a skill newly resolves the grinder for RPM.
- **Puck Screen gated-pre-check** (`feedback:77-86`, `diagnose:145-154`; cell-write rule `feedback:137`) is the structural analog: a gated check that **routes to the knowledge file as single source of truth** rather than carrying its own numbers. RPM gating + the grind-map RPM cell should mirror it exactly.

**grind-map column structures (exact):**
- `grind-map.example.md` (checked-in, real file): **12 cols, NO RPM** — `| Coffee | Roast | Process | Origin | Days Off Roast | Grind | Profile | Ratio | Temp | Rating | Date | Puck Screen? |`
- live `grind-map.md` (symlink → private data repo): **13 cols, RPM at position 7** — `… | Grind | RPM | Profile | …`, with legend line *"RPM — variable-speed grinder RPM as an integer (e.g. `1100`); leave blank for fixed-speed grinders."*

## Web Research

Light pass only (RPM *science* explicitly out of scope; confirmed no science searches run). Takeaways:
- **No off-the-shelf RPM-logging standard exists** — the DF64V hardware/app does not persist or export RPM. We are defining the convention; keep it lightweight and our own.
- **Structural prior art for grinder-specific fields**: community dialing logs scope grinder-specific columns *to the grinder* (record the grinder's setting range alongside the setting), yielding empty/NA cells for grinders lacking that attribute — validates "RPM is a grinder-conditional field, blank/NA for fixed-speed."
- **UX for an optional secondary lever**: progressive disclosure — reveal RPM only when relevant (variable-speed resolved), surface it contextually (after primary levers), keep the default path RPM-free. Frame around the **one settled claim** (changing RPM shifts distribution → forces a grind re-dial) rather than the contested body/uniformity story.
- Unfetched (403/load-fail, snippets only): home-barista shot-logging thread; coffeetime DF64V inverter experiment; home-barista DF64V settings thread.

## Requirements & Constraints

No formal `cortex/requirements/` constraints — `project.md` is an unconfigured template. Operative constraints live in **CLAUDE.md** and prior lifecycles:
- **Active Grinder field parsing contract (027, CLAUDE.md rules 1-7)** — resolves the `user-setup.md` Grinder field by case-insensitive substring (sette→SETTE_270.md, df64v→DF64V.md), first match wins, attempt-then-fallback (never pre-check, never error), no hardcoded default. **RPM gating must ride this existing resolution — do not invent a parallel mechanism, do not modify the contract (027 owns it).** `_`-prefixed files (`_TEMPLATE.md`, `_NOTATION.md`) are never map targets.
- **Core Rules (CLAUDE.md)** — "Sour AND bitter = channeling → fix puck prep, NOT grind"; "RPM is a grinder control, not a temp/pressure claim." RPM-as-lever must never be offered as a channeling fix, and must not introduce absolute numbers competing with the temp/pressure/ratio tables.
- **Data Architecture / Auto-commit** — `grind-map.md` is a symlink into the private data repo; the RPM write is a data-writing step that rides the existing `.data-repo-path` commit path (no new commit surface).
- **Parent epic 024 (grinder-agnostic, fork-able)** — RPM applies *only* to variable-speed grinders; fixed-speed (Sette) get no prompts, blank column. Must not hardcode DF64V as default.
- **025 owns the RPM science** — the **seven "wrong-if-stated-baldly" facts** are binding hedges. Fact #2: espresso RPM ~1000–1200 default; 1400 = vendor more-body preference, not a floor. Fact #6 (most load-bearing): "RPM is a body lever" is **contested** — McKeon Aloe measured higher RPM → **coarser/fewer fines** (opposite the vendor story); Hoffmann blind test = null. Hedge hard; never canonize "RPM = body."
- **026 owns the grind-map RPM column structure** — populate, don't restructure. (But note: 026 updated only the *live* file, not the example — see Open Questions.)
- **025 owns `_NOTATION.md`'s chirp/epoch contract** — RPM rules must be additive and consistent, not a redefinition. `_NOTATION.md` is confirmed **silent on RPM today** (genuine gap).

## Active-Grinder Variable-Speed Gating

**Central question: how does a skill know the active grinder is variable-speed vs fixed-speed?** The Active Grinder contract resolves only *which file*; it carries **no speed signal**. Today there is no machine-readable speed field — DF64V.md says "variable-speed" in prose only (intro L3, `## Motor Speed (RPM)` heading L34); SETTE_270.md signals fixed by *absence* of any RPM section; `_TEMPLATE.md` has no speed field (only HTML-comment hints); the `user-setup.md` Grinder field is free prose.

**Two competing detection designs surfaced (see Open Questions for the decision):**
- **(Gating agent) Declarative `**Speed:** variable|fixed` field** added near the top of each `knowledge/grinders/<NAME>.md` + `_TEMPLATE.md`; skill reads it after contract resolution; missing/fallback → fixed (RPM disabled). Pro: explicit, fork-declarable. Con: adds SETTE_270.md + _TEMPLATE.md to touch-points; creates a 3rd place "variable-speed" lives (drift surface); a variable grinder file that *forgets* the field → RPM silently disabled → data-loss against the "logging is the longitudinal study" thesis.
- **(Adversarial agent) Gate on "resolved grinder file contains a Motor Speed / RPM section"** — presence *is* the signal; SETTE already omits it; no new field, no SETTE_270.md / _TEMPLATE.md edits. Pro: can't drift (the section is the capability); a fixed grinder simply has no section. Con: implicit (a forker must know to include an RPM section to enable RPM logging — though arguably that's self-evident).

Both agree: **gate on the resolved grinder FILE, not the user-setup prose** (robust to "DF64V typed without speed words"), and the conservative default (no signal → RPM disabled, never error) composes with the contract's attempt-then-fallback.

## Knowledge-Synthesis Grounding (highest-risk deliverable)

**What the repo actually establishes:** `DF64V_REFERENCE.md` "RPM as a Body/Clarity Lever" (L117-125) states RPM→body is contested (McKeon coarser, Hoffmann null, "hot topic"), and stops at *"the primary practical consequence of changing RPM is that your grind setting needs a re-dial (RPM affects the flow-time at a given collar position)"* — **deliberately no re-dial direction.** The quick-tier `DF64V.md` is thinner: it has the range + "coarse lever / forces re-dial" but omits the McKeon/Hoffmann evidence and, at **L85, leans pro-vendor**: *"manage body via … slightly higher RPM."*

**The re-dial-direction question:** The ticket proposes the quick-tier state "raise RPM → go finer to hold shot time," citing McKeon. McKeon measured "higher RPM → **coarser**." The "go finer" is a **compensation inference** (coarser puck → faster flow → grind finer to restore shot time), NOT a contradiction — it is directionally reasonable and consistent with DF64V_REFERENCE.md's "affects flow-time / forces re-dial." BUT it is a **two-link inference off a single contested (n=1) measurement**, and **no repo artifact actually asserts the direction**. The deep tier (which backs the quick tier) deliberately omits it; the quick tier must not assert *more* certainty than its backing reference.

**Agreed content for the quick-tier "RPM as a dial-in lever" note:** (a) narrow **triggers** — only after grind/ratio/temp/puck-prep are exhausted, OR a deliberate logged body/clarity experiment; never the first move; never a channeling fix; (b) **the re-dial fact** anchored on shot time ("after an RPM change, re-dial grind to restore target shot time; let your timer decide"); (c) **contested hedge** importing McKeon-coarser + Hoffmann-null + "your own logged data is the real signal"; (d) **must-nots** — no unqualified "RPM = body," no direction-as-law, don't claim McKeon itself says "go finer." **Pre-req both agents flag: reconcile/fix DF64V.md L85** — it currently contradicts the hard "no RPM=body" Constraint and would canonize the unhedged claim if a skill surfaced it verbatim. (The *whether to print the "go finer" tendency at all* is an Open Question — knowledge agent: include as hedged tendency; adversarial: omit direction entirely, shot-time only.)

## grind-map Data Format & Writer Correctness

- **`grind-map.example.md` (in scope per user decision):** insert RPM at position 7 — header, separator (`|-----|`), sample row (recommend `1100` to model variable-speed, matching the live legend), and a legend line mirroring the live file **byte-for-byte**: *"RPM — variable-speed grinder RPM as an integer (e.g. `1100`); leave blank for fixed-speed grinders."*
- **`/feedback` writer (feedback:135) — MANDATORY:** currently *"append … these 12 fields … `Coffee, Roast, Process, Origin, Days Off Roast, Grind, Profile, Ratio, Temp, Rating, Date, Puck Screen?`"*. Change to **13 fields, RPM at position 7**: `… Grind, RPM, Profile, Ratio, …`. Add an RPM-cell sub-step parallel to the Puck Screen cell rule: integer RPM for variable-speed (resolved via the contract), **blank** for fixed-speed/unresolved, never infer. Update the L140 "no back-fill" note's column counts (11/12 → 13). **This is not optional plumbing — until fixed, the very next appended row is misaligned (12 fields into a 13-col table).**
- **`_NOTATION.md`:** add a `## Motor Speed (RPM) — A Separate, Non-Chirp Coordinate` section after the Core Principle / before Epoch Binding: integer absolute value; **grinder config, NOT a chirp coordinate, NOT epoch-bound** (a re-zero/burr-swap doesn't invalidate it); blank for fixed-speed; don't infer; logged as an independent column (never folded into `chirp + N marks`). Add a summary-table row.
- **No historical-row repair needed:** the 026 migration (`4e9b63e`) re-created the live `grind-map.md` with the 13-col header and **zero data rows** (Sette rows archived to `grind-map-sette-270.archive.md`, which keeps its old 12-col header, out of scope). So there are no column-shifted rows to fix — the fix is forward-looking (fix the writer before next run). Archive file untouched.
- **Mid-bag RPM-change re-anchor (Edge):** `/feedback` does **not** read grind-map *history* today — it only appends. A full guard needs a new "read latest prior row for active coffee" capability (raises a bag-identity question: title? title+roast-date?). Cheaper alternative (adversarial): a prompt-time nudge ("if the user states a different RPM than last logged, remind them grind needs re-dialing") without a structured last-row parser. (Open Question — build parser vs prompt-nudge.)
- **Parse caveat:** a 13-col row with a *blank* RPM cell is NOT structurally identical to a 12-col row with *no* RPM column. Markdown renders both empty, but any positional (`|`-split, index-7) parser reads "Profile" as RPM on a 12-col row. Relevant only if a column-index parser is ever built (e.g., the mid-bag reader).

## Tradeoffs & Alternatives: /feedback RPM lever aggressiveness

Current `/feedback` adjustment hierarchy: grind → yield/ratio → temp → pressure/profile → puck prep. RPM must slot *below* all of these. Options:
- **A — log-only:** record RPM (variable-speed gated), never suggest changing it. Lowest complexity, zero canonization risk, fully honors "never the first move." Doesn't satisfy the mid-bag re-dial Edge alone.
- **B — log + standing hierarchy lever:** adds RPM as lowest-priority hierarchy entry with a hedged offer. Fully realizes the ticket's "secondary lever" language but **highest canonization risk** (offering RPM-as-body-lever at all is a directional signal to an intermediate barista, against the hard Constraint) + highest maintenance + fragile trigger discipline.
- **C — log + experiment-only:** mention RPM adjustment *only* when the user explicitly frames a body/clarity experiment (user's words are the gate). Safe, useful to the curious, matches the ticket's "deliberately chasing an experiment" trigger.
- **D — log + re-dial guard:** A plus the **one proactive behavior the science fully supports** — warn/re-anchor grind when RPM changes (the re-dial consequence is *uncontested*). Satisfies the Edge at no science risk.

**Research recommendation (input to Plan, not a final call): D (+ optionally C); steer away from B** unless the Plan can pin an enforceable, testable trigger *and* bulletproof hedge wording. Decision axis: how much do we trust scripted hedges to neutralize a *directional* offer of a *measurement-contradicted* lever to an intermediate audience? Low trust → D(+C); high trust → B (with D folded in). The ticket's own "logging *is* the longitudinal study" framing favors data-collection (A/D) over assertion (B).

## Adversarial Review

Strongest challenges (fold into Spec):
- **Scope creep:** the core wave re-expanded a "plumbing + thin synthesis" ticket. **Cut the `**Speed:**` field** (gate on RPM-section presence instead → no SETTE/_TEMPLATE edits). **Cut/defer /diagnose** (RPM isn't in `analyze_shot` telemetry → nothing to correlate; any out-of-range check belongs in /feedback which already has grind context; Acceptance sketch has no /diagnose criterion). **Defer the mid-bag history parser** (prompt-nudge instead).
- **Re-dial direction: omit it.** Even hedged, "raise RPM → go finer" is a 2-link inference off one contested measurement, exceeding the deep tier's own direction-free ceiling. Anchor on the shot timer only.
- **DF64V.md L85 is an active contradiction, not just "under-hedged"** — fix it *first* as a pre-req; a skill surfacing it verbatim canonizes the forbidden claim.
- **/feedback writer is worse than "a column nobody fills"** — it will write *misaligned* rows on next run. Mandatory fix.
- **grind-map.example.md is genuinely unsynced** — the ticket's "already present, do not restructure" premise is false for the example. (Resolved: in scope per user.)
- **consult is the cheapest, safest win** — one keyword-row edit; ship first.
- **new-coffee RPM must enter the SELF_CHECK claims block**, or it's the only starting parameter with no adversarial check.
- Single source of truth: `DF64V.md ## Motor Speed (RPM)` for numbers, `_NOTATION.md` for logging format; skills route, never hardcode the range.

## Open Questions

These are genuine design decisions / inter-agent contradictions for the Spec phase to resolve with the user:

1. **Variable-speed detection mechanism** (contradiction): declarative `**Speed:** variable|fixed` field on every grinder file + `_TEMPLATE.md` (gating agent — explicit, fork-declarable, but +2 touch-points and a silent-disable data-loss risk) **vs.** gate on "resolved grinder file contains a Motor Speed / RPM section" (adversarial — no new field, can't drift, fewer touch-points, but implicit). Recommend leaning to the section-presence gate unless the Spec wants the explicit declaration for forkers; either way gate on the resolved *file*, default-off, never error.
2. **/diagnose in or out of scope** (contradiction): codebase agent mapped an RPM-correlation insertion point; adversarial argues cut/defer entirely (RPM not in telemetry; no diagnostic power beyond what /feedback's grind-map context provides; no Acceptance criterion). Decide whether `/diagnose` is touched at all.
3. **Re-dial direction in the quick-tier note** (contradiction): include "raise RPM → go finer to hold shot time" as an explicitly-hedged *tendency* anchored to shot time (knowledge agent) **vs.** omit the direction word entirely and state only "re-dial to restore target shot time, let your timer decide" (adversarial). Both anchor on shot time; the split is whether to print the directional word.
4. **Mid-bag RPM-change guard depth**: build a new "read latest prior grind-map row for active coffee" capability in `/feedback` (full guard, needs a bag-identity rule) **vs.** a prompt-time nudge only (defer the parser). Tied to the /feedback lever-aggressiveness choice.
5. **/feedback lever aggressiveness (A/B/C/D)** — Plan-phase decision; research recommends D(+C), avoid B. Surfaced here so Spec can set the constraint the Plan implements.
6. **grind-map.example.md sample-row RPM value**: `1100` (models variable-speed, matches live legend) vs blank (models fixed-speed back-compat). Recommend `1100`.
7. **Does /feedback actively prompt for RPM when missing**, or silently leave blank? Affects how often the column gets populated (the "longitudinal study" depends on it). The ticket says "consider prompting for"; needs a decision.
8. **DF64V.md L85 reconciliation** — confirm it's fixed as a pre-req (both agents flag; not really optional, but listed so Spec captures it explicitly as in-scope work).
