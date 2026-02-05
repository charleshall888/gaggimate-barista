# Espresso Pressure Guide

A comprehensive reference for how extraction pressure affects flavor, and how to match pressure to roast level, processing method, and shot style.

---

## Why Pressure Matters

Pressure defines espresso. At ~9 bar, water behaves fundamentally differently from gravity-driven brewing — extracting lipids, emulsified oils, and dissolved solids that would remain insoluble in pour-over or immersion methods. But 9 bar is not always optimal.

### The Physics

- **Primary puck compression** occurs at ~4 bar. Pre-infusion should stay below this to achieve proper saturation without channeling.
- **Flow rate peaks at ~9 bar.** Above this, secondary compression makes the puck denser, *reducing* flow rather than increasing it. This is why 9 bar became the standard — it's the equilibrium point between driving force and puck resistance.
- **Above ~10 bar**, secondary compression causes significant problems: uneven flow, channeling, harsh over-extraction.
- **As a shot progresses**, the puck erodes (less mass, less resistance). A fixed 9-bar profile forces increasing flow through weakening channels — this is why pressure decline is beneficial for most coffees.

→ *For channeling physics, fines migration, and prevention strategies, see `EXTRACTION_SCIENCE.md`*

### What Pressure Controls

| Higher Pressure (8-9+ bar) | Lower Pressure (5-7 bar) |
|----------------------------|--------------------------|
| More body, viscosity | More clarity, transparency |
| More crema | Less crema |
| More oils extracted | Cleaner, tea-like character |
| Risk of channeling as puck degrades | More forgiving puck prep |
| Better for dense, hard-to-extract beans | Better for soluble, easy-to-extract beans |

---

## The Comprehensive Pressure Matrix

### By Roast Level + Processing Method

This table gives **main extraction pressure** (the sustained pressure during the brew phase, after pre-infusion). Pre-infusion should always be 2-4 bar regardless of target extraction pressure.

| | **Light Roast** | **Medium Roast** | **Dark Roast** |
|---|---|---|---|
| **Washed** | 8-9 bar | 9 bar | 7-8 bar |
| **Natural** | 7-8 bar | 8-9 bar | 6-7 bar |
| **Honey (Yellow)** | 8-9 bar | 9 bar | 7-8 bar |
| **Honey (Red/Black)** | 7-8 bar | 8-9 bar | 7-8 bar |
| **Anaerobic** | 6-8 bar | 7-8 bar | 6-7 bar |
| **Carbonic Maceration** | 6-8 bar | 7-8 bar | 6-7 bar |

### Why Each Cell Makes Sense

**Roast level drives solubility:**
- Light roasts are denser, harder to extract. They can tolerate (and sometimes need) higher pressure to reach adequate extraction yield.
- Dark roasts are porous, highly soluble. They extract readily even at low pressure. Higher pressure risks pulling excessive bitter compounds (CGA lactones, phenylindanes).
- Medium roasts sit at the sweet spot where 9 bar was historically optimized.

**Processing method drives intensity and solubility:**
- **Washed** coffees have the lowest solubility — the bean must provide all flavor on its own, with no residual fruit compounds. They handle full pressure well because there's less risk of over-extracting intense fermentation flavors.
- **Natural** coffees absorbed fruit compounds during drying, making them more soluble and flavor-intense. Higher pressure extracts more of these fermentation-derived compounds, which can push the flavor from "blueberry jam" into "overripe fruit wine." Lower pressure keeps the fruit character clean and sweet.
- **Honey** coffees scale with how much mucilage was left on. Yellow honey (less mucilage) behaves closer to washed. Red/black honey (more mucilage, longer fermentation) behaves closer to natural.
- **Anaerobic/Experimental** coffees have the highest concentration of fermentation-derived compounds. These flavors are intense by design — high pressure amplifies the funk and ferment beyond pleasant levels. Lower pressure (6-8 bar) keeps the interesting flavors controlled.

---

## Pressure by Shot Style

Different shot styles use pressure differently. The target extraction pressure, profile shape, and timing all interact.

### Traditional Espresso (Fixed Pressure)

| Parameter | Value |
|-----------|-------|
| Pre-infusion | 2-4 bar, 4-8 seconds |
| Main extraction | Fixed at target (see matrix above) |
| Decline | None (or gentle taper in last 5s) |
| Ratio | 1:2 |
| Time | 25-32 seconds |

Best for: Medium roasts, washed coffees, everyday espresso. The simplest approach — reliable and consistent. For coffees that need lower pressure (naturals, anaerobics), simply set the target pressure lower.

### Blooming Espresso

