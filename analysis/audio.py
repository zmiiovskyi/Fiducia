import logging
import os
import re
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import whisper

from config import Config

# Налаштування логування
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Регулярний вираз для пошуку українських слів
WORD_RE = re.compile(r"[а-щьюяґєії']+")

# Кеш для моделі Whisper
_whisper_model = None


def get_whisper_model():
    """Отримання моделі Whisper з кешуванням"""
    global _whisper_model
    if _whisper_model is None:
        try:
            logger.info(f"Завантаження моделі Whisper: {Config.WHISPER_MODEL}")
            _whisper_model = whisper.load_model(Config.WHISPER_MODEL)
        except Exception as e:
            logger.error(f"Помилка завантаження моделі Whisper: {e}")
            raise
    return _whisper_model


def count_words(text: str) -> Tuple[int, List[str]]:
    """Підрахунок слів у тексті"""
    if not text:
        return 0, []
    words = WORD_RE.findall(text.lower())
    return len(words), words


def count_parasites(words: List[str]) -> int:
    """Підрахунок слів-паразитів"""
    return sum(1 for word in words if word in Config.PARASITES)


def calc_wpm(word_count: int, seconds: float) -> float:
    """Розрахунок слів за хвилину"""
    if seconds <= 0 or word_count <= 0:
        return 0.0
    return round((word_count / seconds) * 60, 1)


def score_language(stats: Dict[str, Any]) -> float:
    """Розрахунок загальної оцінки мовлення"""
    wpm = stats.get("words_per_min", 0)
    parasite_count = stats.get("parasite_count", 0)

    # Оцінка темпу мовлення
    if wpm < Config.SLOW_WPM_THRESHOLD:
        tempo_score = max(0, 5 + (wpm - Config.SLOW_WPM_THRESHOLD) / 40 * 5)
    elif wpm <= Config.OPTIMAL_WPM_MAX:
        tempo_score = 8 + min(2, (wpm - Config.OPTIMAL_WPM_MIN) / 60 * 2)
    else:
        tempo_score = max(0, 10 - (wpm - Config.OPTIMAL_WPM_MAX) / 60 * 5)

    tempo_score = max(0, min(10, tempo_score))

    # Оцінка слів-паразитів
    if parasite_count == 0:
        parasite_score = 10
    elif parasite_count <= 2:
        parasite_score = 9
    elif parasite_count <= 5:
        parasite_score = 8
    elif parasite_count <= 10:
        parasite_score = 6
    elif parasite_count <= 15:
        parasite_score = 4
    else:
        parasite_score = 2

    # Середня оцінка з ваговими коефіцієнтами
    total_score = (tempo_score * 0.6) + (parasite_score * 0.4)
    return round(total_score, 1)


def convert_to_wav(src_path: str, dst_path: str) -> None:
    """Конвертація аудіофайлу у формат WAV"""
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            src_path,
            "-ar",
            str(Config.AUDIO_SAMPLE_RATE),
            "-ac",
            str(Config.AUDIO_CHANNELS),
            "-f",
            "wav",
            dst_path,
        ]

        logger.info(f"Конвертація аудіо: {src_path} -> {dst_path}")
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True, timeout=60
        )
        logger.debug("FFmpeg успішно завершено")

    except subprocess.TimeoutExpired:
        logger.error("Таймаут конвертації аудіо")
        raise Exception("Конвертація аудіо зайняла занадто багато часу")
    except subprocess.CalledProcessError as e:
        logger.error(f"Помилка FFmpeg: {e.stderr}")
        raise Exception(f"Помилка конвертації аудіо: {e.stderr}")
    except Exception as e:
        logger.error(f"Неочікувана помилка конвертації: {e}")
        raise


def validate_audio_file(file_path: str) -> None:
    """Валідація аудіофайлу"""
    if not os.path.exists(file_path):
        raise ValueError("Файл не існує")

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise ValueError("Файл порожній")

    if file_size > Config.MAX_FILE_SIZE:
        raise ValueError(
            f"Файл занадто великий. Максимум: {Config.MAX_FILE_SIZE // (1024 * 1024)}MB"
        )


def analyze_audio(audio_path: str) -> Dict[str, Any]:
    """Аналіз аудіофайлу"""
    try:
        validate_audio_file(audio_path)

        temp_wav = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_wav = f.name

            convert_to_wav(audio_path, temp_wav)
            model = get_whisper_model()
            logger.info("Розпізнавання мови...")

            result = model.transcribe(
                temp_wav,
                language="uk",
                fp16=False,
                temperature=0,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
            )

            text = str(result.get("text", "")).strip()
            segments = result.get("segments", [])

            if segments and len(segments) > 0:
                duration = float(segments[-1]["end"])
            else:
                duration = 1.0

            logger.info(f"Розпізнано {len(text)} символів за {duration:.1f} сек")

            word_count, words = count_words(text)
            parasite_count = count_parasites(words)
            wpm = calc_wpm(word_count, duration)

            stats = {
                "total_words": word_count,
                "parasite_count": parasite_count,
                "words_per_min": wpm,
                "duration": round(duration, 1),
                "language_score": 0,
                "recognized_text": text[:500] + "…" if len(text) > 500 else text,
                "confidence": "high" if len(text) > 10 else "low",
            }

            stats["language_score"] = score_language(stats)

            logger.info(
                f"Аналіз завершено: {word_count} слів, {parasite_count} паразитів, {wpm} WPM"
            )
            return stats

        finally:
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception as e:
                    logger.warning(f"Не вдалося видалити тимчасовий файл: {e}")

    except Exception as e:
        logger.error(f"Помилка аналізу аудіо: {e}")
        raise


def analyze_text(text: str, duration: Optional[float] = None) -> Dict[str, Any]:
    """Аналіз готового тексту"""
    if not text or not text.strip():
        raise ValueError("Текст порожній")

    text = text.strip()

    if len(text) < Config.MIN_TEXT_LENGTH:
        raise ValueError(
            f"Текст занадто короткий. Мінімум: {Config.MIN_TEXT_LENGTH} символів"
        )

    if len(text) > Config.MAX_TEXT_LENGTH:
        raise ValueError(
            f"Текст занадто довгий. Максимум: {Config.MAX_TEXT_LENGTH} символів"
        )

    word_count, words = count_words(text)
    parasite_count = count_parasites(words)

    if duration is None:
        duration = (word_count / 150) * 60  # секунди

    wpm = calc_wpm(word_count, duration)

    stats = {
        "total_words": word_count,
        "parasite_count": parasite_count,
        "words_per_min": wpm,
        "duration": round(duration, 1),
        "language_score": 0,
        "recognized_text": text[:500] + "…" if len(text) > 500 else text,
        "confidence": "high",
    }

    stats["language_score"] = score_language(stats)

    logger.info(
        f"Аналіз тексту: {word_count} слів, {parasite_count} паразитів, {wpm} WPM"
    )
    return stats
