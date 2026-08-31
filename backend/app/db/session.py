from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

if not settings.database_url.startswith("postgresql+psycopg://"):
    raise RuntimeError("DATABASE_URL doit utiliser PostgreSQL avec le driver psycopg.")

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

