from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session
from sqlalchemy import func
import random

from database.db import db
from database.models import User, Word, UserProgress, ProblemWord
import logging
from keyboards.reply import (
    get_learn_words_kb,
    get_start_test_kb,
    get_test_kb,
    get_back_to_menu_kb
)
from handlers.states import FSMLearnWords
from services.utils import update_streak, normalize_text
from handlers.main_menu import show_main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.message(FSMLearnWords.deck_selection, F.text.in_(["База", "IT English", "1000 Частых слов"]))
async def select_deck(message: Message, state: FSMContext):
    if not message.from_user:
        return

    serial_new_words = []
    with db.session_scope() as session:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if not user:
            return

        deck_map = {
            "База": "base",
            "IT English": "it_english",
            "1000 Частых слов": "top1000",
        }
        deck = deck_map.get(message.text or "")
        if not deck:
            return

        await state.update_data(
            selected_deck=deck,
            is_problem_words=False,
            test_answers={},
            current_word_index=0,
        )

        learned_words_subquery = session.query(UserProgress.word_id).filter(
            UserProgress.user_id == user.id,
            UserProgress.learned == True,
        )

        new_words = session.query(Word).filter(
            Word.deck == deck,
            ~Word.id.in_(learned_words_subquery),
        ).order_by(func.random()).limit(5).all()

        if not new_words:
            await message.answer(
                f"🎉 Поздравляем! Вы изучили всю колоду \"{message.text}\"!",
                reply_markup=get_back_to_menu_kb(),
            )
            return

        for w in new_words:
            serial_new_words.append({
                'id': w.id,
                'word': w.word,
                'translation': w.translation,
                'deck': w.deck,
            })

    await state.update_data(current_words=serial_new_words)

    words_text = "🌅 Новые слова на сегодня:\n\n"
    for i, word in enumerate(serial_new_words, 1):
        words_text += f"{i}️⃣ {word['word']} — {word['translation']}\n"

    words_message = await message.answer(words_text, reply_markup=get_start_test_kb())
    await state.update_data(words_message_id=words_message.message_id)
    await state.set_state(FSMLearnWords.show_new_words)

@router.message(FSMLearnWords.deck_selection, F.text == "🔄 Повторить проблемные слова")
async def review_problem_words(message: Message, state: FSMContext):
    if not message.from_user:
        return

    session = db.get_session()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if not user:
            return
        
        problem_words = session.query(Word).join(ProblemWord, ProblemWord.word_id == Word.id).filter(ProblemWord.user_id == user.id).all()

        if not problem_words:
            await message.answer(
                "✅ Проблемных слов для повторения нет!",
                reply_markup=get_learn_words_kb(has_problem_words=False)
            )
            return

        serial_problem_words = []
        for w in problem_words:
            serial_problem_words.append({
                'id': w.id,
                'word': w.word,
                'translation': w.translation,
                'deck': w.deck,
            })

        await state.update_data(
            current_words=serial_problem_words,
            is_problem_words=True,
            selected_deck=None,
            test_answers={},
            current_word_index=0,
        )
        
        words_text = "🔄 Слова для повторения:\n\n"
        for i, word in enumerate(serial_problem_words, 1):
            words_text += f"{i}️⃣ {word['word']} — {word['translation']}\n"
        
        words_msg = await message.answer(words_text, reply_markup=get_start_test_kb())
        await state.update_data(words_message_id=words_msg.message_id)
        await state.set_state(FSMLearnWords.show_problem_words)
    finally:
        session.close()

@router.message(FSMLearnWords.show_new_words, F.text == "✅ Перейти к тесту")
@router.message(FSMLearnWords.show_problem_words, F.text == "✅ Перейти к тесту")
async def start_test(message: Message, state: FSMContext):
    data = await state.get_data()
    words_message_id = data.get('words_message_id')
    
    if words_message_id:
        try:
            chat_id = getattr(message.chat, 'id', None)
            bot = getattr(message, 'bot', None)
            if bot and chat_id:
                await bot.delete_message(chat_id=chat_id, message_id=words_message_id)
        except Exception:
            logger.exception("Failed to delete words message %s for chat %s", words_message_id, getattr(message.chat, 'id', None))
    
    data = await state.get_data()
    testing_state = FSMLearnWords.testing_problem_words if data.get("is_problem_words") else FSMLearnWords.testing
    await state.set_state(testing_state)
    await ask_next_question(message, state, 0)

async def ask_next_question(message: Message, state: FSMContext, word_index: int):
    data = await state.get_data()
    words = data.get('current_words', [])
    
    if word_index >= len(words):
        await finish_test(message, state, words)
        return
    
    current_word = words[word_index]
    
    await state.update_data(
        current_word_index=word_index
    )
    
    word_text = current_word['word'] if isinstance(current_word, dict) else getattr(current_word, 'word', '')
    question_text = f"💬 Напишите перевод для слова {word_text}"
    await message.answer(question_text, reply_markup=get_test_kb())

@router.message(FSMLearnWords.show_new_words, F.text == "📖 Повторить слова")
@router.message(FSMLearnWords.show_problem_words, F.text == "📖 Повторить слова")
async def repeat_words(message: Message, state: FSMContext):
    data = await state.get_data()
    words = data.get('current_words', [])
    is_problem_words = data.get('is_problem_words', False)
    
    words_text = "📖 Слова для повторения:\n\n"
    for i, word in enumerate(words, 1):
        w = word['word'] if isinstance(word, dict) else getattr(word, 'word', '')
        t = word['translation'] if isinstance(word, dict) else getattr(word, 'translation', '')
        words_text += f"{i}️⃣ {w} — {t}\n"
    
    words_msg = await message.answer(words_text, reply_markup=get_start_test_kb())
    await state.update_data(words_message_id=words_msg.message_id)
    
    if is_problem_words:
        await state.set_state(FSMLearnWords.show_problem_words)
    else:
        await state.set_state(FSMLearnWords.show_new_words)

