# Gaggimate Profile Creation Guide

## Overview

This document provides comprehensive guidance for creating custom espresso extraction profiles for Gaggimate-equipped machines (Gaggia Classic Pro, Gaggia Classic Evo, etc.). Gaggimate supports two profile types: **Simple** and **Pro**, with Pro profiles offering advanced features like pressure profiling, flow control, and complex transitions.

> **Looking for ready-to-use profiles?** See `PROFILE_LIBRARY.md` for a curated collection of profiles organized by roast level, processing method, and shot style.

## Profile Versions

- **Gaggimate Standard**: Basic temperature control, volumetric dosing, timed phases
- **Gaggimate Pro**: Advanced pressure/flow profiling, real-time pressure monitoring, complex transitions, multiple stop conditions

---

## JSON Profile Structure

### Top-Level Properties

```json
{
  "label": "Profile Name",
  "type": "pro",
  "description": "Optional description of the profile",
  "temperature": 93,
  "phases": [...]
}
```

#### Top-Level Fields

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `label` | string | Yes | Display name shown on machine | Any string |
| `type` | string | Yes | Profile complexity level | `"simple"` or `"pro"` |
| `description` | string | No | Optional notes about the profile | Any string |
| `temperature` | number | Yes | Global target temperature in °C | 70-100 (typical: 88-96) |
| `phases` | array | Yes | Ordered list of extraction phases | Array of phase objects |

---

## Phase Structure

Each phase represents a distinct stage in the extraction process.

### Phase Object Schema

```json
{
  "name": "Phase Name",
  "phase": "brew",
  "valve": 1,
  "duration": 25,
  "temperature": 0,
  "transition": {...},
  "pump": {...},
  "targets": [...]
}
```

### Phase Fields Reference

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `name` | string | Yes | Display name shown during brew | Any string (e.g., "Pre-infusion", "Ramp", "Hold") |
| `phase` | string | Yes | Phase category for display | `"preinfusion"`, `"brew"`, `"decline"` |
| `valve` | number | Yes | Three-way valve position | `0` = closed, `1` = open |
| `duration` | number | Yes | Maximum phase duration in seconds | 1-60 (typical: 3-30) |
| `temperature` | number | No | Override global temp (0 = use global) | 0 or 70-100 |
| `transition` | object | Yes (Pro) | How to transition to target values | See Transition section |
| `pump` | object | Yes | Pump control configuration | See Pump section |
| `targets` | array | No | Stop conditions (exits phase early) | See Targets section |

### Phase Type Guidelines

- **`preinfusion`**: Low-flow wetting phase (typically 2-5 seconds)
- **`brew`**: Main extraction phase (pressure/flow control)
- **`decline`**: Pressure taper/finish phase (optional)

---

## Pump Configuration

The `pump` object controls how the pump operates during a phase.

### Pump Object Structure

```json
"pump": {
  "target": "pressure",
  "pressure": 9,
  "flow": 0
}
```

### Pump Fields

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `target` | string | Yes | Control mode | `"pressure"`, `"flow"`, `"power"`, `"off"` |
| `pressure` | number | Yes | Target/limit pressure in bars | 0-12 (typical: 6-9) |
| `flow` | number | Yes | Target/limit flow in ml/s | 0-10 (typical: 2-5), `-1` = adaptive |

### Pump Target Modes

#### 1. **Pressure Mode** (`"pressure"`)
- Controls pump to maintain a specific pressure
- `pressure`: Target pressure in bars
- `flow`: Optional flow limit (0 = no limit)
- Example: Hold 9 bars throughout extraction

```json
"pump": {
  "target": "pressure",
  "pressure": 9,
  "flow": 4
}
```

#### 2. **Flow Mode** (`"flow"`)
- Controls pump to maintain a specific flow rate
- `flow`: Target flow in ml/s
- `pressure`: Optional pressure limit (prevents over-pressurization)
- Example: Gentle 2.5 ml/s pre-infusion

```json
"pump": {
  "target": "flow",
  "pressure": 9,
  "flow": 2.5
}
```

#### 3. **Power Mode** (`"power"`)
- Runs pump at fixed percentage (Standard version only)
- `pressure`: Pump power as percentage (0-100)
- `flow`: Ignored in power mode

```json
"pump": {
  "target": "power",
  "pressure": 100,
  "flow": 0
}
```

#### 4. **Adaptive Flow** (`flow: -1`)
- Automatically adjusts flow based on puck resistance
- Maintains consistent extraction across different grind settings
- Ideal for final extraction phase

