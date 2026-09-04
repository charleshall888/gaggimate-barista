---
name: shot-feedback
description: >
  Gather shot feedback, analyze extraction, recommend adjustments, and record results.
  Use when user says: "/shot-feedback", "I just pulled a shot", "how was that", "it tasted [sour/bitter/flat/good]",
  provides a star rating, shares taste observations, or asks "what should I adjust" after a shot.
  Owns the full shot feedback loop: gathering, analysis, grind map updates, tasting notes, and drink format.
---

<command-name>shot-feedback</command-name>

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
| Active grinder reference resolved per the Active Grinder field parsing contract → `knowledge/grinders/` file | User provides or asks about grind settings — Per the CLAUDE.md Active Grinder field parsing contract, read the `user-setup.md` Grinder field, resolve the active grinder reference by case-insensitive substring against the contract's map (first match wins), attempt to load that `knowledge/grinders/` file, and on any miss or unreadable `user-setup.md` degrade to grinder-relative step advice plus the unconfigured nudge — never error. |
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
| **Grind setting** | Ask if not offered | Important for tracking. On a chirp-zeroed/stepless grinder (per the active-grinder reference, e.g. DF64V), interpret a bare number like "11" (or "11 grind") as marks-open-from-the-chirp-zero — the chirp-relative operator coordinate, NOT the absolute printed dial position. Accept it as a bare integer and say it back as "grind 11" (or "11 from chirp" when the anchor needs emphasis). Absolute-scale grinders (e.g. Sette 270 macro+micro codes like 9D) keep their own code — the bare-marks rule does not apply to them. |
| **Dose in** | Ask if not offered | Should match basket size |
| **Shot ID** | Optional | From `list_recent_shots` if user doesn't provide |

**Minimum viable feedback:** Rating + balance + one specific observation.

**Weight estimation — NEVER ask the user for cup weight.** The BT scale often produces artifacts (spikes, drops to 0g, null readings). Estimate dose out from:
1. Last stable weight sample from telemetry (if shot ID available)
2. `total_volume_ml × 0.82` (puck absorption estimate)
3. User's stated ratio × dose in

A +/-2g estimate is fine for diagnosis and recording.

**Operating RPM (variable-speed grinders only — gated by the Step 3 RPM gate):** When the gate is ON, read the current `Operating RPM` from `user-setup.md` (parse: an integer = the current RPM; missing/blank/`None`/non-integer = unknown) and carry it forward as the RPM value for the grind-map row in Step 4b. If the user states a different RPM this session, that stated value overrides the `user-setup.md` value for this row (and triggers the mid-bag re-dial guard). If the gate is ON but Operating RPM is unknown, prompt for it once (light) and, if still unknown, leave it blank — never infer. When the gate is OFF (fixed-speed grinder), do not read or prompt for RPM.

### 3. ANALYZE & RECOMMEND

**Variable-speed RPM gate (pre-check before the adjustment hierarchy):**

Per the CLAUDE.md Active Grinder field parsing contract, read the `user-setup.md` Grinder field, resolve the active grinder reference by case-insensitive substring against the contract's map (first match wins), attempt to load that `knowledge/grinders/` file, and on any miss or unreadable `user-setup.md` degrade to grinder-relative step advice plus the unconfigured nudge — never error. RPM behavior is **ON** iff the resolved **quick-tier** `knowledge/grinders/<NAME>.md` contains a section whose heading is exactly `## Motor Speed (RPM)`. Gating reads the quick-tier file only (not the deep-tier reference, not the Grinder prose). No match, no resolved file, or contract fallback → the grinder is **fixed-speed**: RPM behavior is **OFF** (no RPM prompts, blank RPM column), **never error**. This gate governs the RPM read in Step 2 and the RPM cell of the grind-map writer in Step 4b.

Use the loaded knowledge files (BREWING_BASICS + TASTING_GUIDE) to diagnose and recommend.

**Adjustment hierarchy** — adjust in this order:
1. **Grind size** — largest effect on extraction
2. **Yield/Ratio** — quick correction (5g rule)
3. **Temperature** — fine-tuning after grind is close
4. **Pressure/Profile** — style change or enhancement
5. **Puck prep** — channeling, inconsistency

**Puck Screen presence detection (pre-check before applying sour-path or channeling-path recommendations):**

Scan the Equipment table in `user-setup.md` for a `Puck Screen` row. Per the CLAUDE.md parsing contract, treat any of the following as **no screen present** (skip the guardrails below): missing row, blank value, or value `None` (case-insensitive). Any other non-empty value means **screen present** — apply the gated guardrails below.

The skill does NOT carry its own copy of the guardrail wording — it routes to `knowledge/PUCK_SCREENS.md` §Diagnostic Guardrails as the Single Source of Truth. The cold-screen check is a pre-check inserted before the existing sour → grind-finer path, NOT a reordering of the adjustment hierarchy above.

