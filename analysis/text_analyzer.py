# text_analyzer.py
import re

from .audio import count_words, count_parasites, calc_wpm, score_language


def analyze_text(text: str, duration: float = None):
    """Аналіз готового тексту
    
    Args:
        text: Текст для аналізу
        duration: Тривалість у секундах (опціонально)
    """
    word_count, words = count_words(text)
    parasite_count = count_parasites(words)
    
    # Якщо тривалість не вказана, оцінюємо (приблизно 0.25 секунд на слово)
    if duration is None:
        duration = word_count * 0.25
    
    stats = {
        "total_words": word_count,
        "parasite_count": parasite_count,
        "words_per_min": calc_wpm(word_count, duration),
        "language_score": 0,
        "recognized_text": text[:300] + "…" if len(text) > 300 else text
    }
    
    stats["language_score"] = score_language(stats)
    return stats
