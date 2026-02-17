from aiogram import Router, F
from aiogram.types import Message, InputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import asyncio
import os

from database.db import db
from database.models import User
from keyboards.reply import get_main_menu_kb, get_back_to_menu_kb
from handlers.states import FSMMainMenu

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        
        welcome_text = f"""🚀 Привет, {message.from_user.first_name}. Ты только что подключился к системе обучения английского.

Здесь каждое слово — ключ к новым уровням твоей памяти.
Каждый день — испытание твоей внимательности и упорства.
XP и достижения будут твоей меткой в этой сети знаний.
Начни прямо сейчас и выбирай первый «пакет слов», чтобы развить твои навыки на полную.

🔥 Не теряй стрик — он хранит твою последовательность и силы."""
        
        sent_message = await message.answer(welcome_text)
        
        if not user:
            user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            user.last_active_date = None
            user.streak = 0
            session.add(user)
            session.commit()
        
        await asyncio.sleep(2)

        await show_main_menu(message, user)
        await state.set_state(FSMMainMenu.main_menu)

    finally:
        session.close()

@router.message(Command("info"))
async def cmd_info(message: Message, state: FSMContext):
    await state.clear()
    
    info_text = """ℹ️ Информация о боте

Ты находишься в интеллектуальной системе изучения английского языка, созданной для тех, кто ценит структуру, эффективность и атмосферу прогресса.

Здесь нет случайных слов — каждая единица добавлена с точностью.

📘 Функционал:
• Обучение по тематическим колодам
• Тесты для закрепления материала и система проблемных слов
• Уровни, XP и стрики — чтобы видеть реальный рост
• Статистика по колодам и общему прогрессу
• Профиль с динамическими данными и возможностью полного сброса
• Уведомления и напоминания о занятиях — чтобы не терять темп
• Поддержка и развитие через обновления контента

🧠 База данных:
Содержит более 2000 тщательно отобранных слов с переводом.

При багах перезапусти бота комнадой /start. Если проблема не решится, свяжись со мной.

👨‍💻 Создатель и разработчик:
@fromtimo

Для связи по вопросам, идеям и сотрудничеству — пиши напрямую."""
    
    await message.answer(info_text, reply_markup=get_back_to_menu_kb())

async def show_main_menu(message: Message, user):
    """Показ главного меню с динамическими данными и картинкой"""
    from services.utils import calculate_level, get_level_progress_bar
    from aiogram.types import FSInputFile
    import os
    
    level_info = calculate_level(user.xp)
    
    menu_text = f"""Level {level_info['level']} 🔰 {level_info['xp_in_level']}/{level_info['xp_for_next_level']} XP
{get_level_progress_bar(level_info['progress_percent'])} {level_info['progress_percent']}%
Новый уровень через {level_info['xp_for_next_level'] - level_info['xp_in_level']} XP 🤌
{user.streak} дней подряд 🔥"""
    
    image_path = "images/main_menu.jpg"
    
    try:
        if os.path.exists(image_path):
            photo = FSInputFile(image_path)
            await message.answer_photo(
                photo=photo,
                caption=menu_text,
                reply_markup=get_main_menu_kb(user.subscription)
            )
        else:
            await message.answer(
                menu_text,
                reply_markup=get_main_menu_kb(user.subscription)
            )
            print(f"⚠️ Картинка не найдена по пути: {image_path}")
            
    except Exception as e:
        print(f"❌ Ошибка при отправке фото: {e}")
        await message.answer(
            menu_text,
            reply_markup=get_main_menu_kb(user.subscription)
        )