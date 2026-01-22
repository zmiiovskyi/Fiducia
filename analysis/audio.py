import re
import whisper
import numpy as np
import sounddevice as sd
import wave

def record_audio(filename, duration=5, samplerate=16000):
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    with wave.open(filename, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(samplerate)
        f.writeframes(audio.tobytes())
    return filename

import re
import whisper

# Список типових слів-паразитів (можна доповнювати)
PARASITES = [
    "ну", "ти", "це", "так", "короче", "значить", "взагалі",
    "типу", "якби", "тобто", "мм", "ее", "такс", "в принципі",
    "значить", "якось"
]

def count_words(text: str) -> int:
    words = re.findall(r"\w+", text.lower())
    return len(words), words

def count_parasites(words: list) -> int:
    count = 0
    for w in words:
        if w in PARASITES:
            count += 1
    return count

def calc_wpm(word_count: int, seconds: int) -> float:
    if seconds <= 0:
        return 0
    return round((word_count / seconds) * 60, 1)

def score_language(audio_stats: dict) -> float:
    # Темп (ідеал 120-160)
    wpm = audio_stats.get("words_per_min", 0)

    if wpm < 100:
        tempo_score = 5 + (wpm - 60) / 40 * 5
    elif wpm <= 160:
        tempo_score = 8 + (wpm - 100) / 60 * 2
    else:
        tempo_score = 10 - (wpm - 160) / 60 * 5
    tempo_score = max(0, min(10, tempo_score))

    # Паразити
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

    # Загальний бал (середнє)
    overall = (tempo_score + parasite_score) / 2
    return round(overall, 1)

def analyze_text(full_text: str, record_seconds: int) -> dict:
    # Рахуємо слова
    word_count, words = count_words(full_text)

    # Рахуємо паразити
    parasite_count = count_parasites(words)

    # Темп
    words_per_min = calc_wpm(word_count, record_seconds)

    # Загальна оцінка мови
    audio_stats = {
        "total_words": word_count,
        "parasite_count": parasite_count,
        "words_per_min": words_per_min,
        "recognized_text": full_text[:200] + "..."  # тільки початок
    }

    audio_stats["language_score"] = score_language(audio_stats)
    return audio_stats

# === Приклад використання ===
if __name__ == "__main__":
    # 1) розпізнаємо текст (Whisper)
    model = whisper.load_model("base")
    result = model.transcribe("voice.wav", language="uk", fp16=False)
    text = result["text"]

    # 2) аналізуємо
    stats = analyze_text(text, record_seconds=5)

    print(stats)
