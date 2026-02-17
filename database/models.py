from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import pytz

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    start_date = Column(DateTime, default=lambda: datetime.now(pytz.UTC))
    subscription = Column(Boolean, default=False)
    level = Column(Integer, default=0)
    xp = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    last_active_date = Column(DateTime, default=lambda: datetime.now(pytz.UTC))
    notifications = Column(Boolean, default=True)


    progress = relationship("UserProgress", back_populates="user")
    problem_words = relationship("ProblemWord", back_populates="user")

class Word(Base):
    __tablename__ = 'words'
    
    id = Column(Integer, primary_key=True)
    word = Column(String(100), nullable=False)
    translation = Column(String(200), nullable=False)
    deck = Column(String(50), nullable=False)

class UserProgress(Base):
    __tablename__ = 'user_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    word_id = Column(Integer, ForeignKey('words.id'))
    deck = Column(String(50))
    learned = Column(Boolean, default=False)
    correct_count = Column(Integer, default=0)
    last_review = Column(DateTime, default=lambda: datetime.now(pytz.UTC))
    

    user = relationship("User", back_populates="progress")
    word = relationship("Word")

class ProblemWord(Base):
    __tablename__ = 'problem_words'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    word_id = Column(Integer, ForeignKey('words.id'))
    deck = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC))
    

    user = relationship("User", back_populates="problem_words")
    word = relationship("Word")