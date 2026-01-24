import os
from flask import Flask, render_template, request, jsonify
from analysis.audio import transcribe_and_analyze

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    audio_file = request.files.get("audio")
    duration = int(request.form.get("duration", 5))

    if not audio_file:
        return jsonify({"error": "No audio file"}), 400

    webm_path = os.path.join(app.config["UPLOAD_FOLDER"], "voice.webm")
    wav_path = os.path.join(app.config["UPLOAD_FOLDER"], "voice.wav")
    audio_file.save(webm_path)

    stats = transcribe_and_analyze(webm_path, wav_path, duration)
    return jsonify(stats)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

    