---
schema_version: "1"
uuid: 3d6d9f57-c538-4626-a8e8-24c9f075a363
title: "Operationalize RPM as an extraction variable across the skills (DF64V variable-speed)"
status: backlog
priority: medium
type: feature
created: 2026-06-03
updated: 2026-06-03
parent: "024"
---
## Why

The DF64V is a **variable-speed** grinder — RPM is a genuinely new extraction variable the Sette 270 never had. Today RPM is **documented but not operationalized**:

- **Knowledge layer (025):** `knowledge/grinders/DF64V.md` (quick-ref) and `knowledge/reference/DF64V_REFERENCE.md` (deep-dive) both cover RPM, well-hedged. ✅
- **Data slot (026):** `grind-map.md` has an `RPM` column. ✅
- **Skills:** **Zero** skills recommend, log, or adjust RPM. `/new-coffee`'s output template has no RPM row; `/feedback` never logs or adjusts it; `/diagnose` ignores it; `_NOTATION.md` is silent on how to log it. ❌

026's own research explicitly predicted *"a header schema no skill populates"* — that seam is now real: the column exists and nothing fills it. This item closes the loop by wiring RPM through the skill workflows.

**No new research is warranted** — 025's `research.md` already established the RPM science (and found it contested/null; re-running web research would only re-confirm that). The deep-dive reference (`DF64V_REFERENCE.md`) already carries an *"RPM as a Body/Clarity Lever"* section. This item is therefore **skill plumbing + a thin knowledge-synthesis layer** (authoring findings already in hand into skill-consumable lever guidance), **not** a research spike. See Non-Goals.

## Role / What

Operationalize RPM as a first-class variable across the workflows (user chose the "full lever" scope over config-only). Areas a solution could explore:

- **`/new-coffee`:** one approach is to add an RPM row to the Starting Parameters output, recommending a starting RPM resolved from the active grinder reference (DF64V default ~1000–1100), hedged.
- **`/feedback`:** consider prompting for / logging RPM into the existing grind-map RPM column (closing 026's seam), and offering RPM as a *secondary, well-hedged* adjustment lever — explored only after grind + puck prep, never the first move.
- **`/diagnose`:** could factor RPM context into telemetry correlation (e.g., flag RPM unusually high/low vs the configured range).
- **`_NOTATION.md`:** likely needs RPM logging rules (integer RPM; when to record; that it is grinder-config, not a chirp coordinate; blank for fixed-speed grinders — consistent with the grind-map legend).
- **Knowledge synthesis (`knowledge/grinders/DF64V.md`):** the quick-tier lever framing is thinner than the deep tier — and the quick tier is what skills load first via the Active Grinder contract. Consider authoring a crisp, skill-consumable *"RPM as a dial-in lever"* note: the **narrow triggers** for reaching for RPM at all (grind/ratio/temp exhausted; deliberately chasing a body/clarity experiment), the RPM↔grind re-dial **direction** implied by the McKeon Aloe measurement (raise RPM → likely go finer to hold shot time) stated as a **tendency, not a law**, and a firm *"this is contested; your own logged data is the real signal"* hedge. This is synthesis from research already done — no new sources needed.

The plan phase should decide exactly how aggressive the `/feedback` lever is, given the contested science below.

## Integration / Constraints (firm — established facts/patterns, not up for re-litigation)

- **Inherit 025's seven-fact hedges.** Especially: RPM→body is **contested** — Hoffmann's blind test = null; McKeon Aloe *measured* higher RPM → **coarser** (opposite of the vendor "more RPM = more body" story). ~1000–1200 is the default; 1400 = vendor more-body preference, **not** a floor. RPM is a **coarse** lever that forces a re-dial, not a fine knob. Skills must **not** canonize an unqualified "RPM = body" claim to an intermediate barista.
- **Obey the CLAUDE.md Active Grinder field parsing contract (027):** RPM guidance applies **only** when the resolved active grinder is variable-speed. Fixed-speed grinders (Sette) get **no** RPM prompts and leave the column blank. Attempt-then-fallback, never error.
- The grinder reference files remain **authoritative** for RPM numbers; skills point to them rather than hardcoding competing values (mirrors the CLAUDE.md guard: RPM is a grinder control, not a temp/pressure claim).

## Edges

- Fixed-speed grinder active → no RPM prompts, blank RPM column.
- grind-map RPM column already exists (026) — **populate** it; do not re-add or change column structure.
- Mixed-epoch grind-map rows: pre-existing blank RPM = unknown (back-compat); do not infer a value.
- RPM changed mid-bag → forces a grind re-dial; `/feedback` should warn and re-anchor, not silently carry the old grind setting forward.

## Touch-points (candidates)

The `skills/` edits are **lifecycle-protected** (per CLAUDE.md), so implementation **must** go through `/cortex-core:lifecycle`. The `knowledge/` edits are **not** protected (plain content), but are tightly coupled to the skill logic — doing them in the **same lifecycle run** keeps skill guidance and the knowledge it cites consistent.

**Lifecycle-protected (`skills/`):**
- `skills/new-coffee/SKILL.md` — synthesize step + output template
- `skills/feedback/SKILL.md` — gather + grind-map write + adjustment logic
- `skills/diagnose/SKILL.md` — correlation
- `skills/consult/SKILL.md` — optional RPM Q&A routing (minor)

**Not protected, but coupled (`knowledge/`):**
- `knowledge/grinders/DF64V.md` — quick-tier "RPM as a dial-in lever" synthesis (the skill-consumable layer)
- `knowledge/grinders/_NOTATION.md` — RPM logging rules
- `knowledge/reference/DF64V_REFERENCE.md` — existing "RPM as a Body/Clarity Lever" section is the backing depth (likely reference-only)

**Reference only (do not restructure):**
- `grind-map.md` / `grind-map.example.md` — RPM column already present (026 owns the structure)
- Auto-generated mirrors under `plugins/cortex-core/` regenerate via pre-commit — edit canonical sources only.

## Dependencies

- **Blocked-by:** none — 025, 026, 027 all complete.
- **Relationship to 028** (commission DF64V + phased re-dial): complementary. Landing this **before/with 028** means the commissioning re-dial logs RPM correctly from the start.

## Non-Goals

- **No new web-research spike on RPM.** 025's research stands; the literature is contested/null (Hoffmann blind-test = null; a single McKeon Aloe measurement pointing the *opposite* way to the vendor story). More desk research would re-confirm the uncertainty, not reduce it — and would risk manufacturing false confidence the hedges exist to prevent.
- **The evidence going forward is personal data, not literature.** Once this ships and `/feedback` populates the RPM column, the user's own RPM↔outcome history on these burrs/these beans is the authoritative signal. In effect, 029's logging *is* the longitudinal RPM study — which is why getting the logging right matters more than chasing more sources.
- Not changing the grind-map column structure (026 owns it); not altering fixed-speed-grinder behavior.

## Acceptance (sketch — refine in spec)

- `/new-coffee` output includes an RPM row when the active grinder is variable-speed.
- `/feedback` logs RPM into the grind-map column for variable-speed grinders.
- `_NOTATION.md` documents RPM logging.
- `knowledge/grinders/DF64V.md` carries skill-consumable "RPM as a dial-in lever" guidance (narrow triggers + re-dial-direction *tendency* + contested/own-data hedge), consistent with the deep-ref section.
- All RPM-as-lever guidance is hedged per 025's seven facts (no unqualified "RPM = body").
- Fixed-speed grinder path: no RPM prompts, RPM column left blank.