"""
Two-page organiser
/prompt  – sort by real SD prompts
/tagger  – tag images with imgutils.get_wd14_tags and sort by those tags
"""
import os, json, re, shutil, urllib.parse
from typing import List
from flask import Flask, render_template, request, redirect, url_for, send_file
from PIL import Image

# ─────────  WD-tagger via imgutils  ─────────
try:
    from imgutils.tagging import get_wd14_tags
    from imgutils.tagging.wd14 import MODEL_NAMES as tagger_model_names
except ImportError:
    def get_wd14_tags(image_path, model_name="SwinV2"):
        raise RuntimeError("Please install `dghs-imgutils` to enable tagging.")
    tagger_model_names = {
        "EVA02_Large": None, "ViT_Large": None, "SwinV2": None,
        "ConvNext": None, "ConvNextV2": None, "ViT": None,
        "MOAT": None, "SwinV2_v3": None, "ConvNext_v3": None, "ViT_v3": None,
    }

MODEL_NAME   = "SwinV2"   # change if you prefer another backbone
TAG_THRESHOLD = 0.35      # score threshold
REPLACE_UNDERSCORES = True
# ────────────────────────────────────────────


app         = Flask(__name__)
ALLOWED_EXT = {'.png', '.jpg', '.jpeg'}


# ───────── helper functions ─────────
def prompt_from_meta(path: str):
    try:
        meta = Image.open(path).info
        if 'parameters' in meta:
            return meta['parameters'].split('\n')[0]
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


def get_rating_class(rating: dict) -> str:
    return max(rating, key=rating.get) if rating else ''


def tag_image(path: str) -> List[str]:
    """
    Returns a flat list of tags (feature+character) above TAG_THRESHOLD.
    """
    rating, feats, chars = get_wd14_tags(path, MODEL_NAME)
    tags = [t for t, s in feats.items() if s > TAG_THRESHOLD]
    tags += [t for t, s in chars.items() if s > TAG_THRESHOLD]
    if REPLACE_UNDERSCORES:
        tags = [t.replace('_', ' ') for t in tags]
    return tags


def safe(name: str) -> str:  # safe folder name
    return re.sub(r'[\\/:*?"<>|]+', '_', name)[:64] or 'unknown'


def image_files(folder):
    return [f for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in ALLOWED_EXT]
# ─────────────────────────────────────


# ───────── routes ─────────
@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')


# — PROMPT PAGE —
@app.route('/prompt', methods=['GET', 'POST'])
def prompt_page():
    folder = (request.form.get('folder','') if request.method=='POST'
              else request.args.get('folder','')).strip()
    images, err = [], ''
    if folder:
        if not os.path.isdir(folder):
            err, folder = 'Invalid folder path.', ''
        else:
            for fn in image_files(folder):
                full = os.path.join(folder, fn)
                images.append({'filename': fn,
                               'full_path': full,
                               'prompt': prompt_from_meta(full) or '(no prompt)'})
    return render_template('prompt.html', folder=folder, images=images, error=err)


@app.route('/prompt/sort', methods=['GET','POST'])
def prompt_sort():
    if request.method=='GET':
        return redirect(url_for('prompt_page'))
    folder = request.form['folder']
    keys   = [t.lower() for t in re.split(r'[,\s]+', request.form['tags']) if t]
    if not keys or not os.path.isdir(folder):
        return redirect(url_for('prompt_page', folder=folder))

    for fn in image_files(folder):
        full = os.path.join(folder, fn)
        p    = (prompt_from_meta(full) or '').lower()
        for k in keys:
            if k in p:
                dst = os.path.join(folder, safe(k))
                os.makedirs(dst, exist_ok=True)
                shutil.move(full, os.path.join(dst, fn))
                break
    return redirect(url_for('prompt_page', folder=folder))


# — TAGGER PAGE —
@app.route('/tagger', methods=['GET', 'POST'])
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


@app.route('/tagger/sort', methods=['GET','POST'])
def tagger_sort():
    if request.method=='GET':
        return redirect(url_for('tagger_page'))
    folder = request.form['folder']
    keys   = [t.lower() for t in re.split(r'[,\s]+', request.form['tags']) if t]
    if not keys or not os.path.isdir(folder):
        return redirect(url_for('tagger_page', folder=folder))

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
    return redirect(url_for('tagger_page', folder=folder))


# — SHARED —
@app.route('/image')
def serve_image():
    return send_file(urllib.parse.unquote(request.args.get('path','')))

@app.route('/api/tags', methods=['POST'])
def api_tags():
    path = urllib.parse.unquote(request.form['path'])
    try:
        tags = tag_image(path)
        return (", ".join(tags), 200, {'Content-Type':'text/plain; charset=utf-8'})
    except Exception as e:
        return (str(e), 500)

if __name__ == '__main__':
    app.run(debug=True)
