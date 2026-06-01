# Specification: document-evtstatusbt-semantic-flip-and-retention-shift

> See [research/gaggimate-1-8-0-upgrade/research.md](../../research/gaggimate-1-8-0-upgrade/research.md) for the epic-level firmware 1.8.0 upgrade research that identified these two traps as cross-cutting items.

## Problem Statement

Firmware 1.8.0 introduced two cross-cutting semantic changes that don't belong inside any single feature ticket: `evt:status.bt` now reflects `profile.isVolumetric()` instead of `settings.isVolumetricTarget()`, and shot-history retention switched from a 100-entry count cap (`MAX_HISTORY_ENTRIES = 100`) to a 500 KB free-space floor (`MIN_FREE_SPACE_BYTES = 500 KB`) with companion `.json` sidecar co-deletion on purge. These traps are easy to miss — the first silently flips the meaning of a connection field that future tooling is likely to read; the second silently orphans old `shot_id` references from `grind-map.md` when capacity is exceeded. This ticket documents both in three dispersed locations chosen so each future reader (agent session, tool extender, parser maintainer) sees the relevant trap at the moment they need it, with cross-references between them so drift is visible to anyone editing any single surface.

## Requirements

1. **CLAUDE.md subsection placed under "Important Notes"**: A new `### Firmware 1.8.0 semantic traps` H3 subsection is inserted inside the existing `## Important Notes` section of `/Users/charlie.hall/Workspaces/gaggimate-barista/CLAUDE.md`, after the last existing Important Notes bullet and before the `---` separator / `## Core Rules` heading. The subsection contains **exactly two bullets**, each in the `- **Bold label**: Body sentence(s).` style matching the rest of the section. Acceptance:
   - `grep -c '^### Firmware 1.8.0 semantic traps$' CLAUDE.md` = 1
   - The subsection is inside the `## Important Notes` section. Verify with `awk '/^## Important Notes$/,/^## Core Rules$/' CLAUDE.md | grep -c '^### Firmware 1.8.0 semantic traps$'` = 1
   - Bullet count: `awk '/^### Firmware 1.8.0 semantic traps$/,/^###|^##|^---$/' CLAUDE.md | grep -c '^- \*\*'` = 2

2. **CLAUDE.md bullet 1 — evt:status.bt flip with explicit direction**: The first bullet names `evt:status.bt`, states **both** the pre-1.8.0 meaning (`settings.isVolumetricTarget()`) **and** the 1.8.0 meaning (`profile.isVolumetric()`) with explicit temporal markers (e.g., `"pre-1.8.0 ... reflected ... ; in 1.8.0 ... reflects ..."` or equivalent phrasing that unambiguously identifies which symbol belongs to which era), and warns that future `diagnose_connection`-style extensions must account for the flip. One sentence is a target; clarity over brevity is allowed. Acceptance:
   - `awk '/^### Firmware 1.8.0 semantic traps$/,/^###|^##|^---$/' CLAUDE.md | grep -E 'evt:status.bt' | grep 'profile.isVolumetric()' | grep -c 'settings.isVolumetricTarget()'` = 1 (one line mentions all three identifiers)
   - The same line contains a pre/post temporal marker. Verify: `awk '/^### Firmware 1.8.0 semantic traps$/,/^###|^##|^---$/' CLAUDE.md | grep 'evt:status.bt' | grep -E -c 'pre-1\.8\.0|before 1\.8\.0|1\.7|prior to 1\.8\.0'` ≥ 1 AND `... | grep -E -c 'in 1\.8\.0|from 1\.8\.0|as of 1\.8\.0|now'` ≥ 1.

3. **CLAUDE.md bullet 2 — retention shift with all three facts**: The second bullet states that 1.8.0 replaced `MAX_HISTORY_ENTRIES = 100` with `MIN_FREE_SPACE_BYTES = 500 KB`, notes that capacity purge also deletes the companion `.json` sidecar, and flags that older `shot_id` references in `grind-map.md` may orphan silently. Acceptance:
   - `awk '/^### Firmware 1.8.0 semantic traps$/,/^###|^##|^---$/' CLAUDE.md | grep -c 'MAX_HISTORY_ENTRIES'` ≥ 1
   - `awk '/^### Firmware 1.8.0 semantic traps$/,/^###|^##|^---$/' CLAUDE.md | grep -c 'MIN_FREE_SPACE_BYTES'` ≥ 1
   - `awk '/^### Firmware 1.8.0 semantic traps$/,/^###|^##|^---$/' CLAUDE.md | grep -Ec 'sidecar|\.json'` ≥ 1
   - `awk '/^### Firmware 1.8.0 semantic traps$/,/^###|^##|^---$/' CLAUDE.md | grep -Ec 'orphan|grind-map'` ≥ 1

