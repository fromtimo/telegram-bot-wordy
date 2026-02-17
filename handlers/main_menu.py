from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

from database.db import db
from database.models import User, UserProgress, ProblemWord, Word
from keyboards.reply import (
    get_main_menu_kb, 
    get_learn_words_kb,
    get_settings_kb,
    get_back_to_menu_kb
)
from handlers.states import FSMMainMenu, FSMLearnWords, FSMSettings
from services.utils import update_streak, calculate_level, get_level_progress_bar

router = Router()

@router.message(FSMMainMenu.main_menu, F.text == "🇬🇧 Учить слова")
async def learn_words(message: Message, state: FSMContext):
    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if not user:
            return
        
        problem_words_count = session.query(ProblemWord).filter_by(
            user_id=user.id
        ).count()

        decks_in_db = session.query(Word.deck).distinct().all()
        available_decks = [d for (d,) in decks_in_db]

        await message.answer(
            "📚 Выбери колоду для изучения:",
            reply_markup=get_learn_words_kb(available_decks, problem_words_count > 0)
        )
        await state.set_state(FSMLearnWords.deck_selection)
        
    finally:
        session.close()

@router.message(FSMMainMenu.main_menu, F.text == "📊 Статистика")
async def show_statistics(message: Message, state: FSMContext):
    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if not user:
            return
        
        deck_stats = session.query(
            UserProgress.deck,
            func.count(UserProgress.id).label('total_learned'),
            func.avg(UserProgress.correct_count).label('avg_correct')
        ).filter(
            UserProgress.user_id == user.id,
            UserProgress.learned == True
        ).group_by(UserProgress.deck).all()
        
        total_words_by_deck = session.query(
            Word.deck,
            func.count(Word.id).label('total_words')
        ).group_by(Word.deck).all()
        total_words_dict = {deck: count for deck, count in total_words_by_deck}
        
        problem_words_count = session.query(ProblemWord).filter_by(
            user_id=user.id
        ).count()
        
        total_correct = session.query(func.sum(UserProgress.correct_count)).filter(
            UserProgress.user_id == user.id
        ).scalar() or 0
        
        total_reviews = session.query(func.count(UserProgress.id)).filter(
            UserProgress.user_id == user.id
        ).scalar() or 1
        
        overall_percentage = int((total_correct / (total_reviews * 5)) * 100) if total_reviews > 0 else 0
        
        stats_text = "📚 Колоды:\n\n"
        
        for deck_stat in deck_stats:
            deck_name = deck_stat.deck
            learned = deck_stat.total_learned
            total_in_deck = total_words_dict.get(deck_name, 0)
            percentage = int((learned / total_in_deck) * 100) if total_in_deck > 0 else 0
            avg_correct = int(deck_stat.avg_correct * 20) if deck_stat.avg_correct else 0
            
            deck_display = {
                'base': 'Basic English',
                'it_english': 'IT English', 
                'top1000': '1000 Самых частых слов'
            }.get(deck_name, deck_name)
            
            stats_text += f"{deck_display} — {learned}/{total_in_deck} слов ({avg_correct}% правильных)\n"
        
        stats_text += f"\nПроблемные слова — {problem_words_count}"
        stats_text += f"\n\nОбщий процент правильных ответов за всё время: {overall_percentage}%"
        
        await message.answer(stats_text, reply_markup=get_back_to_menu_kb())
        
    finally:
        session.close()

@router.message(FSMMainMenu.main_menu, F.text == "👤 Профиль")
async def show_profile(message: Message, state: FSMContext):
    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if not user:
            return
        
        learned_words_count = session.query(UserProgress).filter_by(
            user_id=user.id,
            learned=True
        ).count()
        
        level_info = calculate_level(user.xp)
        
        profile_text = f"""👤 Профиль: {user.first_name}
Уровень: {level_info['level']} 🔰
Прогресс до Level {level_info['level'] + 1}: {level_info['xp_in_level']}/{level_info['xp_for_next_level']} XP
Выучено слов: {learned_words_count}
Стрик: {user.streak} дней 🔥"""
        
        await message.answer(profile_text, reply_markup=get_back_to_menu_kb())
        
    finally:
        session.close()

@router.message(FSMMainMenu.main_menu, F.text == "⚙️ Настройки")
async def show_settings(message: Message, state: FSMContext):
    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if not user:
            return
        
        await message.answer(
            "⚙️ Выбери нужный пункт:",
            reply_markup=get_settings_kb()
        )
        await state.set_state(FSMSettings.settings_menu)
        
    finally:
        session.close()

@router.message(FSMMainMenu.main_menu, F.text == "💎 Подписка")
async def show_subscription(message: Message, state: FSMContext):
    await message.answer(
        "💎 Функция подписки в разработке...",
        reply_markup=get_back_to_menu_kb()
    )

@router.message(F.text == "🏠 В меню")
async def back_to_menu(message: Message, state: FSMContext):
    """Обработчик кнопки 'В меню' из любого состояния"""
    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if user:
            # не обновляем стрик просто при возврате в меню
            await show_main_menu(message, user)
            await state.set_state(FSMMainMenu.main_menu)
            session.close()
            return
            await show_main_menu(message, user)
            await state.set_state(FSMMainMenu.main_menu)
        else:
            from handlers.start_info import cmd_start
            await cmd_start(message, state)
            
    finally:
        session.close()

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
