import re
from datetime import datetime, timedelta
import pytz

def normalize_text(text: str) -> str:
    """Нормализация текста для сравнения ответов"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = ' '.join(text.split())
    return text

def calculate_level(xp: int) -> dict:
    """Расчет уровня и прогресса"""
    base_thresholds = {
        0: 0, 
        1: 20,   
        2: 50,
        3: 100,
        4: 150,
        5: 220,
        6: 300,
        7: 380,
        8: 460,
        9: 560,
        10: 700,
    }

    thresholds = dict(base_thresholds)

    current_level = 0
    for lvl in sorted(thresholds.keys()):
        if xp >= thresholds[lvl]:
            current_level = lvl
        else:
            break

    xp_for_current_level = thresholds.get(current_level, 0)
    xp_for_next_level_threshold = thresholds.get(current_level + 1, thresholds.get(current_level, 0))

    xp_in_level = xp - xp_for_current_level
    xp_for_next_level = xp_for_next_level_threshold - xp_for_current_level
    progress_percent = int((xp_in_level / xp_for_next_level) * 100) if xp_for_next_level > 0 else 0

    return {
        'level': current_level,
        'xp': xp,
        'next_level_xp': xp_for_next_level_threshold,
        'xp_in_level': xp_in_level,
        'xp_for_next_level': xp_for_next_level,
        'progress_percent': progress_percent
    }

def get_level_progress_bar(percent: int, length: int = 10) -> str:
    """Генерация строки прогресс-бара"""
    filled = '#' * (percent * length // 100)
    empty = '-' * (length - len(filled))
    return f"[{filled}{empty}]"

def update_streak(user, session):
    """Обновление стрика пользователя"""
    now = datetime.now(pytz.UTC)
    last_active = user.last_active_date
    old_streak = getattr(user, 'streak', 0) or 0

    if last_active:
        yesterday = now - timedelta(days=1)
        if last_active.date() == yesterday.date():
            user.streak = int(old_streak) + 1
        elif last_active.date() < yesterday.date():
            user.streak = 1
    else:
        user.streak = 1

    user.last_active_date = now
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Streak update for user %s: %s -> %s", getattr(user, 'id', None), old_streak, user.streak)
    except Exception:
        pass
