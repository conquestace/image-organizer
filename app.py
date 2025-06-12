from flask import Flask, render_template, request, redirect, send_file, url_for
from PIL import Image
import json, os, re, shutil, urllib.parse

app = Flask(__name__)
ALLOWED_EXTENSIONS = {'.png'}   # add '.jpg' if you wish


# ────────────────────────── metadata helper ──────────────────────────────────
def extract_sd_metadata(path):
    flat = {}
    try:
        img, meta = Image.open(path), Image.open(path).info

        # Automatic1111 / InvokeAI
        if 'parameters' in meta:
            flat['prompt'] = meta['parameters'].split('\n')[0]

        # Simple 'Prompt' key
        if 'Prompt' in meta and not flat.get('prompt'):
            flat['prompt'] = meta['Prompt']

        # JSON chunks (Swarm UI / SUI, A1111 "sd-metadata")
        for chunk in [v for v in meta.values()
                      if isinstance(v, str) and v.lstrip().startswith('{')]:
            try:
                doc = json.loads(chunk)
                if 'sui_image_params' in doc:
                    flat['prompt'] = doc['sui_image_params'].get(
                        'prompt', flat.get('prompt'))
                if 'prompt' in doc and not flat.get('prompt'):
                    flat['prompt'] = doc['prompt']
            except json.JSONDecodeError:
                pass

        # include everything else for completeness
        for k, v in meta.items():
            if k not in flat:
                flat[k] = v
    except Exception as e:
        print(f"[ERROR] reading {path}: {e}")
    return flat


# ─────────────────────────── routes ──────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    • GET  /?folder=...  → show thumbnails for that folder
    • POST (scan form)   → same effect, but from form submission
    """
    folder = ''
    if request.method == 'POST':
        folder = request.form.get('folder', '').strip()
    else:  # GET
        folder = request.args.get('folder', '').strip()

    images, error = [], ''
    if folder:
        if not os.path.isdir(folder):
            error = 'Invalid folder path.'
            folder = ''
        else:
            for fname in os.listdir(folder):
                if os.path.splitext(fname)[1].lower() not in ALLOWED_EXTENSIONS:
                    continue
                fpath  = os.path.join(folder, fname)
                prompt = extract_sd_metadata(fpath).get('prompt',
                                                        '(no prompt found)')
                images.append({'filename': fname,
                               'full_path': fpath,
                               'prompt': prompt})

    return render_template('index.html',
                           images=images,
                           folder=folder,
                           error=error)


@app.route('/image')
def serve_image():
    """Serve raw image bytes for <img> tags."""
    fpath = urllib.parse.unquote(request.args.get('path', ''))
    return send_file(fpath)


@app.route('/prompt', methods=['POST'])
def prompt_api():
    """Return the prompt string for modal display."""
    fpath  = urllib.parse.unquote(request.form['path'])
    prompt = extract_sd_metadata(fpath).get('prompt', '(no prompt found)')
    return prompt, 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/sort', methods=['POST'])
def sort():
    folder = request.form['folder']
    raw    = request.form['tags']
    tags   = [t.strip().lower() for t in re.split(r'[,\s]+', raw) if t.strip()]
    if not tags or not os.path.isdir(folder):
        return redirect(url_for('index', folder=folder))

    for fname in os.listdir(folder):
        if os.path.splitext(fname)[1].lower() not in ALLOWED_EXTENSIONS:
            continue

        fpath  = os.path.join(folder, fname)
        prompt = (extract_sd_metadata(fpath).get('prompt') or '').lower()

        for tag in tags:
            if tag in prompt:
                safe = re.sub(r'[\\/:*?"<>|]+', '_', tag)[:64] or 'unknown'
                dest = os.path.join(folder, safe)
                os.makedirs(dest, exist_ok=True)
                shutil.move(fpath, os.path.join(dest, fname))
                print(f"Moved {fname} → {dest}/")
                break

    # ⬇️ reload same folder view so user stays in context
    return redirect(url_for('index', folder=folder))


if __name__ == '__main__':
    app.run(debug=True)