| Parameter | Value |
|-----------|-------|
| Gentle fill | Flow 2 ml/s, 5-8 seconds |
| Bloom (pump off) | 0 bar, 8-15 seconds |
| Ramp to extraction | Ease-in, 3-5 seconds |
| Main extraction | 7-9 bar (per matrix), with optional decline |
| Ratio | 1:2 to 1:2.5 |
| Time | 30-40 seconds total |

Best for: Light roasts, naturals, anaerobics — any coffee where you want maximum sweetness and even saturation. The bloom phase lets the puck fully saturate and degas before pressure is applied, dramatically reducing channeling.

**Pressure note:** The bloom phase does much of the heavy lifting for controlling intensity. With a bloom, you can sometimes use slightly higher extraction pressure than the matrix suggests, because the bloom ensures even extraction. A natural light roast might handle 8 bar with a bloom but only 7 bar without one.

### Turbo Shot

| Parameter | Value |
|-----------|-------|
| Pre-wet | 5-6 bar, 2-3 seconds |
| Extraction | 5-6 bar constant flow |
| Ratio | 1:2.5 to 1:3 |
| Time | 12-20 seconds |
| Grind | Much coarser than traditional |

Best for: Light to medium roasts where you want maximum clarity and sweetness. The coarser grind + lower pressure = more uniform water distribution, less channeling, and surprisingly high extraction yields (19-22%).

**Pressure note:** Lance Hedrick and the research from Hendon et al. showed that 6-bar shots consistently achieved *higher* extraction yields than 9-bar shots at the same grind — because 9 bar causes more channeling, which creates pockets of over- and under-extraction simultaneously.

### Allongé

| Parameter | Value |
|-----------|-------|
| Pre-infusion | 2-3 bar, 5-8 seconds |
| Ramp | To 6 bar peak |
| Main extraction | Constant flow (~2-3 ml/s), pressure naturally rises then declines |
| Ratio | 1:4 to 1:5 |
| Time | 25-40 seconds |
| Grind | Slightly coarser than traditional |

Best for: Light roasts, showcasing origin character. Scott Rao reports extraction yields up to 27% with this approach — far beyond traditional espresso — delivered through even, gradual extraction rather than aggressive pressure.

**Pressure note:** The allongé uses flow control rather than pressure control. You set a constant flow rate and let pressure be a *result* of puck resistance. Pressure naturally peaks mid-shot and declines as the puck degrades — mimicking a lever machine's behavior.

### Lever Decline

| Parameter | Value |
|-----------|-------|
| Pre-infusion | 2-4 bar, 5-8 seconds |
| Peak | 8-9 bar, 3-5 seconds |
| Decline | Linear from peak to 3-5 bar over 20-30 seconds |
| Ratio | 1:2 |
| Time | 28-35 seconds |

Best for: Medium roasts, natural and honey coffees, any coffee where you want syrupy body with a clean finish. The declining pressure naturally compensates for puck degradation, preventing late-shot channeling.

**Pressure note:** Lance Hedrick considers the fixed 9-bar pump "one of the worst things to happen to espresso" — lever machines naturally declined pressure as the spring relaxed, which was actually *better* for extraction quality. The Gaggimate Pro can replicate this with a linear decline phase.

---

## Pressure's Effect on Specific Flavor Compounds

| Pressure Level | Acids | Sugars | Bitter Compounds | Oils/Body |
|----------------|-------|--------|------------------|-----------|
| **5-6 bar** | Moderate extraction | Good — long contact time compensates | Minimal — low force avoids harsh compounds | Light body, less crema |
| **7-8 bar** | Well extracted | Excellent — sweet spot for balance | Moderate — controlled | Good body, moderate crema |
| **9 bar** | Fully extracted (can be sharp on light roasts) | Good | Higher — especially late in shot as puck degrades | Full body, rich crema |
| **10+ bar** | Over-extracted acids become astringent | Masked by bitterness | Excessive — secondary puck compression forces channeling | Heavy, muddy body |

**Key insight from research:** Higher initial pressure disproportionately extracts acids early in the shot (before the puck saturates evenly). This is why washed light roasts at 9 bar can taste sharp/sour even when total extraction yield is adequate — the acids came out first and dominated the cup.

---

## Interaction With Other Variables

### Pressure + Temperature

Temperature and pressure compound each other's effects on extraction:

