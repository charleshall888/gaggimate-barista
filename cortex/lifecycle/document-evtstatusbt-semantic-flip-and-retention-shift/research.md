# Research: Document evt:status.bt semantic flip and retention shift

## Epic Reference

This ticket scopes to the two cross-cutting firmware 1.8.0 semantic traps that don't belong in any sibling ticket. Broader epic context lives in [research/gaggimate-1-8-0-upgrade/research.md](../../research/gaggimate-1-8-0-upgrade/research.md). That file covers the full 1.8.0 upgrade surface — this research scopes only to the doc-pass items that remained after critical review narrowed 017 from seven topics to two.

## Codebase Analysis

### Files that will change

1. **`CLAUDE.md`** — add a new `### Firmware 1.8.0 semantic traps` subsection under the existing `## Important Notes` (lines 114–119), inserted after line 119 and before the `## Core Rules` header (line 121). Two bullets in the existing `- **Bold label**: body sentence.` format.

2. **`mcp/src/gaggimate_mcp/server.py`** — extend the `diagnose_connection` docstring (lines 679–690) with a WARNING paragraph. Best insertion: between the bulleted `This tool checks:` list (ends line 686) and `Returns:` (line 688). Single `WARNING:`-prefixed sentence, matches Google-style docstring convention used by sibling MCP tools.

3. **`mcp/src/gaggimate_mcp/parsers/shot.py`** — extend the module docstring (lines 1–4) with one added paragraph. The file **does not currently reference** `MAX_HISTORY_ENTRIES`, `MIN_FREE_SPACE_BYTES`, or any retention logic (verified via grep on `mcp/` tree — zero matches). This parser only decodes `.slog` bytes; it has no retention awareness today.

### Relevant existing patterns

**CLAUDE.md "Important Notes" bullet style** (lines 114–119): flat bullets under H2, `- **Bold label**: Body sentence.` No existing semantic-trap or firmware subsection — this is net-new territory, but the `## Important Notes` H2 is the established home for "behavioral gotchas the agent must remember" (weight anomalies, profile uploads, AI suffix rule).

**Python docstring WARNING style**: sibling MCP tools (`list_recent_shots`, `manage_shot_notes`, `diagnose_connection` itself) use Google-style docstrings: summary line → optional bullet list → `Args:` (if any) → `Returns:`. No prior `WARNING`/`NOTE` precedent exists in `server.py`. A `WARNING:` line inserted as its own paragraph before `Returns:` is the cleanest convention-consistent placement. The docstring is sent to the LLM verbatim as the tool description, so emphasis via an all-caps `WARNING:` prefix is the right signal.

**parsers/shot.py docstring style** (lines 1–4): one-line summary, blank line, one-sentence detail tying back to upstream firmware source (`Mirrors shot_log_format.h from the Gaggimate firmware.`). Extending this with a third paragraph about the retention shift matches the existing idiom exactly.

### Integration points — sibling-ticket conflict check

No conflicts. Scanned all `gaggimate-1-8-0-upgrade`-tagged backlog items for edits to `parsers/shot.py` or `diagnose_connection`:

| Ticket | Files touched | Overlap with 017? |
|---|---|---|
| 013 (epic) | none | none |
| 014 | `server.py` — only `manage_shot_notes` tool (not `diagnose_connection`) | no |
| 015 | `transformers/shot.py` (NOT `parsers/shot.py`) | no — 015 explicitly notes parser already reads `vf` |
| 016 | new fixtures + `mcp/tests/test_shot_regression.py` | no |
| 018 | new `mcp/src/gaggimate_mcp/diagnostics/phase_end_stop.py` + parity test | no |
| 021 | investigation-only — writes to `research/gaggimate-1-8-0-upgrade/verification-notes.md` | no |

The 017 top-of-file comment in `parsers/shot.py` will not collide with any planned sibling change.

### MEMORY.md + /consult verification

- **MEMORY.md source-of-truth table**: ticket 017 claims "the source-of-truth table already covers firmware semantics by pointing at CLAUDE.md." Verified: **false as-written** — no row currently points at CLAUDE.md for firmware semantics, `evt:status.bt`, or shot retention. The closest entries (`Profile JSON schema`, `Automatic Pro profile (firmware)`) do not cover these traps. The ticket's AC `MEMORY.md — no update required` is defensible anyway because CLAUDE.md is always loaded into session context (confirmed in the current session's system-reminder), so the CLAUDE.md subsection becomes always-available without needing a MEMORY.md pointer. However, strict adherence to MEMORY.md's "Facts live in ONE place" rule would favor adding a row like `Firmware 1.8.0 semantic traps → CLAUDE.md Important Notes`. Flagged as open decision for Spec.

- **/consult skill**: at `.claude/skills/consult/SKILL.md`. Routes by topic to `knowledge/*` files, not CLAUDE.md. Ticket's AC `/consult — no update required` is correct, but for a different stated reason than the ticket gives: not because `/consult` reads CLAUDE.md, but because CLAUDE.md is loaded unconditionally by the harness. No skill change needed.

### Verified Semantic Facts

