---
name: new-coffee
description: >
  Research a new coffee bean and propose starting extraction parameters.
  Use when: (1) user shares a new bag of coffee (photo, name, or description),
  (2) user says "/new-coffee", "new beans", "dialing in a new coffee",
  (3) user asks "where should I start with this coffee".
  Accepts bag photos (extracts info via vision) or text descriptions.
  Researches origin, process, roast level via web search, checks grind-map.md
  for similar coffees, then recommends temperature, grind, ratio, and profile.
---

<command-name>new-coffee</command-name>

# New Coffee Research Skill

Systematically research a coffee and propose starting extraction parameters.

## Workflow

### 1. GATHER Coffee Info

**If photo provided:**
- Extract from label: roaster, coffee name, origin, roast date, tasting notes
- Note any visible processing info (washed, natural, etc.)

**If text provided:**
- Parse roaster and coffee name
- Ask for roast date if not mentioned

### 2. RESEARCH via Web Search

Search for the specific coffee to find:
- Processing method (washed, natural, honey, anaerobic)
- Origin details (country, region, altitude if available)
- Variety (Bourbon, Gesha, Caturra, etc.)
- Roast level (light, medium, dark) — infer from tasting notes if not stated
- Roaster's tasting notes

**See:** `references/RESEARCH_CHECKLIST.md` for detailed research patterns.

### 3. CONSULT Grind Map

Read `grind-map.md` and find similar coffees:
- Match by: roast level > processing method > origin
- If match found: use as starting point, adjust for freshness
- If no match: use defaults from `knowledge/grinders/SETTE_270.md`

**Freshness adjustment:** Fresher beans (fewer days off roast) need finer grind due to CO2. If historical match was at 14 days and new bag is 7 days, suggest 1-2 micro steps finer.

### 4. SYNTHESIZE Recommendations

Build recommendations using:
- **Temperature:** From `knowledge/ESPRESSO_BREWING_BASICS.md` roast guidelines
- **Grind:** From grind-map match or SETTE_270.md defaults
- **Ratio:** From processing method patterns (see below)
- **Pressure:** From `knowledge/PRESSURE_GUIDE.md` roast × processing matrix (see below)
- **Profile:** From `knowledge/PROFILE_LIBRARY.md` by roast/process, adjusted for correct pressure
- **Dose:** From `user-setup.md` basket size. **Dose = basket size** (e.g., 22g basket → 22g dose). Don't underdose.

**Processing → Ratio patterns:**
| Process | Suggested Ratio | Notes |
|---------|-----------------|-------|
| Washed | 1:2 | Clean, classic starting point |
| Natural | 1:2 to 1:2.5 | Longer to develop fruit sweetness |
| Honey | 1:2 | Between washed and natural |
| Anaerobic | 1:2 to 1:2.5 | Often intense, longer ratio tames it |

**Roast → Temperature:**
| Roast | Temperature |
|-------|-------------|
| Light | 94-96°C |
| Medium | 92-94°C |
| Dark | 88-90°C |

**Processing → Extraction Pressure:**
| Process | Pressure | Notes |
|---------|----------|-------|
| Washed | 9 bar | Clean, handles full pressure well |
| Natural | 7-9 bar | Lower pressure tames fruit intensity; 9 bar OK with bloom |
| Honey | 8-9 bar | Moderate intensity, usually fine at 9 bar |
| Anaerobic / Experimental | 6-8 bar | Lower pressure avoids amplifying ferment funk |

**Key principle:** Intensely processed coffees (anaerobic, carbonic maceration, extended fermentation) benefit from lower extraction pressure to control the intensity of fermentation flavors. 9 bar is not a universal default. See `knowledge/PRESSURE_GUIDE.md` for the full roast × processing matrix, shot style adjustments, and the science behind each recommendation.

### 5. CONFIRM with User

Before finalizing, ask:
> "This [process] [origin] typically shines with [approach]. Would you like to start there, or prefer a more conservative/adventurous approach?"

Options to offer:
- **Conservative:** Classic profile, standard ratio (pressure matched to processing method — not always 9 bar)
- **Recommended:** Profile matched to bean characteristics (roast, process, intensity)
- **Adventurous:** Bloom profile or turbo shot if appropriate

### 6. UPLOAD Profile (if requested)

Use MCP tool to upload:
```
manage_profile(action="create", profile_name="[Coffee Name] [AI]", temperature=X, phases=[...])
```

Always add `[AI]` suffix to profile names.

---

## Output Format

```
## Coffee Research: [Name]

### Bean Profile
- **Roaster:** [roaster]
- **Origin:** [country, region]
- **Process:** [washed/natural/honey/anaerobic]
- **Roast Level:** [light/medium/dark]
- **Variety:** [if known]
- **Tasting Notes:** [from roaster]
- **Days Off Roast:** [X days, or "unknown"]

### Similar Coffees in Your History
[Table from grind-map.md matches, or "No similar coffees yet"]

### Recommended Starting Parameters
| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| Temperature | X°C | [roast level rationale] |
| Grind | XY | [from history or default, freshness adjusted] |
| Ratio | 1:X | [process rationale] |
| Profile | [name] | [why this profile] |
| Dose | Xg in → Xg out | [basket size rationale] |

### Profile
[Link to PROFILE_LIBRARY.md profile, or custom JSON if creating new]

### What to Watch For
- [Specific guidance for first shot based on bean characteristics]
- [What taste outcomes to expect]
- [When to adjust and in which direction]
```

---

## Quick Reference

**User says:** "I got a new bag of [coffee]"
**Action:** Extract info → research → consult grind map → recommend → confirm

**User shares photo:**
**Action:** Vision extract → research → consult grind map → recommend → confirm

**User says:** "/new-coffee"
**Action:** Ask what coffee they have, then proceed with workflow
