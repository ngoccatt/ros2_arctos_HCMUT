"""
Convert labelme per-image JSON files → single COCO JSON.

Reads all labelme *.json files sitting next to images in --images-dir,
skips any non-labelme JSON (e.g. annotations.json), and writes a clean
COCO file with category "cube" (id=1).

Usage:
  python scripts/labelme_to_coco.py \
      --images-dir dataset/images/ \
      --output     dataset/annotations/merged.json

Run this every time you finish an annotation session in labelme.
The output is used directly by train.py (--data-dir dataset/).
"""

import json
import argparse
from pathlib import Path

# -----------------------------------------------------------------------
# Args
# -----------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description="Convert labelme per-image JSONs to a single COCO JSON"
)
parser.add_argument("--images-dir", type=Path,
                    default=Path("./dataset/images"),
                    help="Directory containing *.jpg images and labelme *.json files")
parser.add_argument("--output",     type=Path,
                    default=Path("./dataset/annotations/merged.json"),
                    help="Output COCO JSON path")
args = parser.parse_args()

# -----------------------------------------------------------------------
# Discover labelme JSON files
# -----------------------------------------------------------------------

def is_labelme(path: Path) -> bool:
    """Return True if the JSON was saved by labelme (has 'shapes' and 'imagePath')."""
    try:
        with open(path) as f:
            d = json.load(f)
        return "shapes" in d and "imagePath" in d
    except Exception:
        return False

all_jsons    = sorted(args.images_dir.glob("*.json"))
labelme_jsons = [p for p in all_jsons if is_labelme(p)]

print(f"Found {len(all_jsons)} JSON file(s) in {args.images_dir}")
print(f"  → {len(labelme_jsons)} labelme annotation file(s)")
print(f"  → {len(all_jsons) - len(labelme_jsons)} skipped (non-labelme)")
print()

if not labelme_jsons:
    raise SystemExit(
        "ERROR: No labelme JSON files found.\n"
        "Open labelme, annotate images, then re-run this script."
    )

# -----------------------------------------------------------------------
# Convert
# -----------------------------------------------------------------------

merged = {
    "info":        {"description": "Cube detection dataset (from labelme)"},
    "licenses":    [],
    "categories":  [{"id": 1, "name": "cube", "supercategory": "object"}],
    "images":      [],
    "annotations": [],
}

img_id  = 1
ann_id  = 1
skipped = 0

for jf in labelme_jsons:
    with open(jf) as f:
        lm = json.load(f)

    img_name  = lm["imagePath"]          # e.g. "A_20260418_145002_0003.jpg"
    img_path  = args.images_dir / img_name

    if not img_path.exists():
        print(f"  [WARN] Image not found, skipping: {img_name}")
        skipped += 1
        continue

    shapes = [s for s in lm.get("shapes", [])
              if s.get("shape_type") == "rectangle" and s.get("label") == "cube"]

    if not shapes:
        # File annotated but no cube box drawn yet — skip silently
        skipped += 1
        continue

    h = lm.get("imageHeight", 0)
    w = lm.get("imageWidth",  0)

    merged["images"].append({
        "id":        img_id,
        "file_name": img_name,   # basename only — train.py expects this
        "width":     w,
        "height":    h,
    })

    for shape in shapes:
        pts  = shape["points"]   # [[x1,y1], [x2,y2]]
        xs   = [p[0] for p in pts]
        ys   = [p[1] for p in pts]
        xmin = max(0, min(xs))
        ymin = max(0, min(ys))
        xmax = min(w, max(xs))
        ymax = min(h, max(ys))
        bw   = xmax - xmin
        bh   = ymax - ymin

        if bw <= 0 or bh <= 0:
            continue

        merged["annotations"].append({
            "id":          ann_id,
            "image_id":    img_id,
            "category_id": 1,
            "bbox":        [xmin, ymin, bw, bh],   # COCO: [x, y, w, h]
            "area":        bw * bh,
            "iscrowd":     0,
        })
        ann_id += 1

    img_id += 1

# -----------------------------------------------------------------------
# Save
# -----------------------------------------------------------------------

args.output.parent.mkdir(parents=True, exist_ok=True)
with open(args.output, "w") as f:
    json.dump(merged, f, indent=2)

print(f"Conversion complete:")
print(f"  Annotated images: {len(merged['images'])}")
print(f"  Total boxes:      {len(merged['annotations'])}")
print(f"  Skipped:          {skipped}")
print(f"  Saved to:         {args.output}")
