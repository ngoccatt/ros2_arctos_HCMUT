#!/usr/bin/env python3
"""
Convert all PNG images in a directory tree to JPG.
- Creates a new .jpg file next to each .png (does NOT delete the original).
- Transparent pixels are composited onto a white background before saving.
- Skips files that already have a corresponding .jpg of the same or newer mtime.

Usage:
    py -3 scripts/convert_png_to_jpg.py [directory] [--quality N]

    directory   Root folder to search recursively (default: Thesis_Cat/Images)
    --quality   JPEG quality 1-95 (default: 88)

Example:
    py -3 scripts/convert_png_to_jpg.py
    py -3 scripts/convert_png_to_jpg.py Thesis_Cat/Images --quality 85
"""

import argparse
import pathlib
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit(
        "Pillow is not installed. Run:  py -3 -m pip install pillow"
    )


def png_to_jpg(png_path: pathlib.Path, quality: int) -> pathlib.Path | None:
    """Convert one PNG to JPG. Returns the output path, or None if skipped."""
    jpg_path = png_path.with_suffix(".jpg")

    # Skip if jpg already exists and is newer than the png
    if jpg_path.exists() and jpg_path.stat().st_mtime >= png_path.stat().st_mtime:
        return None

    with Image.open(png_path) as img:
        # Handle palette / RGBA / LA modes — composite onto white
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode in ("RGBA", "LA"):
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            rgb = background
        elif img.mode != "RGB":
            rgb = img.convert("RGB")
        else:
            rgb = img

        rgb.save(jpg_path, "JPEG", quality=quality, optimize=True)

    return jpg_path


def main():
    repo_root = pathlib.Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(description="Convert PNG images to JPG.")
    parser.add_argument(
        "directory",
        nargs="?",
        default=str(repo_root / "Thesis_Cat" / "Images"),
        help="Root directory to search (default: Thesis_Cat/Images)",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=88,
        metavar="N",
        help="JPEG quality 1-95 (default: 88)",
    )
    args = parser.parse_args()

    root = pathlib.Path(args.directory).resolve()
    if not root.exists():
        sys.exit(f"Directory not found: {root}")

    png_files = sorted(root.rglob("*.png"))
    if not png_files:
        print(f"No PNG files found under: {root}")
        return

    converted = 0
    skipped = 0
    errors = 0

    print(f"Scanning: {root}")
    print(f"Found {len(png_files)} PNG file(s). Quality={args.quality}\n")

    for png in png_files:
        try:
            out = png_to_jpg(png, args.quality)
            if out is None:
                skipped += 1
                rel = png.relative_to(repo_root)
                print(f"  [skip]  {rel}  (jpg up-to-date)")
            else:
                converted += 1
                orig_kb = png.stat().st_size / 1024
                new_kb  = out.stat().st_size / 1024
                rel = png.relative_to(repo_root)
                print(
                    f"  [ok]    {rel}"
                    f"  {orig_kb:.0f} KB → {new_kb:.0f} KB"
                    f"  ({100*(1 - new_kb/orig_kb):.0f}% smaller)"
                )
        except Exception as exc:
            errors += 1
            print(f"  [ERROR] {png.name}: {exc}")

    print(f"\nDone. Converted: {converted}  Skipped: {skipped}  Errors: {errors}")


if __name__ == "__main__":
    main()