| Taste signal | Screen present? | Action |
|--------------|-----------------|--------|
| Sour | Yes | Load `knowledge/PUCK_SCREENS.md` → §Diagnostic Guardrails → **Cold-Screen Sour Guardrail**. ASK about **preheat** discipline (was the screen locked into the portafilter during the flush?) BEFORE recommending grind finer. A cold puck screen pulls heat from the puck surface and produces a sour shot; preheat fixes the cause and grinding finer makes it worse. |
| Sour + bitter (channeling signature) | Yes | Load `knowledge/PUCK_SCREENS.md` → §Diagnostic Guardrails → **Channeling-Nuance Note**. Apply the prep-driven-vs-shower-screen-driven distinction: because the puck screen already mitigates shower-screen-driven channeling, the remaining channeling is **likely** (NOT "almost certainly") puck-prep-driven. EXCEPT verify the screen itself is not the source first — check screen orientation (upside-down? smooth side vs textured side per manufacturer), wrong size for the basket, or bent/warped from prior over-dosing. The Core Rule recommendation is preserved verbatim: **fix puck prep, NOT grind**. |

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

**Mid-bag RPM-change re-dial guard (variable-speed only — gated by the Step 3 RPM gate; single `user-setup` read, NO grind-map history parser):**

When the gate is ON and the user states an RPM for this session that **differs** from the current `Operating RPM` read from `user-setup.md` (a single read — do NOT scan prior grind-map rows), do both of the following:
1. **Warn and re-anchor.** Explain that RPM is a coarse lever that shifts the grind distribution, so the old grind setting no longer maps to the same shot. Recommend **re-dialing grind to restore the target shot time** — let the shot timer tell you which way — rather than carrying the old grind number forward. (Do not restate RPM range numbers; for the why, route to `knowledge/grinders/DF64V.md`.)
2. **Update (or create) the Operating RPM field.** Write the new stated RPM into `user-setup.md`'s `Operating RPM` field — **creating the row if it is absent** (per Task 4's documented contract) — mirroring how the Active Coffee section is updated in `/new-coffee`. **Symlink-resolve before writing:** `user-setup.md` is a symlink file into the private data repo and the Edit/Write tool refuses to write through it. Run `readlink user-setup.md`; if it resolves, Read AND Edit the resolved absolute target (e.g. `/Users/charlie.hall/Workspaces/gaggimate-barista-data/user-setup.md`); if `readlink` returns nothing (regular file — no private repo configured), operate on the literal path. The Read-before-edit and the Edit must target the SAME resolved path. This write must reach the Step 4e `.data-repo-path` commit/push **even when no rating is recorded** (a mid-bag RPM report may arrive on an unrated shot), so perform the Step 4e commit path regardless of whether a rating was logged.

When the stated RPM matches the current `Operating RPM` (or no RPM is stated), do nothing here — no warning, no update.

Always explain *why* you're suggesting a change. One primary recommendation, one backup.

**Experiment-triggered RPM guidance (variable-speed only — NOT part of the adjustment hierarchy, never volunteered):**

Do NOT volunteer RPM as a fix during routine sour/bitter/fast/slow diagnosis — it is deliberately absent from the adjustment hierarchy above. Offer RPM guidance **only when the user explicitly frames a deliberate body/clarity experiment** (e.g., "I want to experiment with body via RPM" or "would changing motor speed change clarity?"). In that case, give **hedged** guidance and route the reasoning to `knowledge/grinders/DF64V.md` ("RPM as a dial-in lever" note) rather than restating any RPM numbers or asserting an unqualified "RPM = body" rule — the science is contested and your own logged RPM↔outcome data is the real signal.

### 4. RECORD (silent, no confirmation needed)

Do all of these automatically after feedback is collected:

#### 4a. Tasting Notes → Coffee README

Append a row to the Tasting Notes table in the active coffee's `README.md`:

| # | Date | Shot | Grind | In/Out | Ratio | Profile | Balance | Stars | Observations |
|---|------|------|-------|--------|-------|---------|---------|-------|--------------|

- **#**: Sequential shot number for this coffee
- **Date**: Compact format (e.g., Feb 12)
- **Shot**: Gaggimate shot ID (6-digit, for `/diagnose` cross-reference)
- **Grind**: Record in the active grinder reference's notation (same rule as step 4b.4) — for chirp-zeroed grinders (e.g. DF64V) a **bare integer** = marks from chirp; for absolute-scale grinders (e.g. Sette) the grinder's own code. Ensure the Tasting Notes table carries the one-time footnote `Grind = marks open from chirp zero (<grinder>)` for chirp-zeroed grinders — add it if absent.
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

