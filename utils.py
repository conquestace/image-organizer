import os
import re
import json
from typing import List
from PIL import Image

ALLOWED_EXT = {'.png', '.jpg', '.jpeg'}
TAG_THRESHOLD = 0.35
MODEL_NAME = "SwinV2"
REPLACE_UNDERSCORES = True

try:
    from imgutils.tagging import get_wd14_tags
except ImportError:
    def get_wd14_tags(image_path, model_name="SwinV2"):
        raise RuntimeError("Please install `dghs-imgutils` to enable tagging.")

def safe(name: str) -> str:
    return re.sub(r'[\\\\/:*?"<>|]+', '_', name)[:64] or 'unknown'

def image_files(folder: str) -> List[str]:
    return [f for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in ALLOWED_EXT]

def tag_image(path: str) -> List[str]:
    rating, feats, chars = get_wd14_tags(path, MODEL_NAME)
    tags = [t for t, s in feats.items() if s > TAG_THRESHOLD]
    tags += [t for t, s in chars.items() if s > TAG_THRESHOLD]
    if REPLACE_UNDERSCORES:
        tags = [t.replace('_', ' ') for t in tags]
    return tags

def prompt_from_meta(path: str):
    try:
        meta = Image.open(path).info
        if 'parameters' in meta:
            return meta['parameters'].split('\\n')[0]
        if 'Prompt' in meta:
            return meta['Prompt']
        for v in meta.values():
            if isinstance(v, str) and v.lstrip().startswith('{'):
                d = json.loads(v)
                if 'sui_image_params' in d:
                    return d['sui_image_params'].get('prompt')
                if 'prompt' in d:
                    return d['prompt']
    except Exception:
        pass
    return None