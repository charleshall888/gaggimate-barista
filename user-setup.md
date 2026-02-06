# User Setup

## Equipment

| Component | Details |
|-----------|---------|
| **Machine** | Gaggia Classic Pro + Gaggimate Pro |
| **Grinder** | Baratza Sette 270 (conical burr, micro-adjust) |
| **Basket** | IMS Baristapro Nanotech 22g (ridgeless) |
| **Scale** | Bookoo Themis Ultra (Bluetooth), auto-stop enabled, 200ms predictive delay |

## Workflow

- **Puck Prep**: WDT → tamp (no leveler)
- **Shot Stop**: Automatic via Bluetooth scale

## Preferences

- **Primary Drinks**: Cappuccinos, cortados, flat whites (prefers smaller milk drinks that let the coffee shine)
- **Roast Preference**: Light to medium roasts
- **Flavor Profile**: Fruity/floral notes — prefers drinks where these are prominent, not masked

## Active Coffee

| Field | Value |
|-------|-------|
| **Coffee** | Onyx Ethiopia Bochesa Anaerobic Natural |
| **Directory** | `coffees/onyx-ethiopia-bochesa` |
| **Roast Date** | January 20, 2026 |

## Bluetooth Scale & Auto-Stop

The Bookoo Themis Ultra connects to the Gaggimate Pro via Bluetooth Low Energy (BLE) for automatic shot stopping.

**Scale specs:** 2000g capacity, 0.1g resolution, sub-100ms response time, IP67 waterproof, USB-C charging, ~72 hours battery life. Modes: Weight, Flow, Ratio, Auto. Dimensions: 127mm x 112mm x 18mm.

**How predictive stop works:**
- The scale monitors real-time weight and flow rate during extraction
- When the flow rate and current weight indicate the target will be reached, the scale sends a BLE stop signal to the Gaggimate
- The **200ms predictive delay** is the time between the Gaggimate receiving the stop signal and the pump actually stopping — accounting for water already in transit through the puck and in the spout

**Calibration:**
- If shots consistently **overshoot** the target weight by >1g → increase the delay (e.g., 250ms) so the stop signal fires earlier
- If shots consistently **undershoot** the target weight → decrease the delay (e.g., 150ms) so the stop signal fires later
- Typical adjustment range: 100-300ms. Start at 200ms and adjust in 50ms increments based on results
- Higher flow rates (turbo shots) may need a higher delay value since more water is in transit at any moment

**Troubleshooting:**
- **0g reads / very low dose out:** Cup was likely removed before the scale registered final weight. Ask for actual weight
- **Connection drops:** Move scale closer to machine; avoid metal objects between scale and Gaggimate. Re-pair if persistent
- **Inconsistent stops:** Check that the scale is level and stable. Vibration from the pump can cause jitter — ensure the scale pad is dampening vibrations
- **Scale not found:** Ensure scale is awake (tap to wake) and not connected to another app (Bookoo app, Beanconqueror). Only one BLE connection at a time

## Notes

- **Dose = basket size.** With a 22g basket, dose 22g. Don't underdose. **Exception:** Dense, high-altitude light roasts with bloom profiles may need 21g to avoid screw imprint — check puck headspace.
- Light roasts benefit from higher extraction temps (93-95°C) to bring out sweetness
- Sette 270's micro-adjust is useful for fine-tuning between shots
- Gaggimate Pro enables flow profiling—useful for bloom profiles on light roasts
