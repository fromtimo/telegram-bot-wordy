from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .models import Base
from config_data import config

class Database:
    def __init__(self):

        connect_args = {}
        if config.DATABASE_URL.startswith("sqlite"):

            connect_args = {"check_same_thread": False}

        self.engine = create_engine(
            config.DATABASE_URL,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        return self.SessionLocal()

    @contextmanager
    def session_scope(self):
        """Context manager для сессии SQLAlchemy.

        Используйте:
            with db.session_scope() as session:
                ...
        Автоматически делает commit/rollback и закрывает сессию.
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


db = Database()