Source: `research/gaggimate-1-8-0-upgrade/research.md`. These passages are the authoritative wording the implementer should paraphrase.

**Trap 1 — evt:status.bt semantic flip** (research.md line 41, "On-device data contracts"):

> `evt:status.bt` semantics: now reflects `profile.isVolumetric()` rather than `settings.isVolumetricTarget()`.

Corroborated at research.md line 15:

> Semantic shift: `evt:status.bt` now reflects selected profile's volumetric-target presence rather than the settings flag (trap for future consumers).

And at research.md line 107 (Per-feature recommendations):

> Documentation trap. Not read today, but flip is a pitfall for future connection-surface extensions. Add prominent note to CLAUDE.md + devnotes.

No firmware source-file path cited. The symbol names `profile.isVolumetric()` and `settings.isVolumetricTarget()` are sufficient documentation targets on their own.

**Trap 2 — Shot history retention shift** (research.md line 24, Research Question 5):

> Retention policy shifted: `MAX_HISTORY_ENTRIES = 100` removed, replaced by `MIN_FREE_SPACE_BYTES = 500 KB` floor. Our default `limit=10` is unaffected in the common case. ... Also: capacity purge now also deletes the companion `.json` sidecar — potential grind-map orphaning if notes moved to sidecar.

Sidecar co-deletion confirmed at research.md line 176:

> When capacity purge evicts a `.slog`, does it also evict the sidecar `.json`? Confirmed yes by the schema-diff agent. Implication: any grind-map reference to an old shot_id may orphan silently.

### Conventions to follow

- **CLAUDE.md**: `### Firmware 1.8.0 semantic traps` as H3 under the existing H2 `## Important Notes`. Exactly two bullets per AC.
- **server.py**: insert `WARNING:` paragraph as a single line inside the existing docstring between the `This tool checks:` list and `Returns:`.
- **parsers/shot.py**: extend the module docstring with a third paragraph (no separate `# NOTE:` comment block), maintaining the "one firmware-mirroring docstring at top" convention. Reference the firmware-side constant names (`MAX_HISTORY_ENTRIES`, `MIN_FREE_SPACE_BYTES`) so greps in other repos can find the note.

## Web Research

No upstream firmware documentation confirms either trap directly — the project's own discovery research is authoritative. Useful external patterns:

