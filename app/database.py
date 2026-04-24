# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# engine: objeto principal de conexão com o Postgres
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # testa conexão antes de usar do pool
    pool_size=5,          # conexões simultâneas no pool
    max_overflow=10       # conexões extras além do pool_size
)

# factory de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# base para todos os models SQLAlchemy herdarem
Base = declarative_base()


def get_db():
    """
    Gerador de sessão usado como dependência no FastAPI.
    Garante que a sessão é fechada mesmo se ocorrer uma exceção.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()