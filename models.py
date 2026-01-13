from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text, func, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./padron.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(50), nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PadronRecord(Base):
    __tablename__ = "padron_records"
    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String(32), index=True, nullable=False)
    nombre = Column(String(255), index=True, nullable=True)
    apellido = Column(String(255), index=True, nullable=True)
    domicilio = Column(String(255), nullable=True)
    localidad = Column(String(255), nullable=True)
    provincia = Column(String(255), nullable=True)
    extras = Column(Text, nullable=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)