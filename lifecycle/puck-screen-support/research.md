# Research: puck-screen-support

Add optional puck screen tracking to the user setup equipment table (public template + private user data), a new `knowledge/PUCK_SCREENS.md` knowledge file, plus conditional adjustments across `/diagnose`, `/feedback`, `/new-coffee`, `/gaggimate-profiles`, and `/consult` so the agent factors puck-screen effects on channeling diagnosis, temperature, profile/pressure, puck prep, and dose/headroom — without assuming any user has one. Reference product: Normcore 58.5mm round-hole, 0.8mm thick, 316 stainless, 19 holes, 0.18mm perforation.

## Codebase Analysis

### Files that would change under the maximal (as-invoked) plan

| File | Change type | Notes |
|------|-------------|-------|
| `user-setup.example.md` | Add optional Equipment row | Sentinel "None" per template; must signal optional |
| Private `user-setup.md` (symlink) | User fills in their screen | Normcore 58.5mm round-hole, 0.8mm |
| `knowledge/PUCK_SCREENS.md` | **NEW** (scope under review — see Open Questions) | Quick-ref if created; content partially overlaps existing files |
| `knowledge/reference/PUCK_SCREENS_REFERENCE.md` | NEW (optional) | Deep physics, pattern for quick+deep split (see Open Questions) |
| `CLAUDE.md` | Update 2–5 sections | Knowledge Files list + Core Rules + potentially Workflow/Setup questions |
| `MEMORY.md` single-source-of-truth table | Add row(s) | Wherever the fact lives becomes the authoritative row |
| `.claude/skills/diagnose/SKILL.md` | Narrow conditional | Channeling interpretation + cold-screen guardrail |
| `.claude/skills/feedback/SKILL.md` | **Review: may not need changes** | Adversarial flagged no real need |
| `.claude/skills/new-coffee/SKILL.md` | **Review: may not need changes** | Web found no grind shift for 0.8mm round-hole |
| `.claude/skills/gaggimate-profiles/SKILL.md` | Narrow conditional | Pre-infusion +1–2s note only; minor |
| `.claude/skills/consult/SKILL.md` | 1-line routing row | "puck screen, normcore, screen imprint" → target file |
| `grind-map.example.md` | **Under review — likely no change** | Retroactive-data trap; don't add a column |

### Existing patterns relevant to this feature

1. **Equipment table with inline spec strings** (`user-setup.example.md`): rows carry multi-attribute free-text — e.g., `Baratza Encore ESP (flat burr, stepped adjust)`, `IMS Baristapro Nanotech 18g (ridgeless)`, `Felicita Arc (Bluetooth), auto-stop enabled, 250ms predictive delay`. An optional Puck Screen row would fit this format without schema strain.
2. **Unconfigured check** (CLAUDE.md "Data Architecture"): warns when `user-setup.md` looks like a template. Template rows use realistic-looking values, not blank placeholders — so "Puck Screen | None" is the natural sentinel pattern.
3. **Optional-field skill reads**: skills already read `user-setup.md` at each invocation (stateless). Pattern for adding a new field is: grep/scan the Equipment table, treat missing row as "feature off."
4. **Knowledge-file quick-ref + `reference/TOPIC_REFERENCE.md` deep split**: used for BASKETS, EXTRACTION_SCIENCE, PRESSURE_GUIDE, MILK_AND_DRINKS, PROFILE_LIBRARY, SPECIAL_CATEGORIES, SETTE_270. Every multi-depth topic follows this split. MEMORY.md's SoT table explicitly pairs each quick file with its deep reference.
5. **`/consult` cascade prevention**: max 1 quick + 1 deep reference per question. New topic routing entries are one-line keyword→file mappings.
6. **Core Rules inline tables** (CLAUDE.md): single-row rules like "Sour AND bitter = channeling. Fix puck prep, NOT grind." These are tripwire-simple by design — expanding them risks muddying diagnostic logic.
7. **`conditionally load` skill pattern**: skills like `/gaggimate-profiles` have a table listing "load ONLY when X trigger fires." Adds a knowledge file reference without always-loading it.
8. **Auto-commit policy**: `.data-repo-path` triggers commit/push to private repo after any data-writing step. Since user-setup.md is symlinked, any change to it (even via manual editing) will be captured on the next skill-triggered commit — no explicit skill write needed.

