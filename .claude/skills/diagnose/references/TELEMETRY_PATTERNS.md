# Telemetry Pattern Interpretation Guide

Detailed reference for interpreting Gaggimate shot telemetry and correlating with taste outcomes.

---

## Pressure Patterns

### Normal Pressure Curve
- **Pre-infusion:** 2-4 bar for 3-8 seconds
- **Ramp:** Rises to target over 2-5 seconds
- **Extraction:** Holds at 8-10 bar (or follows profile)
- **Decline (if profiled):** Gradual drop to 6-7 bar

### Pressure Anomalies

| Pattern | Telemetry Signature | Likely Cause | Taste Impact | Fix |
|---------|---------------------|--------------|--------------|-----|
| **Early spike** | >10.5 bar in first 5s, then drops | Fines migration blocking flow, then channeling breaks through | Sour start, bitter finish, astringent | Better distribution (WDT), coarser fines |
| **Sustained spike** | >10 bar throughout extraction | Grind too fine, dose too high | Bitter, harsh, over-extracted | Grind coarser, reduce dose |
| **Never reaches target** | Peak < 8 bar | Grind too coarse, channeling, low dose | Thin, watery, sour | Grind finer, check puck prep |
| **Oscillating** | 7-10 bar fluctuation | Pump issue, pressure profiling instability | Uneven extraction | Check pump, PID settings |
| **Rapid decay** | Drops from 9 to 5 bar mid-shot | Channel opened, puck fractured | Starts balanced, ends sour | Better puck prep, consider paper filter |
| **Slow build** | Takes >8s to reach target | Very fine grind, high dose | May over-extract if not managed | Reduce dose, slightly coarser |

### Pressure Profile Considerations

**Classic 9-bar:** Flat pressure throughout
- Best for: Medium roasts, most coffees
- Watch for: Sustained high pressure indicates over-resistance

**Declining pressure (9→6 bar):** Ramps down through extraction
- Best for: Dark roasts, avoiding bitterness
- Watch for: If pressure drops too fast, channeling suspected

**Blooming profile:** Low pressure (2-3 bar) for 10-20s, then ramp
- Best for: Light roasts, natural process
- Watch for: If bloom doesn't saturate evenly, time to first drip still fast

---

## Flow Patterns

### Normal Flow Curve
- **Pre-infusion:** 0-1 ml/s (saturation phase)
- **First drip:** Appears 4-8 seconds into shot
- **Extraction:** 1.5-2.5 ml/s steady state
- **Peak flow:** Typically at end as puck erodes

### Flow Anomalies

| Pattern | Telemetry Signature | Likely Cause | Taste Impact | Fix |
|---------|---------------------|--------------|--------------|-----|
| **Instant flow** | First drip < 3s | Coarse grind, channeling, low dose | Thin, sour, under-extracted | Grind finer, increase dose |
| **Delayed drip** | First drip > 10s | Very fine grind, high dose | Risk of choking, bitter | Grind coarser, reduce dose |
| **High flow rate** | Avg > 3 ml/s | Low resistance, channeling | Watery, sour | Grind finer, better puck prep |
| **Choked flow** | Avg < 1 ml/s or stalls | Too fine, too high dose | Bitter, astringent, over-extracted | Grind coarser, reduce dose |
| **Flow acceleration** | Starts 1.5 ml/s, ends 4+ ml/s | Channel opening, puck erosion | Balanced start, sour finish | Better puck prep, paper filter |
| **Erratic flow** | Jumps between 1-4 ml/s | Multiple channels, uneven extraction | Inconsistent, muddled | WDT, distribution tool, paper filter |

### Flow-Based Diagnostics

**Time to first drip** is one of the most diagnostic metrics:

| First Drip Time | Interpretation | Action |
|-----------------|----------------|--------|
| < 2 seconds | Severe channeling or very coarse | Major grind adjustment needed |
| 2-4 seconds | Too fast, likely coarse or channel | Grind 1-2 steps finer |
| 4-8 seconds | Optimal range | Monitor taste, fine-tune |
| 8-12 seconds | Slow but acceptable for some profiles | May need slight coarsening |
| > 12 seconds | Risk of choking | Grind coarser, reduce dose |

---

## Temperature Patterns

### Normal Temperature Behavior
- **Target:** Set in profile (typically 92-94°C)
- **Variance:** ±1°C is normal during extraction
- **Between phases:** May vary by design (turbo shots run cooler)

### Temperature Anomalies

| Pattern | Telemetry Signature | Likely Cause | Taste Impact | Fix |
|---------|---------------------|--------------|--------------|-----|
| **Cold start** | Begins >3°C below target | Insufficient pre-heat | Sour, under-extracted | Longer warm-up, flush before shot |
| **Temperature drop** | Falls >2°C during extraction | High thermal mass (cold portafilter, cups) | Progressive sourness | Pre-heat everything, temperature surfing |
| **Overshoot** | >2°C above target early | PID overshoot, just flushed | Bitter notes early | Wait after flush, check PID tuning |
| **Drift up** | Rises through extraction | Heat transfer from group | Bitter finish | Normal on some machines, profile accordingly |
| **Oscillation** | Swings ±3°C | PID instability | Inconsistent extraction | Service machine, check PID settings |

