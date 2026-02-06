---
name: gaggimate-profiles
description: Create custom espresso extraction profiles for Gaggimate-equipped machines (Gaggia Classic Pro, Gaggia Classic Evo, Rancilio Silvia). Use when designing pressure profiles, flow profiles, blooming profiles, lever simulation profiles, or helping with espresso extraction settings and troubleshooting. Also use when the user mentions Gaggimate, espresso profiles, pressure profiling, or extraction parameters.
---

# Gaggimate Profile Creation Skill

Create custom espresso extraction profiles for Gaggimate-equipped machines. Gaggimate supports **Simple** and **Pro** profile types, with Pro profiles offering pressure profiling, flow control, and complex transitions.

## Workflow

### Step 1: Gather Information

If not provided, check `user-setup.md` (including Active Coffee section) and the coffee's `README.md`. Ask about anything still missing:
- Coffee type/origin and roast level
- **Processing method** (washed, natural, anaerobic — affects target pressure)
- Dose amount (**dose = basket size** from user-setup.md; don't underdose)
- Desired output ratio (1:2 is classic)
- Flavor goals (more body, more acidity, reduce bitterness, etc.)
- Whether they have a Bluetooth scale (for volumetric stop conditions)

### Step 2: Select Profile Pattern

Consult these knowledge files to determine settings:
- **Temperature**: `knowledge/ESPRESSO_BREWING_BASICS.md` → "Temperature Guidelines by Roast"
- **Pressure**: `knowledge/PRESSURE_GUIDE.md` → roast × processing matrix
- **Profile pattern**: `knowledge/PROFILE_LIBRARY.md` → select by roast, process, and style

### Step 3: Load Reference Files

For complete documentation, load the appropriate reference file:

- **JSON Schema & Fields**: See [references/PROFILE_STRUCTURE.md](references/PROFILE_STRUCTURE.md)
- **Pump & Transitions**: See [references/PUMP_AND_TRANSITIONS.md](references/PUMP_AND_TRANSITIONS.md)
- **Stop Conditions**: See [references/STOP_CONDITIONS.md](references/STOP_CONDITIONS.md)
- **Complete Examples**: See [references/EXAMPLES.md](references/EXAMPLES.md)
- **Troubleshooting**: See [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md)

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

**Volumetric target:** Always set to `dose × ratio` using the user's basket size from `user-setup.md`. Library profiles in `PROFILE_LIBRARY.md` are sized for 22g.

### Step 5: Explain the Profile

After generating JSON, explain:
- What each phase does and why
- How the profile addresses the user's flavor goals
- Any adjustments they might want to try

### Step 6: Save Profile to Repository

After explaining the profile, save it to the `coffees/` directory:

1. **Find or create** the coffee's directory: use the active coffee directory from `user-setup.md` if the profile is for the active coffee, otherwise `coffees/{roaster}-{coffee-name}/`
   - If the directory exists, use it
   - If not, create it with a minimal `README.md` (Bean Profile table with known info, empty Profiles and Tasting Notes sections)
2. **Write the profile JSON** to `coffees/{coffee-dir}/{profile-style}.json` (kebab-case, e.g., `natural-bloom.json`, `turbo.json`)
   - Same JSON content that was uploaded to the device
   - Overwrite existing files on update—git tracks iterations
3. **Update the Profiles table** in the coffee's `README.md` with: Profile name, Style, Temp, Pressure, Ratio, and link to the JSON file
4. **Remove `.gitkeep`** from `coffees/` if present

## Quick Reference

For detailed documentation beyond the workflow above:
- **Profile patterns & full JSON examples**: [references/EXAMPLES.md](references/EXAMPLES.md)
- **Pump modes & transition types**: [references/PUMP_AND_TRANSITIONS.md](references/PUMP_AND_TRANSITIONS.md)
- **Stop conditions**: [references/STOP_CONDITIONS.md](references/STOP_CONDITIONS.md)
- **Troubleshooting**: [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md)

## Output Requirements

1. **Always output complete, valid JSON** that can be directly imported
2. **Include all required fields** - don't omit any phase properties
3. **Use sensible defaults** - valve: 1, adaptive: true for most cases
4. **Add a volumetric target** on the final extraction phase (if scale available)
5. **Explain your choices** after the JSON
6. **Save to `coffees/` directory** alongside the coffee's README.md