### Existing content overlaps (critical)

- **`knowledge/EXTRACTION_SCIENCE.md:42`** already contains a Puck Prep Tools row: `| **Puck screen on top** | Protects puck from shower screen imprint, prevents surface erosion | Doesn't improve internal distribution |`
- **`knowledge/EXTRACTION_SCIENCE.md:44`**: `**Recommended combo:** WDT → light tap to settle → tamp → (optional: puck screen on top)`
- **`knowledge/BASKETS.md:16`** owns the screen-kiss / dose-headroom rule: `"If you see a mesh pattern pressed into the surface, reduce your dose by 0.5g."` This rule refers to the **shower screen**, not a puck screen — but puck screens **mask** this evidence, so the rule degrades when a puck screen is installed.

A new `knowledge/PUCK_SCREENS.md` that restates either of these duplicates facts and violates MEMORY.md's "Facts live in ONE place" rule.

### Integration points and dependencies

- **MEMORY.md table**: needs a new SoT row (`Puck screens | knowledge/{file}`). Which file wins depends on Open Question #1.
- **CLAUDE.md Knowledge Files list**: one-line addition naming the authoritative file.
- **CLAUDE.md Core Rules "Sour AND bitter = channeling"**: at risk of nuance-creep. Must not be changed; puck screens are a *passive modifier on expectations*, never a proposed fix.
- **CLAUDE.md "Data Architecture" / Unconfigured check**: optional Puck Screen row should be an explicit "treat as None if missing" rule so skills don't branch on a blank.

## Web Research

### Normcore 0.8mm 316-stainless round-hole 19-hole 0.18mm — effect profile