4. **server.py `diagnose_connection` docstring WARNING**: The docstring of the `diagnose_connection` tool in `/Users/charlie.hall/Workspaces/gaggimate-barista/mcp/src/gaggimate_mcp/server.py` is extended with a `WARNING:`-prefixed paragraph inserted inside the existing docstring (after the `This tool checks:` bullet list and before `Returns:`). Requirements on the WARNING text:
   - **Acknowledges pre-emption**: states that this tool does not currently read `evt:status.bt`, but future extensions that do must account for the flip.
   - **States both eras explicitly**: names both `profile.isVolumetric()` and `settings.isVolumetricTarget()` with a temporal marker that unambiguously identifies which belongs to which era. Drop the unsupported "1.8.0+" forward-compatibility phrasing — say "in firmware 1.8.0" (specific), not "1.8.0+".
   - **Cross-references CLAUDE.md**: includes a pointer like "see CLAUDE.md § Firmware 1.8.0 semantic traps" so a docstring editor is prompted to update CLAUDE.md in lockstep.

   Acceptance:
   - `awk '/async def diagnose_connection/,/^    """$/' mcp/src/gaggimate_mcp/server.py | grep -c 'WARNING:'` ≥ 1
   - `awk '/async def diagnose_connection/,/^    """$/' mcp/src/gaggimate_mcp/server.py | grep -c 'evt:status.bt'` ≥ 1
   - `awk '/async def diagnose_connection/,/^    """$/' mcp/src/gaggimate_mcp/server.py | grep -c 'profile.isVolumetric()'` ≥ 1
   - `awk '/async def diagnose_connection/,/^    """$/' mcp/src/gaggimate_mcp/server.py | grep -c 'settings.isVolumetricTarget()'` ≥ 1
   - `awk '/async def diagnose_connection/,/^    """$/' mcp/src/gaggimate_mcp/server.py | grep -c 'CLAUDE.md'` ≥ 1
   - `awk '/async def diagnose_connection/,/^    """$/' mcp/src/gaggimate_mcp/server.py | grep -Ec '1\.8\.0\+'` = 0 (no forward-compat phrasing)

5. **parsers/shot.py module docstring extension**: The module docstring of `/Users/charlie.hall/Workspaces/gaggimate-barista/mcp/src/gaggimate_mcp/parsers/shot.py` is extended with one additional paragraph in **consequence-first framing**. Requirements on the paragraph text:
   - **Consequence first**: the opening sentence names the reader-visible problem (old `shot_id` references may be silently orphaned) before the mechanism (retention switch).
   - **Mechanism next**: explicitly names both constant names (`MAX_HISTORY_ENTRIES`, `MIN_FREE_SPACE_BYTES`) and the `.json` sidecar co-deletion.
   - **Explicit pre/post framing**: identifies `MAX_HISTORY_ENTRIES` as the pre-1.8.0 mechanism and `MIN_FREE_SPACE_BYTES` as the 1.8.0 replacement (not just listing both).
   - **Cross-references CLAUDE.md**: includes a pointer to "see CLAUDE.md § Firmware 1.8.0 semantic traps" so a parser editor is prompted to update CLAUDE.md in lockstep.

   Acceptance (extract the leading module docstring with an awk range, not a fragile `head -N`):
   - `awk 'NR==1,/^"""$/' mcp/src/gaggimate_mcp/parsers/shot.py | grep -c 'shot_id'` ≥ 1
   - `awk 'NR==1,/^"""$/' mcp/src/gaggimate_mcp/parsers/shot.py | grep -c 'MAX_HISTORY_ENTRIES'` ≥ 1
   - `awk 'NR==1,/^"""$/' mcp/src/gaggimate_mcp/parsers/shot.py | grep -c 'MIN_FREE_SPACE_BYTES'` ≥ 1
   - `awk 'NR==1,/^"""$/' mcp/src/gaggimate_mcp/parsers/shot.py | grep -Ec 'sidecar|\.json'` ≥ 1
   - `awk 'NR==1,/^"""$/' mcp/src/gaggimate_mcp/parsers/shot.py | grep -c 'CLAUDE.md'` ≥ 1

