---
name: consult
description: >
  Answer espresso knowledge questions from authoritative knowledge files.
  Use when the user asks about: temperature, pressure, ratios, grind settings, freshness,
  extraction theory, puck prep, channeling, baskets, decaf, blends, milk steaming, drink specs,
  profiles, shot styles, or any espresso concept. Routes to the correct file and answers
  from its content rather than from memory or training data.
---

<command-name>consult</command-name>

# Espresso Knowledge Consult Skill

You are answering an espresso knowledge question by loading and citing the authoritative knowledge file. Do NOT answer from memory or training data — load the file first, then answer from its content.

## Workflow

### 1. CLASSIFY — Map Question to File

Use the routing table below to identify which file(s) to load. Match on keywords in the user's question.

| Keywords | Primary File | Secondary File |
|----------|-------------|----------------|
| temperature, temp, roast level, how hot | `knowledge/ESPRESSO_BREWING_BASICS.md` | — |
| pressure, bar, processing method | `knowledge/PRESSURE_GUIDE.md` | — |
| ratio, yield, dose, output, how much | `knowledge/ESPRESSO_BREWING_BASICS.md` | — |
| grind, grinder, finer, coarser, grind setting | Active grinder reference resolved per the Active Grinder field parsing contract → `knowledge/grinders/` | `knowledge/ESPRESSO_BREWING_BASICS.md` |
| sour, bitter, taste, flavor, tasting | `knowledge/ESPRESSO_TASTING_GUIDE.md` | `knowledge/ESPRESSO_BREWING_BASICS.md` |
| channeling, puck prep, WDT, distribution | `knowledge/EXTRACTION_SCIENCE.md` | — |
| freshness, rest, degas, storage, freeze | `knowledge/BEAN_FRESHNESS_AND_STORAGE.md` | — |
| profile, bloom, turbo, lever, allonge | `knowledge/PROFILE_LIBRARY.md` | `knowledge/PRESSURE_GUIDE.md` |
| decaf, blend, decaffeinated | `knowledge/SPECIAL_CATEGORIES.md` | — |
| milk, steam, drink, cortado, cappuccino, latte, flat white | `knowledge/MILK_AND_DRINKS.md` | — |
| basket, dose rule, headroom, puck depth | `knowledge/BASKETS.md` | — |
| puck screen, normcore, screen imprint, screen orientation | `knowledge/PUCK_SCREENS.md` | `knowledge/reference/PUCK_SCREENS_REFERENCE.md` |
| automatic pro, firmware, built-in profile | `knowledge/automatic-pro/AUTOMATIC_PRO_GUIDE.md` | — |
| adjust, dial in, what to change, improvement | `knowledge/ESPRESSO_BREWING_BASICS.md` | — |

If the question spans two topics (e.g., "what pressure for a natural at light roast?"), load both the primary and secondary files.

If no keywords match, default to `knowledge/ESPRESSO_BREWING_BASICS.md` — it covers the broadest range of topics.

### 1b. RESOLVE Active Grinder Reference (for grind/grinder questions)

When the question matches the grind/grinder routing row, resolve the active grinder reference before loading:

Per the CLAUDE.md Active Grinder field parsing contract, read the `user-setup.md` Grinder field, resolve the active grinder reference by case-insensitive substring against the contract's map (first match wins), attempt to load that `knowledge/grinders/` file, and on any miss or unreadable `user-setup.md` degrade to grinder-relative step advice plus the unconfigured nudge — never error.

This Grinder-field read is a config read that lies outside the cascade cap (the cap covers only knowledge/reference loads — see §5 below).

### 2. LOAD Primary File

Read the identified primary knowledge file.

### 3. LOAD Secondary File (if needed)

If the question spans two topics, read the secondary file too.

**Stop rule:** Do not load more than 2 quick-reference files per question.

### 4. ANSWER from File Content

Answer the user's question using the content you just loaded. Cite specific tables, thresholds, or sections from the file. Do not paraphrase from memory — use the actual data.

**Good:** "The pressure matrix in PRESSURE_GUIDE.md recommends 7-8 bar for light roast naturals."
**Bad:** "Light roast naturals generally do well at lower pressure." (no file reference, no specific value)

### 5. DEEP REFERENCE (only if needed)

Only load a deep reference file if the user asks "why?", wants theory, or the quick-reference file explicitly doesn't cover their question.

**Cascade prevention rule:** Load at most **ONE** quick-reference file and **ONE** deep reference file per question. If the quick-reference answers it, stop there. Never chain quick->deep->second-quick->second-deep. (Reading the `user-setup.md` Grinder field to select the active grinder reference is a config read outside the cap — it does not count against the one-quick + one-deep limit.)

| Deep Reference | Load ONLY when user asks about... |
|---------------|----------------------------------|
| `knowledge/reference/ESPRESSO_BREWING_REFERENCE.md` (229) | Shot style theory, salami shots, dialing methodology deep-dive |
| `knowledge/reference/ESPRESSO_TASTING_REFERENCE.md` (191) | Flavor wheel, palate development exercises, off-flavor identification |
| `knowledge/reference/BEAN_FRESHNESS_REFERENCE.md` (197) | Degassing science, freezing protocols, staleness chemistry |
| `knowledge/reference/BASKETS_REFERENCE.md` (124) | IMS/VST basket specs, ridged vs ridgeless comparison, wall geometry |
| `knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md` (255) | TDS/EY theory, particle distribution, channeling physics |
| `knowledge/reference/PRESSURE_REFERENCE.md` (95) | Pressure-compound interactions, pressure misconceptions deep-dive |
| `knowledge/reference/MILK_AND_DRINKS_REFERENCE.md` (118) | Milk chemistry, foam science, latte art technique |
| `knowledge/reference/SPECIAL_CATEGORIES_REFERENCE.md` (85) | Decaffeination chemistry, blend philosophy analysis |
| Active grinder's deep reference, resolved per the contract's explicit deep-tier map under `knowledge/reference/` | Grinder calibration, burr wear, maintenance deep-dive — `consult` proceeds without a deep reference when the active grinder has no deep-map row |

**Gated to other skills only (never load from /consult):**
- `knowledge/reference/PROFILE_CREATION_REFERENCE.md` — only via `/gaggimate-profiles`
- `knowledge/reference/PROFILE_LIBRARY_REFERENCE.md` — only via `/gaggimate-profiles`

---

## Quick Reference

**User asks:** "What temperature for a light roast?"
**Action:** Load ESPRESSO_BREWING_BASICS.md → cite Temperature Guidelines table → answer "94-96°C"

**User asks:** "What pressure for an anaerobic natural?"
**Action:** Load PRESSURE_GUIDE.md → cite Comprehensive Pressure Matrix → answer "6-8 bar for light, 7-8 bar for medium"

**User asks:** "Why does pressure affect body?"
**Action:** Already loaded PRESSURE_GUIDE.md → check if it answers → if not, load PRESSURE_REFERENCE.md for deep theory

**User asks:** "How do I store beans long-term?"
**Action:** Load BEAN_FRESHNESS_AND_STORAGE.md → answer from storage section → if user asks "why does freezing work?", load BEAN_FRESHNESS_REFERENCE.md