**Temperature**
- Thick screens (1.7mm+, e.g., BPlus) draw 2–3°C at the puck surface from cold; manufacturers recommend +2–3°C boiler compensation for those.
- At 0.8mm, community consensus: ≤1°C when preheated, negligible when preheated by locking the screen into the portafilter during the flush (Normcore's own care instructions).
- **Takeaway**: +1°C is defensible only if the user doesn't preheat; preheat-first is the correct guidance, not temperature compensation.

**Flow / pressure**
- Measured effect at 0.8mm round-hole is modest: "redistributes flow rather than restricting it." One controlled trial (Nucleus Coffee) measured shots >1s faster on average with screen vs without.
- Coffee ad Astra (Jonathan Gagnon) has quantitative hydraulic-resistance data only for **bottom paper filters** (43% reduction); top-puck-screen data is qualitative: "I suspect that the puck screens are in fact usually good for extraction … I do not yet have hard data to back this up."
- Pre-infusion: may benefit from +1–2s to let gentled initial wetting saturate the dense puck evenly.
- **Takeaway**: no grind shift needed. Pre-infusion time is the only parameter plausibly affected for 0.8mm.

**Channeling reduction**
- Real effect on **shower-screen-driven** channeling (distributed flow beats concentrated jets).
- **Does NOT fix puck-prep-driven channeling** (WDT, distribution, tamp). This caveat is universal across Clive Coffee, Coffee Chronicler, Home Ground, Coffee ad Astra.
- Nucleus blind tasting: "more balanced, less astringent, softer acidity, more uniform crema color without tiger striping" — extraction-yield difference trivial (21% vs 20.7%).
- **Takeaway**: puck screens are a supplementary distribution aid, not a puck-prep replacement.

**Dose / headroom**
- 0.8mm is the headroom-friendly tier. Community consensus: no dose reduction needed at 22g in a 22g basket.
- Over-dosing + screen = hydraulic lock or "sneezing"; bent screen is a documented failure.
- **Takeaway**: keep "dose = basket size." Warn only if user already borderline-overdoses.

**Light-roast specificity**
- Community-reported: screens help light roasts more (dense, slow-wetting pucks more sensitive to uneven initial wetting). No controlled A/B testing located.
- **Takeaway**: **hedge the claim** — "community-reported; effect size uncertain; primary benefit remains even wetting." Do not use as a reason to change starting parameters in `/new-coffee`.

**Round-hole vs mesh**
- Round-hole (Normcore 0.18mm × 19 holes): easier to clean, retains fewer oils, but disperses water less evenly than fine mesh.
- Fine mesh (IMS ~200µm, Sworks, Pesado): best dispersion, more oil retention → more maintenance.
- Normcore's 0.18mm (180µm) holes are *finer* than IMS's 200µm mesh holes — partially offsets the fewer-holes disadvantage.

**Pitfalls to call out**
- Cold screen → sour shot (preheat critical).
- Over-dosing + screen → choke / bent screen.
- Upside-down placement → reduced effectiveness.
- Wrong size (e.g., 58.5mm in a 54mm basket) → pressure spikes.
- Maintenance: rinse daily, Cafiza weekly; 316 stainless is corrosion-resistant but not immune.
- Diminishing returns on machines with already-excellent shower screens.
- **Not a substitute for good puck prep.**

### Contested / vendor-marketing claims (to be excluded from knowledge file content)

- "22% extraction uniformity improvement" — banleecoffee.com, cited to "Decent Espresso trials"; no primary source found.
- "4–7% extraction yield increase" — banleecoffee.com, cited to "Barista Magazine"; no primary source found.
- "90% channeling reduction at a Melbourne café" — vendor marketing.
- "Copper-core 2× faster heat transfer" — vendor marketing for custom products, not Normcore standard.
- Exact °C temperature drop for 0.8mm screens — no primary controlled measurement located.

### Key sources

home-barista.com (Scace test request, puck screen workflow, thickness, light-roast channeling threads); coffeeadastra.com (Jonathan Gagnon); Scott Rao (filter sandwich); Decent Espresso / Blooming Espresso profile work; Normcore product + care pages; BPlus boiler-compensation guidance; Pesado blog; Clive Coffee, Nucleus Coffee, Papel Espresso consumer verdicts; Lance Hedrick's "Naked Portafilters Are Liars…Sometimes" YouTube.

## Requirements & Constraints

No `requirements/` directory. Architectural constraints are encoded in `CLAUDE.md` and `~/.claude/projects/…/memory/MEMORY.md`:

1. **Single Source of Truth (MEMORY.md)** — facts live in ONE place. Skills and CLAUDE.md reference knowledge files; they don't re-embed data.
2. **Knowledge-file convention** — ALL_CAPS naming at top of `knowledge/`; optional deep companion in `knowledge/reference/TOPIC_REFERENCE.md`. Every multi-depth topic in the SoT table follows the split.
3. **`/consult` cascade prevention** — max 1 quick + 1 deep per question.
4. **Skills must handle missing optional fields gracefully** — default is "skip this feature," not "ask the user." Reinforced by the saved user-preference memory `feedback_agent_autonomy_over_light_path.md`: when agent capability is at stake, user prefers full agency; this memory is **not** a mandate for file-structure maximalism.
5. **Public-repo / shared-by-others** — template must work for users without a screen. Skill logic must treat missing field as "no screen" silently; no interactive probing.
6. **Auto-commit policy** — `.data-repo-path` triggers commits to private repo after data writes. `user-setup.md` is symlinked into the private repo; changes propagate automatically.
7. **Symlink data architecture** — `user-setup.md`, `grind-map.md`, `coffees/` live in private repo via symlink. Public template is `user-setup.example.md`.
8. **Core Rules tripwire** — "Sour AND bitter = channeling. Fix puck prep, NOT grind." is deliberately simplified. Any new content that nuances this rule risks diagnostic regressions.

## Tradeoffs & Alternatives

### A. Where the field lives in `user-setup.md`
- **A1 — new row in Equipment table** *(user's pick, recommended)*: zero new structure, matches existing Basket/Scale pattern. Caveat: requires an explicit sentinel so absence is unambiguous.
- A2 — separate Accessories section: over-engineering for one field.
- A3 — Notes text: unparseable; rejected.

### B. How skills detect presence
- **B1 — stateless read** *(recommended)*: matches all existing skill patterns. Skills already read `user-setup.md` at invocation.
- B2 — parsed context object: no precedent in codebase.
- B3 — `/consult has-puck-screen`: misuses `/consult` which is for knowledge Q&A.
- B4 — sentinel `None` vs product string: a representation detail that supports B1. **Adopt.**

### C. Knowledge-file depth (contested — see Open Questions)
- C1 — single `knowledge/PUCK_SCREENS.md`: user's initial pick. Breaks the project-wide quick+deep pattern and risks duplicating `EXTRACTION_SCIENCE.md:42` and `BASKETS.md:16`.
- **C2 — quick `PUCK_SCREENS.md` + `reference/PUCK_SCREENS_REFERENCE.md`** *(matches project pattern)*: extra file but consistent with every other multi-depth topic.
- **C3 — in-place edits to EXTRACTION_SCIENCE.md + BASKETS.md + optional `reference/` deep** *(adversarial-recommended)*: avoids duplication, respects SoT. May be hard to /consult-route coherently.

### D. Skill branching scope (contested)
- D1 — every skill explicit branches: rejected, ballooning cost.
- D2 — light-touch: all skills reference knowledge file; agent loads contextually.
- D3 — hybrid: explicit branches in safety-critical skills, light-touch elsewhere (user's direction via Q&A).
- **D-reduced — /consult routing + /diagnose cold-screen guardrail only; knowledge file carries the rest passively** *(adversarial-recommended)*: 5 skills → 2. Rationale:
  - `/feedback` doesn't change its adjustment hierarchy; puck prep advice is unchanged.
  - `/new-coffee` doesn't need a branch — web research confirmed no grind/temp shift for 0.8mm.
  - `/gaggimate-profiles` only benefits from a +1–2s pre-infusion note — fits in knowledge file, not the skill.
  - `/diagnose` has a real failure mode: cold-screen-causes-sour-shot would be misdiagnosed as under-extraction → grind-finer → worse.
  - `/consult` only needs a routing row, not a skill branch.

### E. Template default
- **E1 — "Puck Screen | None"** *(recommended)*: disambiguates opt-out from forgot-to-fill; binary check.
- E2 — row omitted entirely: ambiguous; HTML comments unreliable.
- E3 — two-row variant: visually weird.

### F. Spec representation
- F1 — boolean: loses type/thickness info that genuinely affects recommendations (0.2mm mesh ≠ 1.7mm thick mesh).
- **F2 — product string (e.g., "Normcore 58.5mm round-hole, 0.8mm")** *(recommended per pattern)*: matches Basket/Scale free-text.
- F3 — structured sub-fields: no precedent; over-engineering.
- **F-canonical — "Thin round-hole (0.8mm) — Normcore"** *(adversarial-recommended)*: attribute-first, vendor-second. Skill logic keys off "thin/thick × round-hole/mesh"; exact SKU is color. Reduces drift if user swaps brand.

### G. Grind-map column
- G1 — add "Puck Screen?" column: retroactive-data trap (blank for old shots; similarity matchers misfire).
- **G2 — no column** *(recommended)*: user-setup.md is one-user-one-setting; screen changes are captured in git history of user-setup.md.

### H. Auto-commit write path
- H1 — skills write to user-setup.md: risks lost-writes when `/feedback` simultaneously updates Active Coffee.
- **H2 — screen field is user-edited only (or via `bin/setup-data-repo.sh`), never skill-written** *(recommended)*: auto-commit still captures the change on the next trigger; no collision.

## Adversarial Review

**1. Knowledge duplication / Single-Source-of-Truth conflict (verified).**
`EXTRACTION_SCIENCE.md:42` already has the "Puck screen on top" row with pros/cons. `BASKETS.md:16` owns the screen-kiss/dose rule (about the shower screen, but puck screens *mask* this evidence). A new `PUCK_SCREENS.md` that restates these duplicates facts.

**2. Core Rule tripwire.**
`CLAUDE.md` Core Rules: *"Sour AND bitter = channeling. Fix puck prep, NOT grind."* If `/diagnose` ever proposes "try a puck screen" for channeling, the Core Rule's intent — fix the root cause — is diluted. **Mitigation**: the agent must *never propose* a screen. Screen status is a passive modifier on expectations only.

**3. Scope inflation — 3 of 5 skills don't need real changes.**
- `/feedback`: adjustment hierarchy unchanged. Drop.
- `/new-coffee`: no grind/temp shift. Drop.
- `/gaggimate-profiles`: +1–2s pre-infusion is knowledge content, not a branch. Drop (or 1-line note).
- `/consult`: 1-line routing keyword row, not a branch.
- `/diagnose`: real, narrow need (cold-screen sour misdiagnosis + channeling-interpretation nuance).

The "D3 hybrid" recommendation is a symptom of pattern-match overreach.

**4. User-memory misapplication.**
`feedback_agent_autonomy_over_light_path.md` — the user's "full port over light path" preference is about **agent capability**, not file-structure maximalism. The C1-over-C2 pick should be re-examined against that distinction.

**5. Grind-map retroactive-data trap.**
Adding a "Puck Screen?" column leaves every old row blank. Matchers either ignore it (why add?) or treat blank as "no screen" (wrong — it's "unknown"). **No column.**

**6. Auto-commit concurrency.**
`user-setup.md` is already written by `/feedback` (Active Coffee) and `/new-coffee`. A third skill-write path increases collision risk. **Field is user-edited only; skills read but don't write it.**

**7. Multi-user template contamination.**
Public repo means other users copy the template. Baking the Normcore spec into the template as a default would leak misinformation to users without a screen. **Template sentinel: `None`. Example file shows both "None" and a configured example.**

**8. Cold-screen → sour misdiagnosis trap.**
Today `/diagnose` diagnoses sour as under-extraction → grind finer. With a cold (not preheated) screen, this advice makes it worse. **`/diagnose` must carry a guardrail: if sour + screen present, check preheat before recommending grind.**

**9. Light-roast claim under-evidenced.**
Web agent marked this as community-reported only. Writing it with high confidence would push the user (a light-roast-primary user per MEMORY.md) to over-weight screen use. **Hedge the language; don't use as a reason to change `/new-coffee` starting parameters.**

**10. Vendor-marketing contamination.**
Strip contested claims ("22% uniformity," "4–7% yield," "90% channeling reduction") — unsourced vendor copy.

**11. Device-spec drift.**
Storing "Normcore 58.5mm round-hole, 0.8mm, 19 holes, 0.18mm" verbatim creates maintenance tax if the user swaps. Skill logic only needs type (mesh vs round-hole) and thickness class (≤1mm vs >1mm). **F-canonical recommended over raw product string.**

### Adversarial-recommended plan (for consideration in spec)

1. **No new `PUCK_SCREENS.md`.** Augment `EXTRACTION_SCIENCE.md` and `BASKETS.md` with ~10 lines each (or introduce quick `PUCK_SCREENS.md` only if the user insists on routing via `/consult` — then it must own the fact and the existing `EXTRACTION_SCIENCE.md:42` row must reference the new file instead of duplicating).
2. **Touch 2 skills, not 5.** `/consult` keyword row; `/diagnose` cold-screen + channeling-interpretation guardrail.
3. **No grind-map column.**
4. **Template sentinel `None` + canonical-attribute format for the configured case.**
5. **Explicit Core Rule preservation**: channeling remains "fix puck prep, NOT grind." Screen never proposed.
6. **Cold-screen-causes-sour explicit diagnostic fork in `/diagnose`.**
7. **Hedged light-roast language; no parameter changes in `/new-coffee`.**

## Open Questions

**(Must be resolved by the user before spec is finalized.)**

1. **Knowledge-file scope — duplication vs pattern.** The user picked C1 (single `PUCK_SCREENS.md`). Adversarial verified that `EXTRACTION_SCIENCE.md:42` already owns one of the core facts; `BASKETS.md:16` owns a rule that's affected. Three options for the spec:
   - (a) **Inline-only** — extend EXTRACTION_SCIENCE.md + BASKETS.md; no new file; `/consult` routes "puck screen" to EXTRACTION_SCIENCE.md. Smallest surface; zero duplication.
   - (b) **Quick `PUCK_SCREENS.md` only** (user's original pick) — move the `EXTRACTION_SCIENCE.md:42` row into the new file with a cross-reference stub left behind; update BASKETS.md:16 to reference. Single new file; partial pattern (no `reference/` deep).
   - (c) **Quick + deep split `PUCK_SCREENS.md` + `reference/PUCK_SCREENS_REFERENCE.md`** (matches project-wide pattern) — same as (b) plus a deep file covering physics. Most complete; most effort; may be thin given topic depth.
   **Question**: (a), (b), or (c)? *Defer to spec §3: user must explicitly confirm or revise Clarify's C1 pick.*

2. **Skill-modification scope — 5 vs 2.** User's Q&A picked "Full port" including all four behavior branches (channeling, temperature, profile/pressure, puck prep discussion, dose/headroom). Adversarial argues 3 of these don't need skill changes for a 0.8mm screen; the knowledge file carries them passively.
   **Question**: Full port (5 skills with conditional branches) or tight port (2 skills: `/consult` routing + `/diagnose` cold-screen guardrail)? *Defer to spec §3.*

3. **Equipment-table representation format.** Options:
   - F2: `"Normcore 58.5mm round-hole, 0.8mm, 19 holes, 0.18mm perforation"` (current product-string convention)
   - F-canonical: `"Thin round-hole (0.8mm) — Normcore 58.5mm"` (attribute-first)
   **Question**: which format? (Also: do we accept free-text and let the agent parse, or lock to a schema?) *Defer to spec §3.*

4. **Core Rule preservation** — confirm that `CLAUDE.md` Core Rule *"Sour AND bitter = channeling. Fix puck prep, NOT grind."* is **not** modified. Puck screens never appear as a proposed fix in `/diagnose` channeling guidance. *Spec must include a "don't modify Core Rule" constraint.*

5. **Cold-screen misdiagnosis guard in `/diagnose`** — confirm the new diagnostic fork ("if sour + screen present, ask about preheat before recommending grind change") is scoped, with the exact wording to surface. *Spec §3.*

6. **MEMORY.md SoT table target** — once Open Question #1 is resolved, pick the SoT row(s). *Mechanical; deferred.*

7. **Grind-map column** — adversarial recommends no change. *Defer to spec §3 to confirm user agrees.*

8. **Dose-headroom rule interaction** — `BASKETS.md:16` recommends dose -0.5g if you see mesh imprint. With a puck screen installed, this evidence is masked. Options:
   - (a) Do nothing; user learns from the knowledge-file-carried dose guidance.
   - (b) Add a one-line note to `BASKETS.md:16`: *"If puck screen installed, this check is masked — rely on flow behavior and measured headroom instead."*
   **Question**: (a) or (b)? *Defer to spec §3.*
