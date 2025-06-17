from flask import Flask, render_template, request, send_file
import urllib.parse
from prompt_routes import prompt_bp
from tagger_routes import tagger_bp
from rating_routes import rating_bp
from metadata_routes import metadata_bp
from utils import prompt_from_meta

app = Flask(__name__)
app.register_blueprint(prompt_bp)
app.register_blueprint(tagger_bp)
app.register_blueprint(rating_bp)
app.register_blueprint(metadata_bp)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/image")
def serve_image():
    return send_file(urllib.parse.unquote(request.args.get("path", "")))


@app.route("/api/prompt", methods=["POST"])
def api_prompt():
    path = urllib.parse.unquote(request.form["path"])
    return (
        prompt_from_meta(path) or "(no prompt)",
        200,
        {"Content-Type": "text/plain; charset=utf-8"},
    )


if __name__ == "__main__":
    app.run(debug=True)
