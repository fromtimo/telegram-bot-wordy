from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from database.db import db
from database.models import User, UserProgress, ProblemWord
from keyboards.reply import (
    get_settings_kb,
    get_notifications_kb,
    get_delete_confirmation_kb,
    get_back_to_menu_kb
)
from handlers.states import FSMSettings
from services.utils import update_streak
from handlers.main_menu import show_main_menu

router = Router()

@router.message(FSMSettings.settings_menu, F.text == "🔔 Уведомления")
async def notifications_settings(message: Message, state: FSMContext):
    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if not user:
            return

        status_text = "✅ Уведомления включены" if user.notifications else "❌ Уведомления выключены"
        await message.answer(
            status_text,
            reply_markup=get_notifications_kb(user.notifications)
        )
        await state.set_state(FSMSettings.notifications)
        
    finally:
        session.close()

@router.message(FSMSettings.notifications, F.text == "🔔 Включить")
async def enable_notifications(message: Message, state: FSMContext):
    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if user:
            user.notifications = True
            session.commit()
            await message.answer("✅ Уведомления включены")
        
        await message.answer(
            "⚙️ Выбери нужный пункт:",
            reply_markup=get_settings_kb()
        )
        await state.set_state(FSMSettings.settings_menu)
        
    finally:
        session.close()

@router.message(FSMSettings.notifications, F.text == "🔕 Выключить")
async def disable_notifications(message: Message, state: FSMContext):
    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if user:
            user.notifications = False
            session.commit()
            await message.answer("❌ Уведомления выключены")
        
        await message.answer(
            "⚙️ Выбери нужный пункт:",
            reply_markup=get_settings_kb()
        )
        await state.set_state(FSMSettings.settings_menu)
        
    finally:
        session.close()

@router.message(FSMSettings.settings_menu, F.text == "🗑️ Удалить все данные")
async def delete_data_confirmation(message: Message, state: FSMContext):
    warning_text = """⚠️ ВНИМАНИЕ: Удаление всех данных

Это действие необратимо и удалит:
• Все изученные слова и прогресс 📚
• Все активные колоды и настройки обучения 🗂
• Все уровни 🎖
• Всю историю повторений и стрик дней 🔥

Ваш аккаунт останется, но все данные будут очищены.

Вы уверены, что хотите удалить всю информацию?"""
    
    await message.answer(warning_text, reply_markup=get_delete_confirmation_kb())
    await state.set_state(FSMSettings.delete_confirmation)

@router.message(FSMSettings.delete_confirmation, F.text == "✅ Да, удалить все")
async def confirm_delete_data(message: Message, state: FSMContext):
    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if user:
            user.level = 1
            user.xp = 0
            user.streak = 0
            
            # Удаляем прогресс изучения слов
            session.query(UserProgress).filter_by(user_id=user.id).delete()
            
            # Удаляем проблемные слова
            session.query(ProblemWord).filter_by(user_id=user.id).delete()
            
            session.commit()
            
            await message.answer("✅ Все данные удалены")
        
        await show_main_menu(message, user)
        await state.clear()
        
    finally:
        session.close()

@router.message(FSMSettings.delete_confirmation, F.text == "❌ Нет, отменить")
async def cancel_delete_data(message: Message, state: FSMContext):
    await message.answer(
        "❌ Удаление отменено",
        reply_markup=get_settings_kb()
    )
    await state.set_state(FSMSettings.settings_menu)