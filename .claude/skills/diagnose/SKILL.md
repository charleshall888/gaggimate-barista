---
name: diagnose
description: >
  Diagnose espresso extraction issues by correlating machine telemetry with taste feedback.
  Use when user says: "/diagnose", "what went wrong", "analyze that shot", "why did it taste [sour/bitter/flat]",
  "my shots are inconsistent", or asks about pressure spikes, flow issues, or extraction problems.
  Fetches shot data via analyze_shot MCP tool, interprets patterns, and provides actionable recommendations.
---

<command-name>diagnose</command-name>

# Espresso Diagnostic Skill

You are diagnosing espresso extraction issues by correlating Gaggimate telemetry data with taste feedback.

## Diagnostic Workflow

Follow this sequence for every diagnosis:

### 1. GATHER Information

**Required inputs:**
- Shot ID (from `list_recent_shots` if not provided)
- Taste feedback: sour, bitter, flat, astringent, balanced, or specific descriptors
- Any visual observations (channeling, spurting, blonde early, etc.)

**Fetch telemetry:**
```
Use: analyze_shot(shot_id)
```

**Fetch shot notes if available:**
```
Use: manage_shot_notes(shot_id, action="get")
```

### 1b. IDENTIFY Shot Style

Before analyzing, identify the shot style so you compare against the right expectations. Use three tiers of detection (try in order, use first that succeeds):

**Tier 1 — Fetch profile definition (preferred):**

If `analyze_shot` returns a `profile_id`, fetch the full profile:
```
Use: manage_profile(action="get", profile_id=<profile_id>)
```

Classify by phase structure:
- Has a phase with pump off (`"target": "power"` and `"pressure": 0`) → **Bloom** (light roast bloom or natural process bloom)
- Flow-targeted extraction with flow >= 3.5 ml/s → **Turbo**
- Brew phase with pressure declining >= 4 bar over >= 15s → **Lever Decline**
- Extraction pressure <= 7 bar + high volumetric target (>= dose × 3.5) → **Allongé**
- Extraction pressure < 9 bar, no bloom, no decline → **Dark/Gentle**
- Default → **Classic 9-Bar**

**Tier 2 — Profile name keywords (fallback):**

If profile definition is unavailable, match `profile_name` from `analyze_shot`:
- Contains "turbo" → **Turbo**
- Contains "bloom", "natural bloom" → **Bloom**
- Contains "allongé", "allonge", "lungo" → **Allongé**
- Contains "lever", "decline" → **Lever Decline**
- Contains "gentle", "dark", "milk" → **Dark/Gentle**
- Otherwise → **Classic 9-Bar**

**Tier 3 — Telemetry fingerprint (last resort):**

If neither profile definition nor meaningful profile name is available, classify from the shot telemetry itself. See `references/TELEMETRY_PATTERNS.md` (Style Detection Fingerprints section) for the fingerprint table.

### 2. ANALYZE Telemetry

**Load style-specific expectations** from `knowledge/PRESSURE_GUIDE.md` (Pressure by Shot Style section) and `knowledge/PROFILE_LIBRARY.md` (Quick Reference table). Compare the shot's telemetry against those style-specific ranges — not generic 9-bar ranges.

**Universal thresholds** (style-independent):

| Metric | Normal | Anomaly |
|--------|--------|---------|
| Temperature variance | ±1°C from target | >2°C = equipment instability |
| Pressure spike above profile target | — | >1.5 bar above = too fine / channeling |

**Style-specific thresholds** — loaded from knowledge files per identified style:

| Metric | Source |
|--------|--------|
| Expected pressure range | `knowledge/PRESSURE_GUIDE.md` → Pressure by Shot Style |
| Expected time, ratio, flow | `knowledge/PROFILE_LIBRARY.md` → Quick Reference table |
| Anomaly interpretation | `references/TELEMETRY_PATTERNS.md` → Per-Style Diagnostic Notes |

Flag an anomaly only when a metric falls **outside the identified style's expected range**. For example, 6 bar and 17s is anomalous for Classic 9-Bar but perfectly normal for Turbo.

### 2b. COMPARE Intended vs Actual (when profile definition available)

If you fetched the profile definition in Step 1b (Tier 1), compare each phase's intended parameters against the actual telemetry:

| Comparison | Interpretation |
|------------|----------------|
| Pressure exceeded profile target by >1.5 bar | Grind too fine or dose too high |
| Pressure never reached target (>1.5 bar below) | Grind too coarse or channeling |
| Bloom phase showed significant flow (>1 ml/s) | Puck too permeable for bloom — grind finer |
| Volumetric target reached much earlier than phase duration | Grind too coarse (flow too fast) |
| Volumetric target not reached within phase duration | Grind too fine (flow too slow) |
| Decline phase dropped pressure faster than intended | Channel opened mid-shot |
| Flow during extraction well above/below profile's flow target | Grind mismatch for this style |

