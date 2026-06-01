# Plan: document-evtstatusbt-semantic-flip-and-retention-shift

## Overview

Four tasks: one pre-flight (capture git baseline + re-verify anchor points), three parallel prose edits (CLAUDE.md, server.py diagnose_connection docstring, parsers/shot.py module docstring), and one verification-and-commit task. Tasks 1–3 **do not commit** — they leave a dirty working tree that Task 4 then verifies and commits atomically via the `/commit` skill. This design makes the baseline ref unambiguous, avoids parallel-commit races on the shared working tree, and produces a single "017: document evt:status.bt flip + retention shift" commit that satisfies the spec's Req 6 scope-containment check.

## Commit Model (authoritative)

This plan uses a **single atomic commit** produced by Task 4. Tasks 1–3 edit files but MUST NOT run `git add` or `git commit` — they leave changes as unstaged modifications. Only Task 4 runs `/commit`. Rationale: (a) the overnight runner dispatches `Depends on: none` tasks in parallel on a shared working tree, so per-task `git` invocations race on `.git/index.lock`; (b) the spec's Req 6 scope check (`git diff --name-only $BASELINE_REF..HEAD` lists exactly three files) is cleanest when all three edits land in a single commit. The `/commit` skill is the commit path, per the user's global CLAUDE.md rule.

## Tasks

