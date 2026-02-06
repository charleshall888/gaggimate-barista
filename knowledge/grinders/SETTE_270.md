# Baratza Sette 270 Grinder Reference

A static reference for grinder mechanics, calibration, and maintenance. For your personal grind settings that have worked well, see the dynamic `grind-map.md` in the project root.

---

## Adjustment System

The Sette 270 uses a **macro + micro** adjustment system:

### Macro Adjustment (Ring)
- Numbers 1-31 on the outer ring
- Lower numbers = finer grind
- Each step is approximately 75-100 microns

### Micro Adjustment (Lever)
- Letters A-Q (17 steps) between each macro number
- A = finest within that macro setting
- Q = coarsest within that macro setting
- Each micro step is approximately 4-6 microns

### Reading Your Setting

Settings are written as **[Macro Number][Micro Letter]**:
- `9D` = Macro 9, Micro D (toward fine end of macro 9)
- `10M` = Macro 10, Micro M (middle of macro 10)
- `11A` = Macro 11, Micro A (finest setting within macro 11)

### Espresso Range

For espresso, you'll typically be in the **8-14** macro range:

| Roast Level | Typical Range | Notes |
|-------------|---------------|-------|
| Light | 8-10 | Needs finer to slow extraction |
| Medium | 9-12 | Standard espresso range |
| Dark | 11-14 | Coarser to avoid over-extraction |

**Important:** These are starting points. Your actual settings depend on:
- Bean freshness (fresher = coarser)
- Humidity (higher = finer)
- Dose size
- Target ratio and time

---

## Single-Dosing Tips

The Sette 270 wasn't designed for single-dosing but works reasonably well with some adjustments:

### Retention
- Typical retention: ~0.5g
- First shot of the day: Purge 1-2g to clear stale grounds
- Between shots: Brief purge if changing beans

### Popcorning Prevention
- Popcorning = beans bouncing in hopper, inconsistent feed
- Mitigation options:
  1. **Bellows attachment**: Aftermarket bellows push beans down
  2. **Gentle tapping**: Tap hopper during grinding
  3. **Weight on beans**: Use a small weight or puck on top of beans

### Workflow for Single-Dosing

1. Weigh beans (dose + 0.5g for retention)
2. Place in hopper
3. Grind until hopper empties
4. Brief pulse to clear chute
5. WDT to break clumps
6. Weigh output, adjust dose if needed

---

## Clumping and Static

The Sette produces moderate clumps and static, especially in dry conditions.

### Clump Management
- **WDT is essential**: Use a distribution tool to break clumps before tamping
- Clumps are more pronounced with:
  - Fresh (high CO2) beans
  - Light roasts
  - Dry/low humidity environments

### Static Reduction

1. **RDT (Ross Droplet Technique)**
   - Add 1-2 drops of water to beans before grinding
   - Spray bottle or wet finger works
   - Significantly reduces static cling

2. **Humidity**
   - Higher ambient humidity = less static
   - Some users keep a damp towel near the grinder

3. **Grounds container**
   - Metal or glass catches grounds better than plastic
   - Ground to portafilter adapters help

---

## Calibration

### When to Calibrate

Recalibrate if:
- Grind setting that used to work is suddenly too coarse/fine
- You've disassembled the grinder for cleaning
- Burrs have been replaced

### Calibration Process

1. Set macro ring to 9
2. Remove hopper and upper burr carrier
3. Look for calibration marks inside
4. Adjust the calibration ring (requires tool) until marks align
5. Reassemble and test

**Note:** Minor drift is normal over time. If shots are running fast, try going 1-2 micro steps finer before recalibrating.

---

## Maintenance Schedule

### Daily
- Brush loose grounds from chute
- Empty catch container

### Weekly
- Remove upper burr, brush out fines
- Wipe exterior
- Check for grounds in adjustment mechanism

### Monthly
- Deep clean upper burr assembly
- Vacuum lower burr chamber (careful not to touch burrs)
- Inspect burrs for wear

### Annually (or every ~500kg of coffee)
- Replace burrs
- Full disassembly and cleaning
- Check motor brushes (if applicable)

---

## Burr Wear Indicators

Replace burrs when you notice:
- Increased fines/clumping even after cleaning
- Need to grind significantly finer than before
- Grind time has increased noticeably
- Visible wear on cutting edges (requires inspection)

Typical burr life: 500-1000 kg of coffee, depending on roast level (darker roasts are softer, less wear).

---

## Common Issues

### Grinder Won't Start
- Check hopper is seated (safety interlock)
- Check power connection
- Let motor cool if overheated (rare with single-dosing)

### Inconsistent Particle Size
- Clean burrs thoroughly
- Check for calibration drift
- Verify beans aren't bouncing (popcorning)
- Consider burr replacement if cleaning doesn't help

### Motor Noise/Strain
- Grind too fine for flow rate
- Foreign object in burrs (check for stones)
- Motor bearing wear (requires service)

### Grounds Everywhere
- Static buildup (try RDT)
- Chute clog (clean chute path)
- Seal wear on upper burr carrier

---

## Sette 270 vs 270Wi

The **270Wi** adds a built-in scale that weighs output in real-time. For single-dosing espresso, this is helpful but not essential since you're dosing by input weight.

Key differences:
- 270Wi stops automatically at target weight
- Useful for cafe workflow, less critical for single-dosing
- Standard 270 works fine with a separate scale

---

## Quick Adjustment Guide

Starting from a working shot:

| Problem | Adjustment | Magnitude |
|---------|------------|-----------|
| Shot too fast, sour | Go finer | 1-2 micro steps |
| Shot too slow, bitter | Go coarser | 1-2 micro steps |
| Big change needed | Move macro | 1 macro number |
| Fine-tuning | Use micro | A-Q within macro |

**Rule of thumb:** Start with micro adjustments. Only move macro if you're more than 5-6 micro steps from your target.

---

*For your personal successful settings, see `grind-map.md` in the project root.*