```json
"pump": {
  "target": "flow",
  "pressure": 9,
  "flow": -1
}
```

---

## Transition Configuration

Transitions control how the pump moves from one phase's settings to the next.

### Transition Object Structure

```json
"transition": {
  "type": "linear",
  "duration": 3,
  "adaptive": true
}
```

### Transition Fields

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `type` | string | Yes | Ramp curve shape | `"instant"`, `"linear"`, `"ease-in"`, `"ease-out"`, `"ease-in-out"` |
| `duration` | number | Yes | Ramp duration in seconds | 0-10 (0 = instant) |
| `adaptive` | boolean | Yes | Start from current or previous target | `true` = current, `false` = previous target |

### Transition Types Explained

#### **Instant** (`"instant"`)
- Immediate jump to new target
- No ramping
- Use for: Phase starts, step changes

```json
"transition": {
  "type": "instant",
  "duration": 0,
  "adaptive": true
}
```

#### **Linear** (`"linear"`)
- Constant rate change
- Predictable, smooth
- Use for: Standard pressure ramps

```json
"transition": {
  "type": "linear",
  "duration": 4,
  "adaptive": true
}
```

#### **Ease-In** (`"ease-in"`)
- Slow start, fast finish
- Gradual pressure build
- Use for: Gentle pre-infusion to main extraction

```json
"transition": {
  "type": "ease-in",
  "duration": 3,
  "adaptive": true
}
```

#### **Ease-Out** (`"ease-out"`)
- Fast start, slow finish
- Smooth pressure decline
- Use for: Tapering at end of shot

```json
"transition": {
  "type": "ease-out",
  "duration": 5,
  "adaptive": true
}
```

#### **Ease-In-Out** (`"ease-in-out"`)
- Slow start and finish, fast middle
- Most natural feeling
- Use for: Complex pressure profiles

```json
"transition": {
  "type": "ease-in-out",
  "duration": 4,
  "adaptive": true
}
```

### Adaptive Behavior

**`adaptive: true`** (Start from current value)
- If Phase 1 targets 3 bar but only reaches 2 bar
- Phase 2 ramps from 2 bar → 7 bar
- More responsive to puck resistance

**`adaptive: false`** (Start from previous target)
- If Phase 1 targets 3 bar but only reaches 2 bar
- Phase 2 ramps from 3 bar → 7 bar
- More predictable, ignores actual performance

---

## Stop Conditions (Targets)

Stop conditions (targets) allow a phase to exit early when a condition is met. Without targets, phases run for their full `duration`.

### Target Object Structure

```json
"targets": [
  {
    "type": "volumetric",
    "operator": "gte",
    "value": 36
  }
]
```

### Target Fields

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `type` | string | Yes | Measurement type | `"volumetric"`, `"water_pumped"`, `"pressure"`, `"flow"` |
| `operator` | string | Yes | Comparison operator | `"gte"` (≥), `"lte"` (≤), `"gt"` (>), `"lt"` (<) |
| `value` | number | Yes | Threshold value | Depends on type |

### Target Types

#### 1. **Volumetric** (`"volumetric"`)
- Exit when scale weight reaches target
- **Requires Bluetooth scale** (or estimates based on pressure/flow)
- Most common for final shot weight
- Value in grams

```json
"targets": [
  {
    "type": "volumetric",
    "operator": "gte",
    "value": 36
  }
]
```

#### 2. **Water Pumped** (`"water_pumped"`)
- Exit when X ml of water has been pumped
- Independent of scale
- Useful for pre-infusion timing
- Value in milliliters

```json
"targets": [
  {
    "type": "water_pumped",
    "operator": "gte",
    "value": 40
  }
]
```

#### 3. **Pressure Above** (`"pressure"` + `"gte"`)
- Exit when pressure exceeds threshold
- Use for: Ensuring pressure build is complete
- Value in bars

```json
"targets": [
  {
    "type": "pressure",
    "operator": "gte",
    "value": 8.5
  }
]
```

#### 4. **Pressure Below** (`"pressure"` + `"lte"`)
- Exit when pressure drops below threshold
- Use for: Spring lever simulation
- Value in bars

```json
"targets": [
  {
    "type": "pressure",
    "operator": "lte",
    "value": 3
  }
]
```

#### 5. **Flow Above/Below** (`"flow"`)
- Exit when flow exceeds or drops below threshold
- Use for: Flow-based profiling
- Value in ml/s

