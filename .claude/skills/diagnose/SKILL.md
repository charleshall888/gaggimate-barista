---
name: diagnose
description: >
  Diagnose espresso extraction issues by correlating machine telemetry with taste feedback.
  Use when user says: "/diagnose", "what went wrong", "analyze that shot", "why did it taste [sour/bitter/flat]",
  "my shots are inconsistent", or asks about pressure spikes, flow issues, or extraction problems.
  Fetches shot data via analyze_shot MCP tool, interprets patterns, and provides actionable recommendations.
---

<command-name>diagnose</command-name>

# Espresso Diagnostic Skill

You are diagnosing espresso extraction issues by correlating Gaggimate telemetry data with taste feedback.

## Diagnostic Workflow

Follow this sequence for every diagnosis:

### 1. GATHER Information

**Load coffee context:**
- Read `user-setup.md` → Active Coffee section
- If set, read the coffee's `README.md` (bean profile, processing method, recent tasting notes) — this informs diagnosis (e.g., a natural at 7.5 bar has different expectations than a washed at 9 bar)
- If not set, ask the user what coffee they're brewing before proceeding

**Required inputs:**
- Shot ID (from `list_recent_shots` if not provided)

**Optional inputs (enhance diagnosis but do NOT wait for them):**
- Taste feedback: sour, bitter, flat, astringent, balanced, or specific descriptors
- Visual observations (channeling, spurting, blonde early, etc.)

**Always lead with the full telemetry analysis.** Do NOT ask the user how it tasted before presenting the analysis. The telemetry tells its own story — present it first. If the user hasn't volunteered taste feedback, ask at the END of the analysis so you can refine recommendations.

**Fetch telemetry:**
```
Use: analyze_shot(shot_id)
```

**Fetch shot notes if available:**
```
Use: manage_shot_notes(shot_id, action="get")
```

### 1b. IDENTIFY Shot Style

Before analyzing, identify the shot style so you compare against the right expectations. Use three tiers of detection (try in order, use first that succeeds):

**Tier 1 — Fetch profile definition (preferred):**

If `analyze_shot` returns a `profile_id`, fetch the full profile:
```
Use: manage_profile(action="get", profile_id=<profile_id>)
```

Classify by phase structure:
- Has a phase with pump off (`"target": "power"` and `"pressure": 0`) → **Bloom** (light roast bloom or natural process bloom)
- Flow-targeted extraction with flow >= 3.5 ml/s → **Turbo**
- Brew phase with pressure declining >= 4 bar over >= 15s → **Lever Decline**
- Extraction pressure <= 7 bar + high volumetric target (>= dose × 3.5) → **Allongé**
- Extraction pressure < 9 bar, no bloom, no decline → **Dark/Gentle**
- Default → **Classic 9-Bar**

**Tier 2 — Profile name keywords (fallback):**

If profile definition is unavailable, match `profile_name` from `analyze_shot`:
- Contains "turbo" → **Turbo**
- Contains "bloom", "natural bloom" → **Bloom**
- Contains "allongé", "allonge", "lungo" → **Allongé**
- Contains "lever", "decline" → **Lever Decline**
- Contains "gentle", "dark", "milk" → **Dark/Gentle**
- Otherwise → **Classic 9-Bar**

**Tier 3 — Telemetry fingerprint (last resort):**

If neither profile definition nor meaningful profile name is available, classify from the shot telemetry itself. See `references/TELEMETRY_PATTERNS.md` (Style Detection Fingerprints section) for the fingerprint table.

### 2. ANALYZE Telemetry

**First, determine the final weight — NEVER ask the user.** The BT scale frequently produces artifacts: spikes, drops to 0g, or null readings near end-of-shot. You MUST estimate the dose out yourself using the telemetry. Do not ask the user what the cup weighs — figure it out from the data.

