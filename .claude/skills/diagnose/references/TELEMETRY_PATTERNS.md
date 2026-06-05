# Telemetry Pattern Interpretation Guide

Detailed reference for interpreting Gaggimate shot telemetry and correlating with taste outcomes.

---

## Bluetooth Scale Artifacts

The Bookoo BT scale communicates with the Gaggimate via BLE, and the connection can produce spurious data — especially near the end of a shot when the pump stops or the cup is moved.

### Known Artifact Patterns

| Pattern | Signature | How to Handle |
|---------|-----------|---------------|
| **End-of-shot volume spike** | Weight/volume jumps sharply upward in the final 1-3 samples (e.g., 16g → 67g) | Discard. Use the last stable reading before the spike. |
| **Drop to zero** | Weight drops to 0g in final samples (cup removed or BLE disconnect) | Discard. Use the last non-zero reading before the drop. |
| **Spike then drop** | Volume spikes up then immediately drops to 0g | Both are artifacts. Use the last stable reading before the spike began. |
| **Null final weight** | `final_weight_g` is null despite liquid in cup | BLE lost sync before registering final weight. Estimate from last stable weight sample, or use flow meter total minus ~15-20% puck absorption. |

### Detection Rules

1. **Scan the last 3-5 weight/volume samples** of the shot. If any sample differs from the preceding trend by more than 2× the average inter-sample change, treat it as an artifact.
2. **A reading of exactly 0g after non-zero readings** is always a disconnect artifact — never a real measurement.
3. **NEVER ask the user for the weight.** When artifacts are detected or `final_weight_g` is null, estimate the dose out yourself: use the last stable weight reading, or fall back to `total_volume_ml × 0.82` (puck absorption estimate). State your estimate and reasoning, then proceed with the diagnosis. A ±2g estimate is sufficient for diagnostic purposes.
4. **Do not flag artifact-caused anomalies.** Volume overshoots, weight spikes/drops, or volumetric stop failures caused by BLE artifacts are not extraction problems — don't diagnose them as such.
5. **Pressure, flow rate, and temperature data** from the machine's own sensors are reliable and unaffected by BT scale issues. Only weight/volume readings from the scale are suspect.

---

## Flow Meter vs Cup Weight During Bloom

The flow meter measures water **entering the group head**, not water **exiting the basket**. During bloom (pump off, valve open), these can diverge significantly — and misreading this causes false channeling diagnoses.

### Disambiguation Table

| Flow Meter | Cup Weight | Interpretation |
|------------|-----------|----------------|
| 0 ml/s | 0g | Standard bloom — fill water held in puck |
| >1 ml/s | 0g | **Puck absorption** — gravity/residual pressure feeding water from boiler into group; puck is absorbing it. **Not channeling.** |
| >1 ml/s | >0g (increasing) | **Through-flow** — water passing through the puck. Possible channel or puck too permeable. |

### Why bloom flow varies between shots

Even with the same grind and profile, bloom-phase flow meter readings can differ shot to shot:

- **Higher dose** = more dry coffee = more absorption capacity = more flow into puck
- **Shorter fill phase** = less saturated puck entering bloom = puck draws in more water
- **Residual system pressure** varies with machine warm-up state and flush timing

On the Gaggia Classic Pro, the boiler sits above the group head. When the pump turns off but the solenoid valve stays open (valve: 1), boiler water can drain into the group by gravity. The flow meter registers this, but it's water entering the puck from above — not exiting below.

### Diagnostic Rule

**Never diagnose bloom-phase flow as channeling without corroborating cup weight.** The flow meter alone cannot distinguish absorption from through-flow. Cup weight is ground truth.

- Flow during bloom + **zero cup weight** = absorption (benign, possibly beneficial — more saturation)
- Flow during bloom + **increasing cup weight** = through-flow (investigate puck prep or grind)

### Impact on Other Metrics

Bloom absorption flow inflates `total_volume_ml` and can trigger a misleadingly early `time_to_first_drip_s` (since first drip is detected from the flow meter, not the scale). When comparing shots with different bloom absorption:

