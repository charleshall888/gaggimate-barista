# DF64V Grinder Reference

A quick reference for grind settings and adjustments on the **DF64V Gen-3 variable-speed single-dose grinder** with factory-fitted **SSP Cast Lab Sweet V3 Red Speed espresso burrs** (64 mm flat, pre-installed). For your personal grind settings that have worked well, see `grind-map.md` in the project root. Log all settings using the format in [`_NOTATION.md`](_NOTATION.md).

> **Deep dive:** Seasoning schedule, RDT/bellows workflow, commissioning, stall troubleshooting, and burr notes in [`../reference/DF64V_REFERENCE.md`](../reference/DF64V_REFERENCE.md).

---

## Adjustment System

The DF64V uses a **stepless collar** — there are no fixed macro or micro steps. Grind size is set by rotating the upper burr carrier collar; finer is clockwise (inward), coarser is counter-clockwise.

### Finding Your Zero (Chirp Point)

The DF64V is zeroed by motor-assisted chirp dialing:

1. Start the motor at your working RPM.
2. Slowly rotate the collar finer until the burrs make first contact — a faint, brief chirp or scratch.
3. Back off 1–2 marks immediately. This is your **zero reference**.
4. Log this zero date in `grind-map.md` as `zero set: YYYY-MM-DD` (see [`_NOTATION.md`](_NOTATION.md)).

Re-zero after any burr removal, reinstallation, or alignment adjustment. Prior-epoch rows in your grind map do not carry forward — see [`_NOTATION.md`](_NOTATION.md) for the superseding convention.

### Logging Your Setting

Record your grind as **`chirp + N marks`** from your current zero — this is an operator coordinate, not a micron or particle-size claim. No microns-per-mark figure exists for the DF64V's stepless collar; do not treat mark counts as absolute gap measurements.

### Espresso Start Window

For espresso, begin dialing around **chirp + 10–20 marks** from zero. This is a starting window only — your actual setting will depend on bean, dose, roast, and freshness. Dial from this range; do not assume it is a working shot.

---

## Motor Speed (RPM)

The DF64V Gen-3 is variable-speed. For espresso, the recommended operating range is approximately **1000–1200 RPM**:

- **~1000–1200 RPM** is the standard espresso window converged on by independent testers.
- **~1400 RPM** is a retailer preference reported to shift toward more body (vendor-framed; see Burr Character note below); it is not a floor or default.
- **Below ~700–800 RPM** risks a low-RPM stall with dense, light-roast beans fed all at once — this is an edge case, not a motor-torque flaw (see Deep Dive for context).

Start at **~1000–1100 RPM** and adjust if you want to experiment with body. RPM changes shift the grind distribution and may require a grind-setting re-dial; treat RPM as a coarse lever, not a fine-tuning tool.

---

## Espresso Range

For espresso with the SSP Cast V3 Red Speed, typical starting windows by roast level:

| Roast Level | Typical Start Window | Notes |
|-------------|----------------------|-------|
| Light       | chirp + 10–15 marks  | Fine end; slow target time likely needed |
| Medium      | chirp + 13–18 marks  | Standard espresso range |
| Dark        | chirp + 16–22 marks  | Coarser to avoid over-extraction |

**These are starting points only.** Actual settings depend on bean freshness (fresher = slightly coarser), dose, target ratio/time, and your current zero epoch. The DF64V with SSP Cast burrs has a reputation for a narrower-than-average dial-in window — expect to work the range methodically.

---

## Quick Adjustment Guide

Starting from a working shot, adjust grind setting by small steps:

| Problem | Adjustment | Magnitude |
|---------|------------|-----------|
| Shot too fast, tastes sour | Go finer | 1–3 marks |
| Shot too slow, tastes bitter | Go coarser | 1–3 marks |
| Large correction needed | Move several marks, then fine-tune | 5+ marks |
| Both sour and bitter | Do not adjust grind — fix puck prep (channeling) | — |

**Rule of thumb:** Adjust in small increments — 1–3 marks per change. Taste, then adjust again if needed. The stepless collar is sensitive; large sweeps overshoot easily.

---

## Burr Character Note

> **This is a tendency/vendor-framed characterisation, not a measured guarantee. Dial against your actual cup.**

The SSP Cast Lab Sweet V3 Red Speed is a **64 mm flat espresso burr**. Flat burrs tend toward clarity (distinct, separated flavours) relative to conical burrs — but this is a contested tendency, not a deterministic law (Hoffmann's blind tasting found no clean burr-shape → body/clarity correlation).

Within the SSP flat range, the **Cast** line produces **higher fines than typical low-fines flats** (such as the SSP Multipurpose). This means the "flat = clarity, less body" characterisation applies with less force here than on lower-fines flat burrs.

The **Red Speed** TiAlCN coating is vendor-described as adding body relative to the Silver Knight (DLC) variant; the vendor itself notes this is "secondary and grinder-dependent." Treat as plausible, not established.

**Practical implication:** If you want to dial body on the DF64V, the primary levers are **dose, ratio, and RPM** — not burr choice (that's fixed). Manage body via higher dose or slightly higher RPM (with the caveats above); manage clarity via lower dose or lower RPM. The cup-character details defer to your specific extraction and taste rather than the burr specification.

---

*For your personal successful settings, see `grind-map.md` in the project root. For the logging format and epoch conventions, see [`_NOTATION.md`](_NOTATION.md).*
