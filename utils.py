import os
import re
import json
from typing import Iterable, List
from functools import lru_cache
from PIL import Image

ALLOWED_EXT = {".png", ".jpg", ".jpeg"}
TAG_THRESHOLD = 0.35
MODEL_NAME = "SwinV2"
REPLACE_UNDERSCORES = True

_SAFE_RE = re.compile(r'[\\/:*?"<>|]+')


try:
    from imgutils.tagging import get_wd14_tags
except ImportError:

    def get_wd14_tags(image_path, model_name="SwinV2"):
        raise RuntimeError("Please install `dghs-imgutils` to enable tagging.")


def safe(name: str) -> str:
    """Sanitize folder and file names."""
    return _SAFE_RE.sub("_", name)[:64] or "unknown"


def image_files(folder: str) -> Iterable[str]:
    """Yield image filenames from *folder* with allowed extensions."""
    for entry in os.scandir(folder):
        if entry.is_file() and os.path.splitext(entry.name)[1].lower() in ALLOWED_EXT:
            yield entry.name


@lru_cache(maxsize=512)
def _cached_tags(path: str, mtime: float) -> List[str]:
    rating, feats, chars = get_wd14_tags(path, MODEL_NAME)
    tags = [t for t, s in feats.items() if s > TAG_THRESHOLD]
    tags += [t for t, s in chars.items() if s > TAG_THRESHOLD]
    if REPLACE_UNDERSCORES:
        tags = [t.replace("_", " ") for t in tags]
    return tags


def tag_image(path: str) -> List[str]:
    """Return tags for *path*, caching results by modification time."""
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = 0
    return _cached_tags(path, mtime)


def prompt_from_meta(path: str):
    """Extract the first prompt string from image metadata, if any."""
    try:
        with Image.open(path) as im:
            meta = im.info
        if "parameters" in meta:
            return meta["parameters"].split("\\n")[0]
        if "Prompt" in meta:
            return meta["Prompt"]
        for v in meta.values():
            if isinstance(v, str) and v.lstrip().startswith("{"):
                d = json.loads(v)
                if "sui_image_params" in d:
                    return d["sui_image_params"].get("prompt")
                if "prompt" in d:
                    return d["prompt"]
    except Exception:
        pass
    return None

@lru_cache(maxsize=512)
def _cached_rating(path: str, mtime: float) -> str:
    rating, _, _ = get_wd14_tags(path, MODEL_NAME)
    return max(rating, key=rating.get)


def rating_of_image(path: str) -> str:
    """Return rating class for *path*, caching results by modification time."""
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = 0
    return _cached_rating(path, mtime)
