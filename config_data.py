import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables")
    
    DATABASE_URL = "sqlite:///wordy_bot.db"
    
    NOTIFICATION_TIME = "09:00"
    NOTIFICATION_TEXT = "🎯 Выучи новые слова или повтори старые, чтобы не потерять стрик!"

config = Config()