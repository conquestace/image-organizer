#!/usr/bin/env python3
"""Extract metadata from PNG images and organize by rating."""

import argparse
import json
import os
from typing import Dict, Any

from tqdm import tqdm

from PIL import Image, ExifTags

from utils import rating_of_image, safe


def read_metadata(path: str) -> Dict[str, Any]:
    """Return all metadata found in *path* as a dictionary."""
    data = {}
    try:
        with Image.open(path) as im:
            data.update(im.info)
            try:
                exif = im.getexif()
            except Exception:
                exif = None
            if exif:
                tag_map = {ExifTags.TAGS.get(k, k): exif.get(k) for k in exif}
                data["EXIF"] = tag_map
    except Exception as e:
        data["error"] = str(e)
    return data


def process(folder: str, out_dir: str) -> None:
    """Walk *folder* and save metadata to *out_dir* grouped by rating."""
    classes = ["general", "sensitive", "questionable", "explicit"]
    for cls in classes:
        os.makedirs(os.path.join(out_dir, safe(cls)), exist_ok=True)

    paths = []
    for root, _, files in os.walk(folder):
        for name in files:
            if os.path.splitext(name)[1].lower() == ".png":
                paths.append(os.path.join(root, name))

    for path in tqdm(paths, desc="Extracting metadata"):
        try:
            try:
                rating = rating_of_image(path)
            except Exception:
                rating = "general"
            meta = read_metadata(path)
            base = os.path.splitext(os.path.basename(path))[0]
            dst_dir = os.path.join(out_dir, safe(rating))
            base_safe = safe(base)
            dst = os.path.join(dst_dir, base_safe + ".json")
            if os.path.exists(dst):
                i = 1
                while True:
                    alt = os.path.join(dst_dir, f"{base_safe} ({i}).json")
                    if not os.path.exists(alt):
                        dst = alt
                        break
                    i += 1
            with open(dst, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Skipping {path}: {e}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", help="Folder containing PNG images")
    p.add_argument("out", help="Destination directory for metadata files")
    args = p.parse_args()
    process(args.folder, args.out)


if __name__ == "__main__":
    main()