**Update process (append-only — preserves header, alignment line, and every existing data row):**
0. **Symlink-resolve before reading-for-edit or writing.** `grind-map.md` is a symlink file into the private data repo and the Edit/Write tool refuses to write through it. Run `readlink grind-map.md`; if it resolves, Read AND Edit the resolved absolute target (e.g. `/Users/charlie.hall/Workspaces/gaggimate-barista-data/grind-map.md`); if `readlink` returns nothing (regular file — no private repo configured), operate on the literal path. The Read-before-edit and the Edit must target the SAME resolved path. Use this resolved path for steps 1–7 below.
1. Read current `grind-map.md` (at the resolved path from step 0). Do NOT touch the header line, the alignment line, or any existing data rows.
2. **Misaligned-row guard (run before appending, every invocation):** Scan the live `grind-map.md` for any data row whose column count ≠ 13. If one is found, flag it to the user (e.g., "Heads up — row N in `grind-map.md` has a column count that doesn't match the 13-column header; you may want to fix it by hand."). Do NOT auto-backfill or rewrite the row — flag only. (At plan time the live file has the 13-column header and zero data rows, but a user may have hand-edited or restored old rows, so this check is a runtime responsibility on every invocation.)
3. Append a new row to the **end** of the file with these 13 fields in order: `Coffee, Roast, Process, Origin, Days Off Roast, Grind, RPM, Profile, Ratio, Temp, Rating, Date, Puck Screen?`
4. **Grind notation:** Defer the recording format to the notation prescribed by the active grinder reference — record exactly the format that reference specifies (a reference may itself defer to the shared `knowledge/grinders/_NOTATION.md`).
   - **Chirp-zeroed/stepless grinders (e.g. DF64V):** the canonical recorded grind value is a **bare integer** equal to the number of marks the collar is opened from the chirp zero (e.g. `11`). A bare number like "11" from the user is recorded as that bare integer. This bare integer is still the **chirp-RELATIVE** operator coordinate — the table header supplies the "from chirp" anchor so the repetitive "chirp + N marks" wording is factored out of every row; it is NOT a blessing of the absolute printed-dial number as the canonical record. Caveats remain in force: it is an operator coordinate, NOT a micron/particle-size claim; the chirp point drifts coarser as burrs season, so the same number drifts finer over time; the zero-set epoch anchor + superseding-divider conventions remain.
   - **Mandatory header declaration:** the bare integer is meaningful only because the grind-map table carries a one-time header/footnote declaration: "Grind = marks open from chirp zero (<grinder>)" (e.g. "(DF64V)"). For chirp-zeroed grinders this declaration is **mandatory** — a bare number without it is meaningless. Ensure the table carries it; **add it if absent**.
   - **Absolute-scale grinders (e.g. Sette 270):** UNCHANGED — record the grinder's own absolute code (macro+micro like `9D`). The bare-marks-from-chirp rule does NOT apply to them.
5. **RPM cell — value comes from the Step 2 / Step 3 RPM gate (never infer):**
   - Variable-speed (gate ON): write the Operating RPM resolved in Step 2 as a plain **integer** (the `user-setup.md` value, or the session-stated value if the user overrode it). If the gate is ON but RPM is still unknown after the one light prompt, write a **blank** cell.
   - Fixed-speed (gate OFF), unresolved grinder, or contract fallback: write a **blank** cell.
6. **Puck Screen? cell — read from `user-setup.md` Equipment table (stateless read; do NOT write):**
   - Missing row, blank value, or value `None` (case-insensitive) or whitespace-only → write a **blank cell**
   - Any other non-empty value → write `Y`
7. **No back-fill of existing rows.** Old 12-column (or shorter) rows in `grind-map.md` are left untouched; only the newly appended row is 13-column. Under markdown-table semantics the missing cells on old rows parse as blank ("unknown" per the grind-map.example.md contract). Header/schema migration is owned separately and is NOT this skill's concern.

#### 4c. Shot Notes → Device

If a shot ID is available, sync feedback to the device:
```
manage_shot_notes(shot_id, action="update", rating=X, balance_taste="...", notes="...", grind_setting="...", dose_in=X, dose_out=X, bean_type="...")
```

**`bean_type` parameter — source rules:**
1. Read `user-setup.md` → Active Coffee section.
2. If the section is present and not the placeholder `No active coffee`, parse the coffee's display title from the table and pass it as `bean_type`, **truncated to 200 characters** (`bean_type[:200]`, no word-boundary fanciness).
3. If the user's feedback prose explicitly names a different bean (e.g. "this was actually the decaf bag"), prefer the user's value over the Active Coffee title (still truncate to 200 chars).
4. If Active Coffee is absent or matches the `No active coffee` placeholder, **omit `bean_type` entirely** — do not pass the placeholder string. The device sidecar's existing `beanType` (if any) will be preserved by the MCP read-modify-write logic.

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

**User says:** "3 stars, sour, current grind, 22g in"
**Action:** Load context → record → diagnose (sour = extract more) → recommend grind/yield change → update tasting notes + grind map + shot notes

**User says:** "5 stars, balanced, amazing sweetness"
**Action:** Load context → celebrate → record to grind map + tasting notes → recommend drink format

**User says:** "it was sour AND bitter"
**Action:** Load context → diagnose **channeling** (from BREWING_BASICS line 129) → recommend puck prep fix, NOT grind change → record