**Weight estimation priority (use first available):**
1. **Last stable weight sample** — scan weight samples backward from end-of-shot, skip any that drop to 0g or spike >2× the inter-sample trend. The last reading consistent with the trend is your true weight.
2. **Flow meter total minus puck absorption** — if weight data is too sparse or entirely null, use `total_volume_ml × 0.82` (≈18% absorbed by puck) as your dose-out estimate. This is approximate but sufficient for diagnosis.
3. **Interpolate from mid-shot weight + flow** — if you have a reliable weight reading mid-shot and flow data for the remainder, project forward.

State your estimated dose out and how you derived it, then move on. A ±2g estimate is fine for diagnostic purposes — don't let imperfect weight data stall the analysis.

**Then, filter other BT scale artifacts.** Beyond weight, volume readings can also spike. If any late-shot sample differs from the preceding trend by >2× the average inter-sample change, discard it. See `references/TELEMETRY_PATTERNS.md` (Bluetooth Scale Artifacts section) for full detection rules.

**Load style-specific expectations** from `knowledge/PRESSURE_GUIDE.md` (Pressure by Shot Style section) and `knowledge/PROFILE_LIBRARY.md` (Quick Reference table). Compare the shot's telemetry against those style-specific ranges — not generic 9-bar ranges.

**Universal thresholds** (style-independent):

| Metric | Normal | Anomaly |
|--------|--------|---------|
| Temperature variance | ±1°C from target | >2°C = equipment instability |
| Pressure spike above profile target | — | >1.5 bar above = too fine / channeling |

**Style-specific thresholds** — loaded from knowledge files per identified style:

| Metric | Source |
|--------|--------|
| Expected pressure range | `knowledge/PRESSURE_GUIDE.md` → Pressure by Shot Style |
| Expected time, ratio, flow | `knowledge/PROFILE_LIBRARY.md` → Quick Reference table |
| Anomaly interpretation | `references/TELEMETRY_PATTERNS.md` → Per-Style Diagnostic Notes |

Flag an anomaly only when a metric falls **outside the identified style's expected range**. For example, 6 bar and 17s is anomalous for Classic 9-Bar but perfectly normal for Turbo.

### 2b. COMPARE Intended vs Actual (when profile definition available)

If you fetched the profile definition in Step 1b (Tier 1), compare each phase's intended parameters against the actual telemetry:

| Comparison | Interpretation |
|------------|----------------|
| Pressure exceeded profile target by >1.5 bar | Grind too fine or dose too high |
| Pressure never reached target (>1.5 bar below) | **Context matters.** In a post-bloom ramp (starting from 0 bar), this is often normal — the ease-in curve needs time to build from zero, and Peak Hold finishes the job. Only flag as "too coarse" in non-bloom profiles where the pump starts from pre-infusion pressure (2-4 bar). |
| Bloom phase showed significant flow (>1 ml/s) | **Cross-reference with cup weight.** Flow + zero cup weight = puck absorption, not channeling (see TELEMETRY_PATTERNS.md "Flow Meter vs Cup Weight During Bloom"). Flow + increasing cup weight = through-flow, puck too permeable — grind finer. |
| Volumetric target reached much earlier than phase duration | Grind too coarse (flow too fast) |
| Phase duration reached before volumetric target | **The volumetric target controls the final cup weight; duration is just a safeguard.** If the phase timed out before reaching its volumetric target, the most likely fix is extending the phase duration — not changing grind. Only suspect grind if the flow rate is abnormally low for the style. |
| Decline phase pressure stayed >1 bar above target floor | Grind too fine — high puck resistance prevents pressure from dropping. See Pressure-Resistance Physics in TELEMETRY_PATTERNS.md. |
| Decline phase dropped pressure faster than intended | Channel opened mid-shot |
| Flow during extraction well above/below profile's flow target | Grind mismatch for this style |

This phase-by-phase comparison is the most precise diagnostic — it shows exactly *where* in the shot things diverged from intent. Include the comparison in your diagnosis when available.

