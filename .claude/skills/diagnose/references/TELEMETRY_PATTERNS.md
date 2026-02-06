# Telemetry Pattern Interpretation Guide

Detailed reference for interpreting Gaggimate shot telemetry and correlating with taste outcomes.

---

## Pressure Patterns

### Pressure Curve by Style

"Normal" pressure depends entirely on the shot style. Load specific expectations from `knowledge/PRESSURE_GUIDE.md` (Pressure by Shot Style section).

| Style | Pre-infusion | Extraction Pressure | Curve Shape |
|-------|-------------|---------------------|-------------|
| Classic 9-Bar | 2-4 bar, 4-8s | 8-10 bar flat | Flat hold |
| Bloom | 2-3 bar fill, then pump off | 7-9 bar | Bloom pause → ramp → hold |
| Turbo | 5-6 bar, 2-3s | 5-6 bar | Flat at lower pressure |
| Allongé | 2-3 bar, 5-8s | ~6 bar peak | Flow-controlled, pressure rises then naturally declines |
| Lever Decline | 2-4 bar, 5-8s | 8-9 bar peak → 3-5 bar | Linear decline through extraction |
| Dark/Gentle | 2-3 bar, 4-6s | 7-8 bar | Flat or gentle taper |

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

### Flow Curve by Style

| Style | Pre-infusion Flow | Extraction Flow | First Drip |
|-------|-------------------|-----------------|------------|
| Classic 9-Bar | 0-1 ml/s | 1.5-2.5 ml/s steady | 4-8s |
| Bloom | 1-2 ml/s fill, ~0 during bloom | 1.5-2.5 ml/s | Delayed by bloom (15-25s from start) |
| Turbo | Brief pre-wet | 3-5 ml/s (high flow is intentional) | 2-4s |
| Allongé | 0.5-1 ml/s | 2-3 ml/s constant flow-target | 5-10s |
| Lever Decline | 0-1 ml/s | Starts 1.5-2 ml/s, increases as pressure drops | 4-8s |
| Dark/Gentle | 0-1 ml/s | 1.5-2.5 ml/s | 4-7s |

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

**Time to first drip** is one of the most diagnostic metrics, but expected values vary by style:

| Style | Expected First Drip | Too Fast | Too Slow |
|-------|---------------------|----------|----------|
| Classic 9-Bar | 4-8s | < 3s | > 10s |
| Bloom | 15-25s from start (delayed by bloom pause) | Flow during bloom > 1 ml/s | > 30s from start |
| Turbo | 2-4s | < 1.5s | > 6s |
| Allongé | 5-10s | < 3s | > 12s |
| Lever Decline | 4-8s | < 3s | > 10s |
| Dark/Gentle | 4-7s | < 3s | > 9s |

**Important:** For bloom profiles, first drip time is measured from the *start of the extraction phase* (after bloom), not from the start of the shot. A bloom shot showing "first drip at 20s" is normal — the bloom pause accounts for 10-15s of that.

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

Use this matrix to work backwards from taste to likely telemetry cause. All thresholds are **relative to the identified shot style** — load expected ranges from `knowledge/PRESSURE_GUIDE.md` and `knowledge/PROFILE_LIBRARY.md`.

| Taste Descriptor | Primary Telemetry Suspect | Secondary Suspect | Tertiary Suspect |
|------------------|---------------------------|-------------------|------------------|
| **Sour** | Flow above style's expected range | First drip below style's expected time | Temperature too low |
| **Bitter** | Extraction time well above style range | Temperature too high | Pressure sustained above style target |
| **Astringent** | Pressure spike + drop (any style) | Channeling (erratic flow) | Over-extracted fines |
| **Watery** | Pressure below style's expected range | Flow above style range | Extraction time below style range |
| **Harsh** | Flow well below style range (choked) | Extraction time far above style range | High temperature |
| **Flat/Muted** | Temperature drift (any style) | Insufficient preinfusion/bloom | Stale beans (not telemetry) |
| **Unbalanced** | Erratic flow/pressure (any style) | Channeling evidence | Multiple extraction zones |
| **Thin body** | Flow above style range | Time below style range | Pressure below style range |
| **Heavy/Syrupy** | Flow below style range | Time above style range | Fine grind (not anomalous if balanced) |

