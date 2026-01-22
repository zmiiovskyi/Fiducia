import os
import re
import subprocess
import whisper

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

def webm_to_wav(webm_path: str, wav_path: str):
    subprocess.run([
        "ffmpeg", "-y", "-i", webm_path,
        "-ar", "16000", "-ac", "1",
        wav_path
    ], check=True)

# Завантажуємо модель один раз
model = whisper.load_model("small")

def transcribe_and_analyze(webm_path: str, wav_path: str, duration: int):
    # конвертація
    webm_to_wav(webm_path, wav_path)

    # розпізнавання
    result = model.transcribe(wav_path, language="uk", fp16=False)
    text = result["text"]
    # аналіз
    return analyze_text(text, duration)
