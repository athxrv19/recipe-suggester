# database.py
# SQLite swapped for MySQL. Everything else is identical.

import os
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# Set this env var or edit the string directly:
# mysql+pymysql://username:password@host/database_name
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:yourpassword@localhost/recipes_db"  # <-- edit this line
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Recipe(Base):
    __tablename__ = "recipes"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    ingredients_key  = Column(String(64), unique=True, nullable=False)
    title            = Column(String(255))
    calories         = Column(Integer)
    time_limit       = Column(Integer)
    ingredients_list = Column(Text)
    instructions     = Column(Text)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()