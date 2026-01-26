import re
import subprocess
import whisper
import os
from flask import Flask, render_template, request, jsonify, send_from_directory

PARASITES = {
    "ну", "короче", "значить", "типу",
    "якби", "тобто", "мм", "ее", "такс",
    "взагалі", "в принципі"
}

WORD_RE = re.compile(r"[а-щьюяґєії]+")


def count_words(text: str):
    words = WORD_RE.findall(text.lower())
    return len(words), words


def count_parasites(words: list[str]):
    return sum(1 for w in words if w in PARASITES)


def calc_wpm(word_count: int, seconds: float):
    if seconds <= 0:
        return 0.0
    return round((word_count / seconds) * 60, 1)


def score_language(stats: dict):
    wpm = stats["words_per_min"]

    if wpm < 100:
        tempo = 5 + (wpm - 60) / 40 * 5
    elif wpm <= 160:
        tempo = 8 + (wpm - 100) / 60 * 2
    else:
        tempo = 10 - (wpm - 160) / 60 * 5

    tempo = max(0, min(10, tempo))

    p = stats["parasite_count"]
    parasite = 10 if p == 0 else 8 if p <= 5 else 6 if p <= 10 else 4 if p <= 15 else 2

    return round((tempo + parasite) / 2, 1)


def convert_to_wav(src: str, dst: str):
    subprocess.run(
        ["ffmpeg", "-y", "-i", src, "-ar", "16000", "-ac", "1", dst],
        check=True,
        capture_output=True
    )


model = whisper.load_model("medium")


def analyze_audio(audio_path: str):
    base, ext = os.path.splitext(audio_path)
    wav_path = base + ".wav"

    convert_to_wav(audio_path, wav_path)

    result = model.transcribe(
        wav_path,
        language="uk",
        fp16=False,
        temperature=0,
        condition_on_previous_text=False,
        no_speech_threshold=0.6
    )

    text = result["text"]
    segments = result.get("segments", [])
    duration = segments[-1]["end"] if segments else 0.0

    word_count, words = count_words(text)
    parasite_count = count_parasites(words)

    stats = {
        "total_words": word_count,
        "parasite_count": parasite_count,
        "words_per_min": calc_wpm(word_count, duration),
        "language_score": 0,
        "recognized_text": text[:300] + "…" if len(text) > 300 else text
    }

    stats["language_score"] = score_language(stats)
    return stats


def analyze_text(text: str):
    """Аналіз готового тексту"""
    word_count, words = count_words(text)
    parasite_count = count_parasites(words)

    # Оцінюємо тривалість (приблизно 0.25 секунд на слово)
    estimated_duration = word_count * 0.25

    stats = {
        "total_words": word_count,
        "parasite_count": parasite_count,
        "words_per_min": calc_wpm(word_count, estimated_duration),
        "language_score": 0,
        "recognized_text": text[:300] + "…" if len(text) > 300 else text
    }

    stats["language_score"] = score_language(stats)
    return stats


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)

ALLOWED_EXTENSIONS = {"webm", "wav", "mp3", "m4a"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("audio")
    if not file or file.filename == "":
        return jsonify({"error": "Файл не вибрано"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Непідтримуваний формат"}), 400

    filename = file.filename
    path = os.path.join(UPLOAD_DIR, filename)
    file.save(path)

    try:
        stats = analyze_audio(path)
        return jsonify(stats)
    except Exception as e:
        print(f"Помилка при аналізі: {e}")
        return jsonify({"error": f"Помилка при обробці аудіо: {str(e)}"}), 500


@app.route("/analyze-text", methods=["POST"])
def analyze_text_route():
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Текст не надано"}), 400

        text = data["text"].strip()
        if not text:
            return jsonify({"error": "Текст порожній"}), 400

        stats = analyze_text(text)
        return jsonify(stats)
    except Exception as e:
        print(f"Помилка при аналізі тексту: {e}")
        return jsonify({"error": f"Помилка при обробці тексту: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=8000)