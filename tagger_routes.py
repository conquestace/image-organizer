import os
import re
import shutil
import json
import urllib.parse
from flask import Blueprint, render_template, request, redirect, url_for, send_file
from utils import tag_image, image_files, safe

tagger_bp = Blueprint('tagger', __name__, url_prefix='/tagger')

@tagger_bp.route('/', methods=['GET', 'POST'])
def tagger_page():
    folder = (request.form.get('folder','') if request.method=='POST'
              else request.args.get('folder','')).strip()
    images, err = [], ''
    if folder:
        if not os.path.isdir(folder):
            err, folder = 'Invalid folder path.', ''
        else:
            for fn in image_files(folder):
                full = os.path.join(folder, fn)
                try:
                    tag_list = tag_image(full)
                except Exception as e:
                    tag_list = [f"[ERROR: {e}]"]
                images.append({'filename': fn,
                               'full_path': full,
                               'tags': tag_list})
    return render_template('tagger.html', folder=folder, images=images, error=err)

@tagger_bp.route('/sort', methods=['GET','POST'])
def tagger_sort():
    if request.method=='GET':
        return redirect(url_for('tagger.tagger_page'))
    folder = request.form['folder']
    keys   = [t.lower() for t in re.split(r'[,\s]+', request.form['tags']) if t]
    if not keys or not os.path.isdir(folder):
        return redirect(url_for('tagger.tagger_page', folder=folder))

    for fn in image_files(folder):
        full = os.path.join(folder, fn)
        try:
            tag_set = {t.lower() for t in tag_image(full)}
        except Exception:
            continue
        for k in keys:
            if k in tag_set:
                dst = os.path.join(folder, safe(k))
                os.makedirs(dst, exist_ok=True)
                shutil.move(full, os.path.join(dst, fn))
                break
    return redirect(url_for('tagger.tagger_page', folder=folder))

@tagger_bp.route('/api/tags', methods=['POST'])
def api_tags():
    path = urllib.parse.unquote(request.form['path'])
    try:
        tags = tag_image(path)
        return (", ".join(tags), 200, {'Content-Type':'text/plain; charset=utf-8'})
    except Exception as e:
        return (str(e), 500)