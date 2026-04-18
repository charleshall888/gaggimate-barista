---
name: feedback
description: >
  Gather shot feedback, analyze extraction, recommend adjustments, and record results.
  Use when user says: "/feedback", "I just pulled a shot", "how was that", "it tasted [sour/bitter/flat/good]",
  provides a star rating, shares taste observations, or asks "what should I adjust" after a shot.
  Owns the full shot feedback loop: gathering, analysis, grind map updates, tasting notes, and drink format.
---

<command-name>feedback</command-name>

# Shot Feedback & Dialing Skill

You are gathering shot feedback, diagnosing extraction, recording results, and recommending the next adjustment.

## Always Load (every invocation)

Read these files before proceeding:
1. `user-setup.md` — active coffee, basket size, grinder
2. Active coffee's `coffees/{dir}/README.md` — recent tasting notes, profiles, bean profile
3. `knowledge/ESPRESSO_BREWING_BASICS.md` — adjustment strategies, diagnostic decision tree, 5g rule
4. `knowledge/ESPRESSO_TASTING_GUIDE.md` — sour vs bitter diagnosis, tasting methodology

## Conditionally Load

| File | When |
|------|------|
| `knowledge/PRESSURE_GUIDE.md` (152) | Feedback suggests pressure/profile style change |
| `knowledge/grinders/SETTE_270.md` (64) | User provides or asks about grind settings |
| `grind-map.md` | Grind setting provided |
| `knowledge/MILK_AND_DRINKS.md` (148) | User asks about drink format, or shot is dialed in (4+ balanced) and user has milk drink preferences |

---

## Workflow

### 1. GATHER Context

- Read `user-setup.md` → Active Coffee section
- If set: read the coffee's `coffees/{dir}/README.md` (bean profile, processing, recent tasting notes)
- If not set: ask the user what coffee they're brewing before proceeding
- **Stale check:** If roast date is 30+ days old, gently ask if user is still on this bag

### 2. COLLECT Feedback

