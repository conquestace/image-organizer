import os
import shutil
import urllib.parse
from flask import Blueprint, render_template, request, jsonify, redirect, url_for

from utils import rating_of_image, image_files, safe, walk_images

rating_bp = Blueprint('rating', __name__, url_prefix='/rating')


@rating_bp.route('/', methods=['GET', 'POST'])
def rating_page():
    folder = (
        request.form.get('folder', '') if request.method == 'POST' else request.args.get('folder', '')
    ).strip()
    show = (request.form.get('show') or request.args.get('show')) is not None
    images, err = [], ''
    if folder:
        if not os.path.isdir(folder):
            err, folder = 'Invalid folder path.', ''
        else:
            for full in walk_images(
                folder, ignore=['questionable', 'explicit', 'sensitive', 'general']
            ):
                images.append({'filename': os.path.relpath(full, folder), 'full_path': full})
    return render_template('rating.html', folder=folder, images=images, error=err, show_images=show)


@rating_bp.route('/sort', methods=['POST'])
def rating_sort():
    folder = request.form['folder']
    moved = []
    if not os.path.isdir(folder):
        return jsonify({'moved': moved})

    for full in walk_images(
        folder, ignore=['questionable', 'explicit', 'sensitive', 'general']
    ):
        try:
            cls = rating_of_image(full)
        except Exception:
            continue
        dst = os.path.join(os.path.dirname(full), safe(cls))
        os.makedirs(dst, exist_ok=True)
        shutil.move(full, os.path.join(dst, os.path.basename(full)))
        moved.append(urllib.parse.quote_plus(full))

    return jsonify({'moved': moved})


@rating_bp.route('/api/rating', methods=['POST'])
def api_rating():
    path = urllib.parse.unquote(request.form['path'])
    move = request.form.get('move')
    try:
        cls = rating_of_image(path)
        if move:
            dst = os.path.join(os.path.dirname(path), safe(cls))
            os.makedirs(dst, exist_ok=True)
            shutil.move(path, os.path.join(dst, os.path.basename(path)))
        return (cls, 200, {'Content-Type': 'text/plain; charset=utf-8'})
    except Exception as e:
        return (str(e), 500)
