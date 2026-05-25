"""Downscale large images in Thesis_Cat/Images to a maximum dimension.

Usage:
    py -3 scripts/resize_thesis_images.py [--max-dim N] [--quality Q] [--dry-run]

Defaults: max_dim=1800 (px), quality=85
"""
import argparse
import pathlib
from PIL import Image

REPO = pathlib.Path(__file__).resolve().parent.parent
TARGET_DIR = REPO / "Thesis_Cat" / "Images"


def resize_images(target_dir: pathlib.Path, max_dim: int, quality: int, dry_run: bool):
    images = sorted(target_dir.rglob("*.jpg"))
    resized = skipped = 0

    for p in images:
        with Image.open(p) as im:
            w, h = im.size
            if w <= max_dim and h <= max_dim:
                skipped += 1
                continue

            # Compute new size preserving aspect ratio
            scale = max_dim / max(w, h)
            new_w = round(w * scale)
            new_h = round(h * scale)
            orig_kb = p.stat().st_size // 1024

            if dry_run:
                print(f"[DRY] {p.name}: {w}x{h} → {new_w}x{new_h}  ({orig_kb} KB)")
                resized += 1
                continue

            resized_im = im.resize((new_w, new_h), Image.LANCZOS)
            # Re-open to avoid saving with wrong mode
            if resized_im.mode in ("RGBA", "P"):
                bg = Image.new("RGB", resized_im.size, (255, 255, 255))
                bg.paste(resized_im, mask=resized_im.split()[-1] if resized_im.mode == "RGBA" else None)
                resized_im = bg
            elif resized_im.mode != "RGB":
                resized_im = resized_im.convert("RGB")

            resized_im.save(p, "JPEG", quality=quality, optimize=True)
            new_kb = p.stat().st_size // 1024
            print(f"  {p.name}: {w}x{h} → {new_w}x{new_h}  {orig_kb} KB → {new_kb} KB  (saved {orig_kb - new_kb} KB)")
            resized += 1

    print(f"\nDone: {resized} resized, {skipped} already ≤ {max_dim}px (skipped).")


def main():
    parser = argparse.ArgumentParser(description="Resize large thesis images.")
    parser.add_argument("--max-dim", type=int, default=1800, help="Max width or height in pixels (default: 1800)")
    parser.add_argument("--quality", type=int, default=85, help="JPEG quality (default: 85)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be resized without changing files")
    args = parser.parse_args()

    print(f"Target: {TARGET_DIR}")
    print(f"Max dimension: {args.max_dim}px, JPEG quality: {args.quality}")
    if args.dry_run:
        print("DRY RUN — no files will be changed\n")

    resize_images(TARGET_DIR, args.max_dim, args.quality, args.dry_run)


if __name__ == "__main__":
    main()