- Subtract bloom-phase flow from `total_volume_ml` before comparing extraction volumes
- Use first cup weight appearance (not `time_to_first_drip_s`) as the true first-drip indicator
- The `0.82` puck absorption factor for weight estimation may undercount when bloom absorption is high — cross-reference with weight trajectory instead

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
| **Never reaches target** | Peak < 8 bar | Grind too coarse (water escapes faster than pump fills), channeling, low dose. **Exception:** post-bloom ramps starting from 0 bar often don't hit target — this is normal ease-in behavior, not a grind issue. | Thin, watery, sour | Grind finer, check puck prep (but verify it's not a normal post-bloom ramp first) |
| **Capped below target** | Pressure plateaus below target AND flow sits pegged at the phase's `flow` limit (e.g. flat at exactly 4.0 ml/s) | The **flow limit is the binding constraint**, not grind — the pump can't push enough flow to build pressure on a permeable puck | Thin, sour, under-extracted | Raise (or remove → `flow: 0`) the phase's flow limit so pressure can build, OR grind finer so the puck reaches target pressure at a lower flow. Don't keep grinding finer if the cap is the real ceiling. To gentle a build *without* this trap, lengthen the ease-in instead of capping flow (see GAGGIMATE_PROFILE_CREATION_GUIDE.md). |
| **Oscillating** | 7-10 bar fluctuation | Pump issue, pressure profiling instability | Uneven extraction | Check pump, PID settings |
| **Rapid decay** | Drops from 9 to 5 bar mid-shot | Channel opened, puck fractured | Starts balanced, ends sour | Better puck prep, consider paper filter |
| **Slow build** | Takes >8s to reach target | Grind too coarse (low resistance lets water escape), or normal post-bloom ramp behavior (ease-in from 0 bar). NOT caused by fine grind — finer grind builds pressure faster. | Under-extraction if coarse; not an issue if post-bloom | If coarse: grind finer. If post-bloom ramp: likely normal — check that Peak Hold reaches target. |

### Pressure-Resistance Physics (bathtub model)

**Pressure = pump force vs. puck drainage.** Think of the group head as a bathtub: the pump is the faucet, the puck is the drain. Resistance affects ALL phases consistently:

| Grind | Resistance | Ramp (filling) | Hold | Decline (draining) |
|-------|-----------|-----------------|------|---------------------|
| **Finer** | Higher (small drain) | Pressure builds **faster** — water backs up | Pressure stays high easily | Pressure drops **slowly** — floor stays above target |
| **Coarser** | Lower (big drain) | Pressure builds **slower** — water escapes | Pump works harder to maintain | Pressure drops **readily** — tracks the declining target |

**CRITICAL: Resistance holds pressure up in BOTH directions.** Do not claim that finer grind causes slow pressure build — the opposite is true. Finer grind = more resistance = pressure builds faster (ramp) AND drops slower (decline). Coarser grind = less resistance = pressure builds slower (ramp) AND drops faster (decline).

**Common misdiagnosis to avoid:** If a ramp phase doesn't reach its pressure target after a bloom pause, this is likely normal behavior for the ease-in curve starting from 0 bar — NOT caused by grind being too fine. If anything, a finer grind helps the ramp. Only flag slow ramp as "too coarse" in non-bloom profiles where the pump starts from pre-infusion pressure (2-4 bar), not from 0.

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
- **Flow meter reading >0 during pump-off does NOT mean channeling.** Cross-reference with cup weight. Flow + zero cup weight = puck absorption (normal — boiler gravity feed saturating the puck). Only flag bloom flow as a problem if cup weight is also increasing. See "Flow Meter vs Cup Weight During Bloom" section.
- `time_to_first_drip_s` may report early if the flow meter detects bloom absorption flow. Use **first cup weight appearance** as the true first-drip indicator for bloom profiles.
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
| Flow meter during bloom | Variable (0-3 ml/s) | **Not diagnostic alone** — must cross-reference with cup weight. See "Flow Meter vs Cup Weight During Bloom" section. |
| Cup weight during bloom | 0g | >0g and increasing = through-flow (channel or puck too permeable) |

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