```json
"targets": [
  {
    "type": "flow",
    "operator": "gte",
    "value": 4
  }
]
```

### Multiple Stop Conditions

Phases can have multiple targets. The phase exits when **ANY** condition is met (OR logic).

```json
"targets": [
  {
    "type": "volumetric",
    "operator": "gte",
    "value": 36
  },
  {
    "type": "pressure",
    "operator": "lte",
    "value": 2
  }
]
```

---

## Complete Profile Examples

### Example 1: Classic 9-Bar Profile

Simple, reliable extraction for medium roasts.

```json
{
  "label": "Classic 9-Bar",
  "type": "pro",
  "description": "Standard 9-bar extraction with pre-infusion",
  "temperature": 93,
  "phases": [
    {
      "name": "Pre-infusion",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 4,
      "temperature": 0,
      "transition": {
        "type": "instant",
        "duration": 0,
        "adaptive": true
      },
      "pump": {
        "target": "flow",
        "pressure": 9,
        "flow": 3
      }
    },
    {
      "name": "Ramp",
      "phase": "brew",
      "valve": 1,
      "duration": 4,
      "temperature": 0,
      "transition": {
        "type": "linear",
        "duration": 3,
        "adaptive": true
      },
      "pump": {
        "target": "pressure",
        "pressure": 9,
        "flow": 0
      },
      "targets": [
        {
          "type": "pressure",
          "operator": "gte",
          "value": 8.5
        }
      ]
    },
    {
      "name": "Hold",
      "phase": "brew",
      "valve": 1,
      "duration": 25,
      "temperature": 0,
      "transition": {
        "type": "instant",
        "duration": 0,
        "adaptive": true
      },
      "pump": {
        "target": "pressure",
        "pressure": 9,
        "flow": 4
      },
      "targets": [
        {
          "type": "volumetric",
          "operator": "gte",
          "value": 36
        }
      ]
    }
  ]
}
```

### Example 2: Blooming Profile

Enhanced sweetness with soak phase.

```json
{
  "label": "Bloom Profile",
  "type": "pro",
  "description": "Gentle bloom for fruit-forward coffees",
  "temperature": 93,
  "phases": [
    {
      "name": "Fill",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": {
        "type": "instant",
        "duration": 0,
        "adaptive": true
      },
      "pump": {
        "target": "flow",
        "pressure": 9,
        "flow": 2.5
      }
    },
    {
      "name": "Bloom",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 8,
      "temperature": 0,
      "transition": {
        "type": "instant",
        "duration": 0,
        "adaptive": true
      },
      "pump": {
        "target": "power",
        "pressure": 0,
        "flow": 0
      }
    },
    {
      "name": "Ramp",
      "phase": "brew",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": {
        "type": "ease-in-out",
        "duration": 4,
        "adaptive": true
      },
      "pump": {
        "target": "pressure",
        "pressure": 9,
        "flow": 0
      },
      "targets": [
        {
          "type": "pressure",
          "operator": "gte",
          "value": 8.5
        }
      ]
    },
    {
      "name": "Hold",
      "phase": "brew",
      "valve": 1,
      "duration": 20,
      "temperature": 0,
      "transition": {
        "type": "instant",
        "duration": 0,
        "adaptive": true
      },
      "pump": {
        "target": "pressure",
        "pressure": 9,
        "flow": 4
      },
      "targets": [
        {
          "type": "volumetric",
          "operator": "gte",
          "value": 36
        }
      ]
    },
    {
      "name": "Taper",
      "phase": "decline",
      "valve": 1,
      "duration": 6,
      "temperature": 0,
      "transition": {
        "type": "linear",
        "duration": 5,
        "adaptive": true
      },
      "pump": {
        "target": "pressure",
        "pressure": 5,
        "flow": 0
      }
    }
  ]
}
```

### Example 3: Spring Lever Simulation

Declining pressure profile mimicking manual lever machines.

