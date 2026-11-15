# Port notes

## Base and provenance

The tree in [`skyward/`](../skyward) is Skyward **0.3.1**
(`kirklin/skyward`, GPL-3.0-or-later) with the OnePlus compatibility work
from `shawude/skyward-oneplus13-sun` (also GPL-3.0-or-later). That work is
what lets a non-Xiaomi device boot at all:

| File | What the OnePlus work changes |
| --- | --- |
| `crates/skyward-pack/src/main.rs` | rewrites OnePlus's `start phoenix_recovery` to `start recovery` in the stock `init.rc`, and disables `phoenix_recovery` so `class_start default` does not start it beside Skyward |
| `crates/skyward-modules/src/lib.rs` | resolves `modules.dep` dependencies across `vendor_boot`, `vendor_dlkm`, `vendor` and `system_dlkm`, and accepts OnePlus's `system_dlkm/lib/modules` layout |
| `crates/skyward-config/src/lib.rs` | adds `[device] mtp`, `[wlan] unblock`, `[haptics] period` and `[device] permissive` |
| `crates/skyward/src/main.rs` | writes `/sys/fs/selinux/enforce=0` when `permissive` is set, before the installed system's APEX bundles are mounted |
| `crates/skyward/src/main.rs` | asks for `adb` without first taking USB through `none`; closes `/data` before reboot |
| `crates/skyward/src/ui.rs` | tolerates a panel with no backlight node; gates file transfer on `mtp`; closes `/data` before powering off |
| `crates/skyward/src/wlan.rs` | waits 45 s for the interface, tolerates late sysfs switches, unblocks rfkill through `soft` (OnePlus's `state` is the inverse) |
| `crates/skyward/src/input.rs` | `[touch] swap_xy`, `invert_x` and `invert_y`: maps a panel whose axes differ from the display mode; portrait uses the panel's own axes; every tap emits the motor's click when touch vibration is on |
| `crates/skyward-ui/src/surface.rs` | rotates a portrait canvas a quarter counter-clockwise into a landscape KMS buffer; picks the fastest mode by the refresh in its name when the kernel reports 0 |
| `crates/skyward-ui/src/{app/state.rs,app/prefs.rs,app/act.rs,pages.rs,settings.rs}` | `portrait` state/setting, the orientation row, and the restart-to-apply effect |
| `crates/skyward-programs/src/secure.rs` | recognizes Xiaomi's generic `android.hardware.weaver` as a weaver that reaches the secure world directly (`Through::Direct`) |
| `crates/skyward-net/src/iface.rs` | treats an interface that is already up as success, instead of failing with `EBUSY` on the second bring-up |
| `crates/skyward/src/haptics.rs` | derives the motor frequency from `t_lra_us` when `lra_frequency_hz` reads 0 |
| `crates/skyward-crypto/src/data.rs` | detaches busy mounts and tolerates a missing dm device when closing data |
| `crates/skyward-programs/src/script.rs` | accepts `//` and `/* */` comments used by vendor init scripts |
| `crates/skyward-programs/src/phone.rs` | skips an init script init itself would reject |
| `crates/skyward-programs/src/secure.rs` | recognizes OnePlus's NXP weaver name (`.nxp`) |

No further C++/Rust changes were needed: all remaining differences are in
`devices/waffle.toml`.

## OnePlus 12 (`waffle`)

Device observed over adb while porting:

```
ro.build.version.release = 17          ro.build.version.sdk = 37
ro.build.display.id = PJD110_17.0.1.202(Milk！)
ro.build.version.ota = PJD110_11.H.03_3030_202611051947
ro.build.version.security_patch = 2026-11-01
wm size = 1440x3168                    wm density = 640
```

Official ColorOS 17 full package used as the recovery base:
`PJD110_17.0.0.100(CN01)` H.11, 8,853,874,090 bytes. Its recovery is
100 MiB, header v4, LZ4 ramdisk, kernel from `boot`. `init.rc` still has
`start phoenix_recovery` and `service phoenix_recovery /system/bin/phoenix_recovery`,
which the packer rewrites.

| Item | Value used | Source |
| --- | --- | --- |
| Panel | 1440 × 3168, 640 dpi, 6.82″ | `wm size` / `wm density` on the running device |
| Touch | Goodix GT9916S, DT compatible `goodix,gt9916S` | `dtbo.img` strings |
| Touch modules | `oplus_bsp_tp_hbp_goodix_gt99x6`, `goodix_ts` (live modules also show `oplus_bsp_tp_goodix_comnon` as a dependency of the gt9916/gt9966 wrappers) | `lsmod` on ColorOS 17 |
| NFC / eSE | NXP SN220T, `nxp-nci`, `/dev/nq-nci` 0660 nfc:nfc | `persist.sys.nfc.chip_name`, stock `vendor/etc/ueventd.rc` |
| WLAN | `qca_cld3_kiwi_v2`, cnss2/icnss2 | `lsmod`, module list |
| WLAN cfg | `/vendor/etc/wifi/kiwi_v2/WCNSS_qcom_cfg.ini` | running ColorOS 17 |
| WLAN MAC | none: the driver falls back to its default address; stock persist has no `wlan_mac.bin` | CNSS log on the running recovery |
| Haptics | `qcom-hv-haptics` input device (`event4`), frequency from `t_lra_us` | `/sys/class/qcom-haptics`, FF device list |
| Battery | ADSP must run; then `/sys/class/power_supply/battery` appears | live test: ADSP offline hid the icon, starting it brought `capacity`/`status` |
| Modem | `4080000.remoteproc-mss`, deliberately left offline | `/sys/class/remoteproc`; starting it resets this kernel to EDL |

Configuration choices:

- `[modules] load = ["oplus_bsp_tp_hbp_goodix_gt99x6", "goodix_ts", "nxp-nci"]`.
- `[firmware] partition = "modem"`; `[partitions] mounted = ["persist"]`.
- The `mss` remoteproc is **not** started: on the installed "Milk" kernel
  starting it wedges the modem watchdog and the phone falls to EDL within a
  minute. Wi-Fi comes up without it; only cellular is unavailable in
  recovery.
- Three NFC services are started explicitly, with the same service names
  declared in the stock ODM VINTF manifests:
  - `vendor.oplus.hardware.nfc_aidl-service` →
    `vendor.oplus.hardware.nfc.IOplusNfc/default`
  - `vendor.oplus.hardware.nfcExtns-service` →
    `vendor.oplus.hardware.nfcExtns.INfcExtns/default`
  - `android.hardware.nfc-service.nxp` →
    `android.hardware.nfc.INfc/default`, plus
    `vendor.nxp.nxpnfc_aidl.INxpNfc/default`
- `[[owners]]` was **not** needed: the stock ColorOS 17 recovery's
  `ueventd.qcom.rc` already creates `/dev/nq-nci` as `nfc:nfc 0660`.
- `[wlan]` writes both `/sys/kernel/cnss/fs_ready` and
  `/sys/devices/platform/soc/b0000000.qcom,cnss-kiwi/fs_ready`, sets
  `unblock = true`, and uses the gstatic probe. The unblock path writes
  `soft=0`: on OnePlus's rfkill, `state=0` actually blocks the radio, which
  is why the first build stayed in `RF-kill`. Wi-Fi then gets a DHCP lease
  and passes traffic.
- `[device] mtp = false`: OnePlus's recovery USB gadget resets when
  `mtp,adb` is offered.
- `[haptics]` uses `qcom-hv-haptics`: `lra_frequency_hz` reads 0 until the
  motor is first played, so `period = "/sys/class/qcom-haptics/t_lra_us"` is
  the fallback the port's haptics code uses (130 Hz). The switch and slider
  now show on the settings page.
- ADSP is started on its own (not MSS) for the battery gauge and charging
  screen; `/sys/class/power_supply/battery` appears once it is up, and the
  status bar's battery icon returns.
- `[stock]` is omitted from the committed config because the official
  package is a short-lived share link; the build script takes `--stock`
  explicitly.

Stock recovery used: `stock/waffle/recovery.img`,
SHA-256 `46c71af1d10f8e84d9877ba6dc01c590b807519a34264d1de3b190f527da7b2b`.
The older ColorOS 16 base is kept in `stock/waffle16/`.

## How the image was built

```sh
export ANDROID_NDK_HOME=.../android-ndk-r29
cargo build --release -p skyward-pack
cargo build --release --target aarch64-linux-android -p skyward
RUSTFLAGS="-C target-feature=+crt-static" \
  cargo build --release --target aarch64-linux-android \
  -p skyward-system-init --target-dir target/system-init

skyward/target/release/skyward-pack recovery \
  --stock stock/waffle/recovery.img \
  --binary skyward/target/aarch64-linux-android/release/skyward \
  --system-init skyward/target/system-init/aarch64-linux-android/release/system-init \
  --config skyward/devices/waffle.toml \
  --font skyward/resources/fonts/MiSansVF.ttf \
  --mono skyward/resources/fonts/KirkMono-Regular.ttf \
  --mono-license skyward/resources/fonts/KirkMono-OFL.txt \
  --out out/skyward-0.3.1-waffle-PJD110_17.0.0.100.img
```

Or run `scripts/build.sh waffle stock/waffle/recovery.img <output>` after
putting the stock recovery in `stock/waffle/`.

## Verification status

- The image passes `skyward-pack list` and embeds its TOML byte for byte;
  its `init.rc` starts `recovery` instead of `phoenix_recovery`.
- Booted on the phone: display runs at `1440x3168x120cmd` (120 Hz), touch
  works, `/data` and `/sdcard` mount, and Wi-Fi gets a DHCP address.
- Battery icon/readings appear after ADSP is started; `qcom-hv-haptics`
  plays on touch taps, the back gesture and the strength slider.
- The ColorOS version is read from `my_manifest` (`ro.build.display.id`):
  `PJD110_17.0.1.202(Milk！)`.
- Cellular/MSS is deliberately not started; the stock recovery used as the
  base is not committed, get it from `PJD110_17.0.0.100(CN01)` H.11.