### Task 0: Pre-flight — capture baseline + re-verify anchors
- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/lifecycle/document-evtstatusbt-semantic-flip-and-retention-shift/.baseline-ref` (new; created by this task)
- **What**: Capture the current `git rev-parse HEAD` into `lifecycle/{feature}/.baseline-ref` for Task 4's scope check. Then verify the three anchor points named in Tasks 1–3 still match expected content (CLAUDE.md `## Important Notes`, server.py `async def diagnose_connection`, parsers/shot.py leading module docstring). Line numbers may have drifted since plan-write time (2026-04-19) if sibling ticket 014 or other work landed — the grep checks below are content-addressed and will still locate the anchors even after drift, so the implementer should NOT treat the line numbers in Tasks 1–3 Context as authoritative; they are plan-write-time observations.
- **Depends on**: none
- **Complexity**: simple
- **Context**:
  - Work is being performed on branch `main` (per current `git status`). `git merge-base` against main degenerates on main; instead, capture the exact pre-feature HEAD commit SHA.
  - Tasks 1–3 will run in parallel after this task completes. Task 4 reads `.baseline-ref` to know which commit to diff against.
  - The `.baseline-ref` file lives inside the lifecycle directory so it is co-located with other lifecycle artifacts; it is not committed (it's transient).
- **Verification**:
  - Baseline captured: `test -s lifecycle/document-evtstatusbt-semantic-flip-and-retention-shift/.baseline-ref && git cat-file -e $(cat lifecycle/document-evtstatusbt-semantic-flip-and-retention-shift/.baseline-ref)^{commit}` exits 0 — pass if the file exists, is non-empty, and names a valid commit object.
  - Anchor 1 (CLAUDE.md): `grep -c '^## Important Notes$' CLAUDE.md` = 1 — pass if count = 1.
  - Anchor 2 (server.py): `grep -c 'async def diagnose_connection' mcp/src/gaggimate_mcp/server.py` = 1 — pass if count = 1.
  - Anchor 3 (parsers/shot.py): `awk 'NR==1 && /^"""/{found=1} /^"""/ && NR>1 && found{print "OK"; exit}' mcp/src/gaggimate_mcp/parsers/shot.py` prints `OK` — pass if output is `OK` (confirms a leading module docstring delimited by `"""` exists, regardless of exact line numbers).
- **Status**: [x] completed

### Task 1: Add "Firmware 1.8.0 semantic traps" subsection to CLAUDE.md
- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/CLAUDE.md`
- **What**: Insert a new `### Firmware 1.8.0 semantic traps` H3 subsection inside the existing `## Important Notes` section, after its last existing bullet and before the next H2 section. The subsection contains exactly two bullets, using the same `- **Bold label**: Body sentence(s).` style as the parent section. **Do not run `git add` or `git commit`** — leave the edit unstaged for Task 4.
- **Depends on**: [0]
- **Complexity**: simple
- **Context**:
  - At plan-write time (2026-04-19), `## Important Notes` sat at CLAUDE.md lines 114–119 with four bullets (Weight anomalies, Profile uploads, Personal taste, AI profiles), followed by `---` separator on line 120 and `## Core Rules` on line 121. Re-verify with the Task 0 anchor grep before editing — line numbers may have drifted.
  - Existing bullet style: `- **Bold label**: Body sentence.` Match this style exactly.
  - **Bullet 1 must encode explicit pre/post-era pairing**. The recommended phrasing model: *"**`evt:status.bt` semantic flip**: pre-1.8.0 this field reflected `settings.isVolumetricTarget()`; in 1.8.0 it reflects `profile.isVolumetric()` — future `diagnose_connection`-style extensions reading this field must account for the flip."* The ordering — old symbol with pre-era marker first, new symbol with post-era marker second — is the directional-inversion guard; the verification grep below enforces this pairing.
  - **Bullet 2 must encode all four retention facts with pre/post-era pairing**. Recommended phrasing: *"**Shot history retention**: 1.8.0 replaced `MAX_HISTORY_ENTRIES = 100` (pre-1.8.0 count cap) with a `MIN_FREE_SPACE_BYTES = 500 KB` free-space floor; capacity purge also deletes the companion `.json` sidecar, so old `shot_id` references in `grind-map.md` may orphan silently."*
  - Do not use "1.8.0+" phrasing anywhere — use "in 1.8.0", "as of 1.8.0", or "1.8.0 replaced".
  - Source for all facts: `research/gaggimate-1-8-0-upgrade/research.md` lines 15, 24, 41, 42, 107, 176 (quoted in lifecycle `research.md` under "Verified Semantic Facts").
- **Verification**:
  - Subsection present and unique: `grep -c '^### Firmware 1.8.0 semantic traps$' CLAUDE.md` = 1.
  - Subsection inside `## Important Notes`: `awk '/^## Important Notes$/,/^## /' CLAUDE.md | grep -c '^### Firmware 1.8.0 semantic traps$'` = 1. (Stop pattern `/^## /` matches the next H2 unambiguously.)
  - Bullet 1 present with all three identifiers on one line: `awk '/^### Firmware 1.8.0 semantic traps$/,/^## /' CLAUDE.md | grep 'evt:status.bt' | grep 'profile.isVolumetric()' | grep -c 'settings.isVolumetricTarget()'` = 1.
  - **Directional inversion guard — pre-era marker tied to OLD symbol**: `awk '/^### Firmware 1.8.0 semantic traps$/,/^## /' CLAUDE.md | grep -E 'pre-1\.8\.0|before 1\.8\.0|prior to 1\.8\.0|1\.7' | grep -c 'settings.isVolumetricTarget()'` ≥ 1 — pass if the pre-era marker appears on a line also containing the OLD symbol.
  - **Directional inversion guard — post-era marker tied to NEW symbol**: `awk '/^### Firmware 1.8.0 semantic traps$/,/^## /' CLAUDE.md | grep -E 'in 1\.8\.0|as of 1\.8\.0|1\.8\.0 replaced|now reflects' | grep -c 'profile.isVolumetric()'` ≥ 1 — pass if the post-era marker appears on a line also containing the NEW symbol.
  - Bullet 2 retention facts: each of `grep -c 'MAX_HISTORY_ENTRIES'`, `grep -c 'MIN_FREE_SPACE_BYTES'`, `grep -Ec 'sidecar|\.json'`, `grep -Ec 'orphan|grind-map'` run against `awk '/^### Firmware 1.8.0 semantic traps$/,/^## /' CLAUDE.md` returns ≥ 1.
  - No forward-compat phrasing: `awk '/^### Firmware 1.8.0 semantic traps$/,/^## /' CLAUDE.md | grep -Ec '1\.8\.0\+'` = 0.
  - New bullets match parent-section format: `awk '/^### Firmware 1.8.0 semantic traps$/,/^## /' CLAUDE.md | grep -cE '^- \*\*[^*]+\*\*:'` = 2 — pass if exactly two bullets match the `- **Label**: ...` style.
  - Four existing Important Notes bullets preserved: each of `grep -c '^- \*\*Weight anomalies\*\*' CLAUDE.md`, `grep -c '^- \*\*Profile uploads\*\*' CLAUDE.md`, `grep -c '^- \*\*Personal taste\*\*' CLAUDE.md`, `grep -c '^- \*\*AI profiles\*\*' CLAUDE.md` = 1.
- **Status**: [x] completed

### Task 2: Add pre-emption WARNING to diagnose_connection docstring
- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/mcp/src/gaggimate_mcp/server.py`
- **What**: Insert a `WARNING:`-prefixed paragraph inside the existing `diagnose_connection` docstring, positioned after the `This tool checks:` bullet list and before the `Returns:` block. The WARNING must: (a) acknowledge pre-emption (this tool does not currently read `evt:status.bt`), (b) name both symbols with explicit pre/post-era pairing (old symbol with pre-era marker, new symbol with post-era marker, in that order — same directional-inversion guard as Task 1 bullet 1), (c) cross-reference the CLAUDE.md subsection by its **exact** title ("Firmware 1.8.0 semantic traps"). Do not use "1.8.0+" phrasing. **Do not `git add` or `git commit`** — leave the edit unstaged.
- **Depends on**: [0]
- **Complexity**: simple
- **Context**:
  - At plan-write time, the tool was at `@mcp.tool()` line 677 and `async def diagnose_connection() -> str:` line 678; docstring spanned lines 679–690. If sibling ticket 014 (which edits `manage_shot_notes` upstream at lines 514–628) has landed, these line numbers shifted — use the content grep from Task 0 to locate `async def diagnose_connection` at the current line.
  - Google-style docstring convention matches sibling tools (`list_recent_shots`, `manage_shot_notes`).
  - Recommended phrasing model: *"WARNING: This tool does not currently read `evt:status.bt`, but any future extension that does must account for firmware 1.8.0's semantic flip: pre-1.8.0 this field reflected `settings.isVolumetricTarget()`; in firmware 1.8.0 it reflects `profile.isVolumetric()`. See CLAUDE.md § Firmware 1.8.0 semantic traps."*
- **Verification**:
  - Use `awk` to extract the `diagnose_connection` docstring range — the open pattern is `/async def diagnose_connection/`, the close pattern is `/^    """$/` (first docstring close, 4-space indent).
  - WARNING present: extracted range `| grep -c 'WARNING:'` ≥ 1.
  - Field name present: extracted range `| grep -c 'evt:status.bt'` ≥ 1.
  - Both symbols present: extracted range `| grep -c 'profile.isVolumetric()'` ≥ 1 AND extracted range `| grep -c 'settings.isVolumetricTarget()'` ≥ 1.
  - **Directional inversion guard — pre-era marker tied to OLD symbol**: extracted range `| grep -E 'pre-1\.8\.0|before 1\.8\.0|prior to 1\.8\.0' | grep -c 'settings.isVolumetricTarget()'` ≥ 1.
  - **Directional inversion guard — post-era marker tied to NEW symbol**: extracted range `| grep -E 'in 1\.8\.0|as of 1\.8\.0' | grep -c 'profile.isVolumetric()'` ≥ 1.
  - Cross-reference to CLAUDE.md section by **exact title**: extracted range `| grep -c 'Firmware 1.8.0 semantic traps'` ≥ 1. (This is tighter than a bare `CLAUDE.md` match — it enforces the code-site→subsection title pairing.)
  - No forward-compat phrasing: extracted range `| grep -Ec '1\.8\.0\+'` = 0.
- **Status**: [x] completed

### Task 3: Extend parsers/shot.py module docstring with retention note
- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/mcp/src/gaggimate_mcp/parsers/shot.py`
- **What**: Extend the **leading module docstring** (first `"""…"""` block at the top of the file) with one additional paragraph in consequence-first framing: open with "old `shot_id` references … may be silently orphaned"; then state the mechanism (pre-1.8.0 `MAX_HISTORY_ENTRIES = 100` count cap → 1.8.0 `MIN_FREE_SPACE_BYTES = 500 KB` free-space floor, with `.json` sidecar co-deletion); include cross-reference to CLAUDE.md's subsection by its **exact** title. Do not use "1.8.0+". **Do not `git add` or `git commit`** — leave the edit unstaged.
- **Depends on**: [0]
- **Complexity**: simple
- **Context**:
  - At plan-write time, the existing docstring occupied lines 1–4:
    ```
    """Parser for .slog binary shot files.

    Mirrors shot_log_format.h from the Gaggimate firmware.
    """
    ```
  - **Fallback instruction**: if lines 1–4 no longer match this content, locate the file's leading module docstring by finding the first two `"""` delimiters (the opening at line 1 or the line after any shebang/future-import, and the first closing `"""` after that). Extend that docstring regardless of its line position — the acceptance verification is content-addressed.
  - Extend the same docstring with a third paragraph — do NOT introduce a separate `# NOTE:` comment below. Preserves the file's one-docstring-at-top convention.
  - File does NOT currently reference `MAX_HISTORY_ENTRIES` or `MIN_FREE_SPACE_BYTES` anywhere — this paragraph is the sole reference.
  - Recommended phrasing model: *"Firmware 1.8.0 retention note: old `shot_id` references (e.g. from `grind-map.md`) may be silently orphaned — retention switched from a pre-1.8.0 100-entry count cap (`MAX_HISTORY_ENTRIES = 100`) to a 1.8.0 `MIN_FREE_SPACE_BYTES = 500 KB` free-space floor, and capacity purge also deletes the companion `.json` sidecar. See CLAUDE.md § Firmware 1.8.0 semantic traps."*
- **Verification**:
  - Extract the leading docstring range with awk — open pattern matches the first `"""` and close pattern matches the next `"""` on its own line: `awk '/^"""/{if(++n==1)found=1; else if(found){print; exit} } found' mcp/src/gaggimate_mcp/parsers/shot.py` captures lines between the first and second `"""` delimiters (inclusive of the closing line), robust to added shebangs or future imports that may push the docstring off line 1.
  - For the greps below, use a simpler awk range that captures the same region and is easier to pipe: `awk 'NR==1,/^"""$/' mcp/src/gaggimate_mcp/parsers/shot.py` — this works for the standard case of the docstring starting at line 1. If the file later gains leading code before the docstring, use the more robust extraction above.
  - Consequence language present: extracted range `| grep -c 'shot_id'` ≥ 1.
  - Both constant names present: extracted range `| grep -c 'MAX_HISTORY_ENTRIES'` ≥ 1 AND extracted range `| grep -c 'MIN_FREE_SPACE_BYTES'` ≥ 1.
  - Sidecar fact present: extracted range `| grep -Ec 'sidecar|\.json'` ≥ 1.
  - **Directional marker — pre-era tied to OLD constant**: extracted range `| grep -E 'pre-1\.8\.0|before 1\.8\.0|prior to 1\.8\.0' | grep -c 'MAX_HISTORY_ENTRIES'` ≥ 1.
  - Cross-reference to CLAUDE.md section by **exact title**: extracted range `| grep -c 'Firmware 1.8.0 semantic traps'` ≥ 1.
  - No forward-compat phrasing: extracted range `| grep -Ec '1\.8\.0\+'` = 0.
- **Status**: [x] completed

### Task 4: Full-spec verification and /commit
- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/CLAUDE.md`, `/Users/charlie.hall/Workspaces/gaggimate-barista/mcp/src/gaggimate_mcp/server.py`, `/Users/charlie.hall/Workspaces/gaggimate-barista/mcp/src/gaggimate_mcp/parsers/shot.py`
- **What**: (1) Read the baseline SHA from `lifecycle/{feature}/.baseline-ref` (written by Task 0). (2) Run the full spec acceptance grep suite (all Task 1/2/3 greps re-run against the now-modified working tree). (3) Run the spec's Req 6 scope-containment check: `git diff --name-only $(cat lifecycle/.../.baseline-ref)..HEAD` plus `git status --porcelain -- lifecycle/{feature}/`-excluded, must list exactly the three target files. (4) Invoke the `/commit` skill to create a single commit; the commit message should include the ticket id `017` and a short summary. (5) After `/commit` completes, re-run the scope check (now between baseline and the new HEAD) and the commit-log grep.
- **Depends on**: [1, 2, 3]
- **Complexity**: simple
- **Context**:
  - Commit model is single-atomic via `/commit` skill per the "Commit Model" section at the top of this plan and the user's global CLAUDE.md rule. **Do not run `git commit` directly** — always through `/commit`.
  - Before `/commit` runs, Tasks 1–3's edits are unstaged in the working tree; the correct baseline-to-current diff is `git diff --name-only $BASELINE_REF` (no `..HEAD`, which would exclude unstaged changes). After `/commit` completes, the diff is `git diff --name-only $BASELINE_REF..HEAD`.
  - `.baseline-ref` is a transient lifecycle artifact — do NOT commit it. Either delete it as part of Task 4, or ensure the `/commit` skill does not stage lifecycle/*/.baseline-ref.
  - Auto-commit policy in project CLAUDE.md does NOT apply (target files are project-repo files, not private-data-repo symlinks).
- **Verification**:
  - All Task 1 greps pass against current CLAUDE.md (re-run full Task 1 Verification list).
  - All Task 2 greps pass against current server.py (re-run full Task 2 Verification list).
  - All Task 3 greps pass against current parsers/shot.py (re-run full Task 3 Verification list).
  - **Pre-commit scope check**: `git diff --name-only $(cat lifecycle/document-evtstatusbt-semantic-flip-and-retention-shift/.baseline-ref) -- CLAUDE.md 'mcp/src/gaggimate_mcp/**'` lists exactly `CLAUDE.md`, `mcp/src/gaggimate_mcp/parsers/shot.py`, `mcp/src/gaggimate_mcp/server.py` — pass if the sorted output matches exactly those three paths.
  - **Scope check — no other files changed**: `git diff --name-only $(cat lifecycle/.../.baseline-ref) -- . ':!CLAUDE.md' ':!mcp/src/gaggimate_mcp/**' ':!lifecycle/**'` returns no output — pass if output is empty (no changes outside the three target files, excluding lifecycle artifacts which may update but are not part of the feature commit).
  - **Post-commit check**: after `/commit` runs, `git log -1 --oneline` shows a commit whose message contains `017` or `evt:status.bt` or `semantic traps` — pass if the most recent commit message matches one of these.
  - **Post-commit scope check**: `git diff --name-only $(cat lifecycle/.../.baseline-ref)..HEAD -- CLAUDE.md 'mcp/src/gaggimate_mcp/**'` lists the same three paths — pass if unchanged from the pre-commit check.
- **Status**: [x] completed

## Verification Strategy

End-to-end verification is Task 4's grep suite plus the scope-containment git-diff check against the `.baseline-ref` SHA captured by Task 0. A pass requires: (a) all directional-inversion guards satisfy their paired-token greps, (b) all three files carry the exact CLAUDE.md subsection title in their cross-references, (c) no file outside the three target paths is modified, (d) a single commit produced by `/commit` references the ticket. Because the change is prose-only with no runtime behaviour, grep-level structural checks are the entirety of the verification surface.

## Veto Surface

- **Single atomic commit via `/commit`** — chosen to avoid parallel-commit races and to produce a clean "017 documentation pass" history. Alternatives: three per-file commits (via three `/commit` invocations, serialized), or worktree isolation. If the user prefers per-file commits, Task 4 splits into 4a/4b/4c with sequential `Depends on` chains.
- **Pre-flight Task 0 vs runner-level baseline capture** — the overnight runner could in principle capture a baseline before dispatch, but putting it in an explicit Task 0 makes the dependency visible and testable. If the runner grows a native baseline-capture hook, Task 0 becomes redundant and can be removed.
- **Reference-wording models vs. strict dictated prose** — Context fields provide recommended phrasings but don't mandate them verbatim. The implementer must satisfy the directional-inversion guards and cross-reference greps, but is free to word the prose otherwise. If the user prefers mandated verbatim phrasing, the Context "Recommended phrasing model" lines can be upgraded to normative.
- **Line-number drift from sibling ticket 014** — ticket 014 (critical, refined) edits server.py upstream of diagnose_connection; if 014 lands first, Task 2's plan-write-time line numbers are stale. Mitigation: all verification greps are content-addressed (awk ranges via `async def diagnose_connection`), so verification still passes. Task 0 re-verifies the anchor points. No blocking concern.
- **`.baseline-ref` file in lifecycle dir** — transient file used to carry state between Task 0 and Task 4. Acceptable because the lifecycle directory is scoped to this feature. Alternative: stash the SHA in the events.log as a `baseline_captured` event and read it back. File-based is simpler.

## Scope Boundaries

Maps to the spec's Non-Requirements section:
- No MEMORY.md update.
- No `vf` / DDSA / `rssi` / native-analyzer-UI / mixed-era documentation (sibling tickets 015, 018, 021).
- No new `knowledge/` or `docs/` file.
- No `/consult` skill update.
- No behavioural code changes, no JSON schema edits, no test edits.
- No firmware source verification (that's ticket 021's scope).
- No filing of a separate drift-management ticket.
