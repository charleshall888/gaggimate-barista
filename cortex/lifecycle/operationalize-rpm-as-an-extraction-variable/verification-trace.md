# Verification Trace — operationalize-rpm-as-an-extraction-variable (Task 10)

**Verification record artifact** (not shipped product). Records the two-part Headless
Verification Protocol prescribed by `spec.md` → Technical Constraints → "Headless verification
protocol": (1) discriminating structural greps confirmed runnable under ugrep, and (2) an
agent-reasoned behavioral trace over two described input states. A requirement passes only when
**both** its grep ACs and its behavioral-trace expectation hold.

- **Engine:** `grep` routes to `ugrep 7.5.0 aarch64-apple-darwin23.6.0` (confirmed via `grep --version`).
- **Date:** 2026-06-03
- **Scope of this task:** READ-ONLY against skill/knowledge files; the ONLY write is this trace
  file. The two input states (A/B) are described **inline**, NOT materialized — the skills read the
  fixed relative-path symlinked `user-setup.md`, so a `$TMPDIR` copy would never be consumed, and
  the protocol forbids touching the real symlinked `user-setup.md`/`grind-map.md`.
- **Retired regex NOT attempted:** the complex `grep -inE "(higher|more…).{0,40}…"` quantified-
  alternation regex errors under ugrep (`exceeds complexity limits`, exit 2) and silently
  false-passes (errors print no lines → naive check misreads as clean). The hedge audit below is
  therefore done by **agent reasoning** over fixed-string-surfaced candidate lines, per Task 1(d).

---

## Part 1 — Discriminating structural greps (runnable)

### 1.1 — R15 global "no hardcoded RPM numbers" scan (all four skill files)

Command:

```
grep -rEc "\b(1000|1100|1200|1400)\b" .claude/skills/new-coffee/SKILL.md .claude/skills/feedback/SKILL.md .claude/skills/diagnose/SKILL.md .claude/skills/consult/SKILL.md
```

Observed output:

```
.claude/skills/consult/SKILL.md:0
.claude/skills/feedback/SKILL.md:0
.claude/skills/new-coffee/SKILL.md:0
.claude/skills/diagnose/SKILL.md:0
```

**Verdict: PASS.** Every one of the four skill files returns `0` — no authored RPM-range literals
(`1000`/`1100`/`1200`/`1400`) appear in any skill. The numbers live only in `DF64V.md` /
`user-setup.md` and are read at runtime. (Note: `grep -rEc` exits 1 when all counts are 0 because
no lines matched; the per-file `:0` counts are the observable evidence, not the exit code.)

### 1.2 — R7 gate-signal discriminator (`## Motor Speed (RPM)` heading)

Commands and observed output:

```
$ grep -c "## Motor Speed (RPM)" knowledge/grinders/DF64V.md
1            (exit 0)
$ grep -c "## Motor Speed (RPM)" knowledge/grinders/SETTE_270.md
0            (exit 1)
```

**Verdict: PASS.** The literal gate heading `## Motor Speed (RPM)` is present exactly once in the
variable-speed `DF64V.md` (= 1) and absent from the fixed-speed `SETTE_270.md` (= 0). This is the
single signal every skill's R7 gate keys on. It also guards against drift: a `## Motor Speed (RPM)`
line accidentally added to the untouched `SETTE_270.md` would flip its count to ≥1 and fail here.

Drift corroboration — `SETTE_270.md`'s only `##` headings are non-RPM:

```
$ grep -n "^## " knowledge/grinders/SETTE_270.md
9:## Adjustment System
49:## Quick Adjustment Guide
```

### 1.3 — Task 8(ii) `RPM_RECOMMENDATION` claim in SELF_CHECK `<claims>` block

```
$ grep -c "RPM_RECOMMENDATION" .claude/skills/new-coffee/references/SELF_CHECK.md
1            (exit 0)
```

Location confirmed inside the `<claims>` block (block opens line 13, closes line 28; claim at
line 25):

