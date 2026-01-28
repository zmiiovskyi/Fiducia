import os
import re
import subprocess
import tempfile

import whisper
from config import *

model = whisper.load_model(WHISPER_MODEL)

WORD_RE = re.compile(r"[а-щьюяґєії']+")


def count_words(text):
    words = WORD_RE.findall(text.lower())
    return len(words), words


def analyze_text(text, duration=None):
    if len(text) < MIN_TEXT_LENGTH:
        raise ValueError("text too short")

    words_count, words = count_words(text)
    parasites = sum(1 for w in words if w in PARASITES)

    if not duration:
        duration = (words_count / 150) * 60

    wpm = round((words_count / duration) * 60, 1)

    score = 10
    if wpm < 80 or wpm > 180:
        score -= 2
    if parasites > 5:
        score -= 2

    return {
        "total_words": words_count,
        "parasite_count": parasites,
        "words_per_min": wpm,
        "duration": round(duration, 1),
        "language_score": max(score, 0),
        "recognized_text": text[:500],
        "confidence": "high",
    }

def analyze_audio(path):
    import tempfile
    import subprocess
    import os

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()

    cmd = [
        "ffmpeg",
        "-y",
        "-i", path,
        "-ar", "16000",
        "-ac", "1",
        tmp.name
    ]

    res = subprocess.run(cmd)

    if res.returncode != 0:
        os.remove(tmp.name)
        raise RuntimeError("ffmpeg error")

    result = model.transcribe(tmp.name, language="uk", fp16=False)
    text = result.get("text", "").strip()

    os.remove(tmp.name)

    if not text:
        raise ValueError("speech not recognized")

    return analyze_text(text)
