from flask import Blueprint, render_template, request, jsonify
import urllib.parse
import os

import extract_metadata

metadata_bp = Blueprint("metadata", __name__, url_prefix="/metadata")


@metadata_bp.route("/", methods=["GET", "POST"])
def metadata_page():
    folder = (
        request.form.get("folder", "")
        if request.method == "POST"
        else request.args.get("folder", "")
    ).strip()
    out = (
        request.form.get("out", "")
        if request.method == "POST"
        else request.args.get("out", "")
    ).strip()
    message = ""
    if request.method == "POST":
        if not os.path.isdir(folder):
            message = "Invalid source folder."
        elif not out:
            message = "Please specify output folder."
        else:
            try:
                extract_metadata.process(folder, out)
                message = "Metadata extraction complete."
            except Exception as e:
                message = str(e)
    return render_template("metadata.html", folder=folder, out=out, message=message)


@metadata_bp.route("/api/list", methods=["POST"])
def api_list():
    folder = request.form["folder"]
    paths = []
    if os.path.isdir(folder):
        for root, _, files in os.walk(folder):
            for name in files:
                if os.path.splitext(name)[1].lower() == ".png":
                    paths.append(os.path.join(root, name))
    return jsonify({"paths": paths})


@metadata_bp.route("/api/extract", methods=["POST"])
def api_extract():
    path = urllib.parse.unquote(request.form["path"])
    out = request.form["out"]
    try:
        extract_metadata.process_single(path, out)
        return ("ok", 200, {"Content-Type": "text/plain; charset=utf-8"})
    except Exception as e:
        return (str(e), 500)
