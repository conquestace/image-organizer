import os
import re
import shutil
import json
from flask import jsonify
import urllib.parse
from flask import Blueprint, render_template, request, redirect, url_for, send_file
from utils import tag_image, image_files, safe

_NORMALIZE_RE = re.compile(r"[(){}\[\]]+")
_SPLIT_RE = re.compile(r"[,\s]+")

tagger_bp = Blueprint("tagger", __name__, url_prefix="/tagger")


def normalize(text: str) -> str:
    """Normalize tags and keywords for comparison and folder naming."""
    return _NORMALIZE_RE.sub("", text.replace("_", " ").lower()).strip()


@tagger_bp.route("/", methods=["GET", "POST"])
def tagger_page():
    folder = (
        request.form.get("folder", "")
        if request.method == "POST"
        else request.args.get("folder", "")
    ).strip()
    images, err = [], ""
    if folder:
        if not os.path.isdir(folder):
            err, folder = "Invalid folder path.", ""
        else:
            for fn in image_files(folder):
                full = os.path.join(folder, fn)
                images.append({"filename": fn, "full_path": full})
    return render_template("tagger.html", folder=folder, images=images, error=err)


@tagger_bp.route("/sort", methods=["POST"])
def tagger_sort():
    folder = request.form["folder"]
    keys = [normalize(t) for t in _SPLIT_RE.split(request.form["tags"]) if t]
    moved = []
    if not keys or not os.path.isdir(folder):
        return jsonify({"moved": []})

    for fn in image_files(folder):
        full = os.path.join(folder, fn)
        try:
            tag_set = {normalize(t) for t in tag_image(full)}
        except Exception:
            continue
        for k in keys:
            if k in tag_set:
                dst = os.path.join(folder, safe(k))
                os.makedirs(dst, exist_ok=True)
                shutil.move(full, os.path.join(dst, fn))
                moved.append(
                    urllib.parse.quote_plus(full)
                )  # encode path for HTML attribute match
                break

    return jsonify({"moved": moved})


@tagger_bp.route("/api/tags", methods=["POST"])
def api_tags():
    path = urllib.parse.unquote(request.form["path"])
    try:
        tags = tag_image(path)
        return (", ".join(tags), 200, {"Content-Type": "text/plain; charset=utf-8"})
    except Exception as e:
        return (str(e), 500)
