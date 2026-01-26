import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from analysis.audio import analyze_audio
from analysis.text_analyzer import analyze_text


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
def analyze_audio_route():
    """Обробка аудіофайлів"""
    # Перевірка, чи файл був відправлений
    if "audio" not in request.files:
        return jsonify({"error": "Файл не знайдено"}), 400
    
    file = request.files["audio"]
    
    # Перевірка, чи файл вибраний
    if file.filename == "":
        return jsonify({"error": "Файл не вибрано"}), 400
    
    # Перевірка формату файлу
    if not allowed_file(file.filename):
        return jsonify({"error": "Непідтримуваний формат файлу"}), 400
    
    # Збереження файлу
    filename = os.path.join(UPLOAD_DIR, file.filename)
    file.save(filename)
    
    try:
        # Аналіз аудіо
        stats = analyze_audio(filename)
        return jsonify(stats)
    except Exception as e:
        # Логування помилки для дебаггінгу
        print(f"Помилка при аналізі аудіо: {e}")
        return jsonify({"error": f"Помилка при обробці аудіо: {str(e)}"}), 500
    finally:
        # Спроба видалити тимчасовий файл
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print(f"Не вдалося видалити файл: {e}")

@app.route("/analyze-text", methods=["POST"])
def analyze_text_route():
    """Обробка тексту для аналізу"""
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Текст не надано"}), 400
        
        text = data["text"].strip()
        if not text:
            return jsonify({"error": "Текст порожній"}), 400
        
        # Опціональна тривалість
        duration = data.get("duration")
        
        # Аналіз тексту
        stats = analyze_text(text, duration)
        return jsonify(stats)
        
    except Exception as e:
        print(f"Помилка при аналізі тексту: {e}")
        return jsonify({"error": f"Помилка при обробці тексту: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8000)
