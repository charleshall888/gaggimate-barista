# Research: Switch the grind map and user-setup to the DF64V (item 026)

**Scope anchor (clarified intent):** Flip the private-repo data layer from the Sette 270 to the DF64V + SSP Cast Lab Sweet V3: snapshot the telemetry behind the Sette grind history's rated shots, archive the Sette grind map as a history-preserving `git mv` to `grind-map-sette-270.archive.md` inside the private data repo, start a fresh grinder-agnostic DF64V grind map (grinder-neutral Grind column **+ a dedicated RPM column, no Grinder column**), and repoint the `user-setup.md` Grinder field to the DF64V (with its RPM note). Targets are symlinks into `/Users/charlie.hall/Workspaces/gaggimate-barista-data`. Non-goals: converting Sette codes to DF64V marks; changing other user-setup sections.

**Tier:** complex · **Criticality:** high · **Owns:** epic-024 work-streams **C** (snapshot + archive), **D** (fresh map), **G** (user-setup repoint).

---

## Codebase Analysis

### Files that change (all in the private data repo, via symlink targets)
- `…/gaggimate-barista-data/grind-map.md` → `git mv` to `grind-map-sette-270.archive.md` (exact filename per `cortex/backlog/026-…:43`), then a **fresh** `grind-map.md` (12 cols + RPM) created at the same path.
- `…/gaggimate-barista-data/user-setup.md:8` → Grinder-field line edited.
- `…/gaggimate-barista-data/mcp-data/shot-archive/<id>.slog` (new) → **only** for rated shots the device still serves (see Telemetry, below).

### Files 026 must NOT change (owned elsewhere / out of scope)
- `grind-map.example.md` and `user-setup.example.md` — **real files in the main repo**, format references only. `user-setup.example.md:8` is already grinder-neutral (`Baratza Encore ESP`) → **no edit**. `grind-map.example.md` is owned by **025** (its "notation and Grind-column format" touch point); 026 reads it, does not write it. *(Note the ticket touch-point contradiction in Open Questions.)*
- `knowledge/grinders/SETTE_270.md`, `knowledge/reference/SETTE_270_REFERENCE.md` — 025 / work-stream E+I.
- `.claude/skills/feedback|new-coffee|consult/SKILL.md` — 027 / work-stream F (lifecycle-protected paths).
- `user-setup.md:59` Notes line ("Sette 270's micro-adjust…") — Sette-specific but **out of scope** per the non-goal "changing other user-setup sections."

### Patterns & integration points
- **Symlink contract:** `bin/setup-data-repo.sh:62-78` hard-requires the private repo to contain a file literally named `grind-map.md` (the `for required in "coffees" "grind-map.md" "user-setup.md"` loop `exit 1`s if missing) and creates `grind-map.md -> $PRIVATE_REPO/grind-map.md`. The fresh map **must keep the `grind-map.md` filename** or the symlink dangles and setup breaks. The symlink targets a **path**, so after the rename the symlink dangles until the fresh file is created at that same path — **no re-pointing needed** (verified `ls -la`).
- **Auto-commit:** `.data-repo-path` = `/Users/charlie.hall/Workspaces/gaggimate-barista-data` (auto-commit active). Commits use `git --git-dir=…-data/.git --work-tree=…-data <cmd>`, **separate Bash calls, no chaining, no `git -C`** (CLAUDE.md auto-commit policy). The private repo tree is currently clean.
- **`ratings.json`** (`…/mcp-data/ratings.json`, **git-tracked**): keyed by zero-padded `shot_id`, carries `timestamp`, `grind_setting`, `dose_in/out`, `rating`, `notes`. Written by `mcp/src/gaggimate_mcp/storage/ratings.py` to `{GAGGIMATE_STORAGE_PATH}/ratings.json`; `GAGGIMATE_STORAGE_PATH` → `{private-repo}/mcp-data/`.
- **Telemetry source:** `analyze_shot` / `list_recent_shots` (`mcp/.../api/http.py`, `server.py`) fetch `http://gaggimate.local/api/history/{id}.slog` from the **device** — telemetry curves are **not** in the private repo except 3 fixtures.
- **No skill/hook** parses the grind-map header positionally in a way the new RPM column breaks today (new-coffee reads columns by name; feedback self-declares header migration out of scope at `feedback/SKILL.md:140`). **No skill/hook references** the archive filename. **No automated hook** reads the Grinder field.

