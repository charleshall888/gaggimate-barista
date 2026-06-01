# Research: Parameterize feedback/new-coffee/consult to read the active grinder

**Clarified intent**: Parameterize the feedback, new-coffee, and consult skills (`.claude/skills/{feedback,new-coffee,consult}/SKILL.md`) so they read the active grinder from the `user-setup.md` Grinder field and defer to the matching per-grinder knowledge reference plus the shared grinder-neutral grind notation, with a grinder-relative step-advice fallback when the named grinder has no specific reference. Replace **every** hardcoded Baratza Sette 270 reference in these skills with selector-driven loading, keep the Sette path valid through the same selector, and introduce no DF64V hardcode. (Ticket 027, epic 024, `blocked-by: 025`, complexity: complex, criticality: high.)

---

## Codebase Analysis

### Files in scope (027's literal surface)
Three files, all under `.claude/skills/` (NOT `skills/` — that prefix in the ticket touch-points is wrong; no `skills/` or `plugins/cortex-core/skills/` mirror exists in this repo, these are the canonical and only copies):
- `.claude/skills/feedback/SKILL.md`
- `.claude/skills/new-coffee/SKILL.md`
- `.claude/skills/consult/SKILL.md`

### Exhaustive Sette audit — the complete in-skill set is **7 lines, not the ticket's 5**
| File:line | What it is | In ticket touch-points? |
|---|---|---|
| `feedback/SKILL.md:29` | Conditionally-Load table row → `knowledge/grinders/SETTE_270.md` (with stale `(64)` line-count hint) | ✅ yes |
| `feedback/SKILL.md:136` | Grind-map record step: "Full Sette 270 format: macro + micro letter (e.g. 9D, 10M, 11A)" — the **WRITE side** of the notation contract | ✅ yes |
| `new-coffee/SKILL.md:58` | "If no match: use defaults from `knowledge/grinders/SETTE_270.md`" | ✅ yes |
| `new-coffee/SKILL.md:60` | Freshness adjustment uses Sette-specific "1-2 micro steps coarser" vocabulary | ❌ **omitted** |
| `new-coffee/SKILL.md:66` | "**Grind:** From grind-map match or SETTE_270.md defaults" | ❌ **omitted** |
| `consult/SKILL.md:28` | CLASSIFY routing-table row: keywords `grind, Sette, finer, coarser, grind setting` → `knowledge/grinders/SETTE_270.md` | ✅ yes |
| `consult/SKILL.md:77` | DEEP REFERENCE table → `knowledge/reference/SETTE_270_REFERENCE.md` (with stale `(156)` hint) | ✅ yes |

### Reference files loaded by new-coffee that ALSO hardcode the Sette (NOT in ticket touch-points — scope-boundary decision required)
- `new-coffee/references/SELF_CHECK.md:14` — claims-block template: `(source: [grind-map match name | Sette 270 default range])`
- `new-coffee/references/SELF_CHECK.md:133` — arbiter prompt: "the Sette 270 espresso range starts around X; expect to dial from there."
- `new-coffee/references/RESEARCH_CHECKLIST.md:231,233` — freshness table in "1-2 micro steps coarser/finer"
- `new-coffee/references/RESEARCH_CHECKLIST.md:240–242` — worked example uses Sette codes `9D`, `9F`, `9G`, `9B`, `9C`

**Critical**: these are loaded at runtime by `/new-coffee`. If left as Sette hardcodes, a DF64V user running `/new-coffee` still gets a critic instructed that the grind source is "Sette 270 default range" and a freshness table in "micro steps" — i.e. the skill is **not parameterized in observable behavior** even after its SKILL.md is edited. "Parameterize the three skills" is not satisfiable while the reference files those skills pull still hardcode the Sette. (See Open Question 1.)

### Repo-wide blast radius (context only — owned by 025, NOT 027)
`knowledge/grinders/SETTE_270.md`, `knowledge/reference/SETTE_270_REFERENCE.md`, `knowledge/EXTRACTION_SCIENCE.md` (grinder-archetype table + cross-ref), `knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md`, `knowledge/SPECIAL_CATEGORIES.md`, `knowledge/reference/{BEAN_FRESHNESS_REFERENCE,ESPRESSO_BREWING_REFERENCE,PROFILE_LIBRARY_REFERENCE}.md`, `CLAUDE.md` index entry, `README.md`. These appear in **025's** touch-points, confirming the ownership split.

