# Research: DF64V Gen 3 + SSP Cast Lab Sweet V3 Red Speed (espresso) migration

> Prior art: this builds on `cortex/research/burr-recommendation.md`, which recommended exactly this burr/grinder combo. The **burr/grinder selection is locked and the user is committed to moving fully onto the DF64V** — not re-litigating MP-vs-Cast or Gen-2-vs-Gen-3. This artifact answers "how do we accommodate it" — workflow, profiles, grind map, knowledge files, and a multi-user-aware grinder layer. (Earlier drafts of this artifact over-weighted "can't build espresso pressure" warnings; on review those signals trace to the **filter-oriented V2 Silver Knight burr, to non-DF64V grinders, or to fixable alignment issues** — NOT to the V3 Red Speed *espresso* burr on a DF64V, which is purpose-cut for espresso. See the recalibration in Q2 and the Decision Records.)

**Clarify-phase decisions carried in:** (1) DF64V becomes the **sole** grinder — Sette retired; (2) archive the Sette grind map, start a fresh DF64V map; (3) profile strategy is **deferred to this research**; (4) NEW constraint — others may use this repo for their own setups, so the grinder layer should be **swappable**, not hardcoded.

---

## Research Questions

1. **What is the "DF64V Gen 3" really, and what specs matter for dialing?**
   → **"Gen 3" is a fuzzy retailer/marketing label, not a clean engineering generation.** The hardware is the current variable-speed **DF64V** (df64coffee.com titles it "Gen 3"; DF's own dfgrinders.com still calls the same unit "Gen 2"; the Turin page title says "Gen 3" while its URL slug says "gen-2"). No independent reviewer (Hoffmann, Hedrick, Tom's Grinder Lab, Coffee Chronicler) has reviewed a unit *explicitly badged "Gen 3"* — all substantive independent data is of "the DF64V." The marketed "Gen 3" deltas (single chute, magnetic detachable chute + anti-popcorn ring, metal "flickable" declumper flap, plasma/ion static generator, possibly stronger motor) are **marketing-sourced, not bench-confirmed**. **What actually matters for dialing:** RPM range **600–1800** (stroboscope-verified by Tom's Grinder Lab); takes standard **64mm flats** including SSP drop-in; **~0.1 g retention** with bellows. *(Confidence: HIGH that "Gen 3" is a soft label; HIGH on RPM/burr/retention.)*

2. **What is the SSP Cast Lab Sweet V3 Red Speed (espresso) burr, and how does it behave?**
   → **"V3" is a generation, "Red Speed" is a coating** — V3 ships in both Red Speed and Silver Knight. There is **no separate "espresso geometry" SKU**: V3 *is* the espresso-leaning re-cut of the filter-oriented V2 (fixed burr identical to V2; rotary burr re-cut with ~15% more cutting edges + increased fineness so it can reach espresso pressure). So "the espresso version" = **V3 + Red Speed coating** (Red Speed → more friction → more fines/body; Silver Knight → cleaner/lighter). Positioned as a **body↔clarity middle ground** (more body than SSP MP, less ultra-clarity than HU). Favors **light-to-medium roasts; avoid oily/dark.** **No quantitative particle-size data exists anywhere.** **Espresso capability — recalibrated:** the V3 Red Speed *is the espresso burr* (V3 was re-cut finer specifically so the Lab Sweet geometry could reach espresso pressure, which the filter-oriented **V2 Silver Knight** struggled to do). The "can't build espresso pressure / disrecommended for espresso" chatter in the wild attaches to (a) the **V2 filter burr**, (b) **other grinders** (e.g. Zerno) with different gap/RPM behavior, or (c) **alignment/debris/loose-upper-plate** mechanical faults — not to a correctly-aligned, seasoned V3 Red Speed on a DF64V (a proven espresso platform that takes SSP espresso burrs cleanly). Expect **dial-in to be somewhat fiddly with a possibly narrow choke margin and a fine working point**, not incapable. *(Confidence: HIGH on the V2/V3 mechanism and roast fit; the flavor/PSD picture rests on near-identical reshipped retailer copy.)*

3. **How do you express, record, and translate grind settings on the stepless collar?**
   → **No reliable conical→flat numeric translation exists — re-dial from scratch.** Record settings as **"chirp + N marks"** (marks coarser from the burr-touch/zero point), never the printed number (the printed "0" is meaningless and the chirp point *moves* when burrs are swapped — SSP burrs are thicker). DF64V ring has ~90 marks, stepless; ~12.5 µm/mark (rule-of-thumb, single source). Espresso starting window for SSP on a DF: **~10–30 marks from zero, light roast at the finer end**; move 1–3 marks at a time. Re-verify chirp after any clean/burr swap. *(Confidence: HIGH on relative-to-zero principle; MEDIUM on the micron figure and the exact window.)*

4. **What do flat/unimodal burrs imply for profiles — and what should happen to the current 7.5-bar bloom-slide profiles?**
   → Flats produce a more unimodal grind (one retailer guide — Complete Home Barista — claims SSP "cuts fines ~30–40%" vs stock burrs; **this is an SSP-general retailer figure, not a measured Cast-V3-specific number, and no quantitative PSD data exists for this burr** — treat as directional only), which generally wants a **finer grind** to hit the same flow, accelerates flow faster, and (in theory, **magnitude contested**) tolerates higher pressure with less fines-migration channeling. **Recommendation: phased, change-one-variable-at-a-time.** Keep the gentle bloom-slide profiles (they align with the low-pressure-profiling philosophy and with fruit-forward light naturals); **re-dial grind first** to re-establish target flow on the new burr, *then* optionally nudge peak toward 8–9 bar and/or trim bloom **only when a shot is diagnosed under-extracted** (see operationalized trigger below). Do NOT re-engineer profiles up front — seasoning drift (Q6) makes early re-engineering premature. *(Confidence: HIGH on phased approach; MEDIUM on the specific pressure/bloom tweaks, which are experiments to A/B with telemetry.)*

   **Operationalizing the Phase-1→Phase-2 trigger (so it can be ticketed):** "thin" and "under-extracted" are *different axes* and the pressure bump only addresses one. **Under-extracted** (the trigger for a pressure/temp/finer-grind change) = sour/sharp acidity, salty, short/empty finish, watery — diagnose via `ESPRESSO_TASTING_GUIDE.md` sour-vs-bitter methodology; telemetry signature: shot pulls fast / flow ramps early / fails to reach target resistance. **Thin** (body/mouthfeel alone) on a balanced or sweet shot is the *expected* flat-burr clarity trade and is NOT a pressure-bump trigger — manage it with RPM (toward ~1200), ratio (toward 1:2.5–3), or burr-shape acceptance, not by cranking pressure (which risks over-extraction/bitterness). **Phase-1 ("re-dial") is declared done** when three consecutive shots at a fixed grind land in your target time/ratio band with the seasoning trend flattened (≥~3 kg through, settings no longer drifting shot-to-shot) — only then open Phase-2 pressure/bloom experiments.

5. **Where do Sette/grinder assumptions live in the repo, and what changes vs archives?**
   → Touch-points span **knowledge files, three skills, the grind-map column format, user-setup, and per-coffee profiles** (full citations in Codebase Analysis below). The grind-map `Grind` column and the `/feedback` skill hardcode the Sette `9D`/macro+micro notation `[skills/feedback/SKILL.md:136]`; `/new-coffee` falls back to `SETTE_270.md` `[skills/new-coffee/SKILL.md:58]`; `/consult` routes the "Sette" keyword to `SETTE_270.md` `[skills/consult/SKILL.md:28]`. MCP stores `grind_setting` as a free string → **no code change needed**. *(Confidence: HIGH — direct file:line evidence.)*

6. **Should the grinder layer be generalized for a shareable multi-user repo?**
   → **Yes.** `knowledge/grinders/` currently holds a single hardcoded `SETTE_270.md` with no template `NOT_FOUND(query="grinder template", scope="knowledge/grinders/")`. The cleanest design splits **grinder-agnostic mechanics** (a notation guide + relative-step dialing language the skills can always fall back to) from a **per-grinder file** keyed off the `user-setup.md` Grinder field. The example template (`user-setup.example.md` uses a generic "Baratza Encore ESP") and the README customization note are already grinder-neutral — the gap is the *knowledge files and skills* that name the Sette directly. *(Confidence: HIGH.)*

---

## Codebase Analysis

Source: thorough read-only sweep (Explore agent). All claims carry `[file:line]`.

**Sette-named knowledge content (rewrite or archive):**
- `[knowledge/grinders/SETTE_270.md:1]` — entire file is the Sette adjustment reference (macro 1–31 ring, micro A–I, "8–14 macro range for espresso").
- `[knowledge/reference/SETTE_270_REFERENCE.md:1]` — deep-dive maintenance/calibration/retention ("Typical retention: ~0.5g" `[…:14]`, "moderate clumps and static" `[…:38]`).
- `[knowledge/EXTRACTION_SCIENCE.md:15]` — grinder-archetype table: "**High-fines conical** (Sette 270, Niche)" → 7–8 bar / gentler ramp; `[…:21]` cross-ref to `SETTE_270.md`; `[…:46]` paper-filter advice keyed to "high-fines grinders (like the Sette 270)". Notably `[…:16]` already names "**Low-fines flat** (EK43, SSP burrs) → can handle 9 bar consistently" — the framework already anticipates the flat case.
- `[knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md:126,134]` — "Sette 270 uses conical burrs… produce more fines → lower extraction pressure."

**Sette-coupled *advice* expressed in macro steps (de-couple to grinder-relative language):**
- `[knowledge/SPECIAL_CATEGORIES.md:17,24]` — decaf: "1–3 macro steps coarser", "On the Sette 270, start 2–3 macro steps coarser".
- `[knowledge/reference/BEAN_FRESHNESS_REFERENCE.md:149]` — frozen beans: "1–2 macro steps coarser".
- `[knowledge/reference/ESPRESSO_BREWING_REFERENCE.md:35]` and `[knowledge/reference/PROFILE_LIBRARY_REFERENCE.md:353]` — turbo: "2–4 macro steps coarser".

**Skills (parameterize off user-setup):**
- `[skills/feedback/SKILL.md:136]` — "**Grind notation:** Full Sette 270 format: macro + micro letter (e.g., '9D')" — hardcoded in the record-to-grind-map step. `[…:29]` loads `SETTE_270.md` on grind questions.
- `[skills/new-coffee/SKILL.md:58]` — "If no match: use defaults from `knowledge/grinders/SETTE_270.md`".
- `[skills/consult/SKILL.md:28]` — routes keyword "Sette" → `SETTE_270.md`; `[…:77]` loads `SETTE_270_REFERENCE.md` for calibration questions.
- `[CLAUDE.md:29]` — knowledge-file index entry for `grinders/SETTE_270.md`.

**Grind map (archive + restart, format change):**
- `grind-map.md` header (exact): `| Coffee | Roast | Process | Origin | Days Off Roast | Grind | Profile | Ratio | Temp | Rating | Date | Puck Screen? |` — the `Grind` column holds Sette codes (`13D`, `13E`, `12E`…). All 12 rows are Sette-format. `grind-map.example.md` mirrors this format.

**user-setup (update Grinder field):**
- `user-setup.md` → `| **Grinder** | Baratza Sette 270 (conical burr, micro-adjust) |` (active data, in private repo via symlink).
- `user-setup.example.md:8` → generic "Baratza Encore ESP (flat burr, stepped adjust)" — already grinder-neutral.

**Per-coffee profiles (re-dial after seasoning):**
- Representative `coffees/onyx-ethiopia-bochesa/bloom-slide.json`: 5 phases, `temperature: 96`, bloom = pump off (`pressure:0`), ramp/peak-hold at **7.5 bar**, fruit-slide decline to 4 bar, volumetric stop. README explicitly: "Reduced pressure (7.5 bar)… controls fermentation intensity" and "prone to channeling due to **Sette 270 fines** + anaerobic stickiness." Profiles were authored against the Sette's high-fines bimodal bed.

**No code change needed:**
- MCP stores `grind_setting` as a generic string (`grind_setting="9D"` is just a string in tests) — a stepless notation drops in without schema change. `NOT_FOUND(query="grind_setting type validation", scope="mcp/**")` — no parser constrains the format.

**Skills NOT grinder-coupled (no change needed):**
- `/gaggimate-profiles` references grind only generically — `[skills/gaggimate-profiles/references/PUMP_AND_TRANSITIONS.md:146]` ("consistent extraction across different grind settings"); no Sette/macro notation. `/diagnose`: `NOT_FOUND(query="sette|macro|grind notation", scope="skills/diagnose/**")` — no grinder coupling. So only `/feedback`, `/new-coffee`, `/consult` need parameterizing (work-stream F).

**Architecture gaps for multi-user:**
- `NOT_FOUND(query="grinder template file", scope="knowledge/grinders/")` — only `SETTE_270.md` exists; no template, no per-grinder scaffolding.
- README customization note ("Replace `knowledge/grinders/SETTE_270.md` with a guide for your grinder") is already grinder-neutral — the *skills and shared knowledge files* are the part that hardcodes the Sette.

---

## Web & Documentation Research

### DF64V "Gen 3" hardware
- **Generation labeling is unreliable.** df64coffee.com → "Gen 3"; dfgrinders.com → "Gen 2" for the same current unit; Turin page title "Gen 3" / URL slug "gen-2". *Verify the actual spec sheet on the specific unit, not the badge.* (retailer/marketing; cross-checked across sellers)
- **RPM 600–1800**, stroboscope-verified (Tom's Grinder Lab — independent). Marketing variously says 800–1800 or 900–1800 (likely the espresso-safe sub-range or a different voltage unit).
- **Low-RPM stall is the load-bearing operational fact.** Motor lacks low-end torque; **stalls in the ~600–800 RPM zone, especially dense light roasts at fine espresso settings dumped all at once.** MiiCoffee's own support article recommends **1400 RPM for espresso**; Home-Barista users say **"1000 RPM and above."** Practical espresso floor ≈ **1000 RPM (1400 to be safe)**. Mitigations: hot-start (motor already spinning), slow-feed. Unit-to-unit variance is significant. (manufacturer + independent)
- **Notable:** switching to **SSP *Multipurpose*** burrs reportedly *eliminates* the low-RPM stall (less cutting resistance). ⚠️ This is reported for **MP**, not the Cast/Lab-Sweet line — Cast has *more* cutting edges/fines, so **do not assume the stall mitigation transfers.** (independent — Coffee Chronicler, Tom's, Reddit)
- **Burr fitment:** standard 64mm flats drop in; SSP sets fit **without shims** (Tom's Grinder Lab tested SSP incl. espresso/HU). *Exceptions:* Fiorenzato and Mazzer 64mm "failed to function" — "any 64mm" is not literally true.
- **Retention ~0.1 g with bellows** (bellows mandatory; measured by brewcoffeehome + Tom's). **Static/clumping is the main gripe** → RDT recommended.
- **Factory alignment generally good** (Tom's: "all seven arrived perfectly aligned"; Coffee Chronicler concurs) but **QC not flawless** — chute magnet fell out during one review; alignment/shim complaints exist on the DF64 line. Budget a return-window alignment check.
- **Workflow:** single-dose only, 58mm dosing cup, no PF fork. **Price ~$499–599 stock; ~$699–800 SSP-equipped.** Time-to-grind-22g: **no sourced figure** (inference ~12–20 s at higher RPM).

### SSP Cast Lab Sweet V3 Red Speed (espresso)
- **V3 = espresso-leaning re-cut of filter V2**: identical fixed burr, rotary re-cut with **~15% more cutting edges + increased fineness** so espresso pressure becomes achievable (V2 "struggled at espresso"). Consistent across Sigma, Zerno, Someware, Eight Ounce. (retailer + mfr-adjacent)
- **Red Speed coating** (most sources: TiAlCN; one says TiN — likely error) → higher friction → **more fines/body**; Silver Knight (DLC) → cleaner/lighter.
- **Flavor (marketing):** "Bright, Juicy, Sweet, Medium Body"; favors **light–medium roasts, avoid oily/dark** (Zerno, Espresso Outlet). **No process-specific (natural/anaerobic vs washed) guidance exists.**
- **Seasoning:** SSP founder (via Coffee Chronicler) — **2–3 kg, coffee only, NOT rice**; a Turin customer corroborates 3 kg; a forum synthesis says noticeably better at ~2–5 kg, improving to 8 kg+; Cast specifically cited as a long/stubborn ~5–10 kg seasoner. **Plan: don't trust settings until ≥3 kg, expect drift up to ~5–10 kg.**
- **RPM is genuinely contested:** Zerno (vendor, sells low-RPM grinder) says **300 RPM** for "surgical clarity"; Coffee Chronicler (independent) says Cast burrs "become much cleaner around **900 RPM**." **300 RPM is below the DF64V floor anyway** → moot. Converges with prior art on **~1000–1200 RPM** as the practical espresso operating point.
- **Espresso dial-in can be fiddly — but capability is not in doubt for the V3 Red Speed espresso burr.** Reading the negative signals carefully: the "unable to grind fine enough to build full espresso pressure" reports are on **Zerno grinders** (different gap/RPM mechanics) and largely concern the **V2**; "V3 only slightly better than V2" is a Zerno-user comparison, not a DF64V verdict. Espresso Outlet's "DISRECOMMENDS Cast Lab Sweet for espresso ('difficult to dial in')" is a **fiddliness/dial-in claim about the broader/older Cast line** (they separately sell the V3 Red Speed *as* the espresso variant) — not "can't build pressure." On a DF64V specifically, "can't grind fine enough" reports are "**usually traced to alignment, debris, or a loose upper plate rather than the burrs themselves**" (Home-Barista t94555). Net: expect a **fine working point and a possibly narrow choke margin** that rewards good alignment + seasoning + patience — plan for fiddly dial-in, not failure.
- **Price ~$185–235**; frequently out of stock. V1 had a historical alignment defect (fixed in V2) — not a current V3 concern.

### Conical → flat practical shift
- **Dialing grammar:** find chirp (burrs kiss, then back off to faint scratch); log "chirp + N marks"; printed numbers meaningless and move on burr swap; optional dial-indicator for repeatability; re-verify chirp after cleaning.
- **No conical→flat translation** — re-dial from scratch; expect to land **finer** than Sette instinct.
- **Profiles:** finer grind to hit flow; faster-accelerating flow; higher-pressure tolerance is **theory with contested magnitude** (Prima calls it "a hot topic of debate"); clarity-leaning flats can taste thin → many push **longer ratios (1:2.5–1:3)**.
- **Flavor shift:** more clarity/acidity/fruit, less body — **real but evolutionary, not revolutionary.** ⚠️ **Hoffmann's blind testing found NO clean correlation between burr shape and the body↔clarity axis** — judge specific burr *sets*, not "flat vs conical" as categories. This is the strongest expectation-management caveat.
- **Workflow tax vs Sette:** **RDT every dose** (static) + **WDT non-negotiable** (clumping) — uniform particles do NOT fix prep-induced channeling. Retention comparable/better with bellows technique.
- **Variable speed is a real lever:** low RPM → clarity/less body; high RPM → more body. Mid **~1000–1200 RPM** is a common espresso sweet spot (and dodges the stall). Use RPM to *partially recover the body* the flat geometry costs.
- **Seasoning counterintuitive direction:** as burrs round in, grind drifts **coarser** → you chase it **finer**. Don't lock a "house setting" until ~5–10 kg through. Season on cheap/stale beans (use up old Sette-era bags).

---

## Domain & Prior Art
- **Single-dose-to-single-dose** is the easy part — the Sette is already single-dose, so the leap is smaller than for a hopper-grinder migrant. The genuine new workflow costs are **static/RDT** and **stepless logging**, not the dosing model.
- **The "flats = clarity" narrative is oversold** (Hoffmann) — set this user's expectations as "a clarity nudge and a body trade you'll manage," not a new machine.
- **Prior burr-recommendation.md already framed this honestly** as a *ceiling/clarity upgrade, not a problem-fix* — six existing 5★ shots on the Sette. The migration's success bar is "more separation on coffees already enjoyed," and the floor scenario ("matches or slightly underperforms the Sette for ~$684") is plausible and should be accepted before committing time.

---

## Feasibility Assessment

| Approach (work-stream) | Effort | Risks | Prerequisites (implementation-sequencing) |
|---|---|---|---|
| **0. Commission & first-light** (in hand, non-blocking: verify factory alignment — DF64V QC isn't flawless; find the chirp/zero point; season ~3 kg on stale beans; pull first shots and note the practical RPM floor on *your* unit). Just good new-grinder hygiene — the repo migration below does **not** wait on it. | S | DF64V QC notes (chute magnet, occasional shim) → a quick alignment check is worth it. Expect a fine working point + narrow choke margin (fiddly dial-in), not incapability. Only escalate to a return if a genuine *defect* (misalignment that won't shim, motor stall that SSP doesn't cure) shows up within the window. | New grinder in hand |
| **A. New `DF64V.md` grinder reference** (stepless dialing, RPM floor, seasoning, workflow) | S | Spec drift if "Gen 3" features mis-stated → keep it operational (RPM/dialing/seasoning), not marketing-feature-led | None |
| **B. Grinder-agnostic grind notation guide** + adopt "chirp + N marks" | S | Notation must survive re-zero/burr swap; user must establish chirp first | A drafted |
| **C. Archive Sette artifacts** (`git mv` grind map → `grind-map-sette-270.archive.md` *inside the private data repo* to preserve rename history; `SETTE_270.md`/reference → archived, read-only). **First snapshot the shot telemetry** the archived map's `shot_id`s reference (export the `.json` sidecars to the private repo) — per the firmware-1.8.0 retention note, the device's free-space purge can delete those sidecars silently, so the markdown alone is NOT a complete audit trail. | S | "lose nothing" only holds *with* the telemetry snapshot; without it the archived rows become dead `shot_id` links | Fresh map exists (D); telemetry snapshotted (quick, non-blocking) |
| **D. Fresh DF64V grind map** (grinder-agnostic `Grind` column + add RPM column) | S | Empty until shots pulled; format must be multi-user-neutral | B (notation) |
| **E. De-Sette shared knowledge files** (EXTRACTION_SCIENCE, SPECIAL_CATEGORIES, BEAN_FRESHNESS, BREWING, PROFILE_LIBRARY refs) → grinder-relative language | M | Many small edits; must not lose the high-fines-vs-low-fines *teaching*, just re-key it | A (so they can cross-ref DF64V) |
| **F. Parameterize skills** (feedback/new-coffee/consult read Grinder from user-setup; fall back to relative-step advice) | M | Skills are behavioral contracts — needs lifecycle (skills are protected paths); must not break existing flows | A, B |
| **G. Update `user-setup.md`** Grinder field + RPM note | S | Private-repo data write — overwrites the only in-repo Sette record; **recovery is git history via the auto-commit policy** (so the prior `Baratza Sette 270` value stays retrievable). Commit before and after. | None |
| **H. Phased profile re-dial** (re-dial grind first; nudge pressure/bloom only when a shot is *diagnosed under-extracted* per Q4; re-author per-coffee profiles after seasoning). **Snapshot first:** copy each proven profile to a `*.sette.json` sibling (or git-tag) before re-authoring in place — the six 5★ configs must stay recoverable. **Obey "Repo first, device second":** write the repo JSON, *then* upload via MCP. | L (spread over ~2 wks seasoning) | Seasoning drift; don't over-fit early shots; in-place re-author destroys the proven config unless snapshotted | New grinder seasoned (≥~3 kg); proven profiles snapshotted |
| **I. Multi-user grinder layer** (template `knowledge/grinders/_TEMPLATE.md`; README/CLAUDE.md note) | S–M | Scope creep into a full plugin-ization; keep minimal — template + neutral fallbacks | E, F define what "agnostic" means |

**Two independent tracks — sequence them separately:**
- **Physical track (clock-driven):** Commission (0) → archive Sette (C) + fresh map (D) + user-setup (G) can all proceed immediately and in parallel → re-dial profiles (H) once seasoned. This is what you do with the grinder in hand under the seasoning clock. None of it needs `/cortex-core:lifecycle`. Archiving the old map does **not** wait on anything (per user direction).
- **Software/knowledge track (no external clock):** A, B, E, then F and the skills part of I. **Editing skills, hooks, and certain `bin/`/`cortex_command` paths requires `/cortex-core:lifecycle`** (protected paths) — F and parts of I must route through it; A/B/E are plain content edits.
- **Day-one caveat:** until F lands, `/feedback` still hardcodes Sette `9D` notation `[skills/feedback/SKILL.md:136]`. To record DF64V settings during seasoning *before* the lifecycle-gated F completes, log them manually in the fresh DF64V map (D) using "chirp + N marks" — do not block the physical track on the skills refactor.

---

## Architecture

### Pieces
- **The grinder reference** — a per-grinder knowledge file (new `DF64V.md`) describing how *this* grinder is dialed and run (stepless collar, ~1000–1200 RPM operating point + stall floor, seasoning schedule, RDT/bellows workflow). Replaces the Sette's role; the Sette file becomes an archived sibling.
- **The dialing notation** — a grinder-agnostic convention ("chirp + N marks", re-verified after burr swaps) that both the grind map and the skills speak, so grind settings are recordable on any stepless or stepped grinder.
- **The grind history** — split into a frozen **archived Sette map** (read-only audit trail, moved via `git mv` inside the private repo to keep rename history, with its referenced shot telemetry snapshotted alongside) and a **fresh DF64V map** whose `Grind` column is free-text notation plus a new RPM column.
- **The shared extraction knowledge** — the teaching files that currently use the Sette as the worked example, re-keyed from "macro steps / Sette conical" to grinder-relative language ("go finer/coarser by a small step") while preserving the high-fines-vs-low-fines lesson the framework already half-states.
- **The skills** — `/feedback`, `/new-coffee`, `/consult` read the active grinder from `user-setup.md`, reference whatever per-grinder file exists, and fall back to relative-step advice when none matches — instead of hardcoding the Sette.
- **The profile strategy** — a phased plan that snapshots the proven profiles first (`*.sette.json` siblings), keeps the gentle bloom-slide, re-dials grind on the seasoned burr, and only then nudges pressure/bloom per-coffee when a shot is *diagnosed under-extracted*, with telemetry as the arbiter.
- **The setup pointer** — `user-setup.md`'s Grinder field, the single source of truth the skills key off to pick the right grinder reference.

### How they connect
`user-setup.md`'s Grinder field is the hub: the skills read it to decide which per-grinder reference (the **grinder reference** piece) to load and which fallback to use. The **dialing notation** is the shared language between the grinder reference, the fresh **grind history**, and the skills — change it in one place and all three stay consistent. The **shared extraction knowledge** depends on the grinder reference only for a cross-link; its job is to stop *naming* the Sette so it reads correctly for any user. The **profile strategy** sits downstream of everything physical: it begins once the grinder is seasoned, and its outputs (re-dialed grind settings, possibly higher peak pressure) flow back into the fresh grind history and the per-coffee profile JSONs. The multi-user generalization is **not a separate component but a design principle threaded through every piece**: the grinder reference is per-grinder-file-shaped, the grind history column is notation-neutral, the shared knowledge stops naming the Sette, and the skills key off the setup pointer. Only the **skills refactor** is lifecycle-gated and is sequenced as a fast-follow so it never blocks the physical dial-in — but because the design is agnostic from the start, nothing built earlier has to be undone to support the next user's grinder.

---

## Decision Records

**Fresh grind map over combined.** User-chosen and research-confirmed: Sette macro+micro codes (`13E`) have no defined relationship to a DF64V stepless mark, and SSP seasoning drift means even the DF64V's own early numbers are unstable. Mixing grammars in one table would mislead future lookups. The archived Sette map stays as a read-only record of what *tastes* worked (roast/process/ratio/temp/rating remain transferable signal even though grind doesn't).

**Phased profile strategy over up-front re-engineering.** Research is firm on change-one-variable-at-a-time and on keeping the gentle bloom-slide (it aligns with low-pressure-profiling philosophy and fruit-forward light naturals; constant 9 bar raises late-shot channeling). Re-engineering profiles *before* the burr is seasoned would tune against a moving target — seasoning drifts grind coarser over ~5–10 kg. So: re-dial grind first, treat 8–9 bar peak and shorter bloom as *experiments triggered by an under-extraction diagnosis* (Q4's operationalized trigger — sour/short-finish + fast-pull telemetry, NOT mere thinness), not defaults. (The grinder-archetype table anticipates flats handling ~9 bar — but Hoffmann's null result and Prima's "contested magnitude" mean we earn the pressure bump empirically, not on faith; the 8–9 figure is borrowed from the general pressure matrix, not from any Cast-V3-specific evidence.)

**Generalize the grinder layer — as a core design principle, built in from the start (not bolted on later).** The user wants the repo to work for others with different grinders, so we build the new pieces **grinder-agnostic from the first keystroke** rather than Sette→DF64V hardcoding that we'd later have to undo. Concretely, the multi-user design is:
1. **Per-grinder knowledge files** — `knowledge/grinders/<GRINDER>.md`, one per grinder, each documenting *that* grinder's dialing system (stepped vs stepless, RPM, seasoning, workflow). `DF64V.md` (A) takes the active role; `SETTE_270.md` archives; a `_TEMPLATE.md` (I) scaffolds new ones so a forker drops in their grinder.
2. **`user-setup.md` Grinder field is the selector** (G) — the one place a user names their grinder; skills read it to choose which grinder file to load. The example template is already grinder-neutral.
3. **Grinder-agnostic grind map** (D) — the `Grind` column becomes free-text (whatever notation that grinder uses: `13E` for a Sette, `chirp+22 @1150rpm` for a DF64V) + an RPM column, with a short notation guide (B) teaching "record relative to a fixed reference (zero/chirp)."
4. **Skills fall back to relative-step language** (F) — instead of Sette-specific "go 1–2 micro steps finer," skills say "go finer by a small step" and defer absolute specifics to the active grinder file; when no grinder file matches, grinder-relative advice still works.
5. **Shared knowledge de-Setted** (E) — EXTRACTION_SCIENCE etc. teach high-fines-vs-low-fines as a general principle and cross-link to whatever grinder file is active, instead of using the Sette as *the* worked example.

Honest cost note: the **personal** dial-in is unblocked by A+D+G + the physical track; the generalization adds E (five shared files) + F (three skills, **the one lifecycle-gated piece**) + I (template). F is sequenced as a fast-follow so it never blocks the physical dial-in — but the *design* is agnostic throughout, so nothing here is throwaway. Bounded below a full grinder-plugin system (no per-grinder code, no registry — just files + a selector field + neutral language).

**Operate at ~1000–1200 RPM (working hypothesis, not a converged fact).** This rests on **one** load-bearing constraint — the DF64V low-RPM stall floor (~1000 practical, 1400 safe per MiiCoffee + Home-Barista), which is *manufacturer/forum-sourced, unit-variable, and reported for stock/MP burrs, NOT confirmed for the higher-fines Cast burr*. The two supporting notes are weaker than "independent corroboration": Coffee Chronicler's ~900 RPM clarity note actually points *below* the stall floor (it argues for going lower, if the motor allowed), and the prior burr-recommendation's "1100–1200" is this project's own sibling document, not a third independent source. So: start at ~1100–1200 as a stall-safe espresso default and **find your unit's actual floor empirically** (Gate 0 / OQ2). The "RPM as body-recovery lever" idea (low→clarity, high→body) is **vendor-framed and unproven** — the same body↔clarity axis Hoffmann's blind test nulled — so try it as an experiment, don't bank on it.

**Honest success bar (carried from prior art).** This is a ceiling/clarity upgrade, not a fix — six 5★ Sette shots already exist, so the bar is "more separation on coffees already enjoyed," and the realistic floor is "works well but only matches/slightly betters the Sette for the ~$684 spend." Accept that floor before sinking ~2 weeks of re-dialing. The honest *cost* is **patience**: the V3 Red Speed is espresso-capable but lives at a fine working point with a possibly narrow choke margin, so expect dial-in to be fiddlier than the Sette's forgiving conical, and expect settings to drift through seasoning before they settle. ("Can't build pressure at all" is **not** the expected outcome — that reputation is the V2 filter burr / other grinders / alignment, per Q2.)

---

## Open Questions
- **How fine/fiddly is the light-roast choke margin on *this* unit, and what's its real RPM floor?** (Downgraded from the earlier "can it build pressure at all" framing — Q2 establishes the V3 Red Speed is espresso-capable; the incapability reports are V2-filter/other-grinder/alignment.) Practical, not existential: during Commission (0), verify alignment, season ~3 kg, and learn where espresso lands on the collar and how low you can push RPM before stall. Budget patience for a fine working point. A genuine *defect* (un-shimmable misalignment, persistent stall SSP doesn't cure) is the only return trigger, and the window covers it.
- **Does the Cast V3 reduce the DF64V low-RPM stall the way SSP MP reportedly does?** Unknown — MP has fewer cutting edges; Cast has more. Don't assume the mitigation transfers; test the practical RPM floor on your unit.
- **Exact seasoning distance for *this* set** — sources span 2–10 kg. Treat 3 kg as "don't trust settings before," ~5–10 kg as "fully stable." Season on stale beans.
- **Keep or delete the archived Sette knowledge files?** Recommend keep-archived (read-only) for provenance and for any future Sette user of the repo — but this is a user call at decompose.
- **Should the fresh grind map add both an RPM column and a Grinder column?** RPM yes (it's now a real variable); Grinder column only matters if the repo expects multiple concurrent grinders per user — for a single-grinder user it's redundant. Decide at decompose.
