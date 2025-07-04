from flask import Flask, render_template, request, send_file
import urllib.parse
from prompt_routes import prompt_bp
from tagger_routes import tagger_bp
from rating_routes import rating_bp
from metadata_routes import metadata_bp
from dir_tagger_routes import batch_bp
from utils import prompt_from_meta

app = Flask(__name__)
app.register_blueprint(prompt_bp)
app.register_blueprint(tagger_bp)
app.register_blueprint(rating_bp)
app.register_blueprint(metadata_bp)
app.register_blueprint(batch_bp)


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
    import argparse
    parser = argparse.ArgumentParser(description="Run the Flask app.")
    parser.add_argument("--port", type=int, default=5000, help="port to run")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="host to expose")
    args = parser.parse_args()
    app.run(debug=True, host=args.host, port=args.port)