### Current user-setup field-reading conventions
- The **Grinder field** is free-text prose: `user-setup.md:8` → `| **Grinder** | Baratza Sette 270 (conical burr, micro-adjust) |`; `user-setup.example.md:9` → `| **Grinder** | Baratza Encore ESP (flat burr, stepped adjust) |` (a **third** grinder that maps to neither SETTE_270.md nor DF64V.md).
- `user-setup.md` is a **symlink** into the private data repo (`gaggimate-barista-data`). Read through the symlink; writes to `grind-map.md` go through the symlink and auto-commit to the **private** repo (`.data-repo-path` present).
- feedback reads user-setup fields (basket, grinder listed in "Always Load"; Puck Screen via **inline substring parse** at `:79` and `:137`). new-coffee reads Puck Screen at `:23`. **consult reads NO user-setup fields today** — it is pure stateless keyword routing. Adding a Grinder-field read to consult is a *new capability* (see Open Question 3).

### Conditional-loading mechanics + the consult cascade cap
- feedback "Conditionally Load" table (`:24-32`); new-coffee table (`:19-23`, grinder loading is inline prose not in the table); consult has two tables — CLASSIFY routing (`:23-38`) and DEEP REFERENCE (`:67-77`).
- **consult cascade-prevention cap** (`consult/SKILL.md:52,65`): "Load at most ONE quick-reference file and ONE deep reference file per question." Selector-driven loading must resolve to exactly **one** file per tier; a fallback that loads a grinder file *and* `_TEMPLATE.md` *and* re-keyed EXTRACTION_SCIENCE would breach the cap.

### Protected-path / lifecycle constraint
`.claude/skills/` and `.claude/skills/**/*` are `noDeletePaths` in `.claude/hooks/damage-control/patterns.yaml` (edit/write **allowed**, delete/rename **blocked**). `knowledge/**` likewise. `.env`/`.mcp.json` zero-access. Skill edits must route through `/cortex-core:lifecycle` (per 027 Edges and CLAUDE.md).

---

## Web Research

The generalizable pattern (config-driven selection of a knowledge file by parsing a free-text field, with a generic fallback, for a forkable agent-skill) maps cleanly onto established prior art:

- **Anthropic Agent Skills progressive disclosure** (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) is the closest, authoritative reference. The "domain-specific organization" pattern (SKILL.md is a navigation table; load only the one matching reference) and "conditional workflow" pattern are exactly the mechanism 027 needs. Two anti-patterns are directly load-bearing:
  - **"Avoid deeply nested references — keep references one level deep from SKILL.md."** → the selector should link **directly** to the grinder reference, not chain SKILL.md → shared-notation file → grinder reference → deep `_REFERENCE.md`.
  - **"Avoid offering too many options; provide a default with an escape hatch."** → pick the matched reference, fall back to grinder-relative steps, don't enumerate alternatives.
  - The "flexible template" pattern ("sensible default format, use your judgment") blesses 025's empty `_TEMPLATE.md` and 027's generic fallback.
