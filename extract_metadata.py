#!/usr/bin/env python3
"""Extract metadata from PNG images and organize by rating."""

import argparse
import json
import os
from typing import Dict, Any, Iterable

from PIL import Image, ExifTags

from utils import rating_of_image, safe


def iter_png_files(folder: str) -> Iterable[str]:
    """Yield paths to PNG files under *folder* recursively."""
    for root, _, files in os.walk(folder):
        for name in files:
            if os.path.splitext(name)[1].lower() == ".png":
                yield os.path.join(root, name)


def print_progress(index: int, total: int) -> None:
    """Print a simple progress bar."""
    bar_len = 30
    pct = index / total
    filled = int(bar_len * pct)
    bar = "#" * filled + "-" * (bar_len - filled)
    print(f"\r[{bar}] {index}/{total}", end="", flush=True)


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


def process(folder: str, out_dir: str, *, progress: bool = False) -> None:
    """Walk *folder* and save metadata to *out_dir* grouped by rating."""
    classes = ["general", "sensitive", "questionable", "explicit"]
    for cls in classes:
        os.makedirs(os.path.join(out_dir, safe(cls)), exist_ok=True)

    paths = list(iter_png_files(folder))
    total = len(paths)
    for i, path in enumerate(paths, 1):
        try:
            rating = rating_of_image(path)
        except Exception:
            rating = "general"
        meta = read_metadata(path)
        base = os.path.splitext(os.path.basename(path))[0]
        dst = os.path.join(out_dir, safe(rating), safe(base) + ".json")
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        if progress:
            print_progress(i, total)
    if progress and total:
        print()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder", help="Folder containing PNG images")
    p.add_argument("out", help="Destination directory for metadata files")
    p.add_argument("--no-progress", action="store_true", help="Hide the progress bar")
    args = p.parse_args()
    process(args.folder, args.out, progress=not args.no_progress)


if __name__ == "__main__":
    main()