Gather from the user (ask for what's missing):

| Field | Required | Notes |
|-------|----------|-------|
| **Rating** (1-5 stars) | Yes | Overall satisfaction |
| **Balance** (sour/balanced/bitter) | Yes | Primary extraction indicator |
| **Observations** | Yes (1+ specific note) | Body, sweetness, finish, flavor, mouthfeel |
| **Grind setting** | Ask if not offered | Important for tracking |
| **Dose in** | Ask if not offered | Should match basket size |
| **Shot ID** | Optional | From `list_recent_shots` if user doesn't provide |

**Minimum viable feedback:** Rating + balance + one specific observation.

**Weight estimation — NEVER ask the user for cup weight.** The BT scale often produces artifacts (spikes, drops to 0g, null readings). Estimate dose out from:
1. Last stable weight sample from telemetry (if shot ID available)
2. `total_volume_ml × 0.82` (puck absorption estimate)
3. User's stated ratio × dose in

A +/-2g estimate is fine for diagnosis and recording.

### 3. ANALYZE & RECOMMEND

Use the loaded knowledge files (BREWING_BASICS + TASTING_GUIDE) to diagnose and recommend.

**Adjustment hierarchy** — adjust in this order:
1. **Grind size** — largest effect on extraction
2. **Yield/Ratio** — quick correction (5g rule)
3. **Temperature** — fine-tuning after grind is close
4. **Pressure/Profile** — style change or enhancement
5. **Puck prep** — channeling, inconsistency

**Critical diagnostic rules:**

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Sour + fast (<20s) | Under-extracted, grind too coarse | Grind finer |
| Sour + normal time | Under-extracted at correct flow | Increase yield by 5g, then temp |
| Sour + slow (>35s) | Channeling likely | Better puck prep, longer pre-infusion |
| Bitter + slow (>35s) | Over-extracted, grind too fine | Grind coarser |
| Bitter + normal time | Over-extracted at correct flow | Decrease yield by 5g, then temp |
| **Sour AND bitter** | **Channeling** — uneven extraction | **Fix puck prep (WDT, distribution, even tamp). NOT grind.** |
| Balanced but flat | Under-developed | Increase temp 1°C, or try longer ratio |
| Balanced but thin | Low body | Shorter ratio, or finer grind |

**The "sour AND bitter" rule (Scott Rao):** When a shot tastes both sour and bitter simultaneously, water is finding paths of least resistance — over-extracting some grounds while under-extracting others. The fix is puck prep, not grind. Grinding finer when channeling is present makes it worse.

Always explain *why* you're suggesting a change. One primary recommendation, one backup.

### 4. RECORD (silent, no confirmation needed)

Do all of these automatically after feedback is collected:

#### 4a. Tasting Notes → Coffee README

Append a row to the Tasting Notes table in the active coffee's `README.md`:

| # | Date | Shot | Grind | In/Out | Ratio | Profile | Balance | Stars | Observations |
|---|------|------|-------|--------|-------|---------|---------|-------|--------------|

- **#**: Sequential shot number for this coffee
- **Date**: Compact format (e.g., Feb 12)
- **Shot**: Gaggimate shot ID (6-digit, for `/diagnose` cross-reference)
- **In/Out**: Dose in/out as "22/48g"
- **Ratio**: Actual ratio as 1:X.X
- **Profile**: Short profile style name (matches Profiles table)
- **Balance**: Sour / Balanced / Bitter
- **Observations**: Brief sensory notes (5-10 words)

#### 4b. Grind Map → grind-map.md

**Trigger conditions** (all must be true):
- Grind setting was provided
- Coffee information is known

The Rating column records whether the shot worked — low-rated rows are diagnostic data, not noise.

**Update process:**
1. Read current `grind-map.md`
2. Append new row: Coffee, Roast, Process, Origin, Days Off Roast, Grind, Profile, Ratio, Temp, Rating, Date
3. **Grind notation:** Full Sette 270 format: macro + micro letter (e.g., "9D", "10M", "11A")

#### 4c. Shot Notes → Device

If a shot ID is available, sync feedback to the device:
```
manage_shot_notes(shot_id, action="update", rating=X, balance_taste="...", notes="...", grind_setting="...", dose_in=X, dose_out=X)
```

#### 4d. Profile Updates

If a profile was modified based on feedback, overwrite the JSON file in the coffee directory.

#### 4e. Private Repo Commit

1. Read `.data-repo-path` at the project root.
   - If absent: skip silently (user has no private repo — this is expected for new setups).
   - If present: proceed.
2. Run as separate Bash calls (no chaining, no `git -C`), substituting `{private_repo}` with the path from `.data-repo-path`:
   - `git --git-dir={private_repo}/.git --work-tree={private_repo} add -A`
   - `git --git-dir={private_repo}/.git --work-tree={private_repo} commit -m "feedback: shot {shot_id} — {rating}★ {balance}"`
   - `git --git-dir={private_repo}/.git --work-tree={private_repo} push`
3. If push fails: inform the user — "Private repo push failed — changes saved locally. Run `git push` manually in `{private_repo_path}` when credentials are available."

### 5. SUGGEST Next Steps

Based on the analysis:

**If still dialing in (rating < 4 or not balanced):**
- State the specific change for the next shot
- Explain what to watch for ("Time to first drip should increase" / "Look for more body")

**If dialed in (rating 4+ AND balanced):**
- Celebrate briefly
- Recommend a drink format based on shot character:

| Shot Character | Recommended Format |
|----------------|-------------------|
| Bright, fruity, delicate | Cortado or piccolo |
| Sweet, balanced, medium body | Cappuccino or flat white |
| Intense, heavy body | Latte |
| Clarity-focused, tea-like | Cortado or piccolo |

**Core principle:** Extract for the bean's best expression first, then match the drink format. Never adjust grind/ratio/pressure/temp to "make the shot work in milk."

If user wants full milk science, steaming technique, or drink recipes → load `knowledge/MILK_AND_DRINKS.md`.

---

## Integration with Other Skills

- For deeper shot telemetry analysis → suggest `/diagnose`
- For profile modifications → suggest `/gaggimate-profiles`
- For a new coffee → suggest `/new-coffee`

---

## Quick Reference

**User says:** "3 stars, sour, 14E grind, 22g in"
**Action:** Load context → record → diagnose (sour = extract more) → recommend grind/yield change → update tasting notes + grind map + shot notes

**User says:** "5 stars, balanced, amazing sweetness"
**Action:** Load context → celebrate → record to grind map + tasting notes → recommend drink format

**User says:** "it was sour AND bitter"
**Action:** Load context → diagnose **channeling** (from BREWING_BASICS line 129) → recommend puck prep fix, NOT grind change → record