| Scenario | Effect | When to Use |
|----------|--------|-------------|
| High temp + high pressure | Maximum extraction — risk of harshness | Only for very dense, hard-to-extract light washed coffees |
| High temp + low pressure | Good extraction, gentler approach | Light roast anaerobics — need the temp for extraction but lower pressure to control intensity |
| Low temp + high pressure | Concentrated body, controlled extraction | Medium-dark washed coffees for milk drinks |
| Low temp + low pressure | Minimum extraction | Dark roasts — prevents bitterness on already-soluble beans |

### Pressure + Grind Size

Pressure and grind are deeply interlinked — they're two sides of the same equation:

- **Finer grind + lower pressure** = similar flow rate to coarser grind + higher pressure, but different flavor (more even extraction with finer grind at lower pressure)
- **Coarser grind + lower pressure** = turbo shot territory (fast, clear, sweet)
- **Finer grind + higher pressure** = traditional espresso (slow, rich, full body)
- **Coarser grind + higher pressure** = inconsistent (puck resistance insufficient for the pressure, leading to fast channeling)

### Pressure + Pre-Infusion Length

Research from the Decent Espresso community and Scott Rao shows:

- Longer pre-infusion (10-30 seconds) allows lower main extraction pressure to achieve equivalent or better results than short pre-infusion + high pressure.
- With a 20-second pre-infusion, extraction pressure of 6-7 bar can match or exceed the extraction yield of a 5-second pre-infusion + 9 bar.
- The bloom (pump off after fill) is the extreme version of this — maximum saturation, then moderate extraction pressure.

---

## Decision Framework: How to Pick Pressure

### Step 1: Start with the Matrix

Look up your coffee's roast level + processing method in the matrix above. This gives your target extraction pressure range.

### Step 2: Adjust for Shot Style

- **Traditional** → Use the matrix pressure directly
- **Blooming** → Can go 0.5-1 bar higher than matrix (bloom compensates)
- **Turbo** → 5-6 bar regardless of matrix (style overrides)
- **Allongé** → 6 bar peak, flow-controlled (style overrides)
- **Lever decline** → Start at matrix pressure, decline to matrix minus 4-5 bar

### Step 3: Adjust Based on Taste

| If the shot is... | Adjust pressure... | Why |
|--------------------|--------------------|-----|
| Sour/thin despite correct time | Up by 0.5-1 bar | More extraction force |
| Bitter/harsh/astringent | Down by 0.5-1 bar | Less aggressive extraction |
| Muddy/overly fermented (naturals) | Down by 1 bar | Less fermentation compound extraction |
| Flat/lacking character | Up by 0.5 bar, or try decline profile | More initial extraction, cleaner finish |
| Good balance but thin body | Up by 0.5 bar | More oils and dissolved solids |
| Good balance but too heavy | Down by 0.5 bar | Less body, more clarity |

---

## Common Misconceptions

### "Higher pressure = stronger coffee"
Wrong. Extraction strength (TDS) has more to do with contact time and ratio than pressure. A 6-bar turbo shot at 1:3 can achieve higher *extraction yield* than a 9-bar shot at 1:2.

### "Light roasts need higher pressure because they're harder to extract"
Partially true, partially misleading. Light roasts need more *total extraction* but not necessarily more *pressure*. Longer pre-infusion, bloom phases, or longer ratios can achieve this at lower pressure with better results.

### "9 bar is always correct for traditional espresso"
9 bar was optimized for medium-roast Italian blends. The specialty coffee world works with a much wider range of roasts and processing methods. 9 bar is the starting point, not the destination.

### "More pressure = more crema = better shot"
Crema is CO2 + oils emulsified by pressure. More crema doesn't mean better extraction — it just means more gas and oil in suspension. Some of the best-tasting shots (turbo, allongé) have minimal crema.

---

## Sources & Further Reading

- **Scott Rao** — Blooming espresso profiles, allongé extraction, and high-extraction-yield research (scottrao.com)
- **James Hoffmann** — "Understanding Espresso" series: pressure physics, channeling, and why puck degradation matters
- **Lance Hedrick** — Flow profiling over pressure profiling, turbo shots, and the case against fixed 9-bar extraction
- **Jonathan Gagné** — "The Physics of Filter Coffee" and espresso viscosity research (coffeeadastra.com)
- **Decent Espresso Community** — Empirical pressure profiling data across hundreds of coffees and profiles
- **Hendon et al.** — Research showing 6-bar shots achieve higher extraction yields than 9-bar at equivalent grind settings
- **Seven Miles Coffee** — Controlled experiments at 6, 9, and 12 bar showing flow rate peaks at 9 bar

---

*Pressure is one lever among many. The best shot comes from matching pressure to your specific coffee — its roast, its processing, its age — not from defaulting to a number that worked for someone else's beans.*
