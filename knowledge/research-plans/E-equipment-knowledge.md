# Research Plan E: Equipment Knowledge

Hardware-specific knowledge that affects extraction.

## Research Topics

### E1. Basket Types & Effects — SIGNIFICANT

**Current:** "22g basket" in user setup. No other basket discussion.

**Gaps:** VST vs IMS vs stock Gaggia baskets, hole pattern effects on flow/channeling, ridged vs ridgeless, basket geometry (depth, taper), what "22g" actually means, upgrade recommendations, precision baskets and puck prep interaction.

**Sources:** VST docs, IMS docs, James Hoffmann basket comparisons, Barista Hustle.

### E2. Bluetooth Scale Integration — MODERATE

**Current:** Mentioned as equipment. Volumetric stop conditions documented.

**Gaps:** How predictive stop works, recommended delay value, calibration method, troubleshooting (connection, 0g reads, inconsistent stops), delay vs accuracy relationship.

### E3. Advanced Shot Styles — MINOR

**Current:** Traditional, turbo, allongé, SOUP, bloom all documented.

**Gaps:** Ristretto (only in ratio table, no profile/guidance), lungo vs allongé distinction, stepped/surfing pressure profiles, adaptive/responsive profiles.

## Execution

1. Research each topic using web search, focusing on the expert sources listed
2. Write basket knowledge to `knowledge/BASKETS.md` (new file) or a new section in `knowledge/ESPRESSO_BREWING_BASICS.md`
3. Write BT scale integration to a new section in `user-setup.md` or a standalone doc
4. Expand shot styles into `knowledge/ESPRESSO_BREWING_BASICS.md` (Shot Styles section) and add missing profiles to `knowledge/PROFILE_LIBRARY.md`
5. Add Sources sections with links to expert references

## Also Fix (No Research Needed)

1. **Natural Process Bloom profile** (`PROFILE_LIBRARY.md`): Extraction at 9 bar but `PRESSURE_GUIDE.md` says light-medium naturals = 7-8 bar. Bloom compensates +0.5-1 bar per the guide, but 9 bar still seems high.

2. **No 22g Automatic Pro profile JSON** exists, though dose-scaling formulas are documented. User has a 22g basket.

3. **User setup** missing BT scale predictive delay value.
