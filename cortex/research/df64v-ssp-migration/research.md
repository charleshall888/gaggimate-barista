# Research: DF64V Gen 3 + SSP Cast Lab Sweet V3 Red Speed (espresso) migration

> Prior art: this builds on `cortex/research/burr-recommendation.md`, which recommended exactly this burr/grinder combo. The **burr/grinder *selection* is locked** (not re-litigating MP-vs-Cast or Gen-2-vs-Gen-3). That lock is on the *shopping decision* — it does NOT foreclose a **return** if the rig physically cannot build espresso pressure on light roasts (see the return-window gate, work-stream 0). This artifact answers "now that it's bought, how do we accommodate it — or bail if it can't perform" — workflow, profiles, grind map, knowledge files, and a multi-user-aware grinder layer.

**Clarify-phase decisions carried in:** (1) DF64V becomes the **sole** grinder — Sette retired; (2) archive the Sette grind map, start a fresh DF64V map; (3) profile strategy is **deferred to this research**; (4) NEW constraint — others may use this repo for their own setups, so the grinder layer should be **swappable**, not hardcoded.

---

## Research Questions

1. **What is the "DF64V Gen 3" really, and what specs matter for dialing?**
   → **"Gen 3" is a fuzzy retailer/marketing label, not a clean engineering generation.** The hardware is the current variable-speed **DF64V** (df64coffee.com titles it "Gen 3"; DF's own dfgrinders.com still calls the same unit "Gen 2"; the Turin page title says "Gen 3" while its URL slug says "gen-2"). No independent reviewer (Hoffmann, Hedrick, Tom's Grinder Lab, Coffee Chronicler) has reviewed a unit *explicitly badged "Gen 3"* — all substantive independent data is of "the DF64V." The marketed "Gen 3" deltas (single chute, magnetic detachable chute + anti-popcorn ring, metal "flickable" declumper flap, plasma/ion static generator, possibly stronger motor) are **marketing-sourced, not bench-confirmed**. **What actually matters for dialing:** RPM range **600–1800** (stroboscope-verified by Tom's Grinder Lab); takes standard **64mm flats** including SSP drop-in; **~0.1 g retention** with bellows. *(Confidence: HIGH that "Gen 3" is a soft label; HIGH on RPM/burr/retention.)*

2. **What is the SSP Cast Lab Sweet V3 Red Speed (espresso) burr, and how does it behave?**
   → **"V3" is a generation, "Red Speed" is a coating** — V3 ships in both Red Speed and Silver Knight. There is **no separate "espresso geometry" SKU**: V3 *is* the espresso-leaning re-cut of the filter-oriented V2 (fixed burr identical to V2; rotary burr re-cut with ~15% more cutting edges + increased fineness so it can reach espresso pressure). So "the espresso version" = **V3 + Red Speed coating** (Red Speed → more friction → more fines/body; Silver Knight → cleaner/lighter). Positioned as a **body↔clarity middle ground** (more body than SSP MP, less ultra-clarity than HU). Favors **light-to-medium roasts; avoid oily/dark.** **No quantitative particle-size data exists anywhere.** *(Confidence: HIGH on the V2/V3 mechanism and roast fit; the entire flavor/PSD picture rests on near-identical reshipped retailer copy.)*

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
- **⚠️ Espresso dial-in difficulty is the most-cited issue.** Multiple users (Zerno FB group, Home-Barista) report being **unable to grind fine enough to build full espresso pressure** on washed/light roasts even with V3 ("V3 only slightly better than V2"). **Espresso Outlet outright DISRECOMMENDS Cast Lab Sweet for espresso** ("difficult to dial in") — a strong credibility signal since it's against their own sales interest.
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
| **0. Return-window feasibility GATE** (in hand: confirm factory alignment; pull a light-roast test shot; confirm the rig can reach choke / 9-bar-capable resistance and the practical RPM floor on *your* unit). **Hard go/no-go before C and H.** | S (but blocking) | The gate may be partly unreadable pre-seasoning (a can't-choke read may mean *unseasoned*, not *incapable*) — run a quick ~0.5–1 kg seasoning burst on stale beans and retest, and probe with a *medium* roast (easier to choke) before judging light roasts. If still can't build pressure → **return the burr/grinder, do not proceed** | New grinder in hand |
| **A. New `DF64V.md` grinder reference** (stepless dialing, RPM floor, seasoning, workflow) | S | Spec drift if "Gen 3" features mis-stated → keep it operational (RPM/dialing/seasoning), not marketing-feature-led | None |
| **B. Grinder-agnostic grind notation guide** + adopt "chirp + N marks" | S | Notation must survive re-zero/burr swap; user must establish chirp first | A drafted |
| **C. Archive Sette artifacts** (`git mv` grind map → `grind-map-sette-270.archive.md` *inside the private data repo* to preserve rename history; `SETTE_270.md`/reference → archived, read-only). **First snapshot the shot telemetry** the archived map's `shot_id`s reference (export the `.json` sidecars to the private repo) — per the firmware-1.8.0 retention note, the device's free-space purge can delete those sidecars silently, so the markdown alone is NOT a complete audit trail. | S | "lose nothing" only holds *with* the telemetry snapshot; without it the archived rows become dead `shot_id` links | **Gate 0 passed**; fresh map exists (D); telemetry snapshotted |
| **D. Fresh DF64V grind map** (grinder-agnostic `Grind` column + add RPM column) | S | Empty until shots pulled; format must be multi-user-neutral | B (notation) |
| **E. De-Sette shared knowledge files** (EXTRACTION_SCIENCE, SPECIAL_CATEGORIES, BEAN_FRESHNESS, BREWING, PROFILE_LIBRARY refs) → grinder-relative language | M | Many small edits; must not lose the high-fines-vs-low-fines *teaching*, just re-key it | A (so they can cross-ref DF64V) |
| **F. Parameterize skills** (feedback/new-coffee/consult read Grinder from user-setup; fall back to relative-step advice) | M | Skills are behavioral contracts — needs lifecycle (skills are protected paths); must not break existing flows | A, B |
| **G. Update `user-setup.md`** Grinder field + RPM note | S | Private-repo data write — overwrites the only in-repo Sette record; **recovery is git history via the auto-commit policy** (so the prior `Baratza Sette 270` value stays retrievable). Commit before and after. | None |
| **H. Phased profile re-dial** (re-dial grind first; nudge pressure/bloom only when a shot is *diagnosed under-extracted* per Q4; re-author per-coffee profiles after seasoning). **Snapshot first:** copy each proven profile to a `*.sette.json` sibling (or git-tag) before re-authoring in place — the six 5★ configs must stay recoverable. **Obey "Repo first, device second":** write the repo JSON, *then* upload via MCP. | L (spread over ~2 wks seasoning) | The big unknown is gated upstream by **Gate 0**; seasoning drift; don't over-fit early shots; in-place re-author destroys the proven config unless snapshotted | **Gate 0 passed**; new grinder seasoned (≥~3 kg); proven profiles snapshotted |
| **I. Multi-user grinder layer** (template `knowledge/grinders/_TEMPLATE.md`; README/CLAUDE.md note) | S–M | Scope creep into a full plugin-ization; keep minimal — template + neutral fallbacks | E, F define what "agnostic" means |

**Two independent tracks — sequence them separately:**
- **Physical track (clock-driven):** Gate 0 → G → D → H. This is what you do with the grinder in hand under the return-window + seasoning clock. None of it needs `/cortex-core:lifecycle`.
- **Software/knowledge track (no external clock):** A, B, E, then F and the skills part of I. **Editing skills, hooks, and certain `bin/`/`cortex_command` paths requires `/cortex-core:lifecycle`** (protected paths) — F and parts of I must route through it; A/B/E are plain content edits.
- **Day-one caveat:** until F lands, `/feedback` still hardcodes Sette `9D` notation `[skills/feedback/SKILL.md:136]`. To record DF64V settings during the return-window/seasoning period *before* the lifecycle-gated F completes, log them manually in the fresh DF64V map (D) using "chirp + N marks" — do not block the physical track on the skills refactor.

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
`user-setup.md`'s Grinder field is the hub: the skills read it to decide which per-grinder reference (the **grinder reference** piece) to load and which fallback to use. The **dialing notation** is the shared language between the grinder reference, the fresh **grind history**, and the skills — change it in one place and all three stay consistent. The **shared extraction knowledge** depends on the grinder reference only for a cross-link; its job is to stop *naming* the Sette so it reads correctly for any user. The **profile strategy** sits downstream of everything physical: it cannot begin until **Gate 0 has passed** and the grinder is seasoned, and its outputs (re-dialed grind settings, possibly higher peak pressure) flow back into the fresh grind history and the per-coffee profile JSONs. The multi-user generalization runs as a **separable second track**: it shapes *how* the Sette-specific strings are removed (every one becomes either a per-grinder file or grinder-relative language), but it is sequenced after the personal migration works and can be deferred without blocking the user's own dial-in.

---

## Decision Records

**Fresh grind map over combined.** User-chosen and research-confirmed: Sette macro+micro codes (`13E`) have no defined relationship to a DF64V stepless mark, and SSP seasoning drift means even the DF64V's own early numbers are unstable. Mixing grammars in one table would mislead future lookups. The archived Sette map stays as a read-only record of what *tastes* worked (roast/process/ratio/temp/rating remain transferable signal even though grind doesn't).

**Phased profile strategy over up-front re-engineering.** Research is firm on change-one-variable-at-a-time and on keeping the gentle bloom-slide (it aligns with low-pressure-profiling philosophy and fruit-forward light naturals; constant 9 bar raises late-shot channeling). Re-engineering profiles *before* the burr is seasoned would tune against a moving target — seasoning drifts grind coarser over ~5–10 kg. So: re-dial grind first, treat 8–9 bar peak and shorter bloom as *experiments triggered by an under-extraction diagnosis* (Q4's operationalized trigger — sour/short-finish + fast-pull telemetry, NOT mere thinness), not defaults. (The grinder-archetype table anticipates flats handling ~9 bar — but Hoffmann's null result and Prima's "contested magnitude" mean we earn the pressure bump empirically, not on faith; the 8–9 figure is borrowed from the general pressure matrix, not from any Cast-V3-specific evidence.)

**Generalize the grinder layer — but treat it as a separable, optional second track.** The user explicitly raised multi-user reuse in clarify, so accommodating it is a *stated* goal, not speculative. But be honest about cost: the *personal* migration is fully satisfied by the S-effort trio A (DF64V doc) + D (fresh map) + G (user-setup) plus the physical track. The generalization — E (de-Sette five shared files), F (parameterize three skills, lifecycle-gated), I (template) — is **net-new M-effort work that exists only for the multi-user goal**, not "free on top of work we're doing anyway." It is genuinely valuable and worth doing, but it should be sequenced *after* the personal migration works and can be deferred or dropped without blocking the user's own dial-in. "Minimal" = A+D+G; E/F/I are the deliberate, optional expansion. Bounded below a full grinder-plugin system.

**Operate at ~1000–1200 RPM (working hypothesis, not a converged fact).** This rests on **one** load-bearing constraint — the DF64V low-RPM stall floor (~1000 practical, 1400 safe per MiiCoffee + Home-Barista), which is *manufacturer/forum-sourced, unit-variable, and reported for stock/MP burrs, NOT confirmed for the higher-fines Cast burr*. The two supporting notes are weaker than "independent corroboration": Coffee Chronicler's ~900 RPM clarity note actually points *below* the stall floor (it argues for going lower, if the motor allowed), and the prior burr-recommendation's "1100–1200" is this project's own sibling document, not a third independent source. So: start at ~1100–1200 as a stall-safe espresso default and **find your unit's actual floor empirically** (Gate 0 / OQ2). The "RPM as body-recovery lever" idea (low→clarity, high→body) is **vendor-framed and unproven** — the same body↔clarity axis Hoffmann's blind test nulled — so try it as an experiment, don't bank on it.

**Honest success bar (carried from prior art), with the binary-failure case made explicit.** This is a ceiling/clarity upgrade, not a fix — six 5★ Sette shots already exist. There are **two** downside scenarios, not one: (a) the *performance floor* — the rig works but only matches/slightly underperforms the Sette for the ~$684 spend; accept this before sinking ~2 weeks of re-dialing. (b) the *binary-failure floor* — the rig **cannot build espresso pressure on light roasts at all** (Espresso Outlet disrecommends Cast for espresso; users report can't-grind-fine-enough). Scenario (b) is not a point on the performance continuum; it is a **return trigger**, and Gate 0 exists to catch it inside the return window before any irreversible step.

---

## Open Questions
- **Can this rig build full espresso pressure on light-roast naturals at all?** The single most important unknown, and it is now wired as **work-stream 0 (the return-window go/no-go gate)** that blocks C and H — not a deferred afterthought. Multiple sources report DF64V + Cast burrs unable to grind fine enough for light/washed espresso, and Espresso Outlet disrecommends Cast for espresso. **Tension to manage:** the gate must be read *inside the return window*, but settings can't be fully trusted until ≥3 kg seasoned — so an early "can't choke" reading is ambiguous (unseasoned vs incapable). Mitigation (in Gate 0): run a quick ~0.5–1 kg seasoning burst on stale beans and probe with an easier-to-choke *medium* roast first; if it still cannot reach choke/9-bar-capable resistance, treat as incapable and **return** rather than hoping seasoning rescues it.
- **Does the Cast V3 reduce the DF64V low-RPM stall the way SSP MP reportedly does?** Unknown — MP has fewer cutting edges; Cast has more. Don't assume the mitigation transfers; test the practical RPM floor on your unit.
- **Exact seasoning distance for *this* set** — sources span 2–10 kg. Treat 3 kg as "don't trust settings before," ~5–10 kg as "fully stable." Season on stale beans.
- **Keep or delete the archived Sette knowledge files?** Recommend keep-archived (read-only) for provenance and for any future Sette user of the repo — but this is a user call at decompose.
- **Should the fresh grind map add both an RPM column and a Grinder column?** RPM yes (it's now a real variable); Grinder column only matters if the repo expects multiple concurrent grinders per user — for a single-grinder user it's redundant. Decide at decompose.
