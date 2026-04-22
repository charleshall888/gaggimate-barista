#!/usr/bin/env node
// capture.js — JS reference harness entry script.
//
// Runs the vendored v1.8.0 analyzer against shot fixtures and writes
// canonical (sorted-key) JSON sidecars used by the Python parity test.
//
// Usage:
//   node capture.js <shot_id>   # process one .slog (e.g. `node capture.js 246`)
//   node capture.js --all       # process every .slog in the parent shots dir
//
// Output: <shot_id>.reference-js.json written next to <shot_id>.slog.

import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { dirname, join, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

import { parseBinaryShot } from './parse-binary-shot.v1.8.0.js';
import { calculateShotMetrics } from './analyzer-service.v1.8.0.js';

// Per spec R8 — defaults from web/src/pages/ShotAnalyzer/index.jsx:~111-112 @ v1.8.0
const HARNESS_SETTINGS = { scaleDelayMs: 200, sensorDelayMs: 200, isAutoAdjusted: true };

const HARNESS_DIR = dirname(fileURLToPath(import.meta.url));
const SHOTS_DIR = dirname(HARNESS_DIR);

/**
 * Recursively sort object keys alphabetically. Arrays preserve order.
 * Returns a new value suitable for JSON.stringify with stable key ordering.
 */
function sortKeys(value) {
  if (Array.isArray(value)) {
    return value.map(sortKeys);
  }
  if (value !== null && typeof value === 'object') {
    const sorted = {};
    for (const key of Object.keys(value).sort()) {
      sorted[key] = sortKeys(value[key]);
    }
    return sorted;
  }
  return value;
}

/**
 * Canonical serializer: recursively sorted keys, 2-space indent, trailing newline.
 * Re-running against unchanged inputs must produce byte-identical output.
 */
function canonicalStringify(value) {
  return JSON.stringify(sortKeys(value), null, 2) + '\n';
}

function processFixture(shotId) {
  const slogPath = join(SHOTS_DIR, `${shotId}.slog`);
  const profilePath = join(SHOTS_DIR, `${shotId}.profile.json`);
  const outPath = join(SHOTS_DIR, `${shotId}.reference-js.json`);

  // Read .slog as bytes, hand to parseBinaryShot as ArrayBuffer.
  const slogBuf = readFileSync(slogPath);
  const arrayBuffer = slogBuf.buffer.slice(
    slogBuf.byteOffset,
    slogBuf.byteOffset + slogBuf.byteLength,
  );
  const shotData = parseBinaryShot(arrayBuffer, shotId);

  // Read profile JSON verbatim.
  const profileData = JSON.parse(readFileSync(profilePath, 'utf8'));

  const result = calculateShotMetrics(shotData, profileData, HARNESS_SETTINGS);

  writeFileSync(outPath, canonicalStringify(result));
  console.log(`wrote ${basename(outPath)}`);
}

function main() {
  const args = process.argv.slice(2);
  if (args.length !== 1) {
    console.error('Usage: node capture.js <shot_id> | --all');
    process.exit(2);
  }

  const arg = args[0];
  let shotIds;
  if (arg === '--all') {
    shotIds = readdirSync(SHOTS_DIR)
      .filter(name => name.endsWith('.slog'))
      .map(name => name.slice(0, -'.slog'.length))
      .sort();
  } else {
    shotIds = [arg];
  }

  for (const shotId of shotIds) {
    processFixture(shotId);
  }
}

main();
