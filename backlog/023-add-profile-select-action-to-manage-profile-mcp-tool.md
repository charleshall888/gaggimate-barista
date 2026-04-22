---
schema_version: "1"
uuid: 67b2e47f-c2ce-4690-8c6a-0b6415fc3878
title: "Add profile-select action to manage_profile MCP tool"
status: complete
priority: medium
type: feature
created: 2026-04-22
updated: 2026-04-22
session_id: null
lifecycle_phase: complete
lifecycle_slug: add-profile-select-action-to-manage-profile-mcp-tool
complexity: complex
criticality: medium
---

## Problem

The `manage_profile` MCP tool supports `list`, `get`, `create`, `update`, `delete` — but not selecting an uploaded profile as the active one. After creating a profile via MCP, the user has to tap it on the Gaggimate screen to make it active, which breaks the end-to-end "coffee setup → shot" flow the agent drives.

Today this blocks the `/new-coffee` happy path: the skill uploads a profile, but cannot tell the machine to use it.

## What needs discovery

Firmware protocol — the `selected` boolean exists on profile objects, but no existing MCP request clearly sets it. Options in order of likelihood:

1. **`req:profiles:select`** (or similar) exists on the WebSocket but is not yet wrapped in `mcp/src/gaggimate_mcp/api/websocket.py`. Confirm by sniffing the web UI network traffic when tapping a profile.
2. **HTTP endpoint** on the device web UI (`POST /api/profiles/{id}/select`). Same discovery method.
3. **`req:profiles:save` with `selected: true`** honors the flag. Probably needs paired un-selection of the previous active profile to avoid ambiguity.

## Shape of work

- Discovery: ~10 min with browser devtools pointed at the device web UI
- Add `select` action to `manage_profile` calling the real endpoint/request
- Return the updated `selected` state so the MCP response reflects reality
- Fixture test covering the new action
- Update `mcp/README.md` action table

## Acceptance

- `manage_profile(action="select", profile_id=...)` activates the profile on the machine
- Immediately after, `manage_profile(action="list")` shows `selected: true` on that profile (and `false` on others)
- `/new-coffee` can upload + select a profile in one skill run
