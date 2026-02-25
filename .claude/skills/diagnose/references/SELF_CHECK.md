# Self-Check Protocol: /diagnose

Two-stage multi-agent review to catch reasoning errors before presenting to the user.

---

## Claims Block Format

After completing your draft analysis but before presenting it, extract a `<claims>` block.
List every testable assertion your draft makes. Include ALL grind direction signals — the
critic will fail to catch contradictions if you omit signals that point the wrong way.

```
<claims>
SHOT_STYLE: [Classic 9-Bar | Bloom | Turbo | Allongé | Lever Decline | Dark/Gentle] (tier: [1|2|3])
GRIND_DIRECTION: [FINER | COARSER | HOLD | PUCK_PREP] (signal: [what metric drove this])
GRIND_DIRECTION: [repeat for every grind-direction claim in the draft, including taste-based ones]
PRESSURE_NARRATIVE: [one sentence describing what the pressure curve means]
TASTE_SIGNAL: [sour | bitter | both | flat | balanced | none]
PRIMARY_DIAGNOSIS: [one sentence]
PRIMARY_RECOMMENDATION: [the specific action recommended to the user]
</claims>
```

**Include every GRIND_DIRECTION line** even if they conflict — especially if they conflict.
The critic only checks what you surface here.

---

## Critic Prompt Template

Copy this prompt exactly into the Task tool call, substituting `{{DRAFT}}` and `{{CLAIMS}}`:

```
You are an espresso diagnosis critic. Your job is to find reasoning errors in a draft
diagnosis — not to improve prose or add information.

Apply the Critic Checklist below to the claims block. For each check: either PASS or
flag an OBJECTION with a specific description of the error and why it's wrong.

Return ONLY the following structure (no extra commentary):

STATUS: CLEAR
(if all checks pass)

--- OR ---

STATUS: OBJECTIONS

OBJECTION 1: [Check name] — [Specific error found] — [Why it's wrong] — [How to fix it]
OBJECTION 2: ...
(list only failing checks)

---

DRAFT:
{{DRAFT}}

CLAIMS:
{{CLAIMS}}

---

CRITIC CHECKLIST — apply each check in order:

CHECK 1: Grind Direction Consistency
- List every GRIND_DIRECTION claim from the claims block.
- If ALL point the same direction (finer, coarser, hold, or puck prep) → PASS.
- If any two point OPPOSITE directions (one FINER, one COARSER) → OBJECTION.
  Reason: the physical system cannot simultaneously require both. The contradiction must
  be resolved, not reported to the user. Most common resolution: high pressure + sour taste
  = channeling (fix: puck prep, not grind).

CHECK 2: Pressure-Resistance Physics
- Scan PRESSURE_NARRATIVE and the draft for any of these errors:
  a) "finer grind causes slow pressure build" → ERROR (finer = more resistance = faster build)
  b) "coarser grind causes slow pressure decline" → ERROR (coarser = less resistance = faster decline)
  c) "post-bloom ramp didn't reach target because grind too fine" → ERROR (bloom ramps start from
     0 bar via ease-in; not reaching target is normal, not a grind problem)
- If none found → PASS.

CHECK 3: Sour + High Pressure = Channeling
- If TASTE_SIGNAL contains "sour" AND the draft claims pressure exceeded the style target
  (or pressure spike is mentioned) → OBJECTION.
  Reason: sour taste + elevated pressure is the channeling signature. Water took the channel
  path → high resistance everywhere else (high pressure) + under-extraction in the channel
  (sour taste). Primary fix is puck prep, not grind direction.
  Exception: if the draft already diagnoses channeling as the primary cause → PASS.

CHECK 4: Style-Relative Thresholds
- Identify SHOT_STYLE from claims.
- If SHOT_STYLE is NOT Classic 9-Bar, check whether any anomaly in the draft is measured
  against 9-bar defaults (e.g., flagging 6 bar as "too low" for a Turbo, or flagging
  40s as "too long" for a Bloom) → OBJECTION.
  Reason: anomalies must be relative to the identified style's expected ranges.
```

---

## Arbiter Prompt Template

Use this prompt only when the critic returned OBJECTIONS. Substitute `{{DRAFT}}`,
`{{CLAIMS}}`, and `{{OBJECTIONS}}`:

```
You are an espresso diagnosis arbiter. A critic has found reasoning errors in a draft
diagnosis. Your job is to produce a corrected final diagnosis that resolves the objections.

Rules:
- Resolve every OBJECTION — do not leave any unaddressed.
- Preserve all correct information from the draft.
- If an objection requires choosing between two conflicting hypotheses, choose the one
  consistent with espresso physics (see key rules below). Explain your reasoning briefly.
- Keep the same response structure as the draft (Telemetry Summary, Diagnosis,
  Recommendations, What to Watch For).
- Add a single confidence note at the end:
  > *Confidence: [High/Medium/Low] — [one sentence explaining the basis]*
  Use High when all signals align, Medium when one signal was ambiguous or missing,
  Low when the diagnosis is a best-guess requiring confirmation on the next shot.

Key physics rules to apply when resolving contradictions:
- Finer grind → more resistance → pressure builds faster AND drops slower.
- Coarser grind → less resistance → pressure builds slower AND drops faster.
- Sour taste + high pressure → channeling (puck prep issue, not grind direction).
- Sour taste + low pressure → too coarse (grind finer).
- Bitter taste + high pressure → too fine (grind coarser).
- Both sour AND bitter → channeling (fix puck prep, do NOT adjust grind).

OBJECTIONS TO RESOLVE:
{{OBJECTIONS}}

ORIGINAL DRAFT:
{{DRAFT}}

CLAIMS:
{{CLAIMS}}
```

---

## Confidence Calibration

When the arbiter adds a confidence note, use these criteria:

| Level | When to use |
|-------|-------------|
| **High** | All telemetry signals agree, style identified via Tier 1, taste confirms |
| **Medium** | One signal is ambiguous, or style identified via Tier 2/3, or taste not provided |
| **Low** | Diagnosis required choosing between competing hypotheses, or critical data missing (no weight, no taste) |

If the critic returned CLEAR and you present the draft as-is, add a confidence note only
if confidence is Low or Medium. Skip the note for High-confidence diagnoses — it adds
noise without value.
