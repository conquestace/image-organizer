#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch WD-14 tagger test
-----------------------
usage:
    python wd_batch_tagger.py /path/to/folder  [--model SwinV2] [--thr 0.4]

• Scans the folder for *.png / *.jpg.
• For each image prints:
      filename
      rating
      top tags  (score > threshold)
      character tags (score > threshold)
• Works with any model listed in tagger_model_names.
"""

import argparse, glob, os
from typing import Union
from PIL import Image

try:
    from imgutils.tagging import get_wd14_tags
    from imgutils.tagging.wd14 import MODEL_NAMES as tagger_model_names
except ImportError:                # fallback if dghs-imgutils not installed
    def get_wd14_tags(image_path, model_name):
        raise RuntimeError("Tagger feature not available; install dghs-imgutils")
    tagger_model_names = {
        "EVA02_Large": None,
        "ViT_Large":  None,
        "SwinV2":     None,
        "ConvNext":   None,
        "ConvNextV2": None,
        "ViT":        None,
        "MOAT":       None,
        "SwinV2_v3":  None,
        "ConvNext_v3":None,
        "ViT_v3":     None,
    }

# ---------- helpers copied from your snippet ----------
def get_rating_class(rating: dict) -> str:
    return max(rating, key=rating.get)

def tags_above(tags: dict, thr=0.4):
    return [t for t, s in tags.items() if s > thr]

def replace_underscore(tag: str) -> str:
    return tag.replace('_', ' ')

def tag_one(img: Union[str, Image.Image],
            thr: float,
            model: str,
            replace: bool = False) -> dict:
    rating, feat, char = get_wd14_tags(img, model)
    res = {
        'rating': get_rating_class(rating),
        'tags':   tags_above(feat, thr),
        'chars':  tags_above(char, thr),
    }
    if replace:
        res['tags']  = [replace_underscore(t) for t in res['tags']]
        res['chars'] = [replace_underscore(t) for t in res['chars']]
    return res
# ------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", help="folder with images")
    parser.add_argument("--model", default="SwinV2",
                        choices=list(tagger_model_names.keys()))
    parser.add_argument("--thr", type=float, default=0.4,
                        help="probability threshold (default 0.4)")
    args = parser.parse_args()

    if args.model not in tagger_model_names:
        parser.error(f"unknown model {args.model}")

    patt = os.path.join(args.folder, "**", "*.[pjPJ][npNP][geGE]*")
    files = glob.glob(patt, recursive=True)
    if not files:
        print("No PNG/JPG images found"); return

    for fp in files:
        try:
            out = tag_one(fp, args.thr, args.model, replace=True)
            print(f"\n=== {fp} ===")
            print("rating :", out['rating'])
            print("tags   :", ', '.join(out['tags']  [:25]))
            print("chars  :", ', '.join(out['chars'][:25]))
        except Exception as e:
            print(f"[ERROR] {fp}: {e}")

if __name__ == "__main__":
    main()
