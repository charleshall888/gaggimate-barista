---
name: new-coffee
description: >
  Research a new coffee bean and propose starting extraction parameters.
  Use when: (1) user shares a new bag of coffee (photo, name, or description),
  (2) user says "/new-coffee", "new beans", "dialing in a new coffee",
  (3) user asks "where should I start with this coffee".
  Accepts bag photos (extracts info via vision) or text descriptions.
  Researches origin, process, roast level via web search, checks grind-map.md
  for similar coffees, then recommends temperature, grind, ratio, and profile.
---

<command-name>new-coffee</command-name>

# New Coffee Research Skill

Systematically research a coffee and propose starting extraction parameters.

## Conditionally Load

| File | When |
|------|------|
| `knowledge/PUCK_SCREENS.md` | `user-setup.md` Equipment table has a Puck Screen row with value ≠ `None` (informs discussion only — does NOT alter grind/temp/ratio starting recommendations) |

## Workflow

### 1. GATHER Coffee Info

**If photo provided:**
- Extract from label: roaster, coffee name, origin, roast date, tasting notes
- Note any visible processing info (washed, natural, etc.)

**If text provided:**
- Parse roaster and coffee name
- Ask for roast date if not mentioned

### 2. RESEARCH via Web Search

Search for the specific coffee to find:
- Processing method (washed, natural, honey, anaerobic)
- Origin details (country, region, altitude if available)
- Variety (Bourbon, Gesha, Caturra, etc.)
- Roast level (light, medium, dark) — infer from tasting notes if not stated
- Roaster's tasting notes

**Capture research synthesis:** As you research, note the flavor implications of this coffee's
origin, variety, processing, and altitude. These insights get saved to the README's
"What to Expect" section — not just presented in conversation.

**See:** `references/RESEARCH_CHECKLIST.md` for detailed research patterns.

### 3. CONSULT Grind Map

Read `grind-map.md` and find similar coffees:
- Match by: roast level > processing method > origin
- **Consider profile style compatibility**: A grind setting from a bloom profile at 7.5 bar won't translate directly to a turbo at 6 bar. When presenting matches, include the Profile, Ratio, and Temp columns so the user sees the full extraction context.
- If match found: use as starting point, adjust for freshness and profile style differences
- If no match: load the active grinder reference resolved per the Active Grinder field parsing contract (`knowledge/grinders/` file) with the Req 4 attempt-then-fallback — Per the CLAUDE.md Active Grinder field parsing contract, read the `user-setup.md` Grinder field, resolve the active grinder reference by case-insensitive substring against the contract's map (first match wins), attempt to load that `knowledge/grinders/` file, and on any miss or unreadable `user-setup.md` degrade to grinder-relative step advice plus the unconfigured nudge — never error.

**Freshness adjustment:** Fresher beans (fewer days off roast) need **coarser** grind — CO2 adds puck resistance. If historical match was at 14 days and new bag is 7 days, suggest a small step / 1-2 steps coarser.

### 4. SYNTHESIZE Recommendations

Build recommendations using:
- **Temperature:** From `knowledge/ESPRESSO_BREWING_BASICS.md` roast guidelines
- **Grind:** From grind-map match or the active grinder reference's defaults
- **Ratio:** From processing method patterns (see below)
- **Pressure:** From `knowledge/PRESSURE_GUIDE.md` roast × processing matrix (see below)
- **Profile:** From `knowledge/PROFILE_LIBRARY.md` by roast/process, adjusted for correct pressure
- **Dose:** From `user-setup.md` basket size. **Dose = basket size** (e.g., 22g basket → 22g dose). Don't underdose.
- **Volumetric target:** When using a library profile, confirm its volumetric stop matches dose × ratio. Library profiles are sized for 22g.
- **RPM (variable-speed grinders only — gated):** After resolving the active grinder per the Active Grinder field parsing contract (already done in Step 3 CONSULT), check whether the resolved **quick-tier** `knowledge/grinders/<NAME>.md` contains a section heading exactly `## Motor Speed (RPM)`. **If it does → RPM behavior ON:** include an RPM starting recommendation in the output table (see the conditional RPM row below). The rendered value is the user's `Operating RPM` from `user-setup.md` (per its integer parse rule) if set, else the reference default from that grinder file's `## Motor Speed (RPM)` section — do not restate the literal numbers here; read them at runtime. **If the heading is absent / no quick-tier file resolved / the Active Grinder contract fell back to fallback / `user-setup.md` is unreadable → RPM behavior OFF:** this is a **fixed-speed** path — omit the RPM row entirely and **never error**.

### 4b. SELF-CHECK via Multi-Agent Review

Before confirming with the user, run a two-stage reasoning check.
Full protocol (claims format, prompt templates, confidence calibration) in
[references/SELF_CHECK.md](references/SELF_CHECK.md).

