import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from analysis.audio import analyze_audio, analyze_text
from config import Config, config


def create_app(config_name: str = None) -> Flask:
    """Фабрика додатку Flask"""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ініціалізація конфігурації
    config[config_name].init_app(app)

    # Налаштування логування
    setup_logging(app)

    return app


def setup_logging(app: Flask) -> None:
    """Налаштування логування"""
    if not app.debug:
        log_file = app.config.get("LOG_FILE") or "logs/app.log"
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, app.config.get("LOG_LEVEL", "INFO")))

        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
        file_handler.setFormatter(formatter)

        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config.get("LOG_LEVEL", "INFO")))


# Створення додатку
app = create_app()


def allowed_file(filename: str) -> bool:
    """Перевірка дозволених розширень файлів"""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


def generate_secure_filename(original_filename: str) -> str:
    """Генерація безпечного імені файлу"""
    if "." in original_filename:
        extension = original_filename.rsplit(".", 1)[1].lower()
    else:
        extension = "unknown"

    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{timestamp}_{unique_id}.{extension}"


@app.errorhandler(413)
def too_large(e):
    """Обробник помилки занадто великого файлу"""
    return jsonify(
        {
            "error": f"Файл занадто великий. Максимум: {Config.MAX_FILE_SIZE // (1024 * 1024)}MB"
        }
    ), 413


@app.errorhandler(500)
def internal_error(e):
    """Обробник внутрішньої помилки"""
    app.logger.error(f"Внутрішня помилка: {e}")
    return jsonify({"error": "Внутрішня помилка сервера"}), 500


@app.route("/")
def index():
    """Головна сторінка"""
    return render_template("index.html")


@app.route("/health")
def health_check():
    """Перевірка здоров'я сервісу"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
        }
    )


@app.route("/analyze", methods=["POST"])
def analyze_audio_route():
    """Обробка аудіофайлів"""
    filepath = None
    try:
        if "audio" not in request.files:
            return jsonify({"error": "Файл не знайдено"}), 400

        file = request.files["audio"]

        if not file or file.filename == "":
            return jsonify({"error": "Файл не вибрано"}), 400

        if not allowed_file(file.filename):
            return jsonify(
                {
                    "error": f"Непідтримуваний формат файлу. Дозволені: {', '.join(Config.ALLOWED_EXTENSIONS)}"
                }
            ), 400

        secure_name = generate_secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_DIR, secure_name)

        try:
            file.save(filepath)
            app.logger.info(f"Збережено файл: {secure_name}")
        except Exception as e:
            app.logger.error(f"Помилка збереження файлу: {e}")
            return jsonify({"error": "Помилка збереження файлу"}), 500

        try:
            app.logger.info(f"Початок аналізу файлу: {secure_name}")
            stats = analyze_audio(filepath)
            app.logger.info(f"Аналіз завершено успішно: {secure_name}")
            return jsonify(stats)

        except ValueError as e:
            app.logger.warning(f"Помилка валідації: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            app.logger.error(f"Помилка аналізу аудіо: {e}")
            return jsonify(
                {"error": "Помилка при обробці аудіо. Спробуйте ще раз."}
            ), 500

    except Exception as e:
        app.logger.error(f"Неочікувана помилка при завантаженні: {e}")
        return jsonify({"error": "Неочікувана помилка"}), 500

    finally:
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                app.logger.debug(f"Видалено тимчасовий файл: {filepath}")
        except Exception as e:
            app.logger.warning(f"Не вдалося видалити файл {filepath}: {e}")


@app.route("/analyze-text", methods=["POST"])
def analyze_text_route():
    """Обробка тексту для аналізу"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Дані не надано"}), 400

        if "text" not in data:
            return jsonify({"error": "Текст не надано"}), 400

        text = data["text"]
        if not isinstance(text, str):
            return jsonify({"error": "Текст має бути рядком"}), 400

        text = text.strip()
        if not text:
            return jsonify({"error": "Текст порожній"}), 400

        if len(text) < Config.MIN_TEXT_LENGTH:
            return jsonify(
                {
                    "error": f"Текст занадто короткий. Мінімум: {Config.MIN_TEXT_LENGTH} символів"
                }
            ), 400

        if len(text) > Config.MAX_TEXT_LENGTH:
            return jsonify(
                {
                    "error": f"Текст занадто довгий. Максимум: {Config.MAX_TEXT_LENGTH} символів"
                }
            ), 400

        duration = data.get("duration")
        if duration is not None:
            try:
                duration = float(duration)
                if duration <= 0:
                    return jsonify({"error": "Тривалість має бути більше 0"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Неправильний формат тривалості"}), 400

        try:
            app.logger.info(f"Аналіз тексту ({len(text)} символів)")
            stats = analyze_text(text, duration)
            app.logger.info("Аналіз тексту завершено успішно")
            return jsonify(stats)

        except ValueError as e:
            app.logger.warning(f"Помилка валідації тексту: {e}")
            return jsonify({"error": str(e)}), 400

        except Exception as e:
            app.logger.error(f"Помилка аналізу тексту: {e}")
            return jsonify(
                {"error": "Помилка при обробці тексту. Спробуйте ще раз."}
            ), 500

    except Exception as e:
        app.logger.error(f"Неочікувана помилка при аналізі тексту: {e}")
        return jsonify({"error": "Неочікувана помилка"}), 500


@app.route("/config", methods=["GET"])
def get_config():
    """Отримання публічної конфігурації для фронтенду"""
    return jsonify(
        {
            "max_file_size": Config.MAX_FILE_SIZE,
            "allowed_extensions": list(Config.ALLOWED_EXTENSIONS),
            "max_text_length": Config.MAX_TEXT_LENGTH,
            "min_text_length": Config.MIN_TEXT_LENGTH,
            "recording_duration": Config.RECORDING_DURATION,
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    app.logger.info(f"Запуск додатку на порті {port} (debug: {debug})")
    app.run(debug=debug, host="0.0.0.0", port=port)
