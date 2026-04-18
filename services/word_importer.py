import logging
from pathlib import Path

from database.db import db
from database.models import Word

logger = logging.getLogger(__name__)


def import_words_from_file(file_path: str, deck_name: str) -> int:
    """Import words from a text file into DB. Returns number of added words."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    added = 0
    with db.session_scope() as session:
        with path.open('r', encoding='utf-8') as file:
            for line_num, raw in enumerate(file, 1):
                line = raw.strip()
                if not line:
                    continue

                parts = line.split(' ', 1)
                if len(parts) != 2:
                    logger.warning("Skipping malformed line %s in %s: %s", line_num, file_path, line)
                    continue

                word = parts[0].strip()
                translation = parts[1].strip()

                existing = session.query(Word).filter_by(word=word, deck=deck_name).first()
                if existing:
                    logger.debug("Word exists: %s (%s)", word, deck_name)
                    continue

                new_word = Word(word=word, translation=translation, deck=deck_name)
                session.add(new_word)
                added += 1
                logger.debug("Added word: %s -> %s (%s)", word, translation, deck_name)

    logger.info("Import finished for %s: %d words added", file_path, added)
    return added

def import_all_decks():
    data_dir = Path(__file__).resolve().parent.parent / "data" / "decks"
    decks = {
        'base.txt': 'base',
        'it_english.txt': 'it_english',
        'top1000.txt': 'top1000',
    }

    total = 0
    for fname, deck in decks.items():
        file_path = data_dir / fname
        try:
            logger.info("Импорт колоды %s: запуск", file_path.name)
            added = import_words_from_file(str(file_path), deck)
            total += added
            logger.info("Слова из %s импортированы успешно: %d новых слов", file_path.name, added)
        except FileNotFoundError:
            logger.warning("Файл колоды не найден: %s", file_path)
        except Exception:
            logger.exception("Ошибка при импорте колоды: %s", file_path)

    if total > 0:
        logger.info("Импорт завершён. Всего добавлено слов: %d", total)
    else:
        logger.info("Импорт завершён. Новые слова не найдены или все слова уже в базе.")

    return total
