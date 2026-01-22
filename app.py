import os
import re
import whisper
import subprocess
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

PARASITES = [
    "ну", "ти", "це", "так", "короче", "значить", "взагалі",
    "типу", "якби", "тобто", "мм", "ее", "такс", "в принципі"
]

def count_words(text: str):
    words = re.findall(r"\w+", text.lower())
    return len(words), words

def count_parasites(words: list):
    return sum(1 for w in words if w in PARASITES)

def calc_wpm(word_count: int, seconds: int):
    if seconds <= 0:
        return 0
    return round((word_count / seconds) * 60, 1)

def score_language(audio_stats: dict):
    wpm = audio_stats.get("words_per_min", 0)

    if wpm < 100:
        tempo_score = 5 + (wpm - 60) / 40 * 5
    elif wpm <= 160:
        tempo_score = 8 + (wpm - 100) / 60 * 2
    else:
        tempo_score = 10 - (wpm - 160) / 60 * 5
    tempo_score = max(0, min(10, tempo_score))

    parasites = audio_stats.get("parasite_count", 0)
    if parasites == 0:
        parasite_score = 10
    elif parasites <= 5:
        parasite_score = 8
    elif parasites <= 10:
        parasite_score = 6
    elif parasites <= 15:
        parasite_score = 4
    else:
        parasite_score = 2

    overall = (tempo_score + parasite_score) / 2
    return round(overall, 1)

def analyze_text(full_text: str, record_seconds: int):
    word_count, words = count_words(full_text)
    parasite_count = count_parasites(words)
    words_per_min = calc_wpm(word_count, record_seconds)

    audio_stats = {
        "total_words": word_count,
        "parasite_count": parasite_count,
        "words_per_min": words_per_min,
        "recognized_text": full_text[:200] + "..."
    }
    audio_stats["language_score"] = score_language(audio_stats)
    return audio_stats

# Завантажуємо модель один раз при старті
model = whisper.load_model("small") # base small medium

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    audio_file = request.files.get("audio")
    duration = int(request.form.get("duration", 5))

    if not audio_file:
        return jsonify({"error": "No audio file"}), 400

    # Зберігаємо webm
    webm_path = os.path.join(app.config["UPLOAD_FOLDER"], "voice.webm")
    wav_path = os.path.join(app.config["UPLOAD_FOLDER"], "voice.wav")
    audio_file.save(webm_path)

    # Конвертуємо webm -> wav (потрібен ffmpeg)
    subprocess.run([
        "ffmpeg", "-y", "-i", webm_path,
        "-ar", "16000", "-ac", "1",
        wav_path
    ], check=True)

    # Розпізнавання
    result = model.transcribe(wav_path, language="uk", fp16=False)
    text = result["text"]

    # Аналіз
    stats = analyze_text(text, duration)
    return jsonify(stats)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
