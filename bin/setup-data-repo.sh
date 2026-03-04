#!/usr/bin/env bash
# bin/setup-data-repo.sh
# Wires a private data repo into the public gaggimate-barista repo.
# Creates symlinks for coffees/, grind-map.md, user-setup.md, configures
# GAGGIMATE_STORAGE_PATH in mcp/.env, and writes .data-repo-path.
#
# Usage: bin/setup-data-repo.sh /absolute/path/to/gaggimate-barista-data
# Idempotent — safe to re-run.

set -euo pipefail

# ── Resolve script's own directory (project root) ──────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ── Validate argument ───────────────────────────────────────────────────────
if [ $# -ne 1 ]; then
  echo "Usage: $0 /path/to/gaggimate-barista-data" >&2
  exit 1
fi

DATA_ARG="$1"

if [ ! -d "$DATA_ARG" ]; then
  echo "Error: '$DATA_ARG' does not exist or is not a directory." >&2
  exit 1
fi

if [ ! -d "$DATA_ARG/.git" ]; then
  echo "Error: '$DATA_ARG' does not appear to be a git repository (no .git/ found)." >&2
  exit 1
fi

# Resolve to absolute path without relying on realpath (not available on stock macOS).
PRIVATE_REPO="$(cd "$DATA_ARG" && pwd)"

echo "Private data repo: $PRIVATE_REPO"

# ── Safety checks ───────────────────────────────────────────────────────────
cd "$SCRIPT_DIR"

# coffees: must not be a real directory (symlinks are fine; rm -f won't remove dirs)
if [ -d "coffees" ] && [ ! -L "coffees" ]; then
  echo "Error: coffees/ is a real directory — not a symlink." >&2
  echo "Run 'git rm -r --cached coffees/' and manually move it to the private repo" >&2
  echo "before running this script." >&2
  exit 1
fi

# grind-map.md: warn if real file (will be replaced by symlink)
if [ -f "grind-map.md" ] && [ ! -L "grind-map.md" ]; then
  echo "Warning: grind-map.md is a regular file and will be replaced by a symlink."
  echo "Back up your customizations if needed before continuing."
fi

# user-setup.md: warn if real file
if [ -f "user-setup.md" ] && [ ! -L "user-setup.md" ]; then
  echo "Warning: user-setup.md is a regular file and will be replaced by a symlink."
  echo "Back up your customizations if needed before continuing."
fi

# ── Verify expected structure exists in private repo ────────────────────────
for required in "coffees" "grind-map.md" "user-setup.md"; do
  if [ ! -e "$PRIVATE_REPO/$required" ]; then
    echo "Error: '$PRIVATE_REPO/$required' not found." >&2
    echo "Ensure the private repo contains coffees/, grind-map.md, and user-setup.md." >&2
    exit 1
  fi
done

# ── Create symlinks ─────────────────────────────────────────────────────────
echo "Creating symlinks..."

rm -f "coffees"
ln -s "$PRIVATE_REPO/coffees" "coffees"
echo "  coffees -> $PRIVATE_REPO/coffees"

rm -f "grind-map.md"
ln -s "$PRIVATE_REPO/grind-map.md" "grind-map.md"
echo "  grind-map.md -> $PRIVATE_REPO/grind-map.md"

rm -f "user-setup.md"
ln -s "$PRIVATE_REPO/user-setup.md" "user-setup.md"
echo "  user-setup.md -> $PRIVATE_REPO/user-setup.md"

# ── Configure mcp/.env ──────────────────────────────────────────────────────
MCP_ENV="$SCRIPT_DIR/mcp/.env"
STORAGE_PATH="$PRIVATE_REPO/mcp-data"
STORAGE_LINE="GAGGIMATE_STORAGE_PATH=$STORAGE_PATH"

echo "Configuring mcp/.env..."

if [ -f "$MCP_ENV" ]; then
  # Strip any existing GAGGIMATE_STORAGE_PATH line, then append updated value.
  grep -v "^GAGGIMATE_STORAGE_PATH=" "$MCP_ENV" > "$MCP_ENV.tmp"
  mv "$MCP_ENV.tmp" "$MCP_ENV"
fi

echo "$STORAGE_LINE" >> "$MCP_ENV"
echo "  GAGGIMATE_STORAGE_PATH=$STORAGE_PATH"

# ── Write .data-repo-path ───────────────────────────────────────────────────
printf '%s' "$PRIVATE_REPO" > "$SCRIPT_DIR/.data-repo-path"
echo "Wrote .data-repo-path: $PRIVATE_REPO"

# ── Create mcp-data/ in private repo if absent ─────────────────────────────
if [ ! -d "$PRIVATE_REPO/mcp-data" ]; then
  mkdir -p "$PRIVATE_REPO/mcp-data"
  echo "Created $PRIVATE_REPO/mcp-data/"
fi

echo ""
echo "Setup complete. Verify symlinks:"
ls -la "$SCRIPT_DIR/coffees" "$SCRIPT_DIR/grind-map.md" "$SCRIPT_DIR/user-setup.md"
