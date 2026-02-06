# Research Plan E: Equipment Knowledge

Hardware-specific knowledge that affects extraction.

## Research Topics

### E1. Basket Types & Effects — COMPLETED

**Delivered:** `knowledge/BASKETS.md` — comprehensive guide covering stock vs precision baskets, IMS Baristapro Nanotech specs (661 holes, 0.30mm diameter, AISI 304 steel), VST comparison, ridged vs ridgeless tradeoffs, what "22g" means, basket geometry and puck physics, precision baskets and puck prep interaction. Sourced from Perfect Daily Grind, Barista Hustle, Robert McKeon Aloe data analysis, IMS/VST manufacturer specs.

### E2. Bluetooth Scale Integration — COMPLETED

**Delivered:** New section in `user-setup.md` — "Bluetooth Scale & Auto-Stop" covering Bookoo Themis Ultra specs (2000g/0.1g, IP67, BLE, sub-100ms response), predictive stop mechanism, 200ms delay calibration guide, troubleshooting (0g reads, connection drops, inconsistent stops).

### E3. Advanced Shot Styles — COMPLETED

**Delivered:** Added to `knowledge/ESPRESSO_BREWING_BASICS.md` — Ristretto subsection (pressure, grind, ratio, time, character, relationship to Classic 9-Bar profile) and Lungo vs Allongé clarification paragraph explaining the key difference (over-extraction vs engineered extended extraction).

## Also Fix (No Research Needed)

1. **Natural Process Bloom profile** — FIXED. Reduced Ramp pressure 9→8 bar, target 8.5→7.5 bar, Extract pressure 9→8 bar. Aligns with PRESSURE_GUIDE.md matrix (light-medium natural = 7-8 bar, +0.5-1 bar bloom compensation = 8 bar ceiling).

2. **22g Automatic Pro profile JSON** — FIXED. Created `knowledge/automatic-pro/profile_files/Automatic Pro vIT3_0_8 22g.json` scaled from 18g/20g pattern: Saturate Puck pumped=14, Extraction Start flow=2.2, Main Extraction volumetric=44.

3. **User setup BT scale predictive delay** — FIXED. Updated equipment table and added comprehensive BT scale section to `user-setup.md`.