6. **Scope containment — only the three named files change**: Only `CLAUDE.md`, `mcp/src/gaggimate_mcp/server.py`, and `mcp/src/gaggimate_mcp/parsers/shot.py` are modified by this ticket. Acceptance: `git diff --name-only main...HEAD` (where `main` is the merge base of the work branch) or equivalent on the work branch lists exactly those three files — no more, no fewer. When running outside a branch workflow, substitute `git diff --name-only HEAD@{1}` or an explicit pre-change commit ref captured before any edits; the ref must be named in the implementation plan, not left implicit.

7. **Regression safety — existing Important Notes content preserved**: The four existing Important Notes bullets (Weight anomalies, Profile uploads, Personal taste, AI profiles) remain in place and unmodified. Acceptance:
   - `grep -c '^- \*\*Weight anomalies\*\*' CLAUDE.md` = 1
   - `grep -c '^- \*\*Profile uploads\*\*' CLAUDE.md` = 1
   - `grep -c '^- \*\*Personal taste\*\*' CLAUDE.md` = 1
   - `grep -c '^- \*\*AI profiles\*\*' CLAUDE.md` = 1
   - `awk '/^## Important Notes$/,/^## Core Rules$/' CLAUDE.md | grep -c '^- \*\*'` = 6 (four existing + two new, both at the H2-level bullet depth). Note: the two new bullets live inside the H3 subsection; if the H3 format places them as `- **Label**:` at the same indent depth as the existing four, the count is 6. If a reviewer finds the implementer used a different bullet indent/format inside the H3, acceptance still passes as long as the four original bullets match their individual greps above.

## Non-Requirements

- **No MEMORY.md update.** Per user decision and ticket AC. CLAUDE.md is loaded unconditionally into every session so the new subsection is always available; a MEMORY.md source-of-truth-table row is out of scope for this XS ticket.
- **No `vf` / DDSA / `rssi` / native-analyzer-UI / mixed-era documentation.** Those belong inside their code-producing sibling tickets (015, 018, 021 and follow-ups) and are explicit Anti-scope in the ticket body.
- **No new `knowledge/` or `docs/` file.** Three dispersed surfaces serve three different readers (agent prompt, tool extender, parser maintainer); consolidating to a standalone doc file would fail agent priming, fail code-site discoverability, and create an orphan folder with no existing repo precedent.
- **No `/consult` skill update.** `/consult` routes by keyword to `knowledge/*` files; it does not read CLAUDE.md directly. The new subsection becomes available via the unconditional CLAUDE.md load, not via skill routing.
- **No behavioural code changes.** This is a prose-only ticket — no Python logic, no JSON schema, no test edits. Adding tests is explicitly out of scope for three one-line edits.
- **No firmware source verification.** Research cited the symbol names (`profile.isVolumetric()`, `settings.isVolumetricTarget()`, `MAX_HISTORY_ENTRIES`, `MIN_FREE_SPACE_BYTES`) but no firmware source-file paths. This ticket trusts research.md verbatim; cross-verifying against firmware source is ticket 021's domain. If 021 later proves a claim inverted, this ticket's three surfaces all need correction — the cross-references required by Req 4 and Req 5 make that correction visible to anyone editing any one file.
- **No filing of a separate drift-management ticket.** The cross-references required by Req 4 and Req 5 (every code-site prose refers to CLAUDE.md) are the drift-mitigation for this ticket. A future rename or firmware semantic change will be visible to anyone editing any surface; a separate drift-tracking ticket is out of this ticket's XS scope.

## Edge Cases