**Compliance metrics (quantitative grind-direction signal):** When `analyze_shot` returns a `compliance_metrics` block, use it alongside the manual table above to sharpen your diagnosis. The metrics operate on brew-phase samples only (filtered at ≥50% of peak pressure), so bloom and ramp data are excluded automatically.

| Metric | Threshold | Interpretation |
|--------|-----------|----------------|
| `max_pressure_overshoot_bar` | > 1.5 bar | Strong "grind too fine" signal — puck resistance is pushing pressure above the profile target. Matches the manual spike check above; this metric makes it automatic. |
| `max_pressure_undershoot_bar` | > 1.5 bar | **Context matters.** Only flag as "grind too coarse" in steady-state brew phases. In profiles with a post-bloom ramp (ease-in from 0 bar), large undershoot values are normal — the machine is climbing from zero to target. Cross-reference with shot style: Bloom profiles always have a ramp. See §2b table row above for full guidance. |
| `pressure_rmse_bar` | No fixed threshold yet | Overall pressure adherence quality. Lower is better. A value materially above 1 bar is worth noting as general context; avoid pinning a diagnosis on it until calibrated data is available. |
| `flow_rmse_ml_s` | No fixed threshold yet | Informational context only. Surface when non-None but do not attach a grind direction to it — calibrate thresholds once real shot data is available. |

`brew_phase_sample_count` is available for confidence context: a count of 3–4 means the metrics are based on very few samples and should be weighted lightly.

### 3. CORRELATE Taste with Telemetry

Cross-reference the user's taste feedback with telemetry patterns.

**See:** `references/TELEMETRY_PATTERNS.md` for detailed correlation matrix.

**RPM as diagnostic context (advisory, when known):** If the RPM used for the shot is known — from the shot's `grind-map.md` row or a value the user states — fold it into the correlation narrative as contextual input. A logged RPM is self-identifying (RPM exists only for variable-speed grinders), so no grinder-resolution or out-of-range gating is needed. For example: a fast/gushing shot at a high logged RPM is consistent with a coarser distribution, and a choked/stalling shot at a low logged RPM points toward the low-RPM-stall edge. Defer all interpretation to `knowledge/grinders/DF64V.md` and `knowledge/reference/DF64V_REFERENCE.md` rather than asserting RPM facts here. **If no RPM is known for the shot, behave exactly as today — skip this context and run the correlation unchanged.**

**Puck Screen presence detection (pre-check before applying sour-path or channeling-path recommendations):**

Scan the Equipment table in `user-setup.md` for a `Puck Screen` row. Per the CLAUDE.md parsing contract, treat any of the following as **no screen present** (skip the guardrails below): missing row, blank value, or value `None` (case-insensitive). Any other non-empty value means **screen present** — apply the gated guardrails below.

The skill does NOT carry its own copy of the guardrail wording — it routes to `knowledge/PUCK_SCREENS.md` §Diagnostic Guardrails as the Single Source of Truth. The cold-screen check is a pre-check inserted before the existing sour → grind-finer path, NOT a replacement for the diagnostic hierarchy.

| Taste signal | Screen present? | Action |
|--------------|-----------------|--------|
| Sour | Yes | Load `knowledge/PUCK_SCREENS.md` → §Diagnostic Guardrails → **Cold-Screen Sour Guardrail**. ASK about **preheat** discipline (was the screen locked into the portafilter during the flush?) BEFORE recommending grind finer. A cold puck screen pulls heat from the puck surface and produces a sour shot; preheat fixes the cause and grinding finer makes it worse. |
| Sour + bitter (channeling signature) | Yes | Load `knowledge/PUCK_SCREENS.md` → §Diagnostic Guardrails → **Channeling-Nuance Note**. Apply the prep-driven-vs-shower-screen-driven distinction: because the puck screen already mitigates shower-screen-driven channeling, the remaining channeling is **likely** (NOT "almost certainly") puck-prep-driven. EXCEPT verify the screen itself is not the source first — check screen orientation (upside-down? smooth side vs textured side per manufacturer), wrong size for the basket, or bent/warped from prior over-dosing. The Core Rule recommendation is preserved verbatim: **fix puck prep, NOT grind**. |

