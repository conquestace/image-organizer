from flask import Blueprint, render_template, request
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
            pngs = [
                f
                for f in os.listdir(folder)
                if os.path.splitext(f)[1].lower() == ".png"
            ]
            if not pngs:
                message = "No PNG files found in source folder."
            else:
                try:
                    extract_metadata.process(folder, out)
                    message = "Metadata extraction complete."
                except Exception as e:
                    message = str(e)
    return render_template("metadata.html", folder=folder, out=out, message=message)