---

## Style Detection Fingerprints

Use this table for Tier 3 detection (last resort) when neither profile definition nor meaningful profile name is available. Classify the shot style from telemetry signatures alone.

| Fingerprint | Detected Style |
|-------------|----------------|
| Total time < 22s AND avg flow > 3 ml/s | **Turbo** |
| Pre-infusion > 12s with near-zero flow pause (pump off period) | **Bloom** |
| Pressure clearly declining through brew phase (>4 bar drop over >15s) | **Lever Decline** |
| Total time > 38s AND avg extraction pressure < 7 bar AND high yield | **Allongé** |
| Extraction pressure 7-8 bar steady, no bloom, no decline | **Dark/Gentle** |
| Extraction pressure 8-10 bar steady, 25-35s total | **Classic 9-Bar** |

**Ambiguity rules:**
- If multiple fingerprints match, prefer the more specific one (e.g., bloom > classic)
- Short shots with moderate flow (22-28s, 2-3 ml/s) are likely Classic with a slightly coarse grind, not Turbo
- Declining pressure at the very end of any shot is normal puck degradation, not Lever Decline — look for intentional, sustained decline starting early in extraction

---

## Per-Style Diagnostic Notes

Common misdiagnosis warnings — what NOT to flag for each style.

### Turbo
- Flow 3-5 ml/s is **EXPECTED**. Only flag > 6 ml/s as too fast.
- Total time 12-20s is **EXPECTED**. Do not flag as "too short."
- Pressure at 5-6 bar is **EXPECTED**. Do not flag as "too low."
- First drip at 2-4s is **EXPECTED** for the coarser grind.
- Sourness likely means ratio too short (needs 1:2.5-1:3) or temp too low, not grind too coarse.

### Bloom
- Delayed first drip (15-25s from shot start) is **EXPECTED** — the bloom pause adds 10-15s.
- No flow during pump-off phase is **NORMAL** — that's the bloom working.
- Total time 30-40s is **EXPECTED**. Do not flag as "too long."
- Lower extraction pressure (7-8 bar) is **EXPECTED** for naturals/anaerobics.
- If sour despite correct parameters, consider longer bloom or higher temperature.

### Allongé
- Total time 25-50s is **EXPECTED**. Do not flag as "too long."
- Pressure at 5-6 bar is **EXPECTED** — flow-controlled, not pressure-controlled.
- Pressure naturally rising then declining is **NORMAL** allongé behavior.
- High yield (1:4-1:5 ratio) is **INTENTIONAL**. Do not flag as over-extracted.
- Bitterness in allongé usually means temperature too high, not over-extraction.

### Lever Decline
- Declining pressure through extraction is **INTENTIONAL**. Do not flag as "pressure dropping."
- Flow increasing as pressure drops is **NORMAL** physics — lower pressure = less resistance.
- Total time 28-35s is **EXPECTED**.
- If bitter, the peak pressure may be too high or held too long before decline starts.

### Dark/Gentle
- Pressure at 7-8 bar is **EXPECTED**. Do not flag as "too low."
- Shorter ratios (1:1.5-1:2) are **NORMAL** for dark roasts.
- Total time 22-28s is **EXPECTED**.
- Temperature at 88-90°C is **EXPECTED** — do not suggest raising it.

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

- [ ] Identify shot style (profile definition → profile name → telemetry fingerprint)
- [ ] Load style-specific expected ranges from knowledge files
- [ ] Check time to first drip against style expectations
- [ ] Check peak pressure against style target
- [ ] Check average flow rate against style range
- [ ] Check temperature stability (universal: ±1°C normal)
- [ ] Compare intended profile vs actual telemetry (if profile definition available)
- [ ] Compare to previous shots if available
- [ ] Correlate with user's taste description using style-relative thresholds
- [ ] Identify primary variable to adjust
- [ ] Provide specific, actionable recommendation