This phase-by-phase comparison is the most precise diagnostic — it shows exactly *where* in the shot things diverged from intent. Include the comparison in your diagnosis when available.

### 3. CORRELATE Taste with Telemetry

Cross-reference the user's taste feedback with telemetry patterns.

**See:** `references/TELEMETRY_PATTERNS.md` for detailed correlation matrix.

### 4. RECOMMEND Actions

Provide specific, prioritized recommendations:
1. **Primary adjustment** (most likely to fix the issue)
2. **Secondary adjustment** (if primary doesn't work)
3. **Profile consideration** (if extraction mechanics need changing)

Always explain WHY each recommendation addresses the diagnosed issue.

---

## Decision Trees

### SOUR Shot Diagnosis

```
SOUR (under-extracted)
├── Time to first drip below style's expected minimum?
│   ├── YES → Channeling or too coarse
│   │   ├── Pressure spike >1.5 bar above style target? → Channeling (fines migration)
│   │   │   └── FIX: Improve puck prep (WDT), check distribution
│   │   └── Pressure below style's expected range? → Too coarse
│   │       └── FIX: Grind 1-2 steps finer
│   └── NO → Continue...
├── Flow rate above style's expected range?
│   └── YES → Resistance too low for this style
│       └── FIX: Grind finer, check dose (may need +0.5g)
├── Temperature < target by >2°C?
│   └── YES → Equipment issue (not fully heated)
│       └── FIX: Longer warm-up, flush before shot
├── Preinfusion shorter than profile specifies?
│   └── YES → Insufficient saturation
│       └── FIX: Extend preinfusion phase in profile
└── None of above?
    └── Extraction time within style range but sour?
        └── FIX: Increase temperature +1-2°C, or grind finer
```

### BITTER Shot Diagnosis

```
BITTER (over-extracted)
├── Total time well above style's expected range?
│   └── YES → Over-extracted (too much contact time)
│       └── FIX: Grind coarser, or reduce ratio
├── Temperature > target by >2°C?
│   └── YES → Running hot
│       └── FIX: Reduce brew temp -2°C, check PID calibration
├── Pressure sustained above style's target through extraction?
│   └── YES → Aggressive extraction
│       └── FIX: Use declining pressure profile, or lower target pressure
├── Flow rate well below style's expected range for extended period?
│   └── YES → Choked flow, prolonged contact
│       └── FIX: Grind coarser, reduce dose -0.5g
└── None of above?
    └── May be bean-related (dark roast, over-roasted)
        └── FIX: Lower temp, shorter ratio, declining pressure
```

### FLAT/MUTED Shot Diagnosis

```
FLAT (lacks vibrancy, dull)
├── Temperature drifting >2°C during shot?
│   └── YES → Thermal instability
│       └── FIX: Better pre-heating, temperature surfing
├── Preinfusion shorter than profile specifies or skipped?
│   └── YES → Poor saturation, uneven extraction
│       └── FIX: Add proper preinfusion phase, or extend existing one
├── Beans > 4 weeks from roast?
│   └── YES → Stale, CO2 depleted
│       └── FIX: Fresh beans; compensate with higher temp, finer grind
├── Extraction time well below style's expected range?
│   └── YES → Under-developed, too fast
│       └── FIX: Grind finer, extend extraction
└── None of above?
    └── May need more extraction
        └── FIX: Higher temp +1-2°C, longer ratio, consider bloom phase
```

### INCONSISTENT Shots Diagnosis

When user reports shot-to-shot variance:

```
INCONSISTENT (variable results)
├── Compare multiple shots via list_recent_shots
├── Check for patterns:
│   ├── Time to first drip varies >3s between shots?
│   │   └── YES → Puck prep inconsistency
│   │       └── FIX: Standardize WDT, distribution, tamping
│   ├── Pressure curves differ significantly?
│   │   └── YES → Grind retention or distribution issues
│   │       └── FIX: Purge grinder, single-dose, better WDT
│   ├── Temperature varies >1.5°C between shots?
│   │   └── YES → Machine thermal management
│   │       └── FIX: Consistent wait time between shots, flush routine
│   └── Flow patterns different?
│       └── YES → Channeling (random), check basket prep
└── Document which variables are changing for pattern recognition
```

---

## Quick Reference: Telemetry → Taste Correlation

All thresholds below are relative to the identified shot style's expected ranges. See Step 1b for style identification and `knowledge/PRESSURE_GUIDE.md` + `knowledge/PROFILE_LIBRARY.md` for expected ranges.

| Telemetry Pattern | Likely Taste | Root Cause |
|-------------------|--------------|------------|
| Pressure spike >1.5 bar above style target | Sour, astringent | Fines migration, channeling |
| Pressure well below style's expected range | Watery, sour | Too coarse, channeling |
| Flow well above style's expected range | Thin, sour | Coarse grind, poor puck integrity |
| Flow well below style's expected range, sustained | Bitter, harsh | Too fine, choked |
| Time to drip well above style's expected range | Bitter if long shot | Very fine grind |
| Time to drip well below style's expected range | Sour, watery | Very coarse, channeling |
| Temp drop > 3°C | Sour, muted | Pre-heat issue, high thermal mass |
| Temp overshoot > 2°C | Bitter notes | PID tuning, flush needed |

---

## Differentiate: Extraction vs Equipment Issues

**Extraction issues** (user can fix):
- Grind size (too fine/coarse)
- Dose (too high/low)
- Distribution (channeling)
- Ratio (too short/long)
- Profile choice (wrong for bean)

**Equipment issues** (machine-related):
- Temperature instability (>2°C variance)
- Pressure not reaching target (pump/OPV)
- Inconsistent flow sensor readings
- Pre-heat insufficient

**When equipment suspected:**
- Recommend `diagnose_connection` tool for connectivity
- Suggest checking OPV setting if pressure consistently high/low
- Recommend cleaning if pressure/flow degrading over time

---

## Multi-Shot Comparison

When diagnosing inconsistency or trends:

1. Fetch last 5-10 shots: `list_recent_shots(limit=10)`
2. Compare key metrics across shots:
   - Peak pressure variance
   - Time to first drip variance
   - Total extraction time variance
   - Flow rate patterns
3. Identify the variable with highest variance → that's the root cause
4. Check if user made changes (grind, dose) between shots

---

## Integration with Other Knowledge

**For style-specific expected parameters (pressure, time, ratio, flow):**
→ Reference `knowledge/PRESSURE_GUIDE.md` (Pressure by Shot Style section)
→ Reference `knowledge/PROFILE_LIBRARY.md` (Quick Reference table)

**For adjustment strategies and diagnostics:**
→ Reference `knowledge/ESPRESSO_BREWING_BASICS.md`

**For deeper extraction theory (shot styles, salami shot, dialing methodology):**
→ Reference `knowledge/reference/ESPRESSO_BREWING_REFERENCE.md`

**For shot evaluation and feedback:**
→ Reference `knowledge/ESPRESSO_TASTING_GUIDE.md`

**For deeper tasting guidance (flavor wheel, palate exercises, off-flavors):**
→ Reference `knowledge/reference/ESPRESSO_TASTING_REFERENCE.md`

**For profile modifications:**
→ Reference `knowledge/GAGGIMATE_PROFILE_CREATION_GUIDE.md`

---

## Response Format

Structure your diagnostic response as:

```
## Shot Analysis: [Shot ID]

### Identified Style: [Style Name]
(detected via [Tier 1: profile definition / Tier 2: profile name / Tier 3: telemetry fingerprint])

### Telemetry Summary
- **Pressure:** [peak] bar (style expects: X-Y bar)
- **Flow:** [avg] ml/s, first drip at [X]s (style expects: A-B ml/s)
- **Temperature:** [avg]°C (target: X°C, variance: ±X°C)
- **Timing:** [total]s total (style expects: E-Fs)

### Phase Comparison (if profile definition available)
[Intended vs actual for each phase — pressure, flow, timing]

### Diagnosis
[Correlation between telemetry and reported taste, interpreted through style-specific expectations]

### Recommendations
1. **[Primary fix]** — [specific action with reasoning]
2. **[Secondary fix]** — [backup if primary doesn't work]
3. **[Profile consideration]** — [if applicable]

### What to Watch For
[What user should observe on next shot to confirm diagnosis]
```

---

## Example Diagnoses

### Example 1: Classic 9-Bar — Sour and Watery

**User says:** "That shot was really sour and watery."

**Style identified:** Classic 9-Bar (expects 8-10 bar, 25-32s, 1.5-2.5 ml/s)

**Telemetry:** Pressure 7.2 bar, first drip 2.8s, flow 3.4 ml/s avg, 22s total

**Diagnosis:**
> Your pressure never reached the Classic 9-Bar range (7.2 bar vs 8-10 bar expected) and the first drip came extremely fast (2.8s). Combined with high flow rate (3.4 ml/s vs 1.5-2.5 expected), the puck offered very little resistance. Classic under-extraction.
>
> **Primary fix:** Grind 2-3 steps finer. We need to build more resistance.
>
> **Watch for:** Time to first drip should increase to 5-7 seconds, and pressure should reach 8-9 bar.

### Example 2: Bloom Profile — NOT a Problem

**User says:** "Shot took 38 seconds and pressure was only 7.5 bar — is that okay?"

**Style identified:** Natural Process Bloom (expects 7-9 bar, 30-38s, bloom pause is normal)

**Diagnosis:**
> For a bloom profile, 38s total and 7.5 bar extraction pressure are right in the expected range. The bloom pause adds 10-15 seconds that a classic shot wouldn't have, and 7.5 bar is intentional for this natural-process coffee. These are features, not bugs. How did it taste?
