from __future__ import annotations

import json
from typing import Optional, List

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models import SessionLocal, User, PadronRecord

pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")


def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    if not email:
        return None
    return db.query(User).filter(User.email == email.lower().strip()).first()


def create_user(db: Session, email: str, password: str, role: str = "user") -> bool:
    email = email.lower().strip()
    if get_user_by_email(db, email):
        return False
    u = User(email=email, password_hash=hash_password(password), role=role)
    db.add(u)
    db.commit()
    return True


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    u = get_user_by_email(db, email)
    if not u:
        return None
    if not verify_password(password, u.password_hash):
        return None
    return u


def seed_initial_users(db: Session) -> dict:
    defaults = [
        ("admin@local", "admin123", "admin"),
        ("user1@local", "user123", "user"),
        ("user2@local", "user123", "user"),
    ]
    created = []
    skipped = []
    for email, pw, role in defaults:
        ok = create_user(db, email, pw, role)
        (created if ok else skipped).append(email)
    return {"created": created, "skipped": skipped}


def upsert_padron_from_rows(db: Session, rows: List[dict]) -> dict:
    count = 0
    for r in rows:
        rec = PadronRecord(
            dni=str(r.get("dni", "")).strip(),
            nombre=(r.get("nombre") or "").strip() or None,
            apellido=(r.get("apellido") or "").strip() or None,
            domicilio=(r.get("domicilio") or "").strip() or None,
            localidad=(r.get("localidad") or "").strip() or None,
            provincia=(r.get("provincia") or "").strip() or None,
            extras=json.dumps(r.get("extras")) if isinstance(r.get("extras"), dict) else (r.get("extras") or None),
        )
        if rec.dni:
            db.add(rec)
            count += 1
    db.commit()
    return {"inserted": count}


def search_padron(db: Session, q: str, limit: int = 50) -> List[PadronRecord]:
    q = (q or "").strip()
    if not q:
        return []
    like = f"%{q}%"
    return (
        db.query(PadronRecord)
        .filter(
            (PadronRecord.dni.like(like))
            | (PadronRecord.nombre.like(like))
            | (PadronRecord.apellido.like(like))
        )
        .limit(limit)
        .all()
    )