```
$ grep -n "RPM_RECOMMENDATION\|<claims>\|</claims>" .claude/skills/new-coffee/references/SELF_CHECK.md
13:<claims>
25:RPM_RECOMMENDATION: [value | N/A — fixed-speed] (source: [user-setup Operating RPM | DF64V.md reference default])
28:</claims>
```

**Verdict: PASS.** Exactly one `RPM_RECOMMENDATION` line, and it is inside the `<claims>` block.
Note the claim line itself routes the value to `user-setup Operating RPM | DF64V.md reference
default` and writes no literal number — consistent with R15.

---

## Part 2 — Task 1(d) agent-reasoned hedge audit (re-run)

**Goal:** No bare directional/body RPM claim survives un-hedged in `knowledge/grinders/DF64V.md`.
The retired complex regex is unrunnable under ugrep, so candidate lines are surfaced with
fixed-string greps (`body`, `higher`, `more rpm`, `more body`, `raise`, `increase`) and each
candidate is reasoned through: a line PASSES only if the directional/body assertion is explicitly
negated or hedged **within the same sentence** (co-occurring with `contested` / `not confirmed` /
`vendor` / `McKeon` / `Hoffmann` / `null` / `unproven` / `plausible` / an explicit negation), or is
itself the hedge framing. A bare match outside a hedged sentence is a FAIL.

| Line | Verbatim text (abbreviated) | Hedge present in-sentence | Verdict |
|------|------------------------------|----------------------------|---------|
| 39 | "**~1400 RPM** is a retailer preference reported to shift toward more body (vendor-framed; …); it is not a floor or default." | `retailer preference`, `vendor-framed`, `it is not a floor or default` | PASS — hedged |
| 42 | "… the link between RPM and cup body is contested, not a settled dial." | `contested, not a settled dial` | PASS — hedged |
| 48 | "… run a *deliberate, logged* body/clarity experiment. RPM is **never** the opening move … **never** a channeling fix …" | frames body as an *experiment*, never an asserted dial; no directional claim | PASS — no bare claim |
| 50 | "… Let your shot timer tell you which way to move the grind — do not assume a direction. (No printed 'raise RPM → go finer' rule lives here on purpose; the timer decides.)" | explicitly *refuses* a printed direction (`do not assume a direction`, `No printed … rule`) | PASS — anti-directional |
| 52 | "**Why 'more RPM → more body' is contested.** The popular framing that higher RPM adds body is **contested**, not established:" | `is contested, not established` | PASS — hedged (heading of the hedge note itself) |
| 54 | "One rigorous independent measurement (McKeon Aloe) found higher RPM shifted the distribution *coarser* … the opposite of the vendor 'more body' story." | `McKeon`, `the opposite of the vendor 'more body' story` | PASS — counter-evidence |
| 55 | "Hoffmann's blind tasting found no clean correlation here at all (null result)." | `Hoffmann`, `null result` | PASS — null evidence |
| 56 | "The vendor-framed 'RPM is a body lever' claim is unproven; treat it as plausible-at-best, not a calibrated dial." | `vendor-framed`, `unproven`, `plausible-at-best, not a calibrated dial` | PASS — hedged |
| 58 | "So do not dial against RPM as if 'RPM = body' were confirmed. **Your own logged RPM↔outcome data is the real signal** …" | explicit negation `do not dial … as if … were confirmed`; own-data hedge | PASS — anti-claim |
| 97 | "Flat burrs tend toward clarity … but this is a contested tendency, not a deterministic law (Hoffmann's blind tasting found no clean burr-shape → body/clarity correlation)." | `contested tendency, not a deterministic law`, `Hoffmann … no clean … correlation` | PASS — hedged (burr, not RPM) |
| 99 | "… the 'flat = clarity, less body' characterisation applies with **less force** here …" | qualifies/weakens the characterisation (`less force`); burr-shape, not RPM | PASS — hedged |
| 101 | "The **Red Speed** TiAlCN coating is vendor-described as adding body … the vendor itself notes this is 'secondary and grinder-dependent.' Treat as plausible, not established." | `vendor-described`, `secondary and grinder-dependent`, `plausible, not established` | PASS — hedged (coating, not RPM) |
| 103 | "… RPM is *not* a settled body dial: the 'more RPM → more body' link is contested (see … McKeon-coarser / Hoffmann-null evidence …). Reach for dose and ratio first; only run RPM as a deliberate, logged experiment." | `not a settled body dial`, `is contested`, `McKeon-coarser / Hoffmann-null` | PASS — hedged |

