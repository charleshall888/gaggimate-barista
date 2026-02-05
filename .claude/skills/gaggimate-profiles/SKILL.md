---
name: gaggimate-profiles
description: Create custom espresso extraction profiles for Gaggimate-equipped machines (Gaggia Classic Pro, Gaggia Classic Evo, Rancilio Silvia). Use when designing pressure profiles, flow profiles, blooming profiles, lever simulation profiles, or helping with espresso extraction settings and troubleshooting. Also use when the user mentions Gaggimate, espresso profiles, pressure profiling, or extraction parameters.
---

# Gaggimate Profile Creation Skill

Create custom espresso extraction profiles for Gaggimate-equipped machines. Gaggimate supports **Simple** and **Pro** profile types, with Pro profiles offering pressure profiling, flow control, and complex transitions.

## When to Use This Skill

- Creating new espresso extraction profiles for Gaggimate machines
- Modifying or troubleshooting existing Gaggimate profiles
- Designing pressure profiles, flow profiles, or blooming profiles
- Helping with espresso extraction issues (channeling, over-extraction, under-extraction)
- Explaining profile concepts like pressure profiling, flow control, transitions
- Suggesting profiles for specific coffee types or roast levels

## Workflow

### Step 1: Gather Information

If not provided, ask about (or check `user-setup.md`):
- Coffee type/origin and roast level
- **Processing method** (washed, natural, anaerobic — affects target pressure)
- Dose amount (**dose = basket size** from user-setup.md; don't underdose)
- Desired output ratio (1:2 is classic)
- Flavor goals (more body, more acidity, reduce bitterness, etc.)
- Whether they have a Bluetooth scale (for volumetric stop conditions)

### Step 2: Select Profile Pattern

| Coffee Type | Temperature | Pressure | Profile Pattern |
|-------------|-------------|----------|-----------------|
| Light roasts (Ethiopia, Kenya) | 94-96°C | 8-9 bar | Bloom profile |
| Medium roasts (Colombia, Brazil) | 92-94°C | 9 bar | Classic 9-bar |
| Medium-dark (Vienna) | 90-92°C | 8-9 bar | Slight decline |
| Dark roasts (French/Italian) | 88-90°C | 7-8 bar | Low pressure with decline |
| **Anaerobic / Experimental** (any roast) | Per roast | **6-8 bar** | Bloom + lower pressure to tame ferment |

**Pressure by processing method:**
- Washed: 9 bar (clean, handles full pressure)
- Natural: 7-9 bar (lower tames fruit intensity)
- Honey: 8-9 bar (yellow closer to washed, red/black closer to natural)
- Anaerobic/Experimental: 6-8 bar (lower avoids amplifying funk)

For the full roast × processing pressure matrix and detailed reasoning, see `knowledge/PRESSURE_GUIDE.md`.

### Step 3: Load Reference Files

For complete documentation, load the appropriate reference file:

- **JSON Schema & Fields**: See [references/PROFILE_STRUCTURE.md](references/PROFILE_STRUCTURE.md)
- **Pump & Transitions**: See [references/PUMP_AND_TRANSITIONS.md](references/PUMP_AND_TRANSITIONS.md)
- **Stop Conditions**: See [references/STOP_CONDITIONS.md](references/STOP_CONDITIONS.md)
- **Complete Examples**: See [references/EXAMPLES.md](references/EXAMPLES.md)
- **Troubleshooting**: See [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md)
- **Quick Reference**: See [references/QUICK_REFERENCE.md](references/QUICK_REFERENCE.md)

### Step 4: Generate Profile JSON

Always output complete, valid JSON with ALL required fields:

```json
{
  "label": "Profile Name",
  "type": "pro",
  "description": "Optional description",
  "temperature": 93,
  "phases": [
    {
      "name": "Phase Name",
      "phase": "preinfusion|brew|decline",
      "valve": 1,
      "duration": 25,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 9, "flow": 0 },
      "targets": [{ "type": "volumetric", "operator": "gte", "value": 36 }]
    }
  ]
}
```

### Step 5: Explain the Profile

After generating JSON, explain:
- What each phase does and why
- How the profile addresses the user's flavor goals
- Any adjustments they might want to try

### Step 6: Save Profile to Repository

After explaining the profile, save it to the `coffees/` directory:

1. **Find or create** the coffee's directory: `coffees/{roaster}-{coffee-name}/`
   - If the directory exists, use it
   - If not, create it with a minimal `README.md` (Bean Profile table with known info, empty Profiles and Tasting Notes sections)
2. **Write the profile JSON** to `coffees/{coffee-dir}/{profile-style}.json` (kebab-case, e.g., `natural-bloom.json`, `turbo.json`)
   - Same JSON content that was uploaded to the device
   - Overwrite existing files on update—git tracks iterations
3. **Update the Profiles table** in the coffee's `README.md` with: Profile name, Style, Temp, Pressure, Ratio, and link to the JSON file
4. **Remove `.gitkeep`** from `coffees/` if present

## Quick Profile Patterns

### Classic 9-Bar (Medium Roasts)
```
Pre-infusion (4s, flow 3 ml/s) → Ramp (4s to 9 bar) → Hold (25s at 9 bar) → Stop at weight
```

### Bloom Profile (Light Roasts)
```
Fill (5s, flow 2.5 ml/s) → Bloom (8s, pump off) → Ramp (5s to 9 bar) → Hold (20s) → Stop at weight
```

### Lever Simulation (Any Roast)
```
Pre-infusion (5s, flow 3 ml/s) → Peak (5s to 9 bar) → Linear decline (25s to 3 bar) → Stop at weight
```

### Dark Roast Low Pressure
```
Pre-infusion (4s, flow 2.5 ml/s) → Ramp (3s to 7 bar) → Hold (25s) → Taper (4s to 4 bar)
```

## Essential Pump Modes

```json
// Pressure mode - maintain specific pressure
{ "target": "pressure", "pressure": 9, "flow": 4 }

// Flow mode - maintain specific flow rate
{ "target": "flow", "pressure": 9, "flow": 2.5 }

// Adaptive flow - auto-adjust to puck resistance
{ "target": "flow", "pressure": 9, "flow": -1 }

// Power mode (for bloom - pump off)
{ "target": "power", "pressure": 0, "flow": 0 }
```

## Essential Transition Types

| Type | Use Case |
|------|----------|
| `instant` | Phase starts, step changes |
| `linear` | Standard pressure ramps |
| `ease-in` | Gentle pre-infusion to extraction |
| `ease-out` | Tapering at end of shot |
| `ease-in-out` | Complex profiles, most natural |

## Output Requirements

1. **Always output complete, valid JSON** that can be directly imported
2. **Include all required fields** - don't omit any phase properties
3. **Use sensible defaults** - valve: 1, adaptive: true for most cases
4. **Add a volumetric target** on the final extraction phase (if scale available)
5. **Explain your choices** after the JSON
6. **Save to `coffees/` directory** alongside the coffee's README.md

## Resources

- **Documentation**: https://docs.gaggimate.eu/
- **Discord Community**: https://discord.gg/APw7rgPGPf
- **Web Interface**: http://gaggimate.local/profiles
- **GitHub**: https://github.com/jniebuhr/gaggimate