- **CLAUDE.md emphasis convention** (Anthropic guidance): use all-caps signal words (`IMPORTANT`, `WARNING`, `NEVER`) for behavioral traps; keep sections lean; "Would removing this cause Claude to make mistakes?" If not, cut it. Source: [Claude Code Best Practices](https://code.claude.com/docs/en/best-practices).

- **Trap documentation shape** (retention-docs pattern, AWS CDK `RemovalPolicy`, MS Purview retention, Databricks VACUUM): **trap → consequence → mitigation**, in three beats, minimum words. Name the specific field/flag/constant, not the category.

- **Gaggimate firmware 1.8.0 release notes** (https://github.com/jniebuhr/gaggimate/releases): PR #605 "Shot history index fixes and capacity-based history limit" corroborates the retention shift; PR #604 "Shot history async rebuild" implies storage-layout changes. `evt:status.bt` semantic flip is **not** documented upstream — ticket documentation stands on its own, referencing the project's own reverse-engineering.

- **MCP tool docstring convention**: docstrings are sent verbatim to the LLM as the tool description, so LLM-readable emphasis (inline `WARNING:` prefix) matters more than Sphinx `.. warning::` directives.

**Synthesized shape** the implementer can lean on for the CLAUDE.md bullets and the docstring WARNING:

```
WARNING: Trap-sentence (what changed). Consequence-sentence (what breaks).
         Mitigation-sentence (what to do instead).
```

## Requirements & Constraints

No `requirements/` directory exists. Stand-in constraint surface:

### From CLAUDE.md

- **"Important Notes" section** (lines 114–119) is the established home for "behavioral gotchas the agent must remember." 017's new subsection fits this genre exactly.
- **"Data Architecture" section** (lines 41–47) encodes auto-commit policy and symlink rules — **not applicable** to 017; all three target files (`CLAUDE.md`, `server.py`, `parsers/shot.py`) are ordinary project-repo files, not private-repo symlinks.
- **"Knowledge Files" section** (lines 18–32): enumerates the espresso-domain `knowledge/*` files. 017 does not target `knowledge/` (firmware plumbing is out of `/consult`'s routing scope).

### From MEMORY.md

- **"Facts live in ONE place"** (MEMORY.md line 3): the explicit single-source-of-truth rule. Code-comment ACs in 017 must be *pointers/warnings*, not copies of the CLAUDE.md prose.
- **Exception for always-available lookup tables**: "CLAUDE.md now embeds compact temp/pressure/ratio lookup tables for always-available context." Extending this exception to a new semantic-trap category is a live question — Spec should decide whether to add a MEMORY.md source-of-truth-table row for the new CLAUDE.md subsection (the ticket's AC says skip; the current MEMORY.md table content does not actually cover this; the rule is "facts live in ONE place" which an unmapped CLAUDE.md subsection technically satisfies).

### From parent epic 013

- Epic scope (line 32) lists 017 as exactly: `Documentation: evt:status.bt semantic flip + retention shift (017)` — two items, nothing more.
- Consolidation note (line 61): `Original 017 bundled 7 doc topics → narrowed to 2 cross-cutting semantic traps; vf doc moved into 015, DDSA doc moved into 018`. Explicit epic-level directive that `vf`, DDSA, `rssi`, mixed-era, and native-analyzer-UI docs are **not** in 017's scope.

### From discovery research

- Per-feature recommendation for `evt:status.bt` (research.md line 107): `Add prominent note to CLAUDE.md + devnotes.` — the doc location was directed at the discovery level.
- Feasibility assessment (research.md line 155): the original `S` sizing assumed cross-file propagation across CLAUDE.md + `knowledge/` + `knowledge/reference/` + skills/ + MEMORY.md; the narrowed 017 reduces this to CLAUDE.md + two code comments only.

## Tradeoffs & Alternatives

### Placement of CLAUDE.md bullets

- **A (ticket default) — new subsection under Important Notes**: ✅ Primes every session. Same genre as existing bullets. Stable anchor for code-comment cross-refs. Cost: 2 lines of firmware-specific prose in a barista-domain system prompt.
- **B — append to Core Rules**: ❌ Semantic mismatch. Core Rules is espresso quick-ref (dose, channeling, turbo ratios); firmware plumbing dilutes that section.
- **C — MEMORY.md Key Principles**: ❌ Violates MEMORY.md's explicit "facts live in ONE place" rule. MEMORY.md is the routing table, not content.
- **D — new `knowledge/reference/FIRMWARE_1_8_0_REFERENCE.md`**: ❌ `knowledge/` is scoped to espresso; `/consult` won't route firmware questions there; the agent won't load it unprompted.
- **E — MEMORY.md pointer + knowledge/ prose**: ❌ Over-engineering for two bullets.

**Pick A.** Same conclusion as the ticket.

### diagnose_connection WARNING scope

- **(a) Docstring WARNING (ticket default)**: ✅ Lives where the tool is defined; shows in IDE tooltips and greps; one-line pre-emptive cost.
- **(b) Skip — add when first read**: ❌ Defeats the trap-prevention intent; the first extender is exactly the person most likely to miss the flip.
- **(c) Shared `mcp/src/gaggimate_mcp/firmware_1_8_0_notes.md`**: ❌ No existing pattern in this repo for out-of-band notes files in the Python tree; such files drift.

**Pick (a).** Same as ticket.

### parsers/shot.py comment granularity

- **(a) One-line top-of-file (ticket default)**: ✅ Matches the existing one-liner docstring style.
- **(b) Multi-line docstring**: ❌ Overkill; the file parses binary and doesn't manage retention.
- **(c) Inline near shot_id code**: ❌ Doesn't exist — `shot.py` is the `.slog` byte parser; shot_id tracking lives elsewhere.
- **(d) Shared firmware-notes file**: ❌ Same orphan-file objection.

**Pick (a), with a refinement:** word the comment in terms of the *consequence visible to a reader of this file* (`shot_id references from grind-map may orphan — 1.8.0 replaced the 100-entry cap with a 500 KB free-space floor`), not just the cause. That converts a drive-by comment into actionable context for the parser reader.

### Consolidation — one file instead of three?

Rejected. Three dispersed surfaces serve three different readers: agent session prompt (CLAUDE.md), tool extender (docstring), parser maintainer (shot.py comment). Consolidating to `docs/FIRMWARE_1_8_0_NOTES.md` would:
1. Fail agent priming — a bare "see docs/…" in CLAUDE.md won't prime the agent.
2. Fail code-site discoverability — a comment pointing elsewhere is worse than an inline one-liner.
3. Introduce an orphan `docs/` folder (no such folder exists today).

**Dispersed is correct.** If 1.8.x traps multiply beyond 3–4, revisit then.

## Open Questions

- **MEMORY.md source-of-truth-table row**: should the ticket add a row like `Firmware 1.8.0 semantic traps → CLAUDE.md Important Notes`? The AC explicitly says skip; the requirements-alignment check shows the table doesn't actually cover this topic today. Spec should make the call:
  - *Deferred — will be resolved in Spec.* The ticket AC is probably authoritative (XS scope; adding a MEMORY.md row is out of stated scope), but the agent should confirm with the user during the Spec interview.

- **WARNING wording in `diagnose_connection`**: does the user want the `WARNING:` to state only the flip, or also acknowledge that `diagnose_connection` itself doesn't read the field today (pre-emptive placement)? The ticket body justifies pre-emptive placement but doesn't specify whether the docstring should itself acknowledge the pre-emption.
  - *Deferred — will be resolved in Spec.*

- **parsers/shot.py comment framing**: does the user prefer the comment's framing to emphasize the consequence (`shot_id may orphan silently`) or the cause (`retention changed from count cap to free-space floor`)? Research recommends consequence-first for parser-maintainer relevance.
  - *Deferred — will be resolved in Spec.*
