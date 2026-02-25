# Self-Check Protocol: /new-coffee

Two-stage multi-agent review to catch reasoning errors before presenting to the user.

---

## Claims Block Format

After completing your synthesis (Step 4) but before confirming with the user, extract a
`<claims>` block. List every assertion the critic needs to evaluate.

```
<claims>
GRIND_ESTIMATE: [setting, e.g., 13E] (source: [grind-map match name | Sette 270 default range])
GRIND_MATCH_SIMILARITY: [HIGH | MEDIUM | LOW | NONE]
  HIGH = same roast level + same process + similar origin
  MEDIUM = same roast level + same process, different origin
  LOW = same roast level only, different process or very different origin
  NONE = no grind-map entry used; defaults only
GRIND_CONFIDENCE: [HIGH | MEDIUM | LOW | NONE]  (mirrors GRIND_MATCH_SIMILARITY)
TEMP: [°C] (basis: [roast level guideline | grind map | other])
PRESSURE: [bar] (basis: [roast × process matrix | other])
PROFILE: [profile name] (basis: [how it was selected])
RATIO: [e.g., 1:2.3] (basis: [processing method | user preference | other])
CONDITIONAL_RECOMMENDATIONS: [list each "if X → Y" adjustment in the draft, one per line]
ADJUSTMENT_COUNT: [count of distinct variables being adjusted in the first-shot recommendation]
</claims>
```

---

## Critic Prompt Template

Copy this prompt exactly into the Task tool call, substituting `{{DRAFT}}` and `{{CLAIMS}}`:

```
You are a new-coffee recommendation critic. Your job is to find reasoning errors in a
draft coffee recommendation — not to improve prose or add information.

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

CHECK 1: Grind Confidence Calibration
- Find GRIND_CONFIDENCE in claims.
- If GRIND_CONFIDENCE is LOW: verify the draft includes explicit uncertainty language
  (e.g., "rough estimate," "starting point," "based on a dissimilar coffee"). If the
  draft presents the grind setting as a confident recommendation without hedging → OBJECTION.
- If GRIND_CONFIDENCE is NONE: verify the draft explicitly says this is a default range
  estimate with no historical anchor. If not → OBJECTION.
- If GRIND_CONFIDENCE is HIGH or MEDIUM → PASS (no hedging required).

CHECK 2: Conditional vs. Universal Framing
- Find CONDITIONAL_RECOMMENDATIONS in claims. List every "if X → Y" recommendation.
- For each conditional: verify it is clearly framed as a branch (one of: "if you taste
  bitterness, go coarser; if sourness, go finer") rather than a flat recommendation.
- If two OPPOSITE adjustments (e.g., "finer" and "coarser") appear in the same
  recommendation block without explicit IF/ELSE framing → OBJECTION.
  Reason: a user reading "go finer" and "go coarser" in the same paragraph will not
  treat them as mutually exclusive. The framing must make the branching unambiguous.
- If any conditional is phrased as a general statement ("grind finer for better
  extraction") without the conditional trigger → OBJECTION.

CHECK 3: Adjustment Count for First Shot
- Find ADJUSTMENT_COUNT in claims.
- If ADJUSTMENT_COUNT > 2 for a first-shot recommendation → OBJECTION.
  Reason: recommending 3+ variables to dial simultaneously on the first shot creates
  too many unknowns. Limit to grind + one other (e.g., ratio), defer the rest to
  "if X, then also consider Y" guidance.

CHECK 4: Internal Alignment
- Cross-check TEMP, PRESSURE, and PROFILE against the same roast/processing archetype.
- Light roast indicators: temp ≥ 93°C, pressure ≤ 9 bar, profile = bloom or lever decline.
- Medium roast indicators: temp 91-93°C, pressure 8-9 bar, standard or bloom profile.
- Dark roast indicators: temp ≤ 91°C, pressure ≤ 8 bar, gentle/dark profile.
- If TEMP suggests light roast but PROFILE is Dark/Gentle (or vice versa) → OBJECTION.
  Reason: inconsistent archetype signals will confuse the user and produce mixed results.
```

---

## Arbiter Prompt Template

Use this prompt only when the critic returned OBJECTIONS. Substitute `{{DRAFT}}`,
`{{CLAIMS}}`, and `{{OBJECTIONS}}`:

```
You are a new-coffee recommendation arbiter. A critic has found reasoning errors in a
draft coffee recommendation. Your job is to produce a corrected recommendation that
resolves the objections.

Rules:
- Resolve every OBJECTION — do not leave any unaddressed.
- Preserve all correct information from the draft.
- For grind confidence: rewrite the estimate with language that matches the evidence
  strength. LOW confidence → use "roughly X as a starting point." NONE → use "the
  Sette 270 espresso range starts around X; expect to dial from there."
- For conditional framing: rewrite conflicting conditionals into a clear IF/ELSE
  structure. Example:
    "Start at 13E. After your first shot:
    → If it tastes sour or pulls fast: go 1 step finer.
    → If it tastes bitter or pulls slow: go 1 step coarser."
  Never put both branches in the same sentence without the conditional triggers.
- For adjustment count: reduce to the 1-2 most impactful variables. Move the rest to
  a "Secondary adjustments (only if needed)" section.
- For internal alignment: identify the correct roast/processing archetype and align all
  parameters to it. State which change you made and why.
- Add a single confidence note at the end of the Starting Parameters section:
  > *Grind confidence: [High/Medium/Low/None] — [one sentence: what the estimate is
    based on and how much to trust it]*

OBJECTIONS TO RESOLVE:
{{OBJECTIONS}}

ORIGINAL DRAFT:
{{DRAFT}}

CLAIMS:
{{CLAIMS}}
```

---

## Confidence Calibration

| Level | When to use |
|-------|-------------|
| **High** | Grind-map match is same roast + same process + same origin family |
| **Medium** | Same roast + same process, different origin |
| **Low** | Same roast only, or matching coffee had a very different profile style |
| **None** | No grind-map match; defaults used. Say so explicitly. |

The confidence note is always shown for new-coffee recommendations because the grind
starting point is the single variable the user most needs to calibrate their expectations
for. Never omit it.