```json
{
  "label": "Cremina Lever",
  "type": "pro",
  "description": "Spring lever-style declining pressure",
  "temperature": 90,
  "phases": [
    {
      "name": "Pre-infusion",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": {
        "type": "instant",
        "duration": 0,
        "adaptive": true
      },
      "pump": {
        "target": "flow",
        "pressure": 9,
        "flow": 3
      }
    },
    {
      "name": "Peak Pressure",
      "phase": "brew",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": {
        "type": "linear",
        "duration": 3,
        "adaptive": true
      },
      "pump": {
        "target": "pressure",
        "pressure": 9,
        "flow": 0
      },
      "targets": [
        {
          "type": "pressure",
          "operator": "gte",
          "value": 8.5
        }
      ]
    },
    {
      "name": "Decline",
      "phase": "brew",
      "valve": 1,
      "duration": 30,
      "temperature": 0,
      "transition": {
        "type": "linear",
        "duration": 25,
        "adaptive": true
      },
      "pump": {
        "target": "pressure",
        "pressure": 3,
        "flow": 0
      },
      "targets": [
        {
          "type": "volumetric",
          "operator": "gte",
          "value": 36
        }
      ]
    }
  ]
}
```

### Example 4: Flow-Based Variable Pressure (Automatic Pro Style)
Pioneered by modsmthng_57901 on Gaggimate Discord

This technique creates **self-regulating pressure** that adapts to your grind size. Instead of targeting a fixed pressure, you target a flow rate with a pressure ceiling—the machine automatically adjusts.

#### How It Works

```json
"pump": {
  "target": "flow",      // Primary control: maintain this flow rate
  "pressure": 9,         // Secondary: never exceed this pressure
  "flow": 1.8            // Target 1.8 g/s
}
```

**The Magic**: 
- If puck resistance is **high** (fine grind) → pressure builds quickly to the 9 bar ceiling, flow may drop below target
- If puck resistance is **low** (coarse grind) → pressure stays low naturally, flow maintained at target
- The profile **adapts automatically** without manual adjustment

#### Advantages of Flow-Based Variable Pressure

1. **Grind Tolerance**: Forgiving of slight grind inconsistencies—no need to dial in perfectly
2. **Channeling Prevention**: Lower initial pressure reduces channeling risk
3. **Flavor Balance**: The 9 bar ceiling prevents over-extraction bitterness
4. **Consistency**: Same profile works across different coffees with minor grind adjustments
5. **Second Blooming Effect**: With fine grinds, the transition from 12→9 bar can create a brief pause, enhancing chocolatey/nutty notes

#### Dose-Based Scaling Formulas

When adapting this profile to different doses, use these formulas:

| Parameter | Formula | 9g | 16g | 18g | 20g | 22g |
|-----------|---------|-----|-----|-----|-----|-----|
| **Flow Rate** | `Dose × 2 / 20s` | 0.9 g/s | 1.6 g/s | 1.8 g/s | 2.0 g/s | 2.2 g/s |
| **Pre-Infusion Water** | `Dose × 1.3 + 7.5ml` | 19ml | 28ml | 31ml | 34ml | 36ml |
| **Ramp Target** | `Flow × 6s` | 5g | 10g | 11g | 12g | 13g |
| **Final Yield (1:2)** | `Dose × 2` | 18g | 32g | 36g | 40g | 44g |

#### Complete Example: Automatic Pro v2 (18g)

```json
{
  "label": "Automatic Pro v2 18g",
  "type": "pro",
  "description": "Flow-based variable pressure - adapts to grind automatically",
  "temperature": 91,
  "phases": [
    {
      "name": "Pre-Infusion",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 10,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": {
        "target": "flow",
        "pressure": 2,
        "flow": 20
      },
      "targets": [
        { "type": "volumetric", "operator": "gte", "value": 1 },
        { "type": "pumped", "operator": "gte", "value": 31 }
      ]
    },
    {
      "name": "Bloom",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 6,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": {
        "target": "flow",
        "pressure": 2,
        "flow": 1.8
      },
      "targets": [
        { "type": "volumetric", "operator": "gte", "value": 1.5 }
      ]
    },
    {
      "name": "Ramp",
      "phase": "brew",
      "valve": 1,
      "duration": 6,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": {
        "target": "flow",
        "pressure": 12,
        "flow": 1.8
      },
      "targets": [
        { "type": "volumetric", "operator": "gte", "value": 11 }
      ]
    },
    {
      "name": "Brew",
      "phase": "brew",
      "valve": 1,
      "duration": 120,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": {
        "target": "flow",
        "pressure": 9,
        "flow": 1.8
      },
      "targets": [
        { "type": "volumetric", "operator": "gte", "value": 36 }
      ]
    }
  ]
}
```

#### Advanced: Declining Flow Profile (v3 Style)

For even more sophistication, add a declining flow during extraction:

