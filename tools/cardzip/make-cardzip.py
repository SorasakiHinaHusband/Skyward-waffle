#!/usr/bin/env python3
"""Build a Skyward card-flash zip from per-partition images.

The generated update-binary writes each image with
    unzip -p "$ZIP" images/<name>.img > /dev/block/{mapper,by-name}/<name><slot>
so it does not depend on dd, and it checks the image size against the target
partition before writing.
"""
import argparse
import hashlib
import os
import sys
import tempfile
import zipfile

LOGICAL = [
    "system", "system_ext", "product", "vendor", "odm",
    "my_bigball", "my_carrier", "my_company", "my_engineering",
    "my_heytap", "my_manifest", "my_preload", "my_product",
    "my_region", "my_stock",
    "system_dlkm", "vendor_dlkm", "odm_dlkm",
]
PHYSICAL = ["vbmeta", "vbmeta_system", "vbmeta_vendor"]


def images_in(folder):
    out = {}
    if not folder:
        return out
    for name in sorted(os.listdir(folder)):
        if name.endswith(".img"):
            out[name[:-4]] = os.path.join(folder, name)
    return out


def collect(args):
    # The main folder is authoritative. Extra folders (an extracted official
    # package, for example) only fill names that are missing and that this
    # tool knows how to flash; boot/dtbo/super there are intentionally ignored.
    found = images_in(args.images)
    known = set(LOGICAL) | set(PHYSICAL) | set(args.logical) | set(args.physical)
    if args.include_recovery:
        known.add("recovery")
    if args.extra and not args.fill:
        raise SystemExit("--extra needs at least one --fill NAME")
    for name in args.skip:
        found.pop(name, None)
    for folder in args.extra:
        for name, path in images_in(folder).items():
            if name in args.fill and name in known and name not in found:
                found[name] = path
    for name in args.fill:
        if name not in found:
            raise SystemExit(f"--fill {name}: not found in --images or --extra")
    if not found:
        raise SystemExit("no .img files found")
    logical = [n for n in LOGICAL if n in found]
    physical = [n for n in PHYSICAL if n in found]
    for n in args.logical:
        if n not in found:
            raise SystemExit(f"--logical {n}: no {n}.img")
        if n not in logical:
            logical.append(n)
    for n in args.physical:
        if n not in found:
            raise SystemExit(f"--physical {n}: no {n}.img")
        if n not in physical:
            physical.append(n)
    if args.include_recovery:
        if "recovery" not in found:
            raise SystemExit("--include-recovery: no recovery.img")
        if "recovery" not in physical:
            physical.append("recovery")
    if not logical and not physical:
        raise SystemExit("nothing to flash")
    ignored = {"recovery"} if not args.include_recovery else set()
    unknown = set(found) - set(logical) - set(physical) - ignored
    if unknown:
        raise SystemExit("unclassified images: " + ", ".join(sorted(unknown)) +
                         " (pass --logical/--physical or remove them)")
    return found, logical, physical


def size_case(names, sizes, indent="            "):
    return "\n".join(f'{indent}{n}) size={sizes[n]} ;;' for n in names)


def main():
    ap = argparse.ArgumentParser(description="Build a Skyward card-flash zip")
    ap.add_argument("--images", required=True, help="folder with <partition>.img")
    ap.add_argument("--extra", action="append", default=[], help="extra folder, e.g. official missing partitions")
    ap.add_argument("--fill", action="append", default=[], help="only take these names from --extra (repeatable)")
    ap.add_argument("--skip", action="append", default=[], help="leave these images out (repeatable)")
    ap.add_argument("--out", help="output zip")
    ap.add_argument("--logical", action="append", default=[], help="extra logical partition name")
    ap.add_argument("--physical", action="append", default=[], help="extra physical partition name")
    ap.add_argument("--include-recovery", action="store_true", help="also flash recovery.img to recovery<slot>")
    ap.add_argument("--no-avb", action="store_true", help="do not run avbctl after flashing")
    ap.add_argument("--description", default="Skyward card flash")
    ap.add_argument("--dry-run", action="store_true", help="print what would be packed, write nothing")
    args = ap.parse_args()
    if not args.dry_run and not args.out:
        ap.error("--out is required unless --dry-run")

    found, logical, physical = collect(args)
    sizes = {n: os.path.getsize(found[n]) for n in logical + physical}
    if args.dry_run:
        for n in logical:
            print(f"logical  {n:16} {sizes[n]:>12} bytes  {found[n]}")
        for n in physical:
            print(f"physical {n:16} {sizes[n]:>12} bytes  {found[n]}")
        return
    template = os.path.join(os.path.dirname(os.path.abspath(__file__)), "update-binary.template")
    text = open(template, encoding="utf-8").read()
    text = (text.replace("@DESCRIPTION@", args.description)
                .replace("@LOGICAL@", " ".join(logical))
                .replace("@PHYSICAL@", " ".join(physical))
                .replace("@SIZES@", size_case(logical, sizes))
                .replace("@PSIZES@", size_case(physical, sizes))
                .replace("@AVB@", "0" if args.no_avb else "1"))
    if "@" in text:
        raise SystemExit("template has an unfilled placeholder")

    manifest = [
        "Skyward card flash",
        "description: " + args.description,
        "logical: " + " ".join(logical),
        "physical: " + " ".join(physical),
        "avb: " + ("off" if args.no_avb else "on"),
    ]
    for n in logical + physical:
        manifest.append(f"image {n}: {sizes[n]} bytes")
    manifest = "\n".join(manifest) + "\n"

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
        f.write(text)
        script = f.name
    os.chmod(script, 0o755)

    try:
        with zipfile.ZipFile(args.out, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as z:
            z.write(script, "META-INF/com/google/android/update-binary")
            z.writestr("cardflash.txt", manifest)
            for n in logical + physical:
                z.write(found[n], f"images/{n}.img")
                print(f"  {n:16} {sizes[n]:>12} bytes", flush=True)
    finally:
        os.unlink(script)

    h = hashlib.sha256()
    with open(args.out, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    print(f"\nwrote {args.out} ({os.path.getsize(args.out)} bytes)")
    print("sha256 " + h.hexdigest())
    print("logical:", " ".join(logical))
    print("physical:", " ".join(physical) or "(none)")


if __name__ == "__main__":
    main()
