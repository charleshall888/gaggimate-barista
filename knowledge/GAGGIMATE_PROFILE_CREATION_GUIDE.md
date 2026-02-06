# Gaggimate Profile Creation Guide

## Overview

This document provides guidance for creating custom espresso extraction profiles for Gaggimate-equipped machines (Gaggia Classic Pro, Gaggia Classic Evo, etc.). Gaggimate supports two profile types: **Simple** and **Pro**, with Pro profiles offering advanced features like pressure profiling, flow control, and complex transitions.

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

### Transition Type Summary

- **Instant** — Immediate jump, no ramp. Use for phase starts.
- **Linear** — Constant rate change. Use for standard pressure ramps.
- **Ease-in** — Slow start, fast finish. Use for gentle pre-infusion → extraction.
- **Ease-out** — Fast start, slow finish. Use for tapering/decline phases.
- **Ease-in-out** — Slow start and finish, fast middle. Use for complex pressure changes.

**Adaptive behavior:** `adaptive: true` starts from the *actual* current value (responsive to puck resistance). `adaptive: false` starts from the *previous target* value (more predictable, ignores actual performance).

> *For detailed transition examples with full JSON and adaptive behavior explanations, see [`reference/PROFILE_CREATION_REFERENCE.md`](reference/PROFILE_CREATION_REFERENCE.md).*

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

### Flow-Based Variable Pressure Technique

Pioneered by modsmthng_57901 on Gaggimate Discord. This technique creates **self-regulating pressure** — target a flow rate with a pressure ceiling, and the machine adapts to puck resistance automatically.

```json
"pump": {
  "target": "flow",      // Primary: maintain this flow rate
  "pressure": 9,         // Secondary: never exceed this pressure
  "flow": 1.8            // Target flow in g/s
}
```

**How it works**: High puck resistance (fine grind) → pressure builds to the ceiling, flow may drop below target. Low resistance (coarse grind) → pressure stays low, flow is maintained. The profile adapts without manual adjustment.

**Advantages**: Grind tolerance, channeling prevention (lower initial pressure), flavor balance (pressure ceiling prevents bitterness), consistency across different coffees.

**Scaling flow to dose**: `Flow = Dose × 2 / 20s` (e.g., 16g → 1.6 g/s, 18g → 1.8 g/s, 22g → 2.2 g/s)

> **Gaggimate's built-in Automatic Pro profile** implements this technique with a 5-phase architecture including declining flow extraction. For the full firmware profile documentation, dose scaling tables, and phase-by-phase analysis, see [`automatic-pro/AUTOMATIC_PRO_GUIDE.md`](automatic-pro/AUTOMATIC_PRO_GUIDE.md).

---

## Profile Design Best Practices

For temperature, ratio, and adjustment strategies, see `ESPRESSO_BREWING_BASICS.md`.
For pressure selection by roast and processing method, see `PRESSURE_GUIDE.md`.
For ready-to-use profile patterns, see `PROFILE_LIBRARY.md`.

### Phase Duration Guidelines

| Phase Type | Typical Duration | Purpose |
|------------|------------------|---------|
| Fast fill | 2-3 seconds | Quick wetting at low pressure |
| Slow pre-infusion | 4-8 seconds | Even saturation, de-gas |
| Bloom/soak | 5-10 seconds | Enhance sweetness |
| Pressure ramp | 3-5 seconds | Build to extraction pressure |
| Hold phase | 15-30 seconds | Main extraction |
| Decline/taper | 3-6 seconds | Smooth finish |

### Flow Rate Guidelines

| Flow Rate | Use Case | Pressure |
|-----------|----------|----------|
| 1.5-2.5 ml/s | Very gentle pre-infusion | <3 bar |
| 2.5-4 ml/s | Standard pre-infusion | 3-6 bar |
| 4-5 ml/s | Main extraction (with flow limit) | 8-9 bar |
| Adaptive (-1) | Final phase, adjusts to resistance | Variable |

---

*For transition details, taste-driven profile tuning, advanced techniques, troubleshooting, lever simulation example, file management, and volumetric estimation — see [`reference/PROFILE_CREATION_REFERENCE.md`](reference/PROFILE_CREATION_REFERENCE.md).*