```json
{
  "name": "Main Extraction",
  "phase": "brew",
  "valve": 1,
  "duration": 90,
  "temperature": 0,
  "transition": {
    "type": "linear",
    "duration": 40,
    "adaptive": true
  },
  "pump": {
    "target": "flow",
    "pressure": 9,
    "flow": 1.2
  },
  "targets": [
    { "type": "volumetric", "operator": "gte", "value": 36 }
  ]
}
```

This creates a **40-second linear decline** from the previous flow (1.8 g/s) down to 1.2 g/s, mimicking high-end lever machine behavior for sweeter, more balanced shots.

---

## Profile Design Best Practices

### Temperature Guidelines

| Coffee Type | Roast Level | Recommended Temp | Adjustment Range |
|-------------|-------------|------------------|------------------|
| Light roast | Nordic style | 94-96°C | Very high extraction |
| Medium roast | City/Full City | 92-94°C | Standard espresso |
| Medium-dark | Vienna | 90-92°C | Balanced sweetness |
| Dark roast | French/Italian | 88-90°C | Avoid over-extraction |

**Temperature Adjustment Strategy:**
- Too sour/acidic → Increase 1-2°C
- Too bitter/harsh → Decrease 1-2°C
- Flat/lifeless → Increase temperature
- Astringent/dry → Decrease temperature

### Ratio and Timing Guidelines

| Ratio | Dose In | Output | Time Range | Style |
|-------|---------|--------|------------|-------|
| 1:1 | 18g | 18g | 20-25s | Ristretto |
| 1:1.5 | 18g | 27g | 22-28s | Short |
| 1:2 | 18g | 36g | 25-32s | Classic |
| 1:2.5 | 18g | 45g | 28-35s | Lungo |
| 1:3 | 18g | 54g | 30-40s | Allongé |

### Phase Duration Guidelines

| Phase Type | Typical Duration | Purpose |
|------------|------------------|---------|
| Fast fill | 2-3 seconds | Quick wetting at low pressure |
| Slow pre-infusion | 4-8 seconds | Even saturation, de-gas |
| Bloom/soak | 5-10 seconds | Enhance sweetness |
| Pressure ramp | 3-5 seconds | Build to extraction pressure |
| Hold phase | 15-30 seconds | Main extraction |
| Decline/taper | 3-6 seconds | Smooth finish |

### Common Profile Patterns

#### 1. **Modern Espresso** (Medium roasts)
```
Pre-infusion (3-4s at 3 ml/s)
→ Ramp (3s to 9 bar)
→ Hold (20-25s at 9 bar)
→ Stop at target weight
```

#### 2. **Light Roast Bloom**
```
Gentle fill (5s at 2 ml/s)
→ Bloom (8s, pump off)
→ Ramp (4s to 9 bar)
→ Hold (15-20s at 9 bar)
→ Stop at target weight
```

#### 3. **Dark Roast Low Pressure**
```
Pre-infusion (4s at 2.5 ml/s)
→ Ramp (3s to 7 bar)
→ Hold (25s at 7 bar)
→ Taper (4s to 4 bar)
→ Stop at target weight
```

#### 4. **Spring Lever Simulation**
```
Pre-infusion (4s at 3 ml/s)
→ Peak (3s to 9 bar)
→ Linear decline (25s from 9→3 bar)
→ Stop at target weight
```

### Flow Rate Guidelines

| Flow Rate | Use Case | Pressure |
|-----------|----------|----------|
| 1.5-2.5 ml/s | Very gentle pre-infusion | <3 bar |
| 2.5-4 ml/s | Standard pre-infusion | 3-6 bar |
| 4-5 ml/s | Main extraction (with flow limit) | 8-9 bar |
| Adaptive (-1) | Final phase, adjusts to resistance | Variable |

---

## Troubleshooting Profiles

### Issue: Shot Channeling

**Symptoms:** Fast flow, under-extracted, sour
**Fixes:**
- Increase pre-infusion duration (5-8 seconds)
- Reduce pre-infusion flow (2-2.5 ml/s)
- Add bloom phase (6-8 seconds soak)

### Issue: Over-Extraction

**Symptoms:** Bitter, harsh, astringent
**Fixes:**
- Reduce temperature (-2°C)
- Shorten extraction time
- Reduce hold phase duration
- Add declining pressure phase

### Issue: Under-Extraction

**Symptoms:** Sour, weak, thin body
**Fixes:**
- Increase temperature (+2°C)
- Extend extraction time
- Increase hold pressure (9 bar)
- Add bloom phase for better saturation