**Step 1 — Extract claims block:**
From your synthesis, extract a `<claims>` block listing: GRIND_ESTIMATE (setting +
source), GRIND_MATCH_SIMILARITY, GRIND_CONFIDENCE, TEMP, PRESSURE, PROFILE, RATIO,
one CONDITIONAL_RECOMMENDATION line per "if X → Y" in the draft, ADJUSTMENT_COUNT.

**Step 2 — Spawn Sonnet critic:**
Spawn a critic via the Task tool (`subagent_type: general-purpose`) using the
Critic Prompt Template from `references/SELF_CHECK.md`, with your draft and claims
block substituted in.

**Step 3 — Evaluate result:**
- `STATUS: CLEAR` → proceed to "CONFIRM with User" using your draft
- `STATUS: OBJECTIONS` → proceed to Step 4

**Step 4 — Spawn Opus arbiter (only when objections found):**
Spawn via Task tool (`subagent_type: general-purpose`, `model: opus`) using the
Arbiter Prompt Template from `references/SELF_CHECK.md`. Use the arbiter's corrected
output when confirming with the user.

The grind confidence note from `references/SELF_CHECK.md` is always included in the
Starting Parameters table — even when the critic returns CLEAR.

---

### 5. CONFIRM with User

Before finalizing, ask:
> "This [process] [origin] typically shines with [approach]. Would you like to start there, or prefer a more conservative/adventurous approach?"

Options to offer (each option creates a dedicated per-coffee profile — see Step 6):
- **Conservative:** Classic profile, standard ratio (pressure matched to processing method — not always 9 bar)
- **Recommended:** Profile matched to bean characteristics (roast, process, intensity)
- **Adventurous:** Bloom profile or turbo shot if appropriate

User confirmation of any of these three options authorizes Step 6 to create + activate a new per-coffee `[AI]` profile. Do NOT ask a second time "shall I upload?" — it's part of the same authorization.

**Reuse exception:** If the user explicitly says "reuse [profile name]", "use the [profile] already on the device", or names an existing `[AI]` profile to apply as-is, skip Step 6's create + select. Note the reused profile in the README's Profiles table with `*(reused from coffees/{other-slug}/)*` and link the JSON via relative path.

### 6. MATERIALIZE Per-Coffee Profile

**Default behavior (runs whenever Step 5 confirmed Conservative/Recommended/Adventurous).** Skip only when the Reuse exception in Step 5 applies.

Per CLAUDE.md "Repo first, device second": the JSON file is the source of truth. Always write to repo before calling MCP.

1. **Write JSON to repo first.** Path: `coffees/{coffee-slug}/{profile-slug}.json`. Profile slug is kebab-case from the style (e.g., `bloom-slide.json`, `turbo.json`, `dark-gentle.json`). The JSON's `label` field must equal `[Coffee Name] [Style] [AI]` (e.g., `Aponte Honey Bloom Slide [AI]`).

2. **Create on device** by passing the same phases array to MCP:
   ```
   created_profile = manage_profile(action="create", profile_name="[Coffee Name] [Style] [AI]", temperature=X, phases=[...])
   ```
   If `created_profile["success"]` is false, surface the error and stop. Do not claim the profile was uploaded. The repo JSON stays — it's still the source of truth and can be retried.

3. **Activate on device** using the returned id:
   ```
   select_response = manage_profile(action="select", profile_id=created_profile["profile"]["id"])
   ```
   If `select_response["success"]` is false, report: "Profile was created but could not be activated on the device: [error]". Do not claim the profile is active.

**Naming rules:**
- Always include `[AI]` suffix.
- Profile name = `{Coffee Short Name} {Style} [AI]` — short enough to be readable in the device list (e.g., `Aponte Honey Bloom Slide [AI]`, not `Onyx Coffee Lab Colombia Aponte Village Honey Bloom Slide [AI]`).
- Style word(s) describe the profile shape (Bloom Slide, Turbo, Dark Gentle, Lever Decline) — same convention as the existing `[AI]` profiles on the device.

### 7. SAVE README to Repository

Create the coffee directory and save the research README:

1. **Create directory:** `coffees/{roaster}-{coffee-name}/` (kebab-case, e.g., `coffees/perc-ethiopia-chelchele/`)
2. **Write `README.md`** using this template:

