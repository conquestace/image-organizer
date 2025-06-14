import os
import re
import shutil
from flask import Blueprint, render_template, request, redirect, url_for
from utils import prompt_from_meta, image_files, safe

_SPLIT_RE = re.compile(r"[,\s]+")

prompt_bp = Blueprint("prompt", __name__, url_prefix="/prompt")


@prompt_bp.route("/", methods=["GET", "POST"])
def prompt_page():
    folder = (
        request.form.get("folder", "")
        if request.method == "POST"
        else request.args.get("folder", "")
    ).strip()
    show = (request.form.get("show") or request.args.get("show")) is not None
    images, err = [], ""
    if folder:
        if not os.path.isdir(folder):
            err, folder = "Invalid folder path.", ""
        else:
            for fn in image_files(folder):
                full = os.path.join(folder, fn)
                images.append(
                    {
                        "filename": fn,
                        "full_path": full,
                        "prompt": prompt_from_meta(full) or "(no prompt)",
                    }
                )
    return render_template(
        "prompt.html", folder=folder, images=images, error=err, show_images=show
    )


@prompt_bp.route("/sort", methods=["GET", "POST"])
def prompt_sort():
    if request.method == "GET":
        return redirect(url_for("prompt.prompt_page"))
    folder = request.form["folder"]
    show = request.form.get("show")
    keys = [t.lower() for t in _SPLIT_RE.split(request.form["tags"]) if t]
    if not keys or not os.path.isdir(folder):
        return redirect(url_for("prompt.prompt_page", folder=folder, show=show))

    for fn in image_files(folder):
        full = os.path.join(folder, fn)
        p = (prompt_from_meta(full) or "").lower()
        for k in keys:
            if k in p:
                dst = os.path.join(folder, safe(k))
                os.makedirs(dst, exist_ok=True)
                shutil.move(full, os.path.join(dst, fn))
                break
    return redirect(url_for("prompt.prompt_page", folder=folder, show=show))