**Verdict: PASS.** Every candidate body/directional line in `DF64V.md` is either the hedge framing
itself, an explicit anti-claim, or co-occurs with a contested/vendor/McKeon/Hoffmann/null/unproven/
plausible hedge in the same sentence. **No bare directional or "RPM = body" assertion survives.**
Corroborates R1(iii) and R2: the prior un-hedged Burr-Character line ("Manage body via higher dose
or slightly higher RPM …") is gone — `grep -c "Manage body via higher dose or slightly higher RPM"
knowledge/grinders/DF64V.md` would return 0 (the L103 successor is the hedged rewrite quoted above).

---

## Part 3 — Agent-reasoned behavioral trace (two described input states)

### Input states (described inline — NOT materialized as files)

- **State A — variable-speed, RPM ON.** Active grinder = **DF64V**. Resolves (per the Active Grinder
  contract) to quick-tier `knowledge/grinders/DF64V.md`, which **contains** a section heading exactly
  `## Motor Speed (RPM)` (Part 1.2 = 1). `user-setup.md` `Operating RPM = 1100`.
- **State B — fixed-speed, RPM OFF.** Active grinder = **Baratza Sette 270**. Resolves to quick-tier
  `knowledge/grinders/SETTE_270.md`, which has **no** `## Motor Speed (RPM)` section (Part 1.2 = 0).
  No `Operating RPM`.

For each skill, the branch is recorded with a **verbatim quote** of the governing gate/writer/output
line that drives it — this makes the trace falsifiable against the actual committed skill text.

---

### 3.1 — `/new-coffee` (`.claude/skills/new-coffee/SKILL.md`)

**Governing gate line (Step 4 SYNTHESIZE, line 72), verbatim:**

> **RPM (variable-speed grinders only — gated):** After resolving the active grinder per the Active Grinder field parsing contract (already done in Step 3 CONSULT), check whether the resolved **quick-tier** `knowledge/grinders/<NAME>.md` contains a section heading exactly `## Motor Speed (RPM)`. **If it does → RPM behavior ON:** include an RPM starting recommendation in the output table (see the conditional RPM row below). The rendered value is the user's `Operating RPM` from `user-setup.md` (per its integer parse rule) if set, else the reference default from that grinder file's `## Motor Speed (RPM)` section — do not restate the literal numbers here; read them at runtime. **If the heading is absent / no quick-tier file resolved / the Active Grinder contract fell back to fallback / `user-setup.md` is unreadable → RPM behavior OFF:** this is a **fixed-speed** path — omit the RPM row entirely and **never error**.

**Governing output-row line (Output Format note, line 260), verbatim:**

> **Note (conditional RPM row):** The `| RPM | [placeholder] | [variable-speed only] |` row is emitted **only when the Step 4 SYNTHESIZE gate is ON** (the resolved quick-tier grinder file has a `## Motor Speed (RPM)` section). When the gate is OFF — a **fixed-speed** grinder, no resolved file, contract fallback, or unreadable `user-setup.md` — omit the row entirely and **never error**. When emitted, the `[placeholder]` renders the user's `Operating RPM` from `user-setup.md` if set, else the reference default …

- **State A → RPM ON.** DF64V's quick-tier file has `## Motor Speed (RPM)` (Part 1.2 = 1), so the
  gate clause "**If it does → RPM behavior ON:** include an RPM starting recommendation in the output
  table" fires. The `| RPM | [placeholder] | [variable-speed only] |` row renders, and its
  `[placeholder]` resolves to the `Operating RPM` (1100) from `user-setup.md` — **read at runtime,
  not written into SKILL.md** (Part 1.1 = 0 confirms no literal). **Expected branch: RPM row rendered. HOLDS.**
- **State B → RPM OFF.** SETTE_270.md has no `## Motor Speed (RPM)` heading (Part 1.2 = 0), so the
  gate's OFF clause "the heading is absent … → RPM behavior OFF … omit the RPM row entirely and
  **never error**" fires, reinforced by the output note "When the gate is OFF — a **fixed-speed**
  grinder … omit the row entirely." **Expected branch: no RPM row. HOLDS.**

**`/new-coffee` verdict: PASS** (State A renders the row, State B omits it; both governed by the
quoted lines).

---

### 3.2 — `/feedback` (`.claude/skills/feedback/SKILL.md`)

**Governing gate line (Step 3 ANALYZE, line 72), verbatim:**

> Per the CLAUDE.md Active Grinder field parsing contract, read the `user-setup.md` Grinder field, resolve the active grinder reference by case-insensitive substring against the contract's map (first match wins), attempt to load that `knowledge/grinders/` file, and on any miss or unreadable `user-setup.md` degrade to grinder-relative step advice plus the unconfigured nudge — never error. RPM behavior is **ON** iff the resolved **quick-tier** `knowledge/grinders/<NAME>.md` contains a section whose heading is exactly `## Motor Speed (RPM)`. Gating reads the quick-tier file only (not the deep-tier reference, not the Grinder prose). No match, no resolved file, or contract fallback → the grinder is **fixed-speed**: RPM behavior is **OFF** (no RPM prompts, blank RPM column), **never error**. This gate governs the RPM read in Step 2 and the RPM cell of the grind-map writer in Step 4b.

**Governing read line (Step 2 COLLECT, line 66), verbatim:**

> **Operating RPM (variable-speed grinders only — gated by the Step 3 RPM gate):** When the gate is ON, read the current `Operating RPM` from `user-setup.md` (parse: an integer = the current RPM; missing/blank/`None`/non-integer = unknown) and carry it forward as the RPM value for the grind-map row in Step 4b. … When the gate is OFF (fixed-speed grinder), do not read or prompt for RPM.

**Governing writer line (Step 4b, line 154), verbatim:**

> 3. Append a new row to the **end** of the file with these 13 fields in order: `Coffee, Roast, Process, Origin, Days Off Roast, Grind, RPM, Profile, Ratio, Temp, Rating, Date, Puck Screen?`

**Governing RPM-cell rule (Step 4b, lines 156–158), verbatim:**

> 5. **RPM cell — value comes from the Step 2 / Step 3 RPM gate (never infer):**
>    - Variable-speed (gate ON): write the Operating RPM resolved in Step 2 as a plain **integer** (the `user-setup.md` value, or the session-stated value if the user overrode it). If the gate is ON but RPM is still unknown after the one light prompt, write a **blank** cell.
>    - Fixed-speed (gate OFF), unresolved grinder, or contract fallback: write a **blank** cell.

- **State A → RPM ON, stamps 1100.** DF64V quick-tier has `## Motor Speed (RPM)` → gate ON
  ("RPM behavior is **ON** iff the resolved **quick-tier** … contains a section whose heading is
  exactly `## Motor Speed (RPM)`"). Step 2 reads `Operating RPM` = 1100 and carries it to Step 4b;
  the writer emits the 13-field row with the RPM cell = the integer `1100` ("write the Operating RPM
  resolved in Step 2 as a plain **integer**"). **Expected branch: 1100 stamped into the row. HOLDS.**
- **State B → RPM OFF, blank cell.** SETTE_270.md has no `## Motor Speed (RPM)` → "No match … →
  the grinder is **fixed-speed**: RPM behavior is **OFF** (no RPM prompts, blank RPM column)". Step 2
  "do not read or prompt for RPM"; Step 4b writes the 13-field row but "Fixed-speed (gate OFF) …
  write a **blank** cell." **Expected branch: no read, blank RPM cell (still 13 columns). HOLDS.**

**Mid-bag delta-only behavior (Step 3 ANALYZE, lines 109–115), governing line verbatim:**

> When the gate is ON and the user states an RPM for this session that **differs** from the current `Operating RPM` read from `user-setup.md` (a single read — do NOT scan prior grind-map rows), do both of the following:
> 1. **Warn and re-anchor.** … Recommend **re-dialing grind to restore the target shot time** … rather than carrying the old `chirp + N marks` setting forward. …
> 2. **Update (or create) the Operating RPM field.** Write the new stated RPM into `user-setup.md`'s `Operating RPM` field …
>
> When the stated RPM matches the current `Operating RPM` (or no RPM is stated), do nothing here — no warning, no update.

- **State A, user states 1200 (≠ stored 1100):** the differs-branch fires — warning + re-anchor +
  `user-setup.md` Operating RPM updated to 1200. The comparison is a single `user-setup` read ("a
  single read — do NOT scan prior grind-map rows"), confirming the no-history-parser constraint.
  **Delta → warn+update. HOLDS.**
- **State A, user states 1100 (= stored 1100) or states nothing:** "When the stated RPM matches the
  current `Operating RPM` (or no RPM is stated), do nothing here — no warning, no update."
  **No delta → silent. HOLDS.** (The warning fires *only* on an RPM delta — delta-only confirmed.)
- **State B (fixed-speed):** the entire guard is "gated by the Step 3 RPM gate" and OFF, so no
  comparison, no warning, no update occurs. **HOLDS.**

**Routine "too sour" yields NO RPM (Step 3 ANALYZE, lines 76–81 + 119–121).** The adjustment
hierarchy block — governing lines verbatim:

> **Adjustment hierarchy** — adjust in this order:
> 1. **Grind size** — largest effect on extraction
> 2. **Yield/Ratio** — quick correction (5g rule)
> 3. **Temperature** — fine-tuning after grind is close
> 4. **Pressure/Profile** — style change or enhancement
> 5. **Puck prep** — channeling, inconsistency

…contains **no** "RPM" entry (R12(i): a `grep -c "RPM"` scoped to just this block = 0). The
experiment-gate line immediately governs the only RPM path, verbatim:

> Do NOT volunteer RPM as a fix during routine sour/bitter/fast/slow diagnosis — it is deliberately absent from the adjustment hierarchy above. Offer RPM guidance **only when the user explicitly frames a deliberate body/clarity experiment** … give **hedged** guidance and route the reasoning to `knowledge/grinders/DF64V.md` … rather than restating any RPM numbers …

- **State A, routine "too sour" input:** the diagnostic table routes sour → grind/yield (e.g.
  "Sour + fast (<20s) … Grind finer"); RPM is "deliberately absent from the adjustment hierarchy"
  and "Do NOT volunteer RPM as a fix during routine sour/bitter/fast/slow diagnosis." **Expected:
  no RPM mention on a routine sour input. HOLDS** — even with the gate ON, RPM is not volunteered.
- **State A, explicit "I want to experiment with body via RPM":** the experiment branch fires —
  hedged guidance routed to `DF64V.md`'s "RPM as a dial-in lever" note, no numbers restated.
  **Expected: hedged routed guidance. HOLDS.**

**`/feedback` verdict: PASS** (State A stamps 1100 / State B blank; mid-bag warns only on delta and
updates `user-setup`; routine "too sour" volunteers no RPM; explicit experiment routes hedged to
`DF64V.md` — all governed by the quoted lines).

---

### 3.3 — `/diagnose` (`.claude/skills/diagnose/SKILL.md`)

**Governing context line (Step 3 CORRELATE, line 145), verbatim:**

> **RPM as diagnostic context (advisory, when known):** If the RPM used for the shot is known — from the shot's `grind-map.md` row or a value the user states — fold it into the correlation narrative as contextual input. A logged RPM is self-identifying (RPM exists only for variable-speed grinders), so no grinder-resolution or out-of-range gating is needed. For example: a fast/gushing shot at a high logged RPM is consistent with a coarser distribution, and a choked/stalling shot at a low logged RPM points toward the low-RPM-stall edge. Defer all interpretation to `knowledge/grinders/DF64V.md` and `knowledge/reference/DF64V_REFERENCE.md` rather than asserting RPM facts here. **If no RPM is known for the shot, behave exactly as today — skip this context and run the correlation unchanged.**

`/diagnose` is intentionally *not* gated on the `## Motor Speed (RPM)` heading — it keys on whether
an RPM value is *known* for the shot, which is self-identifying because "RPM exists only for
variable-speed grinders." The two states map to known-vs-unknown RPM:

- **State A → RPM context ON.** A DF64V shot carries an RPM (e.g. the grind-map row stamped 1100 by
  `/feedback`, or a user-stated value). "If the RPM used for the shot is known … fold it into the
  correlation narrative as contextual input" → the diagnosis gains RPM context (e.g. "fast/gushing
  shot at a high logged RPM is consistent with a coarser distribution"), with all interpretation
  deferred to `DF64V.md` / `DF64V_REFERENCE.md`. **Expected branch: RPM context folded in. HOLDS.**
- **State B → unchanged.** A Sette shot has no RPM value (fixed-speed → blank RPM column, no stated
  RPM), so the fallback "If no RPM is known for the shot, behave exactly as today — skip this
  context and run the correlation unchanged" fires. **Expected branch: unchanged, no RPM context. HOLDS.**

**`/diagnose` verdict: PASS** (State A folds in advisory RPM context routed to `DF64V.md`; State B —
no known RPM — runs unchanged; both governed by the quoted line).

---

## Part 4 — Summary

| Check | Type | Result |
|-------|------|--------|
| 1.1 R15 global scan = 0 (all four skills) | runnable grep | **PASS** |
| 1.2 R7 discriminator = 1 (DF64V) / 0 (SETTE_270) | runnable grep | **PASS** |
| 1.3 Task 8(ii) RPM_RECOMMENDATION = 1 in `<claims>` | runnable grep | **PASS** |
| 2 Task 1(d) hedge audit — no bare directional/body claim | agent-reasoned | **PASS** |
| 3.1 `/new-coffee` State A (row) / State B (no row) | behavioral trace (quoted) | **PASS** |
| 3.2 `/feedback` State A (1100 stamped) / State B (blank) | behavioral trace (quoted) | **PASS** |
| 3.2 `/feedback` mid-bag delta-only warn+update | behavioral trace (quoted) | **PASS** |
| 3.2 `/feedback` routine "too sour" → no RPM | behavioral trace (quoted) | **PASS** |
| 3.3 `/diagnose` State A (context) / State B (unchanged) | behavioral trace (quoted) | **PASS** |

**Overall: PASS.** All discriminating greps return their expected discriminating counts, and every
behavioral-trace expectation holds against the verbatim-quoted governing skill lines. Each
requirement traced here passes both its grep ACs and its behavioral-trace expectation.

**Methodology note (per spec Technical Constraints + plan-phase P7 rule):** prompt-only skill
correctness cannot be proven by command alone — the quoted-evidence trace IS the evidence, and the
residual self-attestation is inherent to prompt-only skills (the spec explicitly accepts this and
designates this trace the primary deliverable of Task 10, with its self-recording benign per the
plan-phase P7 rule). It is not overclaimed as a mechanical proof. The grep portions (Parts 1.1/1.2/
1.3) are concrete runnable commands whose outputs are reproduced verbatim above.
