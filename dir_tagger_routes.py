from flask import Blueprint, render_template, request
import os
import json
from tqdm import tqdm

from utils import tag_image, walk_images

batch_bp = Blueprint("batch", __name__, url_prefix="/batch")


def process(folder: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    out_json = os.path.join(out_dir, "tags.json")
    try:
        with open(out_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    paths = list(walk_images(folder))
    for path in tqdm(paths, desc="Tagging images"):
        txt = os.path.splitext(path)[0] + ".txt"
        if os.path.exists(txt):
            continue
        try:
            tags = tag_image(path)
        except Exception:
            continue
        with open(txt, "w", encoding="utf-8") as f:
            f.write(", ".join(tags))
        rel = os.path.relpath(path, folder)
        data[rel] = tags

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@batch_bp.route("/", methods=["GET", "POST"])
def batch_page():
    folder = (
        request.form.get("folder", "") if request.method == "POST" else request.args.get("folder", "")
    ).strip()
    out = (
        request.form.get("out", "") if request.method == "POST" else request.args.get("out", "")
    ).strip()
    message = ""
    if request.method == "POST":
        if not os.path.isdir(folder):
            message = "Invalid source folder."
        elif not out:
            message = "Please specify output folder."
        else:
            try:
                process(folder, out)
                message = "Tagging complete."
            except Exception as e:
                message = str(e)
    return render_template("dir_tagger.html", folder=folder, out=out, message=message)
