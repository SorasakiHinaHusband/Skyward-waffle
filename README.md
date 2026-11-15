**English** | [简体中文](README.zh-CN.md)

# Skyward for OnePlus 12 (waffle)

A port of [Skyward](https://github.com/kirklin/skyward) 0.3.1 to the OnePlus
12 (`waffle`, `PJD110`) on ColorOS 17 / Android 17. The tree carries the
OnePlus compatibility work from
[shawude/skyward-oneplus13-sun](https://github.com/shawude/skyward-oneplus13-sun),
with a device configuration for `waffle` only.

The image is built from the official ColorOS 17
`PJD110_17.0.0.100(CN01)` H.11 recovery; the phone used for testing runs the
newer `PJD110_17.0.1.202(Milk！)` build. Skyward reads the installed
system's properties and services at runtime, so the same image serves both.

## Download

Image: [**v0.3.1 release asset**](https://github.com/SorasakiHinaHusband/Skyward-waffle/releases/download/v0.3.1/skyward-0.3.1-waffle-PJD110_17.0.0.100.img)

```text
SHA-256: 329dbe58f1ba57e79f06941564dea58da9d404018a85a02a44d4d6a1205ac255
```

The image is a release asset rather than a committed file because it is
about 100 MiB. The stock recovery used as its base is not committed.

## Verified on the phone

- Boots from the recovery partition.
- Display runs at `1440x3168x120cmd` (**120 Hz**).
- Touch works; screen-off/back gestures work.
- Wi-Fi associates and passes traffic (the interface can take about 70 s
  to appear because CNSS waits for the modem's DMS service, then falls
  back to a default MAC).
- `/data` and `/sdcard` mount; decryption works.
- Battery icon/readings work after ADSP is started.
- Haptics work: touch taps, the back gesture and the strength slider.
- The version string is read from `my_manifest`:
  `PJD110_17.0.1.202(Milk！)`.

## Flashing

Both recovery slots:

```sh
fastboot flash recovery_a skyward-0.3.1-waffle-PJD110_17.0.0.100.img
fastboot flash recovery_b skyward-0.3.1-waffle-PJD110_17.0.0.100.img
fastboot reboot recovery
```

Keep the stock recovery for rollback:

```sh
fastboot flash recovery_a stock-waffle-recovery.img
fastboot flash recovery_b stock-waffle-recovery.img
```

## Building

The packer replaces the stock recovery's ramdisk with Skyward's and keeps
the stock kernel. Get the stock `recovery.img` from the ColorOS 17
`PJD110_17.0.0.100(CN01)` full OTA; `scripts/extract-ota.sh` and
`tools/ota-extract` can open `payload.bin` without writing the whole
8.85 GB package.

```sh
export ANDROID_NDK_HOME=/path/to/android-ndk-r29
scripts/build.sh waffle stock/waffle/recovery.img out/skyward-0.3.1-waffle-PJD110_17.0.0.100.img
```

## Configuration

- `skyward/devices/waffle.toml` — the only device file in this tree.
- `permissive = true` lets the recovery mount the installed system's APEX
  bundles under the `kernel` domain.
- `[haptics]` uses `qcom-hv-haptics`; `t_lra_us` is the frequency fallback.
- ADSP is started on its own for the battery gauge; **MSS is deliberately
  not started** because starting it wedges this kernel and resets the phone
  to EDL after about a minute.
- `mtp = false`; file transfer is not offered.
- `[wlan]` uses `kiwi_v2`, `rfkill` and the two CNSS `fs_ready` switches.

## Layout

```text
skyward/               Skyward 0.3.1 source + this port's changes
  devices/waffle.toml  device configuration
  crates/              Rust crates
docs/PORTING.md        what was changed and why
docs/TESTING.md        first-boot checklist
patches/               the port as a patch against upstream Skyward 0.3.1
scripts/build.sh       build + pack
scripts/extract-ota.sh
tools/ota-extract/     OTA payload extractor
```

## Card-flash zip builder

A standalone tool for turning per-partition port images into a
Skyward-installable zip lives at
[**Skyward-cardzip**](https://github.com/SorasakiHinaHusband/Skyward-cardzip).
It checks each image against its target partition and disables AVB after the
writes; it is not OnePlus-specific.

## Repairing a stale OTA state

After an OTA, Skyward can still say "Update written, waiting to merge" when
the target slot has already booted and its snapshots are gone but
libsnapshot's state file was left at `Initiated`/`Unverified` (for example
after a manual `fastboot --set-active`). Repair it with:

```sh
adb shell /system/bin/recovery vab-repair --force
```

The command backs up `/metadata/ota/state` as `state.before`, refuses while
a merge is really running or failed, and marks the update merged. Use it
only after the target slot has started.

## Known limitations

- Cellular/modem is not started: starting `mss` resets the phone to EDL.
  Wi-Fi works without it.
- Wi-Fi takes about 70 s to appear in recovery (DMS timeout).
- MTP/file transfer is disabled.
- The stock recovery base must match `PJD110_17.0.0.100(CN01)` H.11 (or a
  compatible ColorOS 17 build).

## License

GPL-3.0-or-later, as upstream Skyward. See `skyward/LICENSE`.
