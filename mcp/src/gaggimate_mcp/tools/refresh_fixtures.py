"""Refresh shot regression fixtures.

Usage:
    python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>            # regenerate golden from existing .slog
    python -m gaggimate_mcp.tools.refresh_fixtures <shot_id> --fetch    # fetch .slog from device, then regenerate golden

Writes ``mcp/tests/fixtures/shots/<shot_id>.slog`` (fetch mode) and
``mcp/tests/fixtures/shots/<shot_id>.golden.json`` using a byte-stable writer
(sort_keys=True, indent=2, ensure_ascii=False, trailing newline, UTF-8).
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import aiohttp

from gaggimate_mcp.config import GaggimateConfig
from gaggimate_mcp.parsers.shot import parse_binary_shot
from gaggimate_mcp.transformers.shot import transform_shot_for_ai


def _resolve_fixture_dir() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if parent.name == "mcp" and (parent / "tests").is_dir():
            return parent / "tests" / "fixtures" / "shots"
    raise RuntimeError(
        f"Could not locate mcp/ root from {current}; fixtures directory unresolvable."
    )


def _write_golden(path: Path, transformed: object) -> None:
    body = json.dumps(transformed, sort_keys=True, indent=2, ensure_ascii=False)
    path.write_text(body + "\n", encoding="utf-8")


async def _fetch_bytes(shot_id: str) -> Optional[bytes]:
    padded_id = shot_id.zfill(6)
    config = GaggimateConfig()
    protocol = "https" if config.use_https else "http"
    url = f"{protocol}://{config.host}/api/history/{padded_id}.slog"
    timeout = aiohttp.ClientTimeout(total=5.0)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers={"Accept": "application/octet-stream"}) as response:
                if response.status == 404:
                    print(f"Error: shot {shot_id} not found on device.", file=sys.stderr)
                    return None
                if response.status != 200:
                    print(
                        f"Error: HTTP {response.status}: {response.reason}",
                        file=sys.stderr,
                    )
                    return None
                return await response.read()
    except aiohttp.ClientError as exc:
        print(f"Error: device unreachable: {exc}", file=sys.stderr)
        return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="refresh_fixtures",
        description="Refresh shot regression fixtures (.slog + .golden.json).",
    )
    parser.add_argument("shot_id", help="Shot ID (will be zero-padded to 6 digits for device fetch)")
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch .slog bytes from the device before regenerating the golden.",
    )
    args = parser.parse_args(argv)

    fixture_dir = _resolve_fixture_dir()
    fixture_dir.mkdir(parents=True, exist_ok=True)

    shot_id = args.shot_id
    slog_path = fixture_dir / f"{shot_id}.slog"
    golden_path = fixture_dir / f"{shot_id}.golden.json"

    if args.fetch:
        data = asyncio.run(_fetch_bytes(shot_id))
        if data is None:
            return 1
        slog_path.write_bytes(data)
    else:
        if not slog_path.exists():
            print(
                f"Error: {slog_path} not found. Use --fetch to capture from device.",
                file=sys.stderr,
            )
            return 1
        data = slog_path.read_bytes()

    padded_id = shot_id.zfill(6)
    try:
        shot = parse_binary_shot(data, padded_id)
        transformed = transform_shot_for_ai(shot)
    except Exception as exc:
        print(f"Error: failed to process {shot_id}: {exc}", file=sys.stderr)
        return 1

    _write_golden(golden_path, transformed)
    print(f"Wrote {golden_path.relative_to(fixture_dir.parent.parent.parent)}")
    if args.fetch:
        print(f"Wrote {slog_path.relative_to(fixture_dir.parent.parent.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
