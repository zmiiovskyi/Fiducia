import os
import uuid
from datetime import datetime

from flask import Flask, jsonify, render_template, request

from config import *
from analysis.audio import analyze_audio, analyze_text

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


def allowed_file(name):
    return "." in name and name.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/analyze", methods=["POST"])
def analyze_audio_route():
    if "audio" not in request.files:
        return jsonify({"error": "no file"}), 400

    file = request.files["audio"]

    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "bad format"}), 400

    filename = str(uuid.uuid4()) + ".wav"
    path = os.path.join(UPLOAD_DIR, filename)

    file.save(path)

    try:
        result = analyze_audio(path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(path):
            os.remove(path)


@app.route("/analyze-text", methods=["POST"])
def analyze_text_route():
    data = request.get_json()

    if not data or "text" not in data:
        return jsonify({"error": "no text"}), 400

    try:
        result = analyze_text(data["text"], data.get("duration"))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
