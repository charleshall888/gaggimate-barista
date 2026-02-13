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

### Step 3: Load Reference Files (conditionally)

**Default: load ZERO reference files.** Steps 2 + 4 (knowledge files + inline JSON template) are sufficient for standard profiles built from library patterns. Only load a reference file when a specific trigger applies.

**Stop rule:** Load at most **2 reference files** per profile creation session.

| Reference (lines) | Load ONLY when… |
|--------------------|-----------------|
| [EXAMPLES.md](references/EXAMPLES.md) (713) | Need a JSON template for a style **not** in `coffees/` history or `PROFILE_LIBRARY.md` |
| [PUMP_AND_TRANSITIONS.md](references/PUMP_AND_TRANSITIONS.md) (406) | User asks about adaptive flow, ease-in-out transitions, or power mode |
| [STOP_CONDITIONS.md](references/STOP_CONDITIONS.md) (347) | User asks about combining multiple stop conditions or non-volumetric targets |
| [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) (454) | User reports a problem with an **existing** profile — never for new creation |
| [FLOW_VARIABLE_PRESSURE.md](references/FLOW_VARIABLE_PRESSURE.md) (173) | User specifically asks about Automatic Pro technique or flow-based variable pressure |
| [PROFILE_STRUCTURE.md](references/PROFILE_STRUCTURE.md) (166) | Almost never — `knowledge/GAGGIMATE_PROFILE_CREATION_GUIDE.md` covers the same fields |

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

**Repo first, device second.** The JSON file in `coffees/` is the source of truth. Save here BEFORE uploading to the device.

1. **Find or create** the coffee's directory: use the active coffee directory from `user-setup.md` if the profile is for the active coffee, otherwise `coffees/{roaster}-{coffee-name}/`
   - If the directory exists, use it
   - If not, create it with a minimal `README.md` (Bean Profile table with known info, empty Profiles and Tasting Notes sections)
2. **Write the profile JSON** to `coffees/{coffee-dir}/{profile-style}.json` (kebab-case, e.g., `natural-bloom.json`, `turbo.json`)
   - Overwrite existing files on update—git tracks iterations
3. **Update the Profiles table** in the coffee's `README.md` with: Profile name, Style, Temp, Pressure, Ratio, and link to the JSON file
4. **Remove `.gitkeep`** from `coffees/` if present

### Step 7: Upload to Device

After saving to repo, confirm with user then upload:

1. **Ask for confirmation**: "Profile saved to repo. Shall I upload it to your machine?"
2. **Create or update** via `manage_profile` MCP tool (action: `create` for new, `update` for existing)
3. **Verify** the upload succeeded by checking the MCP response

## Quick Reference Index

> **Note:** This is a human-readable index, not a loading instruction. See Step 3 for when to load each file.

| File | Contents |
|------|----------|
| [EXAMPLES.md](references/EXAMPLES.md) | Profile patterns & full JSON examples |
| [PUMP_AND_TRANSITIONS.md](references/PUMP_AND_TRANSITIONS.md) | Pump modes & transition types |
| [STOP_CONDITIONS.md](references/STOP_CONDITIONS.md) | Stop conditions reference |
| [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) | Profile troubleshooting |
| [FLOW_VARIABLE_PRESSURE.md](references/FLOW_VARIABLE_PRESSURE.md) | Automatic Pro flow technique |
| [PROFILE_STRUCTURE.md](references/PROFILE_STRUCTURE.md) | JSON schema & field reference |

## Output Requirements

1. **Always output complete, valid JSON** that can be directly imported
2. **Include all required fields** - don't omit any phase properties
3. **Use sensible defaults** - valve: 1, adaptive: true for most cases
4. **Add a volumetric target** on the final extraction phase (if scale available)
5. **Explain your choices** after the JSON
6. **Save to `coffees/` directory** alongside the coffee's README.md (repo first)
7. **Upload to device** via MCP after user confirms (device second)

