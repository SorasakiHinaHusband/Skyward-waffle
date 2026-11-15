# cardzip

Build a **Skyward card-flash zip** from per-partition images, for ports that
are normally flashed with fastboot (`fastboot flash system system.img`, …).

The generated `META-INF/com/google/android/update-binary` writes each image
into the current slot's logical or physical partition, checks the image size
against the partition first, and disables AVB at the end.

## Quick start

```sh
python3 tools/cardzip/make-cardzip.py \
  --images /path/to/port/images \
  --extra  /path/to/official/images \
  --fill   system_dlkm --fill vendor_dlkm \
  --skip   my_company --skip my_preload \
  --out    OnePlus12_Port_CardFlash.zip \
  --description "OnePlus 12 ColorOS 17 port"
```

Then copy the zip to the phone and install it from Skyward:

```
安装 → 选择文件 → OnePlus12_Port_CardFlash.zip
```

## What goes in

`--images` is authoritative. Every `.img` there must be a known partition
name (or be named with `--logical` / `--physical`); otherwise the tool stops
instead of silently guessing.

`--skip` is for images you do not want to write even though they are in the
port folder; on the OnePlus 12 port, `my_company` and `my_preload` are the
usual ones to leave stock.

`--extra` is for missing partitions from an official package. It is only
used with explicit `--fill NAME` options, so an official folder containing
a full set cannot silently replace partitions you meant to keep. A filled
name must be missing in `--images`; `boot.img`, `dtbo.img`, `super.img` etc.
in the official folder are ignored.

Known logical partitions:

```
system system_ext product vendor odm
my_bigball my_carrier my_company my_engineering my_heytap
my_manifest my_preload my_product my_region my_stock
system_dlkm vendor_dlkm odm_dlkm
```

Known physical partitions: `vbmeta`, `vbmeta_system`, `vbmeta_vendor`.
`recovery` is ignored by default; add `--include-recovery` only if you
really want to overwrite Skyward (Skyward's own "keep recovery" option may
put Skyward back afterwards).

Images must be **raw** partition images (EROFS, ext4, etc.), not Android
sparse images. If `file image.img` says "Android sparse image", convert it
with `simg2img` first. `super.img` is not handled: this tool writes the
individual logical partitions that already exist in the phone's super.

## What the script does

1. Reads the current slot with `getprop ro.boot.slot_suffix` (falls back to
   `_a`).
2. For each logical image:
   - checks `/dev/block/mapper/<name><slot>` exists;
   - reads the image size and the partition size (`blockdev --getsize64`);
   - refuses to write if `image > partition`;
   - writes with `unzip -p "$ZIP" images/<name>.img > "$dev"`.
3. For each physical vbmeta image, writes
   `/dev/block/by-name/<name><slot>`.
4. Runs `avbctl --force disable-verity` and
   `avbctl --force disable-verification`, then `sync`.

It never uses `unzip -p … | dd`. On the tested recovery, `dd` exits
134/139 after a large pipe copy even though the bytes were written; the
shell redirect avoids that entirely. It also avoids `unzip -l | awk … exit`,
which can close the pipe under the recovery's `unzip` and abort it.

## Options

| Option | Meaning |
| --- | --- |
| `--images DIR` | main folder with `<partition>.img` |
| `--extra DIR` | extra folder, repeated; used only with `--fill` |
| `--fill NAME` | take this missing partition from `--extra` (repeatable) |
| `--skip NAME` | leave this image out, keeping the phone's partition (repeatable) |
| `--out FILE` | output zip (ZIP64, stored) |
| `--logical NAME` | add an extra logical partition name |
| `--physical NAME` | add an extra physical partition name |
| `--include-recovery` | also flash `recovery.img` |
| `--no-avb` | do not run `avbctl` |
| `--description TEXT` | shown in the install log and `cardflash.txt` |
| `--dry-run` | print what would be packed, write nothing |

## Before installing

- Battery above 50%, cable in, do not unplug while it writes.
- The zip is unsigned. In Skyward, turn off **安装前校验签名** (check
  signature) or the installer will refuse it.
- If Skyward stops at `unmount /mnt/system_ext: Device or resource busy`,
  run `umount -l /mnt/system_ext` from `adb shell` and retry.
- The port must be compatible with the phone's super layout and slot. This
  tool only checks that the image fits; it cannot make an incompatible port
  boot.
- Keep the stock boot/recovery/super images, or an EDL package, for rollback.

## Tested

Built the OnePlus 12 `OnePlus12_17.0.1.202_Port_From_FindX10ProMax&OnePlus16`
package with this tool: port `system`/`vendor`/`odm`/`my_*` images, official
16.0.10.501 `system_dlkm`/`vendor_dlkm`, and port `vbmeta*`. It installed
through Skyward, disabled AVB, and the phone booted the port.
