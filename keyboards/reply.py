from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu_kb(subscription=False):
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="🇬🇧 Учить слова"))
    builder.add(KeyboardButton(text="📊 Статистика"))
    builder.add(KeyboardButton(text="⚙️ Настройки"))
    builder.add(KeyboardButton(text="👤 Профиль"))
    
    if not subscription:
        builder.add(KeyboardButton(text="💎 Подписка"))
    
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_back_to_menu_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🏠 В меню"))
    return builder.as_markup(resize_keyboard=True)

def get_learn_words_kb(available_decks=None, has_problem_words=False):
    """Return a keyboard with available deck buttons.

    available_decks: optional iterable of deck keys: 'base', 'it_english', 'top1000'.
    If None, all decks will be shown (backwards compatible).
    """
    builder = ReplyKeyboardBuilder()

    deck_labels = {
        'base': 'База',
        'it_english': 'IT English',
        'top1000': '1000 Частых слов',
    }

    if available_decks is None:
        chosen = ['base', 'it_english', 'top1000']
    else:
        chosen = [d for d in ['base', 'it_english', 'top1000'] if d in set(available_decks)]

    for d in chosen:
        builder.add(KeyboardButton(text=deck_labels.get(d, d)))

    if has_problem_words:
        builder.add(KeyboardButton(text="🔄 Повторить проблемные слова"))

    builder.add(KeyboardButton(text="🏠 В меню"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_start_test_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Перейти к тесту"))
    builder.add(KeyboardButton(text="🏠 В меню"))
    return builder.as_markup(resize_keyboard=True)

def get_test_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📖 Повторить слова"))
    builder.add(KeyboardButton(text="🏠 В меню"))
    return builder.as_markup(resize_keyboard=True)

def get_settings_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🔔 Уведомления"))
    builder.add(KeyboardButton(text="🗑️ Удалить все данные"))
    builder.add(KeyboardButton(text="🏠 В меню"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_notifications_kb(notifications_enabled):
    builder = ReplyKeyboardBuilder()
    
    if notifications_enabled:
        builder.add(KeyboardButton(text="🔕 Выключить"))
    else:
        builder.add(KeyboardButton(text="🔔 Включить"))
    
    builder.add(KeyboardButton(text="🏠 В меню"))
    return builder.as_markup(resize_keyboard=True)

def get_delete_confirmation_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Да, удалить все"))
    builder.add(KeyboardButton(text="❌ Нет, отменить"))
    return builder.as_markup(resize_keyboard=True)