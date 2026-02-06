# Diagnostic Decision Trees

Taste-based decision trees for diagnosing espresso extraction issues. All thresholds are **relative to the identified shot style** — load expected ranges from `knowledge/PRESSURE_GUIDE.md` and `knowledge/PROFILE_LIBRARY.md`.

---

## SOUR Shot Diagnosis

```
SOUR (under-extracted)
├── Time to first drip below style's expected minimum?
│   ├── YES → Channeling or too coarse
│   │   ├── Pressure spike >1.5 bar above style target? → Channeling (fines migration)
│   │   │   └── FIX: Improve puck prep (WDT), check distribution
│   │   └── Pressure below style's expected range? → Too coarse
│   │       └── FIX: Grind 1-2 steps finer
│   └── NO → Continue...
├── Flow rate above style's expected range?
│   └── YES → Resistance too low for this style
│       └── FIX: Grind finer, check dose (may need +0.5g)
├── Temperature < target by >2°C?
│   └── YES → Equipment issue (not fully heated)
│       └── FIX: Longer warm-up, flush before shot
├── Preinfusion shorter than profile specifies?
│   └── YES → Insufficient saturation
│       └── FIX: Extend preinfusion phase in profile
└── None of above?
    └── Extraction time within style range but sour?
        └── FIX: Increase temperature +1-2°C, or grind finer
```

## BITTER Shot Diagnosis

```
BITTER (over-extracted)
├── Total time well above style's expected range?
│   └── YES → Over-extracted (too much contact time)
│       └── FIX: Grind coarser, or reduce ratio
├── Temperature > target by >2°C?
│   └── YES → Running hot
│       └── FIX: Reduce brew temp -2°C, check PID calibration
├── Pressure sustained above style's target through extraction?
│   └── YES → Aggressive extraction
│       └── FIX: Use declining pressure profile, or lower target pressure
├── Flow rate well below style's expected range for extended period?
│   └── YES → Choked flow, prolonged contact
│       └── FIX: Grind coarser, reduce dose -0.5g
└── None of above?
    └── May be bean-related (dark roast, over-roasted)
        └── FIX: Lower temp, shorter ratio, declining pressure
```

## FLAT/MUTED Shot Diagnosis

```
FLAT (lacks vibrancy, dull)
├── Temperature drifting >2°C during shot?
│   └── YES → Thermal instability
│       └── FIX: Better pre-heating, temperature surfing
├── Preinfusion shorter than profile specifies or skipped?
│   └── YES → Poor saturation, uneven extraction
│       └── FIX: Add proper preinfusion phase, or extend existing one
├── Beans > 4 weeks from roast?
│   └── YES → Stale, CO2 depleted
│       └── FIX: Fresh beans; compensate with higher temp, finer grind
├── Extraction time well below style's expected range?
│   └── YES → Under-developed, too fast
│       └── FIX: Grind finer, extend extraction
└── None of above?
    └── May need more extraction
        └── FIX: Higher temp +1-2°C, longer ratio, consider bloom phase
```

## INCONSISTENT Shots Diagnosis

When user reports shot-to-shot variance:

```
INCONSISTENT (variable results)
├── Compare multiple shots via list_recent_shots
├── Check for patterns:
│   ├── Time to first drip varies >3s between shots?
│   │   └── YES → Puck prep inconsistency
│   │       └── FIX: Standardize WDT, distribution, tamping
│   ├── Pressure curves differ significantly?
│   │   └── YES → Grind retention or distribution issues
│   │       └── FIX: Purge grinder, single-dose, better WDT
│   ├── Temperature varies >1.5°C between shots?
│   │   └── YES → Machine thermal management
│   │       └── FIX: Consistent wait time between shots, flush routine
│   └── Flow patterns different?
│       └── YES → Channeling (random), check basket prep
└── Document which variables are changing for pattern recognition
```
