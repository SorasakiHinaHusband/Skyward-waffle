#!/usr/bin/env bash
# Extract partitions from a local full OTA zip (payload.bin) without
# unpacking the whole package.
#
#   scripts/extract-ota.sh OTA.zip OUTDIR recovery vendor odm
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZIP="${1:?usage: extract-ota.sh <ota.zip> <out-dir> [partition...]}"
OUT="${2:?usage: extract-ota.sh <ota.zip> <out-dir> [partition...]}"
shift 2
cargo build --release --manifest-path "$ROOT/tools/ota-extract/Cargo.toml"
"$ROOT/tools/ota-extract/target/release/ota-extract" "$ZIP" "$OUT" "$@"
