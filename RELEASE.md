# Skyward 0.3.1 — OnePlus 12 (waffle)

Image for the OnePlus 12 / ColorOS 17 (`PJD110`), built from
`PJD110_17.0.0.100(CN01)` H.11 and tested on `PJD110_17.0.1.202(Milk！)`.

| Image | SHA-256 |
| --- | --- |
| `skyward-0.3.1-waffle-PJD110_17.0.0.100.img` | `329dbe58f1ba57e79f06941564dea58da9d404018a85a02a44d4d6a1205ac255` |

Flash both recovery slots:

```sh
fastboot flash recovery_a skyward-0.3.1-waffle-PJD110_17.0.0.100.img
fastboot flash recovery_b skyward-0.3.1-waffle-PJD110_17.0.0.100.img
fastboot reboot recovery
```

Verified: 120 Hz display, touch, Wi-Fi, `/data`, battery, haptics and the
ColorOS version string. Cellular/MSS stays off. See `README.md` and
`docs/PORTING.md`.
