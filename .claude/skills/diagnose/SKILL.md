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

### 2. ANALYZE Telemetry

Examine the shot data against these thresholds:

| Metric | Normal Range | Anomaly Indicator |
|--------|--------------|-------------------|
| Pressure peak | 8-10 bar | >10.5 bar = spike (too fine/channeling) |
| Pressure peak | 8-10 bar | <7 bar = too coarse |
| Time to first drip | 4-8 seconds | <3s = too coarse / channeling |
| Time to first drip | 4-8 seconds | >10s = too fine |
| Average flow | 1.5-2.5 ml/s | >3 ml/s = channeling or coarse |
| Average flow | 1.5-2.5 ml/s | <1 ml/s = choked / too fine |
| Temperature variance | ±1°C from target | >2°C = equipment instability |
| Preinfusion time | 3-8 seconds | Profile-dependent |
| Total extraction | 25-35 seconds | Target varies by style |

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
├── Time to first drip < 4s?
│   ├── YES → Channeling or too coarse
│   │   ├── Pressure spike >10 bar? → Channeling (fines migration)
│   │   │   └── FIX: Improve puck prep (WDT), check distribution
│   │   └── Pressure low (<8 bar)? → Too coarse
│   │       └── FIX: Grind 1-2 steps finer
│   └── NO → Continue...
├── Flow rate > 2.5 ml/s?
│   └── YES → Resistance too low
│       └── FIX: Grind finer, check dose (may need +0.5g)
├── Temperature < target by >2°C?
│   └── YES → Equipment issue (not fully heated)
│       └── FIX: Longer warm-up, flush before shot
├── Preinfusion < 3s?
│   └── YES → Insufficient saturation
│       └── FIX: Extend preinfusion phase in profile
└── None of above?
    └── Extraction time reasonable but sour?
        └── FIX: Increase temperature +1-2°C, or grind finer
```

### BITTER Shot Diagnosis

```
BITTER (over-extracted)
├── Total time > 40s?
│   └── YES → Over-extracted (too much contact time)
│       └── FIX: Grind coarser, or reduce ratio
├── Temperature > target by >2°C?
│   └── YES → Running hot
│       └── FIX: Reduce brew temp -2°C, check PID calibration
├── Pressure sustained at >9 bar through extraction?
│   └── YES → Aggressive extraction
│       └── FIX: Use declining pressure profile (9→6 bar)
├── Flow rate < 1.5 ml/s for extended period?
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
├── Preinfusion very short (<2s) or skipped?
│   └── YES → Poor saturation, uneven extraction
│       └── FIX: Add proper preinfusion phase (4-6s, 2-3 bar)
├── Beans > 4 weeks from roast?
│   └── YES → Stale, CO2 depleted
│       └── FIX: Fresh beans; compensate with higher temp, finer grind
├── Extraction time < 20s?
│   └── YES → Under-developed, too fast
│       └── FIX: Grind finer, extend extraction
└── None of above?
    └── May need more extraction
        └── FIX: Higher temp +1-2°C, longer ratio (1:2.5), bloom phase
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

| Telemetry Pattern | Likely Taste | Root Cause |
|-------------------|--------------|------------|
| Pressure spike >10 bar early | Sour, astringent | Fines migration, channeling |
| Pressure never reaches 8 bar | Watery, sour | Too coarse, channeling |
| Flow > 3 ml/s | Thin, sour | Coarse grind, poor puck integrity |
| Flow < 1 ml/s sustained | Bitter, harsh | Too fine, choked |
| Time to drip > 10s | Bitter if long shot | Very fine grind |
| Time to drip < 3s | Sour, watery | Very coarse, channeling |
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

### Telemetry Summary
- **Pressure:** [peak] bar (target: X bar)
- **Flow:** [avg] ml/s, first drip at [X]s
- **Temperature:** [avg]°C (target: X°C, variance: ±X°C)
- **Timing:** [preinfusion]s pre-infusion, [total]s total

### Diagnosis
[Correlation between telemetry and reported taste]

### Recommendations
1. **[Primary fix]** — [specific action with reasoning]
2. **[Secondary fix]** — [backup if primary doesn't work]
3. **[Profile consideration]** — [if applicable]

### What to Watch For
[What user should observe on next shot to confirm diagnosis]
```

---

## Example Diagnosis

**User says:** "That shot was really sour and watery."

**After fetching telemetry showing:**
- Pressure peaked at 7.2 bar
- Time to first drip: 2.8s
- Flow rate: 3.4 ml/s avg
- Extraction time: 22s

**Diagnosis:**
> Your pressure never reached target (7.2 bar vs 9 bar expected) and the first drip came extremely fast (2.8s). Combined with high flow rate (3.4 ml/s), this tells me the puck offered very little resistance. The sourness you're tasting is classic under-extraction from water passing through too quickly.
>
> **Primary fix:** Grind 2-3 steps finer. We need to build more resistance.
>
> **Watch for:** Time to first drip should increase to 5-7 seconds, and pressure should reach 8-9 bar. The shot should feel more viscous.