@router.message(FSMLearnWords.testing)
@router.message(FSMLearnWords.testing_problem_words)
async def check_answer(message: Message, state: FSMContext):
    if message.text in ["📖 Повторить слова", "🏠 В меню"]:
        return
    
    data = await state.get_data()
    words = data.get('current_words', [])
    current_index = data.get('current_word_index', 0)
    
    if current_index >= len(words):
        return
    
    current_word = words[current_index]
    user_text = message.text or ""
    user_answer = normalize_text(user_text)
    translation_val = str((current_word.get('translation') if isinstance(current_word, dict) else getattr(current_word, 'translation', '')) or '')
    correct_answer = normalize_text(translation_val)
    
    is_correct = user_answer == correct_answer
    
    test_answers = data.get('test_answers', {})
    test_answers[str(current_index)] = is_correct 
    await state.update_data(test_answers=test_answers)
    cw = current_word['word'] if isinstance(current_word, dict) else getattr(current_word, 'word', None)
    logger.debug("Answer for word %s (%s): %s", current_index, cw, is_correct)
    logger.debug("All answers: %s", test_answers)
    
    if is_correct:
        await message.answer("✅ Верно!")
    else:
        try:
            with db.session_scope() as session:
                word_id = current_word.get('id') if isinstance(current_word, dict) else getattr(current_word, 'id', None)
                deck_val = current_word.get('deck') if isinstance(current_word, dict) else getattr(current_word, 'deck', None)
                existing_problem = session.query(ProblemWord).filter_by(user_id=getattr(message.from_user, 'id', None), word_id=word_id).first()
                if not existing_problem:
                    problem_word = ProblemWord(user_id=getattr(message.from_user, 'id', None), word_id=word_id, deck=deck_val)
                    session.add(problem_word)
        except Exception:
            logger.exception("Failed to add problem word for user %s word %s", getattr(message.from_user, 'id', None), current_word.get('id') if isinstance(current_word, dict) else getattr(current_word, 'id', None))

        correct_t = current_word['translation'] if isinstance(current_word, dict) else getattr(current_word, 'translation', '')
        await message.answer(f"❌ Правильный перевод: {correct_t}")
    
    import asyncio
    await asyncio.sleep(1)
    await ask_next_question(message, state, current_index + 1)

async def finish_test(message: Message, state: FSMContext, words):
    data = await state.get_data()
    test_answers = data.get('test_answers', {})
    selected_deck = data.get('selected_deck')
    is_problem_words = data.get('is_problem_words', False)
    
    logger.debug("Final answers: %s", test_answers)
    logger.debug("Words count: %s", len(words))
    
    correct_count = 0
    for i in range(len(words)):
        if test_answers.get(str(i)):
            correct_count += 1
    
    total_count = len(words)
    percentage = int((correct_count / total_count) * 100) if total_count > 0 else 0
    
    logger.debug("Correct answers: %s/%s", correct_count, total_count)
    
    if percentage >= 90:
        grade = "Отлично"
    elif percentage >= 70:
        grade = "Хорошо" 
    elif percentage >= 50:
        grade = "Нормально"
    else:
        grade = "Стоит повторить"
    
    xp_earned = correct_count
    
    try:
        with db.session_scope() as session:
            user = session.query(User).filter_by(id=getattr(message.from_user, 'id', None)).first()
            if user:
                if not is_problem_words:
                    new_xp = int(getattr(user, 'xp', 0) or 0) + int(xp_earned)
                    setattr(user, 'xp', new_xp)

                for i, word in enumerate(words):
                    if not test_answers.get(str(i)):
                        continue

                    word_id = word.get('id') if isinstance(word, dict) else getattr(word, 'id', None)
                    deck_value = (
                        word.get('deck') if isinstance(word, dict) else getattr(word, 'deck', None)
                    ) or selected_deck

                    existing_progress = session.query(UserProgress).filter_by(
                        user_id=user.id,
                        word_id=word_id,
                    ).first()
                    if existing_progress:
                        new_count = int(getattr(existing_progress, 'correct_count', 0) or 0) + 1
                        setattr(existing_progress, 'correct_count', new_count)
                        setattr(existing_progress, 'learned', True)
                        setattr(existing_progress, 'deck', deck_value)
                    else:
                        progress = UserProgress(
                            user_id=user.id,
                            word_id=word_id,
                            deck=deck_value,
                            learned=True,
                            correct_count=1,
                        )
                        session.add(progress)

                    session.query(ProblemWord).filter_by(user_id=user.id, word_id=word_id).delete()

                if correct_count > 0:
                    try:
                        from services.utils import update_streak
                        old_streak_val = int(getattr(user, 'streak', 0) or 0)
                        update_streak(user, session)
                        new_streak_val = int(getattr(user, 'streak', 0) or 0)
                        if new_streak_val > old_streak_val:
                            await message.answer(
                                f"🔥 Ваш стрик увеличен: {new_streak_val} дней!",
                                reply_markup=get_back_to_menu_kb(),
                            )
                    except Exception:
                        logger.exception("Failed to update streak for user %s", getattr(message.from_user, 'id', None))

    except Exception:
        logger.exception("Failed to finalize test for user %s", getattr(message.from_user, 'id', None))
    
    result_text = f"""🎯 Тест завершен!

Правильных ответов: {correct_count}/{total_count} ({percentage}%)
Оценка: {grade}
Получено XP: +{xp_earned}"""

    await message.answer(result_text, reply_markup=get_back_to_menu_kb())
    await state.clear()