### Telemetry join + what is actually durable
- Grind-map rows are **Date-keyed (no `shot_id`)**. Join row → shot_id via **Date + grind_setting** against `ratings.json`. Confirmed 5★ examples: Onyx Bochesa **Feb 13 / 13D → shot 000092**; Choco La Papaya **Mar 2 / 13E → 000170**, Mar 4 / 13E → 000176, Mar 11 / 13F → 000190.
- **The rated shots' telemetry curves are NOT in the private repo.** The only `.slog` files present are `246/247/249`, none of which are rated grind-map shots (per `mcp/tests/fixtures/shots/README.md`, shot 170 was **already device-evicted** by the 1.8.0 free-space purge before fixture capture). So the curves are on-device-only and likely already purged.
- **`ratings.json` is the durable floor** — every rated shot's rating/notes/grind/dose is already committed in git history.

### Fresh-map schema (recommended)
- Existing header (`grind-map.md:7`): `| Coffee | Roast | Process | Origin | Days Off Roast | Grind | Profile | Ratio | Temp | Rating | Date | Puck Screen? |`.
- Fresh map = **those 12 columns + one dedicated `RPM` column adjacent to `Grind`** (`… | Grind | RPM | Profile | …`), **no Grinder column** (single-grinder; selector lives in user-setup).
- `Grind` cell = **free-text, grinder-neutral** ("chirp + N marks" relative-to-zero). `RPM` cell = integer (e.g. `1100`); **blank for fixed-speed grinders** (mirrors the `Puck Screen?` "blank = unknown/NA" convention, `grind-map.example.md:13`).
- **Create the fresh map populated with its preamble + footer notes (NOT bare header-only)** so it reads as "configured-but-empty," not as an unconfigured template (see Adversarial #5). No historical rows are carried forward (Sette grind values do not translate).

---

## Web Research

- **`git mv` == `cp + rm` at the git tree level.** Git stores content snapshots, not rename ops; renames are inferred at **diff-time** with a default **>50% similarity threshold**. `git log --follow` / `git blame` continuity **breaks if a file is renamed AND substantially rewritten in the same commit**. Best practice: keep the rename free of content changes so similarity stays ~100%.
- **A git tag** is a point-in-time marker only — it gives **no `--follow` continuity** onto a renamed successor. Useful as optional belt-and-suspenders, not as the archive mechanic.
- **Snapshot-at-ingest audit pattern:** materialize referenced data into your own durable store rather than holding a pointer into a store with its own retention. **Anti-pattern:** storing only a foreign id (a `shot_id`) into a purging store — it silently orphans, which is exactly the firmware-1.8.0 trap CLAUDE.md flags.
- **RPM is a genuine first-class, orthogonal dialing variable on the DF64V** (continuous 600–1800 RPM, distinct reproducible cup outcomes independent of grind size) → a dedicated RPM column captures a real second degree of freedom, not redundant data. **"chirp + N marks from zero" is an established stepless-collar logging convention** (printed "0" is a per-unit approximation; record offset from the burr-kiss chirp).

---

## Requirements & Constraints

- **`cortex/requirements/project.md` is an unconfigured TODO template** — contributes no constraints. All load-bearing constraints come from CLAUDE.md, the backlog items, and the discovery research.
- **CLAUDE.md (load-bearing):**
  - *Auto-commit policy* — read `.data-repo-path`; commit + push to the private repo with `--git-dir/--work-tree`, separate Bash calls, no chaining, no `git -C`; on push failure inform the user "Private repo push failed — changes saved locally…". This is the recovery mechanism that makes the user-setup Grinder overwrite recoverable.
  - *Data Architecture* — `grind-map.md`/`user-setup.md` are symlinks into the private repo; `GAGGIMATE_STORAGE_PATH` → `{private-repo}/mcp-data/`. All active-data writes happen **inside the private repo**.
  - *Unconfigured-check* — prose heuristic (model judgment, **not** deterministic code): a freshly empty DF64V map + otherwise-real `user-setup.md` must still read as configured.
  - *Puck Screen parsing contract* — preserve the `Puck Screen?` column and its blank/N semantics; do not touch the user-setup Puck Screen row.
  - *Firmware 1.8.0 retention note* — `MIN_FREE_SPACE_BYTES = 500 KB` purge deletes the companion `.json` sidecar; old `shot_id` references in `grind-map.md` may orphan silently. **This is the justification for snapshot-before-archive.**
- **Scope boundary (025 / 026):** 025 owns the grinder-neutral **notation contract** ("chirp + N marks") and the **`grind-map.example.md` format**; 026 *reads/consumes* the notation and applies it to the **live** `grind-map.md`. 026 owns C/D/G only.
- **Internal order (026):** snapshot telemetry + archive old map → start fresh map → repoint user-setup.
- **Non-goals:** converting Sette codes to DF64V marks; changing other user-setup sections.

---

## Tradeoffs & Alternatives

**A — Archive mechanic.**
- **Prescribed `git mv` → `grind-map-sette-270.archive.md`, then fresh `grind-map.md` (RECOMMENDED).** Preserves the live map's **12-commit `--follow`/`blame` lineage**, keeps the path-based symlink resolving, reads cleanly on fork, honors the "not a lossy copy" Edge.
- *Copy-then-delete* — **rejected**: archive becomes a new file with no ancestry; `--follow` dead-ends; violates the Edge.
- *Tag/branch snapshot* — no `--follow` continuity; fine only as optional extra insurance.
- *One file, append DF64V section* — **rejected**: blends two incompatible notations in one table (the failure the Decision Record rules out) and the RPM column wouldn't apply to Sette rows.

**B — Telemetry snapshot mechanic.**
- *Verify-and-rely on existing `shot-archive/*.slog`* — **insufficient alone**: the 3 present `.slog`s are not the rated shots.
- *Re-export from device via MCP* — **best-effort only**: `diagnose_connection` currently returns **port_closed / DNS-fail** (device unreachable now and possibly at overnight time); old February sidecars are likely already purged on-device too.
- *Snapshot all vs only rated rows* — scope to the **rated rows' shot_ids** (the signal the archive references).
- **Recommended:** keep the **snapshot-before-archive ordering**, make device re-export **best-effort and non-blocking**, and declare **git-tracked `ratings.json` + the archived map the satisfiable "lose-nothing" floor**. "Lose nothing" = "lose no *recoverable* telemetry, and lose no *metadata*."

**RPM representation:** dedicated column **confirmed** (user decision). RPM is a real orthogonal variable deserving first-class, sortable, diff-friendly structure; embedding it in the Grind cell buries it in free text. The `grind-map.example.md` example should also gain the RPM column — but that file is **025's** to edit (see Open Questions).

**Commit atomicity (RECOMMENDED resolution):** do the **rename + fresh-file creation in ONE commit** so the `grind-map.md` path is never empty in any committed/pushed state. Rename detection still works (archive content is byte-identical to the old map; the fresh file is a genuine add). The archive must be moved **byte-identical** — no "ARCHIVED" banner, no column normalization in the same commit (either would risk dropping below the 50% similarity threshold and breaking `--follow`). The user-setup repoint is a separate later step/commit.

---

## Adversarial Review

- **Telemetry "lose nothing" is unsatisfiable as literally written.** The curves are gone and the device is unreachable; an autonomous runner facing "must snapshot before archive" will block, retry forever, or fail. **Mitigation (load-bearing):** rewrite the criterion as best-effort + evidence — attempt MCP re-export for the rated shot_ids; on unreachable/purged, write a **disposition note** (per shot_id: `captured` / `device-unreachable` / `already-purged`) and proceed. Verifiable post-condition = "a disposition is recorded for every rated shot_id," **not** "curves captured." `ratings.json` (git-tracked) + the archived map are the satisfiable floor.
- **Morning-after feedback-skill corruption (high severity).** `.claude/skills/feedback/SKILL.md:135-136` appends a hardcoded **12-field row with Sette-format grind notation**. The instant 026 lands a 13-column DF64V map, the feedback writer is writing 12-column Sette-format rows into it. 027 owns the fix and is a protected path 026 must not touch — but the epic schedules 026 and 027 **in parallel**. **Mitigation:** harden to strict **026 → 027** ordering for the autonomous run, and/or have 026's fresh-map preamble carry a transitional-state note (see Open Questions).
- **Symlink-dangling window.** Between the `git mv` and the fresh-file creation the main-repo symlink dangles; `setup-data-repo.sh` aborts if `grind-map.md` is missing. **Mitigation:** rename + fresh-file as one atomic step/commit so the window never spans a step or commit boundary.
- **Half-migrated state on push failure.** Per-step commits + a push failure after the archive commit but before the fresh-map commit would leave the remote with a dangling target. **Mitigation:** the single atomic commit (above) guarantees no committed/pushed state ever lacks `grind-map.md`.
- **Empty map vs Unconfigured-check.** "No grind history" is literally true of an empty map and the check is prose-judgment. **Mitigation:** ship the fresh map with its preamble + footer (configured-but-empty), not bare header. The CLAUDE.md heuristic carve-out itself is out of 026 scope (flag for 025/027).
- **Do not normalize the archive.** The live rows fill only 11 of 12 cells for 10/12 rows (blank `Puck Screen?` = "unknown"). Move byte-identical; do not "complete" columns or backfill shot_ids (both break `--follow` and are out of scope).

---

## Open Questions

- **026→027 transitional-state handling — DEFERRED to Spec.** Until 027 parameterizes `/feedback`, the skill writes 12-column Sette-format rows into the fresh 13-column DF64V map. Decision for Spec: does 026 (a) add a transitional-state warning note to the fresh-map preamble ("DF64V map — until grinder-aware skills land (item 027), log rows manually in chirp+N marks; /feedback still emits Sette-format rows"), (b) rely on strict 026→027 sequencing enforced by the runner, or (c) both? Rationale for deferral: option (b) depends on 027's schedule (the epic says "parallel"), which is outside 026's control; (a) is the only mitigation 026 can land unilaterally and is the recommended default.
- **`grind-map.example.md` ticket-scope contradiction — RESOLVED.** 026's touch-points list `grind-map.example.md`, but it is a main-repo file owned by 025 ("notation and Grind-column format") and 026's scope is a pure private-repo data change. Resolution: **026 does NOT edit `grind-map.example.md`** — it is a read-only reference. 026 defines the RPM-column shape (dedicated integer column adjacent to Grind, blank for fixed-speed) as a local decision; 025's example must conform to it when 025 lands. Spec should demote the touch-point entry to "reference only."
- **Commit atomicity — RESOLVED (recommendation).** Rename + fresh-file creation in ONE commit (archive moved byte-identical), user-setup repoint as a separate commit; this reconciles the "rename in its own commit" `--follow` guidance with the "never leave the `grind-map.md` path empty" requirement under the per-step auto-commit policy. Spec confirms.
- **"Lose nothing" acceptance criterion — RESOLVED (recommendation).** Encode as best-effort telemetry snapshot + a per-shot disposition note; declare git-tracked `ratings.json` + the byte-identical archived map the satisfiable, device-independent floor. Non-blocking on device reachability.
- **user-setup.md:59 Sette Notes line — RESOLVED.** Out of 026 scope per the "changing other user-setup sections" non-goal; flag as a residual for 025/027 (it teaches Sette-specific adjustment vocabulary). 026 changes only the Grinder field (+ its RPM note).
- **Exact new Grinder-field string — DEFERRED to Spec.** Must name the DF64V (Gen 3, variable-speed) + SSP Cast Lab Sweet V3 **Red Speed espresso** burr (not V2 Silver Knight / not the fixed DF64) and carry an RPM note (~1000–1200 espresso operating point + chirp reference). Exact phrasing is a Spec decision.

---

## Considerations Addressed

- **RPM dedicated column vs grinder-neutral/forkable notation goal:** Addressed and validated. A dedicated integer RPM column is **consistent** with the parent epic's grinder-neutral/forkable goal — a fixed-speed grinder simply leaves the column blank (additive/optional, mirroring the `Puck Screen?` blank convention), and **025's notation contract stays scoped to the grind-setting string only** (RPM is a separate column, not embedded in the "chirp + N marks" notation). The two concerns remain orthogonal; no conflict. Web + Codebase + Requirements + Tradeoffs agents independently concur.
