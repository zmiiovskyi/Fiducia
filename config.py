import os
from datetime import timedelta


class Config:
    """Базова конфігурація додатку"""

    # Flask налаштування
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    # Шляхи
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

    # Файли
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {"webm", "wav", "mp3", "m4a", "ogg", "flac"}

    # Аудіо налаштування
    WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "medium")
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1

    # Аналіз мови
    PARASITES = {
        "ну",
        "короче",
        "значить",
        "типу",
        "якби",
        "тобто",
        "мм",
        "ее",
        "такс",
        "взагалі",
        "в принципі",
        "ну такий",
        "як би",
        "от",
        "це саме",
        "скажімо так",
        "в загальному",
        "так би мовити",
        "і все таке",
    }

    # Оцінка мовлення
    OPTIMAL_WPM_MIN = 100
    OPTIMAL_WPM_MAX = 160
    SLOW_WPM_THRESHOLD = 60
    FAST_WPM_THRESHOLD = 200

    # Ліміти
    MAX_TEXT_LENGTH = 10000
    MIN_TEXT_LENGTH = 10
    RECORDING_DURATION = 5  # секунд

    # Безпека
    RATE_LIMIT = "10/minute"  # максимум запитів на хвилину

    # Логування
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.path.join(BASE_DIR, "logs", "app.log")

    @staticmethod
    def init_app(app):
        """Ініціалізація додатку з конфігурацією"""
        # Створення необхідних директорій
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)


class DevelopmentConfig(Config):
    """Конфігурація для розробки"""

    DEBUG = True
    WHISPER_MODEL = "base"  # Швидша модель для розробки


class ProductionConfig(Config):
    """Конфігурація для продакшену"""

    DEBUG = False
    WHISPER_MODEL = "medium"


class TestingConfig(Config):
    """Конфігурація для тестування"""

    TESTING = True
    WHISPER_MODEL = "tiny"
    UPLOAD_DIR = "/tmp/test_uploads"


# Словник конфігурацій
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
