"""
Merge multiple COCO JSON files (from labelme export) into one merged.json.
Remaps image_id and annotation_id to avoid conflicts.
Forces single category: cube (id=1).
"""

import json
import argparse
from pathlib import Path

# -----------------------------------------------------------------------
# Args
# -----------------------------------------------------------------------

parser = argparse.ArgumentParser(description="Merge COCO JSON files into one")
parser.add_argument("--input-dir", type=Path, required=True,
                    help="Directory containing COCO JSON files to merge")
parser.add_argument("--output",    type=Path, required=True,
                    help="Output path for merged COCO JSON")
args = parser.parse_args()

# Collect all JSON files, excluding the output file itself
json_files = sorted([
    p for p in args.input_dir.glob("*.json")
    if p.resolve() != args.output.resolve()
])

if not json_files:
    raise SystemExit(f"ERROR: No JSON files found in {args.input_dir}")

print(f"Found {len(json_files)} JSON file(s) to merge:")
for f in json_files:
    print(f"  {f.name}")
print()

# -----------------------------------------------------------------------
# Merge
# -----------------------------------------------------------------------

merged = {
    "info":        {"description": "Merged cube detection dataset"},
    "licenses":    [],
    "categories":  [{"id": 1, "name": "cube", "supercategory": "object"}],
    "images":      [],
    "annotations": [],
}

next_img_id = 1
next_ann_id = 1

for json_path in json_files:
    with open(json_path) as f:
        data = json.load(f)

    # Remap image IDs
    img_id_map = {}
    src_images = data.get("images", [])
    for img in src_images:
        img_id_map[img["id"]] = next_img_id
        merged["images"].append({
            "id":        next_img_id,
            "file_name": img["file_name"],   # keep original filename
            "width":     img.get("width",  0),
            "height":    img.get("height", 0),
        })
        next_img_id += 1

    # All categories map to cube (id=1)
    src_anns = data.get("annotations", [])
    for ann in src_anns:
        new_img_id = img_id_map.get(ann["image_id"])
        if new_img_id is None:
            continue  # orphaned annotation — skip
        merged["annotations"].append({
            "id":          next_ann_id,
            "image_id":    new_img_id,
            "category_id": 1,
            "bbox":        ann["bbox"],        # [x_min, y_min, w, h]
            "area":        ann.get("area", ann["bbox"][2] * ann["bbox"][3]),
            "iscrowd":     0,
        })
        next_ann_id += 1

    print(f"  {json_path.name:40s}  "
          f"{len(src_images)} images, {len(src_anns)} annotations")

# -----------------------------------------------------------------------
# Save
# -----------------------------------------------------------------------

args.output.parent.mkdir(parents=True, exist_ok=True)
with open(args.output, "w") as f:
    json.dump(merged, f, indent=2)

print(f"\nMerged dataset summary:")
print(f"  Total images:      {len(merged['images'])}")
print(f"  Total annotations: {len(merged['annotations'])}")
print(f"  Saved to:          {args.output}")