```markdown
# {Roaster} {Coffee Name}

## Bean Profile

| Field | Value |
|-------|-------|
| **Roaster** | ... |
| **Origin** | ... |
| **Process** | ... |
| **Roast Level** | ... |
| **Variety** | ... |
| **Altitude** | ... |
| **Tasting Notes** | {roaster's published tasting notes — actual descriptors, not a placeholder} |
| **Roast Date** | ... |

## What to Expect

{2-3 sentence summary of the coffee's character and what makes it interesting for espresso.
Synthesize origin, variety, processing, and altitude into flavor expectations.}

- **Origin character:** {What this origin typically brings — fruit profile, acidity, body}
- **Variety ({name}):** {How this variety behaves — density, flavor tendencies, quirks}
- **Processing ({method}):** {How processing affects flavor and why we chose this profile style}
- **Density/Altitude:** {If notable (1800+ masl), mention implications for grind and temp}

{Include only bullets that add genuine insight — omit any that just repeat the Bean Profile
table. 2-4 bullets is typical.}

## Profiles

| Profile | Style | Temp | Pressure | Ratio | File |
|---------|-------|------|----------|-------|------|

## Tasting Notes
```

3. **Fill in the Profiles table row** with the per-coffee profile from Step 6 (or the reused profile per the Reuse exception). The `File` column links to the JSON written in Step 6 (or the relative path of the reused JSON).
4. **Remove `.gitkeep`** from `coffees/` if it exists (no longer needed once real content is present)
5. No confirmation needed—this is a standard workflow step

### 8. Set Active Coffee

Update the Active Coffee section in `user-setup.md` with:
- **Coffee**: Full coffee name (e.g., "PERC Ethiopia Chelchele")
- **Directory**: Path to the coffee directory (e.g., `coffees/perc-ethiopia-chelchele`)
- **Roast Date**: From bag info, or "—" if unknown

No confirmation needed—standard workflow step.

### 9. Private Repo Commit

1. Read `.data-repo-path` at the project root.
   - If absent: skip silently (user has no private repo — this is expected for new setups).
   - If present: proceed.
2. Run as separate Bash calls (no chaining, no `git -C`), substituting `{private_repo}` with the path from `.data-repo-path`:
   - `git --git-dir={private_repo}/.git --work-tree={private_repo} add -A`
   - `git --git-dir={private_repo}/.git --work-tree={private_repo} commit -m "new-coffee: add {coffee-name}"`
   - `git --git-dir={private_repo}/.git --work-tree={private_repo} push`
3. If push fails: inform the user — "Private repo push failed — changes saved locally. Run `git push` manually in `{private_repo_path}` when credentials are available."

---

## Output Format

```
## Coffee Research: [Name]

### Bean Profile
- **Roaster:** [roaster]
- **Origin:** [country, region]
- **Process:** [washed/natural/honey/anaerobic]
- **Roast Level:** [light/medium/dark]
- **Variety:** [if known]
- **Tasting Notes:** [from roaster]
- **Days Off Roast:** [X days, or "unknown"]

### Similar Coffees in Your History
[Table from grind-map.md matches, or "No similar coffees yet"]

### Recommended Starting Parameters
| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| Temperature | X°C | [roast level rationale] |
| Grind | XY | [from history or default, freshness adjusted] |
| RPM | [placeholder] | [variable-speed only] |
| Ratio | 1:X | [process rationale] |
| Profile | [name] | [why this profile] |
| Dose | Xg in → Xg out | [basket size rationale] |

### Profile
Created `[Coffee Name] [Style] [AI]` profile, activated on device.
JSON: `coffees/{roaster}-{coffee-name}/{profile-slug}.json`

(If Reuse exception applied: state which existing profile is being reused and link its JSON via relative path.)

### Saved To
`coffees/{roaster}-{coffee-name}/README.md`
Set as active coffee in `user-setup.md`

### What to Watch For
- [Specific guidance for first shot based on bean characteristics]
- [What taste outcomes to expect]
- [When to adjust and in which direction]
```

**Note:** "What to Watch For" above is conversational guidance for the user's first shot.
Research synthesis (origin, variety, processing insights) is separately saved to the README's
"What to Expect" section in Step 7.

**Note (conditional RPM row):** The `| RPM | [placeholder] | [variable-speed only] |` row is emitted **only when the Step 4 SYNTHESIZE gate is ON** (the resolved quick-tier grinder file has a `## Motor Speed (RPM)` section). When the gate is OFF — a **fixed-speed** grinder, no resolved file, contract fallback, or unreadable `user-setup.md` — omit the row entirely and **never error**. When emitted, the `[placeholder]` renders the user's `Operating RPM` from `user-setup.md` if set, else the reference default from the grinder file's `## Motor Speed (RPM)` section (read at runtime — the numbers are never written into this skill).

---

## Quick Reference

**User says:** "I got a new bag of [coffee]"
**Action:** Extract info → research → consult grind map → recommend → confirm → **set active**

**User shares photo:**
**Action:** Vision extract → research → consult grind map → recommend → confirm → **set active**

**User says:** "/new-coffee"
**Action:** Ask what coffee they have, then proceed with workflow → **set active**