### Temperature by Roast Level

| Roast | Suggested Temp | Signs of Wrong Temp |
|-------|----------------|---------------------|
| Light (Nordic) | 94-96°C | Sour if too low, grassy if way too high |
| Medium | 92-94°C | Balanced baseline |
| Medium-dark | 90-92°C | Bitter if too high |
| Dark | 88-90°C | Harsh/burnt if too high, flat if too low |

---

## Taste-to-Telemetry Correlation Matrix

Use this matrix to work backwards from taste to likely telemetry cause:

| Taste Descriptor | Primary Telemetry Suspect | Secondary Suspect | Tertiary Suspect |
|------------------|---------------------------|-------------------|------------------|
| **Sour** | Flow too fast (>3 ml/s) | Time to drip too short (<4s) | Temperature too low |
| **Bitter** | Extraction too long (>35s) | Temperature too high | Pressure sustained high |
| **Astringent** | Pressure spike + drop | Channeling (erratic flow) | Over-extracted fines |
| **Watery** | Low pressure (<7 bar) | High flow (>3 ml/s) | Short extraction |
| **Harsh** | Choked flow (<1 ml/s) | Very long extraction (>45s) | High temperature |
| **Flat/Muted** | Temperature drift | Short preinfusion | Stale beans (not telemetry) |
| **Unbalanced** | Erratic flow/pressure | Channeling evidence | Multiple extraction zones |
| **Thin body** | Fast flow | Short time | Low pressure |
| **Heavy/Syrupy** | Slow flow | Long time | Fine grind (not anomalous) |

---

## Phase-by-Phase Analysis

### Pre-infusion Phase

**Purpose:** Saturate the puck evenly before full pressure

| Metric | Optimal | Problem Indicator |
|--------|---------|-------------------|
| Duration | 4-8 seconds | <3s = insufficient, >12s = very fine |
| Pressure | 2-4 bar | >5 bar defeats purpose |
| Flow | 0.5-1.5 ml/s | >2 ml/s = coarse, channeling |

**Problems in pre-infusion:**
- Too short → Uneven saturation → Channeling later
- Too long → Over-extraction risk if grind is fine
- Pressure too high → Acts like extraction, not pre-infusion

### Bloom Phase (if used)

**Purpose:** Degas fresh coffee, improve saturation for light roasts

| Metric | Optimal | Problem Indicator |
|--------|---------|-------------------|
| Duration | 10-30 seconds | Depends on freshness |
| Pressure | 2-3 bar (or flow-limited) | Higher defeats purpose |
| Observation | Should see even drip | Fast drip = channeling |

### Extraction Phase

**Purpose:** Main extraction at target pressure/flow

| Metric | Optimal | Problem Indicator |
|--------|---------|-------------------|
| Pressure | 8-9 bar (profile dependent) | See pressure anomalies above |
| Flow | 1.5-2.5 ml/s | See flow anomalies above |
| Duration | 20-30 seconds | <15s = fast, >40s = long |

### Decline Phase (if used)

**Purpose:** Reduce extraction intensity, avoid bitterness

| Metric | Optimal | Problem Indicator |
|--------|---------|-------------------|
| Pressure drop | 9→6-7 bar over 10-15s | Too fast = shock, too slow = no benefit |
| Flow | Should increase slightly | Sharp increase = channel opened |

---

## Equipment vs Extraction Differentiation

### Signs of Equipment Issues

| Symptom | Equipment Issue | vs Extraction Issue |
|---------|-----------------|---------------------|
| Pressure never reaches 9 bar | Pump weak, OPV set low | vs grind too coarse |
| Temperature way off target | PID calibration, sensor | vs (temp is user-set) |
| Erratic readings between shots | Sensor issues, connection | vs puck prep variance |
| Flow reads 0 despite liquid | Flow sensor clogged/broken | vs (actual choke reads pressure) |

### When to Suspect Equipment

- **Consistent** anomalies across multiple shots with different beans/grinds
- Readings that don't respond to user adjustments
- Sudden changes without workflow changes
- Values outside physically possible range

**Recommend:** Run `diagnose_connection` if equipment suspected.

---

## Shot Comparison for Inconsistency

When comparing multiple shots, calculate variance in:

| Metric | Acceptable Variance | High Variance Indicates |
|--------|---------------------|-------------------------|
| Peak pressure | ±0.5 bar | Puck prep inconsistency |
| Time to first drip | ±1 second | Distribution or grind retention |
| Total flow | ±3 ml | Dose consistency |
| Extraction time | ±3 seconds | Grind or puck prep |
| Temperature | ±0.5°C | Machine stability |

**High variance root causes:**
1. Puck prep (most common)
2. Grinder retention (single-dose especially)
3. Bean freshness declining
4. Machine thermal cycling

---

## Quick Diagnostic Checklist

When diagnosing a shot:

- [ ] Check time to first drip (most diagnostic single metric)
- [ ] Check peak pressure and when it occurred
- [ ] Check average flow rate
- [ ] Check temperature stability
- [ ] Compare to previous shots if available
- [ ] Correlate with user's taste description
- [ ] Identify primary variable to adjust
- [ ] Provide specific, actionable recommendation
