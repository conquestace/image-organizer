import os
import shutil
import urllib.parse
from flask import Blueprint, render_template, request

from utils import rating_of_image, image_files, safe

rating_bp = Blueprint("rating", __name__, url_prefix="/rating")



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
            for fn in image_files(folder):
                full = os.path.join(folder, fn)
                images.append({'filename': fn, 'full_path': full})
    return render_template('rating.html', folder=folder, images=images, error=err, show_images=show)




@rating_bp.route('/api/rating', methods=['POST'])
def api_rating():
    path = urllib.parse.unquote(request.form['path'])
    try:
        cls = rating_of_image(path)
        folder = os.path.dirname(path)
        dst_dir = os.path.join(folder, safe(cls))
        os.makedirs(dst_dir, exist_ok=True)
        name = os.path.basename(path)
        dest = os.path.join(dst_dir, name)
        if os.path.exists(dest):
            base, ext = os.path.splitext(name)
            i = 1
            while os.path.exists(os.path.join(dst_dir, f"{base}_{i}{ext}")):
                i += 1
            dest = os.path.join(dst_dir, f"{base}_{i}{ext}")
        shutil.move(path, dest)

        return (cls, 200, {'Content-Type': 'text/plain; charset=utf-8'})
    except Exception as e:
        return (str(e), 500)
