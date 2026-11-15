#!/usr/bin/env bash
# Build a Skyward recovery image for piano or waffle on a stock recovery base.
#
#   ANDROID_NDK_HOME=/path/to/android-ndk-r29 \
#     scripts/build.sh piano stock/piano/recovery.img
#
# Rust 1.100.0 with the aarch64-linux-android target is required; the NDK
# must be r29 or newer.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEVICE="${1:?usage: build.sh <piano|waffle> <stock-recovery.img> [output.img]}"
STOCK="${2:?usage: build.sh <piano|waffle> <stock-recovery.img> [output.img]}"
OUT="${3:-$ROOT/out/skyward-0.3.1-$DEVICE.img}"
# Resolve both before changing directory.
STOCK="$(cd "$(dirname "$STOCK")" && pwd)/$(basename "$STOCK")"
case "$OUT" in /*) ;; *) OUT="$(pwd)/$OUT" ;; esac
: "${ANDROID_NDK_HOME:?set ANDROID_NDK_HOME to an Android NDK r29 tree}"

case "$DEVICE" in
    piano|waffle) ;;
    *) echo "device must be piano or waffle" >&2; exit 2 ;;
esac

NDK_BIN="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin"
export PATH="$NDK_BIN:$PATH"
export CC_aarch64_linux_android="$NDK_BIN/aarch64-linux-android30-clang"
export CXX_aarch64_linux_android="$NDK_BIN/aarch64-linux-android30-clang++"
export AR_aarch64_linux_android="$NDK_BIN/llvm-ar"
export RANLIB_aarch64_linux_android="$NDK_BIN/llvm-ranlib"
export CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER="$NDK_BIN/aarch64-linux-android30-clang"

cd "$ROOT/skyward"

echo "--- host packer"
cargo build --release -p skyward-pack

echo "--- aarch64 recovery service"
cargo build --release --target aarch64-linux-android -p skyward

echo "--- aarch64 second-system init (static)"
RUSTFLAGS="-C target-feature=+crt-static" \
    cargo build --release --target aarch64-linux-android -p skyward-system-init \
    --target-dir target/system-init

mkdir -p "$ROOT/out"
echo "--- packing $DEVICE"
"$ROOT/skyward/target/release/skyward-pack" recovery \
    --stock "$STOCK" \
    --binary "$ROOT/skyward/target/aarch64-linux-android/release/skyward" \
    --system-init "$ROOT/skyward/target/system-init/aarch64-linux-android/release/system-init" \
    --config "$ROOT/skyward/devices/$DEVICE.toml" \
    --font "$ROOT/skyward/resources/fonts/MiSansVF.ttf" \
    --mono "$ROOT/skyward/resources/fonts/KirkMono-Regular.ttf" \
    --mono-license "$ROOT/skyward/resources/fonts/KirkMono-OFL.txt" \
    --out "$OUT"
sha256sum "$OUT"
