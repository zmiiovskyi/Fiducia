import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "wav", "mp3", "webm", "ogg", "m4a", "flac"
}

WHISPER_MODEL = "medium"

MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 10000

PARASITES = {
    "ну", "короче", "типу", "якби", "тобто", "мм", "ее"
}

OPTIMAL_WPM_MIN = 100
OPTIMAL_WPM_MAX = 160