### Issue: Inconsistent Shots

**Symptoms:** Different results with same profile
**Fixes:**
- Use volumetric stop condition (requires scale)
- Enable adaptive transitions
- Add pressure-based stop conditions
- Increase pre-infusion time for consistency

### Issue: Pump Strain / Loud Operation

**Symptoms:** Grinding sounds, pressure spikes
**Fixes:**
- Start with flow mode, not pressure
- Use gentler ramp transitions (ease-in)
- Reduce target pressure to 8-8.5 bar
- Check grind isn't too fine

---

## Advanced Techniques

### Multi-Stage Extraction

Create complex flavor profiles with 5+ phases:

```
1. Fast fill (2s, 4 ml/s) → Saturate quickly
2. Bloom (6s, 0 ml/s) → De-gas, enhance sweetness
3. Ramp (4s, ease-in to 9 bar) → Build pressure gently
4. High pressure (8s, 9 bar) → Extract body
5. Medium pressure (12s, 7 bar) → Extract sweetness
6. Low pressure (8s, 5 bar) → Extract acidity
7. Taper (4s, ease-out to 3 bar) → Smooth finish
```

### Adaptive Flow Profiling

Use adaptive flow for the final phase to automatically adjust to puck resistance:

```json
"pump": {
  "target": "flow",
  "pressure": 9,
  "flow": -1
}
```

This maintains consistent extraction across:
- Different grind settings
- Bean varieties
- Freshness levels

### Temperature Profiling (Coming Soon)

Future versions will support per-phase temperature control:
- Start cool (90°C) for acidity
- Increase mid-shot (93°C) for body
- Finish hot (95°C) for sweetness

---

## File Management

### Exporting Profiles

1. Navigate to `http://gaggimate.local/profiles`
2. Click export icon on profile card
3. Save `.json` file

### Importing Profiles

1. Navigate to `http://gaggimate.local/profiles`
2. Click "Import" (top right)
3. Upload `.json` file
4. Click star icon to make available on machine

### Sharing Profiles

- Join Gaggimate Discord: https://discord.gg/APw7rgPGPf
- Share in #profiles channel
- Include coffee recommendations in description
- Test thoroughly before sharing

---

## Volumetric Estimation (No Scale)

Without a Bluetooth scale, Gaggimate estimates volume using:
- Pressure curve analysis
- Flow rate integration
- Time-based modeling

**Calibration Process:**

1. First shot: Let profile run with volumetric target
2. Weigh actual output on regular scale
3. Adjust profile's volumetric value:
   - If 30g target → 35g actual: Change to 27g
   - If 30g target → 25g actual: Change to 33g
4. Re-test and fine-tune

After 2-3 shots, estimation typically becomes accurate within Â±2g.

---

## Quick Reference Card

### Essential Settings by Coffee Type

**Light Roasts (Ethiopia, Kenya, Fruit-forward)**
- Temperature: 94-96°C
- Ratio: 1:2.5 to 1:3
- Profile: Bloom + 9 bar
- Time: 28-35 seconds

**Medium Roasts (Colombia, Brazil, Balanced)**
- Temperature: 92-94°C
- Ratio: 1:2
- Profile: Classic 9 bar or slight decline
- Time: 25-32 seconds

**Dark Roasts (French, Italian)**
- Temperature: 88-90°C
- Ratio: 1:1.5 to 1:2
- Profile: 7-8 bar or declining
- Time: 22-28 seconds

### Most Common Mistakes

1. **Too short pre-infusion** → Add 2-4 seconds
2. **No volumetric target** → Always set weight target
3. **Instant transitions everywhere** → Use linear/ease for ramps
4. **Ignoring temperature** → Adjust by 1-2°C increments
5. **Same profile for all coffees** → Customize per bean

---

## Resources

- **Documentation**: https://docs.gaggimate.eu/
- **Discord Community**: https://discord.gg/APw7rgPGPf
- **Profile Library**: Discord #profiles channel
- **Web Interface**: http://gaggimate.local/profiles
- **GitHub Repository**: https://github.com/jniebuhr/gaggimate

---

## Version History

- **v1.0** (January 2026): Initial comprehensive guide
- Based on Gaggimate firmware v1.6.0+
- Pro profile features documented
- Examples from real-world usage and community

---

This guide was written by Julian Leopold using Claude in order to assist users and LLM agents in creating effective Gaggimate espresso profiles.