- **i18next fallback chains** (https://www.i18next.com/principles/fallback): `specific → general → fallbackLng → the key itself`. Strongest analogy for the no-match fallback. The crucial lesson: the fallback layer is defined **independently of any specific locale**, which is what makes adding a new locale a no-code drop-in. By analogy, 027's fallback must be expressible purely in grinder-neutral terms, not derived from the Sette or DF64V references.
- **Registry / dictionary-dispatch + convention-over-configuration** (registry pattern, `dict.get(key, default)`, https://markheath.net/post/convention-over-configuration): argues against an `elif grinder == "DF64V"` branch per grinder. The `knowledge/grinders/` directory *is* the registry — dropping in `MY_GRINDER.md` is the additive, dispatch-untouched extension.
- **Free-text parsing anti-patterns**: normalize/lowercase before matching; prefer **alias tables over clever regex** (regex on free text risks backtracking + empty-string bugs — https://github.com/cocur/slugify); empty/missing/unknown must hit the fallback, not crash (Python `configparser` `fallback=`, git-config "best match else general"); an **over-broad fallback that always matches creates ambiguity** (Ory Oathkeeper) — so the fallback must be the *last* resort, never a competitor in the match step.
- **"Longest-match-wins"** caution (LibreChat PR #12073, microsoft/terminal #6693): naive substring matching where a short alias shadows a longer specific one. *However* — see Adversarial Review §2 — this collision is **hypothetical** here (no `DF64` reference exists), and the in-repo Puck Screen precedent uses plain substring against non-overlapping keywords with no tie-break rule.

---

## Requirements & Constraints

### From requirements/ files
- `cortex/requirements/project.md` is an **unconfigured TODO template** — every section is placeholder text, **zero actionable constraints, zero Conditional Loading entries**. All governing constraints come from CLAUDE.md, the backlog tickets, and the damage-control hooks.

### Architectural constraints (CLAUDE.md)
- **Puck Screen field parsing contract** — the precedent to mirror: (a) row missing → `None`; (b) value "None" (case-insensitive) or whitespace-only → `None`; (c) any other non-empty value → present, classified by **case-insensitive substring match** against a fixed keyword set (`mesh`, `round-hole`, `thin`, `thick`); "do not invent additional categories or normalize beyond these substring checks." **Important** (per Adversarial §1): this contract is **restated inline** in `feedback/SKILL.md:79` and `diagnose/SKILL.md:147` and merely *attributed* to CLAUDE.md — it is NOT a "cite-only, defined-once" pattern.
- **Data Architecture**: `user-setup.md`/`grind-map.md`/`coffees/` are symlinks into the private data repo; don't assume in-repo.
- **Auto-commit policy**: `.data-repo-path` present → after a data-writing step, commit + push to the private repo (separate Bash calls, `--git-dir`/`--work-tree`). feedback (4e) and new-coffee (9) already implement this; 027's notation change feeds the grind-map write this captures.
- **Core Rules to preserve verbatim**: Dose = basket; "Sour AND bitter = channeling → fix puck prep, NOT grind"; turbo 1:2.5–1:3. feedback preserves the channeling rule "verbatim" at `:86`. 027 must not disturb these.
- **Lifecycle / protected paths**: the three SKILL.md files are lifecycle-gated; no ad-hoc edits.

### Hooks / guardrails
`.claude/skills/**` and `knowledge/**` are `noDeletePaths` (edit allowed; delete/rename blocked). `.env`/`.mcp.json` zero-access. Bash hooks hard-block `rm -rf`, `git reset --hard`, force-push.

### 027 explicit edges (must / must not)
- **Must** read the active grinder from the Grinder field; **must not** hardcode DF64V in place of the Sette.
- **Must not** break Sette users — the Sette path stays valid through the **same selector** (not a special case).
- **Breaks if** the Grinder-field contract changes shape without updating parsing.
- Protected paths → lifecycle-gated.
- **Non-goal**: redesigning the skills' broader behavior beyond grinder selection and notation.

### Cross-ticket dependencies
- **027 `blocked-by: 025`**; 025 is `status: backlog`, **NOT yet built** (`knowledge/grinders/` has only `SETTE_270.md`; no `DF64V.md`, no `_TEMPLATE.md`, no notation guide; `grind-map.example.md` still uses Sette `13C`).
- Epic 024 order: **025 → (026, 027 in parallel) → 028**. 026 (switch grind-map + user-setup to DF64V) runs **parallel to 027, not before** → at 027's build time the live Grinder field **still reads "Baratza Sette 270 (conical burr, micro-adjust)"**. 027's selector must resolve correctly for whatever the field says (Sette now, DF64V after 026, or any forked grinder).
- 025's Edge: re-keyed knowledge "must not introduce adjustment vocabulary that diverges from **the skills' relative-step language**" — 025 and 027 must agree on one relative-step vocabulary (see Open Question 5 / the contract gap).

---

## Tradeoffs & Alternatives

Four contested design decisions. The recommendations below incorporate the Adversarial corrections — read them together with that section.

### Decision A — WHERE the Grinder-field→reference selection rule is defined
- **A1** inline-in-each-skill only: drifts across three copies (the exact failure the Puck Screen contract prevents).
- **A2** one named clause in CLAUDE.md ("Active Grinder field parsing contract") **+ compact inline restatement in each skill** — the *actual* shape of the Puck Screen precedent (Adversarial §1 corrects Agent 4's "cite-only/free" framing). CLAUDE.md is the SSOT-of-record; each skill restates the operative rule because a prompt acts on text present in the skill, not on a contract it is told to "go look up."
- **A3** a new `knowledge/grinders/_SELECTOR.md`: costs against the consult cap (consult must read it *to decide* what to read), invents a new artifact type.
- **Recommended: A2 (corrected)** — CLAUDE.md clause + inline restatement, mirroring Puck Screen exactly. Note: not "free" — CLAUDE.md is always-resident token weight, and each skill carries a compact restatement.

### Decision B — HOW free-text Grinder prose maps to a reference file
- **B1** alias table only (substring `sette`→`SETTE_270.md`, `df64v`→`DF64V.md`): robust, mirrors Puck Screen; but a new grinder needs an alias-table edit (forkability gap).
- **B2** slugify → `knowledge/grinders/{slug}.md`: **dead on arrival** (Adversarial §3) — `Baratza Sette 270 (conical burr, micro-adjust)` slugifies to `baratza-sette-270-conical-burr-micro-adjust`, which cannot match the `UPPERCASE_UNDERSCORE` `SETTE_270.md`. Pure slugify breaks the Sette path.
- **B3** hybrid (alias-first, then slugify-convention fallback): Agent 4's pick — but Adversarial §3 shows the slugify layer can essentially never hit a real file given the `UPPERCASE_UNDERSCORE` convention, so the alias table does 100% of the work and slugify is decoration creating false forkability.
- **Recommended (corrected): plain case-insensitive substring alias match** against an explicit, enumerated alias set (mirroring the Puck Screen precedent literally), missing/blank/None → fallback, "do not invent grinder categories / do not hardcode a default grinder" guardrail. **Drop "longest-match-wins"** (Adversarial §2: it is an invention beyond the precedent; the `DF64`-shadows-`DF64V` collision is hypothetical — no `DF64` reference exists; add a tie-break only if/when two shipped aliases actually overlap). Forkability is honestly "drop a reference + add one alias entry," not zero-edit (see Open Question 6).

### Decision C — the no-matching-reference fallback
- **C1** load `_TEMPLATE.md` as content: semantically wrong (it is deliberately empty per 025) and wastes a cap slot.
- **C2** load nothing grinder-specific; emit grinder-relative step advice from 025's re-keyed shared knowledge — the mechanism 025 builds for exactly this case; zero extra file loads; always works.
- **C3** C2 + a brief "grinder unconfigured — drop a reference in `knowledge/grinders/` or fill `_TEMPLATE.md`" nudge (mirrors CLAUDE.md's "unconfigured check"); never loads `_TEMPLATE.md` as content.
- **Recommended: C3.** Note (Adversarial §3): the fallback is the **common forker case**, not exotic — the shipped `user-setup.example.md` (Encore ESP) lands here. Design and review it as first-class.

### Decision D — the grind notation feedback WRITES into grind-map.md
- **D1** name a literal token (e.g. "chirp+N marks"): re-introduces a DF64V-flavored hardcode — fails the no-DF64V-hardcode edge.
- **D2** defer entirely — "record in the notation prescribed by the active grinder reference / 025's notation guide," naming no format.
- **Recommended: D2.** The current `:136` line ("Full Sette 270 format: macro + micro letter") becomes a deferral. `grind-map.example.md` already supports free-text Grind cells, so no schema change. Depends on 025 actually defining a notation token + file/anchor (Open Question 5).

### Composed recommendation
A2(corrected) + B(plain-alias) + C3 + D2: one CLAUDE.md "Active Grinder field parsing contract" clause + compact inline restatement in each skill; alias-table substring resolution to `knowledge/grinders/<GRINDER>.md` (Sette rescued, no DF64V hardcode); C3 fallback for the no-match/forker case; feedback defers the notation token. Lowest-risk on complexity, maintainability, and pattern-alignment — **conditional on the 025→027 contract being pinned first** and the scope-boundary (reference files) being resolved.

---

## Adversarial Review

1. **A2 "cite, don't duplicate" is factually wrong.** The Puck Screen contract is **restated inline** in `feedback/SKILL.md:79` and `diagnose/SKILL.md:147` and only *attributed* to CLAUDE.md. The realistic design is contract-in-CLAUDE.md **plus** a compact inline restatement in each of the three skills — not "free against the consult cap," not cite-only.
2. **"Longest-match-wins" is an invention beyond the precedent.** Puck Screen uses **plain** case-insensitive substring match against non-overlapping keywords with no tie-break. There is **no `DF64` reference** anywhere — the `DF64`-shadows-`DF64V` collision is hypothetical. Mirror the precedent's plain substring match; add a tie-break only if two shipped aliases overlap.
3. **The slugify convention-fallback collides with the real filename convention and is largely dead on arrival.** Files are `UPPERCASE_UNDERSCORE`; no realistic Grinder string slugifies to `SETTE_270.md`. The alias table does 100% of the work. And `user-setup.example.md` ships a **third** grinder (Encore ESP) → the shipped example/template setup itself lands in the fallback, so fallback is the **common forker case**, not an edge.
4. **Adding a user-setup read to consult is a genuine capability expansion** that risks the "no broader redesign" non-goal. consult is stateless keyword routing today. Open issues: does loading `user-setup.md` to find the grinder count against the ONE-quick-ref cap? consult `:28` routes the literal keyword **"Sette"** — for a DF64V user typing "Sette," route to archived SETTE_270.md or to their active grinder? The selector cannot blindly replace the keyword.
5. **The scope-boundary residue is a correctness bug, not a style nit.** new-coffee:60, :66, and the loaded reference files (`SELF_CHECK.md`, `RESEARCH_CHECKLIST.md`) hardcode the Sette. Left unfixed, a DF64V user's `/new-coffee` is behaviorally Sette-hardcoded despite SKILL.md edits. Either expand 027's scope to them or explicitly assign them to 025 work-item E with 027 verifying — otherwise they fall in the gap between tickets and ship broken.
6. **CLAUDE.md regeneration fear is overstated** (the self-regenerating clause is narrowly scoped to the "Lifecycle worktree authorization" section; a parsing-contract clause elsewhere won't be clobbered; CLAUDE.md is `noDeletePaths`, edit allowed). The real cost is **always-resident token bloat** — every grinder rule there is permanent weight on every turn.
7. **The 025↔027 contract gap is real and currently blocks a writable 027 spec.** 025's Edge defers vocabulary to "the skills' relative-step language"; 027 defers advice content to 025's re-keyed knowledge; **neither pins the actual words/token.** The migration research labels the selector+fallback as work-item F = 027's deliverable. This is a circular deferral — a gap nobody fills.
8. **"Forkable with zero code/skill changes" is false as composed.** A forker must (a) create `knowledge/grinders/<NAME>.md`, (b) add an alias entry, and (c) maybe touch the consult keyword table. The only genuinely zero-edit path is the *degraded fallback*. Honest claim: "forkable to degraded-but-correct fallback with zero edits; full per-grinder support requires a reference file + an alias entry."
9. **Symlink + parallel-026 testability.** Notation written to `grind-map.md` goes through the symlink and auto-commits to the **private** repo — the parameterized change must not alter the public-repo commit logic. At 027 build time the live Grinder field still says Sette (026 is parallel), so only the **Sette and fallback** paths are exercisable against live config; the DF64V path is untestable until 026 lands.
10. **No test harness for prompt-only skills.** Verification can only be (a) static grep that no `Sette`/`SETTE_270`/`9D`/`macro+micro`/`micro step` literal remains on any parameterized path (**including** `new-coffee/references/`), and (b) prompt-level dry-runs with Grinder set to Sette / DF64V / Encore-ESP-fallback / blank. The agents proposed no verification strategy; this must be in the spec's acceptance criteria.

---

## Open Questions

Each is annotated with resolution or explicit deferral per the Research Exit Gate.

1. **Scope of the loaded reference files (`new-coffee/references/SELF_CHECK.md`, `RESEARCH_CHECKLIST.md`) and new-coffee:60/:66.** Are they in 027's scope, or assigned to 025's de-Setting work-item E with 027 only verifying? — **Deferred to Spec**: this is a genuine scope decision for the user/spec interview. Recommended default (per Adversarial §5): include new-coffee:60 and :66 in 027 (same skill, same pattern), and bring the two reference files into 027's scope OR make 027's acceptance criteria assert they are de-Setted (by 025) before 027 is considered behaviorally complete — leaving them produces a residual-hardcode correctness bug.
2. **Should the matching rule be plain substring (Puck Screen precedent) or longest-match-wins?** — **Resolved**: plain case-insensitive substring against an enumerated alias set, mirroring the precedent; no longest-match-wins unless two shipped aliases actually overlap (none do today). (Adversarial §2.)
3. **consult capability expansion.** Does consult gain a `user-setup.md` Grinder-field read (new statefulness), and how does it count against the ONE-quick-ref + ONE-deep-ref cap? How is the literal "Sette" keyword on a DF64V user disambiguated? — **Deferred to Spec**: consequential scope/design decision. Two viable framings for the interview: (a) consult reads the Grinder field (accept the new capability; state cap accounting), or (b) consult only swaps the hardcoded `SETTE_270.md` route *target* for a selector-resolved one without reading user-setup itself.
4. **Where is the selection contract defined — CLAUDE.md clause + inline restatement, or inline-only?** — **Resolved (recommend, confirm in Spec)**: CLAUDE.md "Active Grinder field parsing contract" clause as SSOT + compact inline restatement in each skill, mirroring the Puck Screen precedent's *actual* shape. Final wording/placement confirmed at spec approval.
5. **The 025→027 consumed-artifact contract (HARD blocker).** 025 must commit to, before 027 is implementable: (i) the grind-notation token/format string + the exact file + anchor of the notation guide feedback defers to; (ii) the alias/filename mapping for `knowledge/grinders/<GRINDER>.md`; (iii) the exact grinder-relative step vocabulary the fallback emits (e.g. "go finer/coarser by a small step"). — **Partially resolved**: ownership split is clear (025 owns the notation token + reference files + re-keyed shared knowledge; **027 owns the selector parsing logic + fallback + the deferral mechanism**, per work-item F). **Deferred to Spec for the residual**: the spec must (a) define 027's selector contract self-containedly, and (b) state its consumed-artifact assumptions about 025 explicitly so that if 025 underdelivers the gap is visible. The `blocked-by: 025` ordering means 025 lands first at overnight-execution time; the spec should still pin the assumed notation file/anchor so feedback can cite it precisely.
6. **Forkability claim.** Confirm the honest framing in the spec: zero-edit forkability reaches only the degraded fallback; full per-grinder support requires a reference file + an alias entry. — **Resolved** (framing); reflect it in spec language so the epic's "fork-and-plug-in" promise isn't overstated.
7. **Verification strategy for prompt-only skills.** — **Resolved**: spec acceptance criteria = static grep for zero residual Sette literals on parameterized paths (including `new-coffee/references/`) + dry-runs across Grinder = Sette / DF64V / Encore-fallback / blank; note DF64V path is untestable against live config until 026 lands.

No unresolved, non-deferred bare bullets remain — the Research Exit Gate is satisfied.

---

## Considerations Addressed

- **Validate that the no-matching-reference fallback can be specified independently of, or is fully determined by, 025's grinder-relative notation and re-keyed shared knowledge** — **Addressed**: all three angle agents (Codebase §4, Web, Requirements) and the Adversarial pass converge that the fallback is **fully determined by 025's re-keyed shared knowledge + grinder-neutral notation**, expressible without reference to the Sette or DF64V happy paths (this is precisely the i18next "fallback layer defined independently of any specific locale" property that makes forking a no-code drop-in). It is **independently specifiable but not independently functional until 025 de-Settes the shared knowledge** — so the `blocked-by: 025` relationship is load-bearing for the fallback specifically. One residual risk flagged for the spec: verify 025 leaves the re-keyed shared knowledge usable standalone (no dangling "see your grinder reference" cross-link that dead-ends when no reference matches).
