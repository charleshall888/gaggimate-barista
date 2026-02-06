# Flow-Based Variable Pressure Profiles
Pioneered by modsmthng_57901 on Gaggimate Discord
## Overview

Flow-based variable pressure is an advanced profiling technique where you control **flow rate** as the primary parameter while setting a **pressure ceiling**. This creates self-regulating extraction that adapts to puck resistance automatically.

## The Core Technique

```json
"pump": {
  "target": "flow",      // Primary: maintain this flow rate
  "pressure": 9,         // Secondary: never exceed this pressure
  "flow": 1.8            // Target flow in g/s
}
```

### How It Works

1. The pump attempts to maintain the target flow rate (e.g., 1.8 g/s)
2. As water flows through the puck, pressure builds based on resistance
3. If pressure reaches the ceiling (e.g., 9 bar), flow may drop below target
4. If resistance is low, pressure stays low and flow is maintained

**Result**: The profile automatically adapts to your grind size without manual pressure adjustments.

---

## Advantages

| Benefit | Explanation |
|---------|-------------|
| **Grind Tolerance** | Forgiving of slight grind inconsistencies |
| **Channeling Prevention** | Lower initial pressure reduces channeling risk |
| **Flavor Balance** | Pressure ceiling prevents over-extraction bitterness |
| **Consistency** | Same profile works across different coffees |
| **Adaptability** | No need to re-dial for every bean |

### The "Second Blooming" Effect

When ground very fine, the transition from a high-pressure ramp phase (12 bar) to a lower extraction ceiling (9 bar) can cause flow to briefly pause. This is **intentional** and often produces rich, chocolatey profiles rather than bitterness.

**Best for**: Chocolatey/nutty roasts at 1:1.5 ratio

---

## Dose Scaling Formulas

When adapting flow-based profiles to different doses:

### Flow Rate
```
Flow = Dose × 2 / 20 seconds
```
| Dose | Flow Rate |
|------|-----------|
| 9g | 0.9 g/s |
| 16g | 1.6 g/s |
| 18g | 1.8 g/s |
| 20g | 2.0 g/s |
| 22g | 2.2 g/s |

### Pre-Infusion Water Volume
```
Water = Dose × 1.3 + Headspace (typically 7.5ml)
```
| Dose | Water Pumped |
|------|--------------|
| 9g | ~19ml |
| 16g | ~28ml |
| 18g | ~31ml |
| 20g | ~34ml |
| 22g | ~36ml |

### Ramp Phase Target Weight
```
Ramp Target = Flow × Phase Duration (typically 6s)
```
| Dose | Ramp Target |
|------|-------------|
| 9g | ~5g |
| 16g | ~10g |
| 18g | ~11g |
| 20g | ~12g |
| 22g | ~13g |

---

## Profile Structure

The firmware Automatic Pro profile (vIT3_0_8) implements flow-variable pressure across 5 phases:

1. **Initialization** — System check at minimal flow (0.1 g/s, 1 bar)
2. **Fill Headspace** — Fast fill (10 g/s, 1 bar ceiling) until pressure detected
3. **Saturate Puck** — Moderate flow (2 g/s, 2 bar) until first drip or pumped volume reached
4. **Extraction Start** — Pressure-targeted ramp (12 bar, dose-scaled flow limit)
5. **Main Extraction** — Declining flow (→ 1.2 g/s over 40s, 9 bar ceiling) to target weight

**Key structural patterns for custom profiles:**
- Low-pressure fill phases use `"target": "flow"` with a low pressure ceiling (1-2 bar)
- Ramp phase uses `"target": "pressure"` at 12 bar with flow as a limiter
- Extraction phase uses `"target": "flow"` with declining flow via `"transition": { "type": "linear", "duration": 40 }`
- Volumetric stops on extraction phases, pressure-based stops on fill phases

> **Full phase-by-phase analysis with JSON**: See [`automatic-pro/AUTOMATIC_PRO_GUIDE.md`](../../knowledge/automatic-pro/AUTOMATIC_PRO_GUIDE.md)

---

## Advanced: Declining Flow

For enhanced sweetness, use a declining flow during extraction:

```json
{
  "name": "Main Extraction",
  "transition": {
    "type": "linear",
    "duration": 40,
    "adaptive": true
  },
  "pump": {
    "target": "flow",
    "pressure": 9,
    "flow": 1.2
  }
}
```

This creates a **40-second linear transition** from the previous flow (e.g., 1.8 g/s) down to 1.2 g/s.

**Benefits**:
- Mimics lever machine behavior
- Produces sweeter, more balanced shots
- Reduces late-extraction harshness

---

## Version History

The current firmware version is **vIT3_0_8** (5-phase, declining flow, pressure-targeted ramp). Older documentation may reference the **v2** version (4-phase, constant flow, flow-targeted ramp). For a detailed comparison, see the [Automatic Pro Guide](../../knowledge/automatic-pro/AUTOMATIC_PRO_GUIDE.md#v2-vs-vit3-comparison).

---

## Quick Reference (vIT3_0_8)

### What Stays Constant Across Doses
- Temperature (91°C default)
- Phase durations (3s, 20s, 30s, 6s, 90s)
- Pressure ceilings (1 → 1 → 2 → 12 → 9 bar)
- Main Extraction decline (40s linear to 1.2 g/s)

### What Scales With Dose
- Saturate Puck pumped stop volume
- Extraction Start flow limit
- Final yield (volumetric stop)

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Low pressure throughout | Grind too coarse | Grind finer |
| Shot stalls | Grind too fine | Grind coarser or extend Phase 2 |
| Channeling | Uneven saturation | Increase pre-infusion time |
| Bitter/harsh | Over-extraction | Lower ratio (1:1.5) or lower temp |
| Sour/thin | Under-extraction | Higher ratio (1:2.5+) or higher temp |

---

## Related Resources

- [Automatic Pro Guide](../../knowledge/automatic-pro/AUTOMATIC_PRO_GUIDE.md) — Canonical firmware profile documentation
- [Profile Creation Guide](../../knowledge/GAGGIMATE_PROFILE_CREATION_GUIDE.md) — JSON schema and custom profile examples