- **CLAUDE.md "Important Notes" section relocates later**: If a future restructure moves or renames `## Important Notes`, the `### Firmware 1.8.0 semantic traps` subsection is expected to travel with it, and the cross-reference pointers in `server.py` and `parsers/shot.py` (which name the subsection title, not a line number) remain valid as long as the subsection keeps its title.
- **`diagnose_connection` docstring is ever regenerated / reformatted**: The WARNING paragraph must be resilient to minor whitespace reflow. Keep the WARNING as a single paragraph (no multi-line bullets). The acceptance greps use `awk` to extract the whole docstring range, not a fixed line window — so line-wrapping doesn't break the check.
- **`parsers/shot.py` gains future retention logic**: If ticket 021 or a follow-up implements retention handling in this file, the module-docstring paragraph should be kept and expanded, not removed.
- **Sidecar-deletion behaviour changes in firmware 1.8.x+**: The cross-reference required by Req 5 means anyone editing `parsers/shot.py`'s docstring will be pointed at CLAUDE.md and prompted to update both in lockstep. Drift to 1.8.1/1.9.x semantics is visible, not silent.
- **Research.md is wrong about flip direction**: The explicit pre/post temporal framing required by Req 2 (CLAUDE.md), Req 4 (server.py WARNING), and Req 5 (parsers/shot.py docstring) means that a reader reviewing any of the three surfaces can catch an inversion against the firmware source. If 021 proves the research inverted, the three cross-referenced surfaces are corrected as a unit.

## Changes to Existing Behavior

- **ADDED**: A new `### Firmware 1.8.0 semantic traps` subsection under `## Important Notes` in CLAUDE.md (~4 additional always-loaded lines). No modification or removal of the four existing Important Notes bullets.
- **MODIFIED**: `diagnose_connection` tool docstring gains a WARNING paragraph with a CLAUDE.md cross-reference. The tool's runtime behaviour is unchanged; only the docstring (which MCP sends to the LLM as the tool description) grows by one paragraph.
- **MODIFIED**: `parsers/shot.py` module docstring gains one paragraph with a CLAUDE.md cross-reference. Parser behaviour is unchanged.
- No removed behaviour.

## Technical Constraints

- **CLAUDE.md subsection header style**: H3 (`### Firmware 1.8.0 semantic traps`) under the existing H2 `## Important Notes`. Match the flat bullet style (`- **Bold label**: Body sentence.`) of the parent section.
- **Docstring WARNING placement in server.py**: Insert between the `This tool checks:` bullet list and the `Returns:` block. Single `WARNING:`-prefixed paragraph, no bullet. Match Google-style docstring convention already in use.
- **parsers/shot.py docstring extension**: Extend the existing module docstring with a third paragraph — do not introduce a separate `# NOTE:` comment block below the docstring. Preserves the file's "one firmware-mirroring docstring at top" convention.
- **Consequence-first framing in parsers/shot.py**: Paragraph opens with the reader-visible consequence (old `shot_id` references silently orphaning), not the cause (retention switch). Per user decision in §2.
- **Explicit pre-1.8.0 vs 1.8.0 framing in all three surfaces**: The bullet/WARNING/docstring paragraph in each location must identify which symbol (or constant) belongs to which era with unambiguous temporal markers — not "reflects X rather than Y" (direction-ambiguous). Use forms like "pre-1.8.0 reflected X; in 1.8.0 reflects Y" or "was X; now Y as of 1.8.0". This makes a future inversion editor-visible and grep-detectable.
- **Cross-references from code sites to CLAUDE.md**: server.py and parsers/shot.py both include the literal string "CLAUDE.md" and the subsection title "Firmware 1.8.0 semantic traps". Acts as a drift-surface signal to editors.
- **WARNING in server.py acknowledges pre-emption**: The WARNING text explicitly notes that `diagnose_connection` doesn't read `evt:status.bt` today but any future extension must.
- **No "1.8.0+" forward-compat phrasing**: Say "in firmware 1.8.0" (exact) or "as of firmware 1.8.0" (dated). The `+` asserts forward compatibility the spec cannot guarantee — firmware has flipped semantics once already.
- **Symbol names must match research verbatim**: `profile.isVolumetric()`, `settings.isVolumetricTarget()`, `MAX_HISTORY_ENTRIES`, `MIN_FREE_SPACE_BYTES`, `500 KB`. Do not paraphrase these identifiers; implementers in future will grep for them.
- **Auto-commit not applicable**: All three target files are ordinary project-repo files, not private-data-repo symlinks. CLAUDE.md's auto-commit policy (lines 41–47) does not apply.
- **Acceptance greps use `awk` ranges, not fixed line windows**: Per the critical-review pass, `head -N` and `grep -A N` break on natural prose line-wrapping. Use `awk` range patterns (`/START/,/END/`) to extract the relevant section, then grep within.

## Open Decisions

None. All three deferred research questions were resolved in the §2 user interview, and critical-review objections were either applied as spec strengthening or dismissed with rationale.
