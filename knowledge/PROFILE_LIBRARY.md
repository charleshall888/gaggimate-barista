# Profile Library

Ready-to-use extraction profiles for Gaggimate Pro. Each profile includes complete JSON, recommended parameters, and flavor expectations. These are **generic templates** — coffee-specific profiles created during dialing are saved in `coffees/{roaster}-{coffee-name}/` alongside the coffee's research and tasting notes.

For technical details on profile structure, see `GAGGIMATE_PROFILE_CREATION_GUIDE.md`.

---

## Quick Reference

| Profile | Roast | Temp | Ratio | Time | Best For |
|---------|-------|------|-------|------|----------|
| [Classic 9-Bar](#classic-9-bar) | Medium | 93°C | 1:2 | 25-32s | Everyday espresso |
| [Light Roast Bloom](#light-roast-bloom) | Light | 95°C | 1:2.5 | 28-35s | Fruity, floral coffees |
| [Dark Roast Gentle](#dark-roast-gentle) | Dark | 89°C | 1:1.5-2 | 22-28s | Italian roasts, milk drinks |
| [Natural Process Bloom](#natural-process-bloom) | Light-Med | 94°C | 1:2-2.5 | 30-38s | Natural/dry processed beans |
| [Turbo Shot](#turbo-shot) | Any | 96°C | 1:2.5-3 | 15-20s | Clarity, brightness |
| [Allongé](#allongé) | Light-Med | 94°C | 1:4-5 | 40-50s | Long, sweet, tea-like |
| [Lever Decline](#lever-decline) | Medium | 91°C | 1:2 | 28-35s | Syrupy body, complex |
| [Milk Drink Base](#milk-drink-base) | Med-Dark | 92°C | 1:1.5 | 22-26s | Concentrated, intense body |

---

## Profiles by Roast Level

### Light Roast

#### Light Roast Bloom

Designed for Nordic-style light roasts that need high extraction and benefit from a bloom phase to enhance sweetness and reduce sourness.

**When to use:** Ethiopian naturals, Kenyan AA, light-roasted Gesha, fruit-forward single origins

**Parameters:**
- Temperature: 95°C
- Ratio: 1:2.5 (18g → 45g)
- Expected time: 28-35 seconds
- Grind: Finer than medium roast settings

**Flavor expectations:** Bright acidity, floral notes, stone fruit sweetness, tea-like body

```json
{
  "label": "Light Roast Bloom [AI]",
  "type": "pro",
  "description": "High-temp bloom profile for light roasts - enhanced sweetness and fruit notes",
  "temperature": 95,
  "phases": [
    {
      "name": "Gentle Fill",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 6,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "flow", "pressure": 9, "flow": 2 }
    },
    {
      "name": "Bloom",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 8,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "power", "pressure": 0, "flow": 0 }
    },
    {
      "name": "Ramp",
      "phase": "brew",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": { "type": "ease-in", "duration": 4, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 9, "flow": 0 },
      "targets": [{ "type": "pressure", "operator": "gte", "value": 8.5 }]
    },
    {
      "name": "Extract",
      "phase": "brew",
      "valve": 1,
      "duration": 25,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 9, "flow": 4 },
      "targets": [{ "type": "volumetric", "operator": "gte", "value": 45 }]
    }
  ]
}
```

---

### Medium Roast

#### Classic 9-Bar

The reliable workhorse. A straightforward pre-infusion → ramp → hold pattern that works for most medium roasts.

**When to use:** Colombian, Brazilian, Central American coffees, any "everyday" medium roast

**Parameters:**
- Temperature: 93°C
- Ratio: 1:2 (18g → 36g)
- Expected time: 25-32 seconds
- Grind: Standard espresso

**Flavor expectations:** Balanced, chocolate notes, mild sweetness, medium body

```json
{
  "label": "Classic 9-Bar [AI]",
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
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "flow", "pressure": 9, "flow": 3 }
    },
    {
      "name": "Ramp",
      "phase": "brew",
      "valve": 1,
      "duration": 4,
      "temperature": 0,
      "transition": { "type": "linear", "duration": 3, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 9, "flow": 0 },
      "targets": [{ "type": "pressure", "operator": "gte", "value": 8.5 }]
    },
    {
      "name": "Hold",
      "phase": "brew",
      "valve": 1,
      "duration": 25,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 9, "flow": 4 },
      "targets": [{ "type": "volumetric", "operator": "gte", "value": 36 }]
    }
  ]
}
```

#### Lever Decline

Mimics a spring lever machine with declining pressure throughout extraction. Creates syrupy body and complex sweetness.

**When to use:** Medium roasts where you want more body and sweetness, chocolate-forward beans

**Parameters:**
- Temperature: 91°C
- Ratio: 1:2 (18g → 36g)
- Expected time: 28-35 seconds
- Grind: Slightly finer than classic

**Flavor expectations:** Syrupy body, caramel sweetness, reduced acidity, complex finish

```json
{
  "label": "Lever Decline [AI]",
  "type": "pro",
  "description": "Spring lever-style declining pressure for syrupy body",
  "temperature": 91,
  "phases": [
    {
      "name": "Pre-infusion",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "flow", "pressure": 9, "flow": 3 }
    },
    {
      "name": "Peak",
      "phase": "brew",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": { "type": "linear", "duration": 3, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 9, "flow": 0 },
      "targets": [{ "type": "pressure", "operator": "gte", "value": 8.5 }]
    },
    {
      "name": "Decline",
      "phase": "brew",
      "valve": 1,
      "duration": 30,
      "temperature": 0,
      "transition": { "type": "linear", "duration": 25, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 3, "flow": 0 },
      "targets": [{ "type": "volumetric", "operator": "gte", "value": 36 }]
    }
  ]
}
```

---

### Dark Roast

#### Dark Roast Gentle

Lower temperature and pressure to avoid over-extraction bitterness. Shorter ratio emphasizes body over acidity.

**When to use:** Italian roasts, French roasts, espresso blends intended for milk drinks

**Parameters:**
- Temperature: 89°C
- Ratio: 1:1.5-2 (18g → 27-36g)
- Expected time: 22-28 seconds
- Grind: Coarser than medium roast settings

**Flavor expectations:** Chocolate, caramel, low acidity, full body, no bitterness

```json
{
  "label": "Dark Roast Gentle [AI]",
  "type": "pro",
  "description": "Low temp, lower pressure for dark roasts - avoids bitterness",
  "temperature": 89,
  "phases": [
    {
      "name": "Pre-infusion",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 4,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "flow", "pressure": 8, "flow": 2.5 }
    },
    {
      "name": "Ramp",
      "phase": "brew",
      "valve": 1,
      "duration": 4,
      "temperature": 0,
      "transition": { "type": "ease-in", "duration": 3, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 7.5, "flow": 0 },
      "targets": [{ "type": "pressure", "operator": "gte", "value": 7 }]
    },
    {
      "name": "Hold",
      "phase": "brew",
      "valve": 1,
      "duration": 20,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 7.5, "flow": 4 },
      "targets": [{ "type": "volumetric", "operator": "gte", "value": 32 }]
    },
    {
      "name": "Taper",
      "phase": "decline",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": { "type": "ease-out", "duration": 4, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 5, "flow": 0 }
    }
  ]
}
```

---

## Profiles by Processing Method

### Natural/Dry Process

#### Natural Process Bloom

Extended bloom phase helps tame the intensity of natural process coffees while preserving their fruit-forward character.

**When to use:** Ethiopian naturals, Brazilian naturals, any dry-processed coffee with funky/fermented notes

**Parameters:**
- Temperature: 94°C
- Ratio: 1:2-2.5 (18g → 36-45g)
- Expected time: 30-38 seconds
- Grind: Medium-fine, err toward finer

**Flavor expectations:** Blueberry, strawberry, wine-like, controlled ferment funk, juicy body

```json
{
  "label": "Natural Process Bloom [AI]",
  "type": "pro",
  "description": "Extended bloom for natural process coffees - controls intensity, preserves fruit",
  "temperature": 94,
  "phases": [
    {
      "name": "Gentle Fill",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 6,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "flow", "pressure": 9, "flow": 2 }
    },
    {
      "name": "Bloom",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 10,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "power", "pressure": 0, "flow": 0 }
    },
    {
      "name": "Ramp",
      "phase": "brew",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": { "type": "ease-in-out", "duration": 4, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 9, "flow": 0 },
      "targets": [{ "type": "pressure", "operator": "gte", "value": 8.5 }]
    },
    {
      "name": "Extract",
      "phase": "brew",
      "valve": 1,
      "duration": 25,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 9, "flow": 4 },
      "targets": [{ "type": "volumetric", "operator": "gte", "value": 40 }]
    },
    {
      "name": "Taper",
      "phase": "decline",
      "valve": 1,
      "duration": 6,
      "temperature": 0,
      "transition": { "type": "linear", "duration": 5, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 5, "flow": 0 }
    }
  ]
}
```

---

## Profiles by Shot Style

### Turbo Shot

#### Turbo Shot

Coarse grind, high flow, fast extraction. Emphasizes clarity and brightness over body. Originally popularized by the specialty coffee competition circuit.

**When to use:** Showcasing origin character, light roasts, when you want tea-like clarity

**Parameters:**
- Temperature: 96°C (high temp compensates for short contact time)
- Ratio: 1:2.5-1:3 (18g → 45-54g)
- Expected time: 15-20 seconds (yes, really)
- Grind: Significantly coarser than normal espresso

**Flavor expectations:** Bright, clean, tea-like, clarity of origin flavors, lighter body

**Note:** Requires coarser grind than typical espresso. Expect 2-4 macro steps coarser on most grinders. The longer ratio is essential — with a coarse grind and short contact time, you need more water volume to achieve adequate extraction. A 1:2 turbo will be sour and under-extracted.

**Milk drink note:** Turbo shots have lighter body and higher volume, which can get lost in large milk drinks. If you want turbo clarity in milk, pair with a cortado, piccolo, or flat white rather than a full latte.

```json
{
  "label": "Turbo Shot [AI]",
  "type": "pro",
  "description": "Fast, high-flow extraction for clarity - requires coarse grind",
  "temperature": 96,
  "phases": [
    {
      "name": "Pre-wet",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 3,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "flow", "pressure": 6, "flow": 5 }
    },
    {
      "name": "Extract",
      "phase": "brew",
      "valve": 1,
      "duration": 20,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "flow", "pressure": 6, "flow": 4.5 },
      "targets": [{ "type": "volumetric", "operator": "gte", "value": 54 }]
    }
  ]
}
```

### Allongé

#### Allongé

A long, sweet extraction at extended ratios. Not a lungo (which is just more water) but a true extended extraction that develops sweetness.

**When to use:** Light to medium roasts, when you want a longer, sweeter drink without adding water

**Parameters:**
- Temperature: 94°C
- Ratio: 1:4-5 (18g → 72-90g)
- Expected time: 40-50 seconds
- Grind: Slightly coarser than standard

**Flavor expectations:** Sweet, tea-like, delicate acidity, approachable, long finish

```json
{
  "label": "Allongé [AI]",
  "type": "pro",
  "description": "Long sweet extraction at 1:4-5 ratio - tea-like and approachable",
  "temperature": 94,
  "phases": [
    {
      "name": "Pre-infusion",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "flow", "pressure": 9, "flow": 2.5 }
    },
    {
      "name": "Ramp",
      "phase": "brew",
      "valve": 1,
      "duration": 5,
      "temperature": 0,
      "transition": { "type": "linear", "duration": 4, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 6, "flow": 0 },
      "targets": [{ "type": "pressure", "operator": "gte", "value": 5.5 }]
    },
    {
      "name": "Extract",
      "phase": "brew",
      "valve": 1,
      "duration": 50,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 6, "flow": 4 },
      "targets": [{ "type": "volumetric", "operator": "gte", "value": 80 }]
    }
  ]
}
```

---

## Specialty Profiles

### Milk Drinks

#### Milk Drink Base

A punchy, concentrated shot with high intensity and full body. The shorter ratio emphasizes
sweetness and body over clarity.

**When to use:** When you want maximum intensity — works great as a ristretto-style shot or
as a base for larger milk drinks where you want the coffee to remain prominent

**Parameters:**
- Temperature: 92°C
- Ratio: 1:1.5 (18g → 27g)
- Expected time: 22-26 seconds
- Grind: Standard to slightly finer

**Flavor expectations:** Intense, punchy, chocolate/caramel forward, full body

```json
{
  "label": "Milk Drink Base [AI]",
  "type": "pro",
  "description": "Concentrated ristretto-style shot - maximum intensity at 1:1.5 ratio",
  "temperature": 92,
  "phases": [
    {
      "name": "Pre-infusion",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 4,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "flow", "pressure": 9, "flow": 3 }
    },
    {
      "name": "Ramp",
      "phase": "brew",
      "valve": 1,
      "duration": 4,
      "temperature": 0,
      "transition": { "type": "linear", "duration": 3, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 9, "flow": 0 },
      "targets": [{ "type": "pressure", "operator": "gte", "value": 8.5 }]
    },
    {
      "name": "Hold",
      "phase": "brew",
      "valve": 1,
      "duration": 20,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 9, "flow": 4 },
      "targets": [{ "type": "volumetric", "operator": "gte", "value": 27 }]
    }
  ]
}
```

---

## Flow-Based Profiles

### Automatic Pro v2

A self-regulating profile that adapts to your grind. Uses flow targeting with pressure ceiling to automatically adjust extraction.

**When to use:** When you want consistency across different coffees without constant profile adjustment

**Parameters:**
- Temperature: 91°C
- Ratio: 1:2 (18g → 36g)
- Expected time: 25-35 seconds (varies with grind)
- Grind: More forgiving than pressure-based profiles

**Flavor expectations:** Balanced, consistent, adapts to bean characteristics

See `GAGGIMATE_PROFILE_CREATION_GUIDE.md` for dose-scaling formulas and the complete profile.

---

## Profile Selection Guide

### By Taste Goal

| Want More... | Try This Profile | Key Change |
|--------------|------------------|------------|
| Brightness/acidity | Light Roast Bloom | Higher temp, longer ratio |
| Sweetness | Lever Decline or Natural Process Bloom | Bloom phase, declining pressure |
| Body | Dark Roast Gentle | Lower temp, shorter ratio |
| Clarity | Turbo Shot | Coarse grind, high flow |
| Balance | Classic 9-Bar | Standard parameters |

### By Problem

| Issue | Profile Suggestion | Why |
|-------|-------------------|-----|
| Shots too sour | Light Roast Bloom | Higher temp, bloom for better extraction |
| Shots too bitter | Dark Roast Gentle | Lower temp/pressure, taper at end |
| Want more intensity | Milk Drink Base | Shorter ratio concentrates flavor |
| Inconsistent | Automatic Pro v2 | Self-regulating flow control |
| Channeling | Natural Process Bloom | Extended pre-infusion, gentle fill |

---

*All profiles marked [AI] were created by your barista assistant and can be safely deleted via the MCP tools.*