### 3b. AUTO-TRIGGER Feedback (4-5 Star Shots)

If the user provides a rating of 4 or 5 stars (explicitly like "5/5" or "4 stars", or implied like "this is great", "really dialed in", "best shot yet") **and** provides taste descriptors, automatically run the `/shot-feedback` skill after completing the diagnosis. Do NOT ask — just invoke it with the shot ID, rating, and taste notes gathered during diagnosis. The user expects the full feedback loop (grind map update, tasting notes, device sync) to happen seamlessly.

For shots rated 1-3 or with no clear rating, do NOT auto-trigger — focus on diagnostic recommendations and let the user decide.

### 4. RECOMMEND Actions

Provide specific, prioritized recommendations:
1. **Primary adjustment** (most likely to fix the issue)
2. **Secondary adjustment** (if primary doesn't work)
3. **Profile consideration** (if extraction mechanics need changing)

Always explain WHY each recommendation addresses the diagnosed issue.

**Profile modifications:** If the user approves a profile change, follow the repo-first rule: update the JSON file in `coffees/{coffee}/` first, then upload to device via `manage_profile`. Never modify the device profile without saving to the repo file. Check `user-setup.md` → Active Coffee for the coffee directory path.

**Decision trees:** For taste-based diagnostic trees (SOUR, BITTER, FLAT/MUTED, INCONSISTENT), see [references/DIAGNOSTIC_TREES.md](references/DIAGNOSTIC_TREES.md).

**Telemetry correlation, equipment differentiation, multi-shot comparison:** See [references/TELEMETRY_PATTERNS.md](references/TELEMETRY_PATTERNS.md).

### 4b. SELF-CHECK via Multi-Agent Review

After forming all recommendations (Step 4) but before presenting to the user, run a
two-stage reasoning check. Full protocol (claims format, prompt templates, confidence
calibration) in [references/SELF_CHECK.md](references/SELF_CHECK.md).

**Step 1 — Extract claims block:**
From your full draft (telemetry summary + diagnosis + recommendations), extract a
`<claims>` block listing: SHOT_STYLE, one GRIND_DIRECTION line per grind signal
(including taste-based signals — especially if they conflict with telemetry signals),
PRESSURE_NARRATIVE, TASTE_SIGNAL, PRIMARY_DIAGNOSIS, PRIMARY_RECOMMENDATION.
Include every grind direction signal in the draft, even conflicting ones.

**Step 2 — Spawn Sonnet critic:**
Spawn a critic via the Task tool (`subagent_type: general-purpose`) using the
Critic Prompt Template from `references/SELF_CHECK.md`, with your draft and claims
block substituted in.

**Step 3 — Evaluate result:**
- `STATUS: CLEAR` → present draft to user as-is (omit claims block from output)
- `STATUS: OBJECTIONS` → proceed to Step 4

**Step 4 — Spawn Opus arbiter (only when objections found):**
Spawn via Task tool (`subagent_type: general-purpose`, `model: opus`) using the
Arbiter Prompt Template from `references/SELF_CHECK.md`. Present the arbiter's
corrected output to the user. Add a confidence note only if confidence is Low or Medium.

---

## Integration with Other Knowledge

**Always loaded** (already referenced in Steps 1-4 — no additional loading needed):
- `knowledge/PRESSURE_GUIDE.md` — style-specific pressure expectations (Step 2)
- `knowledge/PROFILE_LIBRARY.md` — expected time, ratio, flow by style (Step 2)
- `knowledge/ESPRESSO_BREWING_BASICS.md` — adjustment strategies (Step 4)

**Load ONLY when trigger applies:**

| File (lines) | Load ONLY when… |
|--------------|-----------------|
| `knowledge/ESPRESSO_TASTING_GUIDE.md` (142) | User asks how to evaluate/describe flavors, or needs a structured feedback template |
| `knowledge/GAGGIMATE_PROFILE_CREATION_GUIDE.md` (172) | Diagnosis leads to a profile modification — load when building the fix, not during analysis |
| `knowledge/reference/ESPRESSO_BREWING_REFERENCE.md` (229) | User asks about shot styles theory, salami shots, or dialing methodology — **not** during routine diagnosis |
| `knowledge/reference/ESPRESSO_TASTING_REFERENCE.md` (191) | User asks about the flavor wheel, palate exercises, or off-flavor identification — **not** during routine diagnosis |

**Stop rule:** Standard diagnosis uses only the always-loaded files + skill references (`TELEMETRY_PATTERNS.md`, `DIAGNOSTIC_TREES.md`). Loading `knowledge/reference/` files during routine diagnosis is over-researching.

---

## Response Format

Structure your diagnostic response as:

```
## Shot Analysis: [Shot ID]

### Identified Style: [Style Name]
(detected via [Tier 1: profile definition / Tier 2: profile name / Tier 3: telemetry fingerprint])

### Telemetry Summary
- **Pressure:** [peak] bar (style expects: X-Y bar)
- **Flow:** [avg] ml/s, first drip at [X]s (style expects: A-B ml/s)
- **Temperature:** [avg]°C (target: X°C, variance: ±X°C)
- **Timing:** [total]s total (style expects: E-Fs)

### Phase Comparison (if profile definition available)
[Intended vs actual for each phase — pressure, flow, timing]
- **Phase {n} ({name}):** exited on {exit_reason_type} at t+{elapsed_s}s ({target summary})
  - Fallback: when a phase's `exit_reason_type == "unknown"` AND `unavailable_reason == "profile_unavailable"`, render the bullet as `- **Phase {n} ({name}):** exit reason unavailable (profile unavailable)` and always emit the Interactive chart link below.
- **Estimated scale delay:** {delay_s}s ({auto | manual})

### Diagnosis
[Correlation between telemetry and reported taste, interpreted through style-specific expectations]

### Recommendations
1. **[Primary fix]** — [specific action with reasoning]
2. **[Secondary fix]** — [backup if primary doesn't work]
3. **[Profile consideration]** — [if applicable]

### What to Watch For
[What user should observe on next shot to confirm diagnosis]

Interactive chart: {analyzer_url}
```

---

## Example Diagnoses

### Example 1: Classic 9-Bar — Sour and Watery

**User says:** "That shot was really sour and watery."

**Style identified:** Classic 9-Bar (expects 8-10 bar, 25-32s, 1.5-2.5 ml/s)

**Telemetry:** Pressure 7.2 bar, first drip 2.8s, flow 3.4 ml/s avg, 22s total

**Diagnosis:**
> Your pressure never reached the Classic 9-Bar range (7.2 bar vs 8-10 bar expected) and the first drip came extremely fast (2.8s). Combined with high flow rate (3.4 ml/s vs 1.5-2.5 expected), the puck offered very little resistance. Classic under-extraction.
>
> **Primary fix:** Grind 2-3 steps finer. We need to build more resistance.
>
> **Watch for:** Time to first drip should increase to 5-7 seconds, and pressure should reach 8-9 bar.

### Example 2: Bloom Profile — NOT a Problem

**User says:** "Shot took 38 seconds and pressure was only 7.5 bar — is that okay?"

**Style identified:** Natural Process Bloom (expects 7-9 bar, 30-38s, bloom pause is normal)

**Diagnosis:**
> For a bloom profile, 38s total and 7.5 bar extraction pressure are right in the expected range. The bloom pause adds 10-15 seconds that a classic shot wouldn't have, and 7.5 bar is intentional for this natural-process coffee. These are features, not bugs. How did it taste?
