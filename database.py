# from fastapi import Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3
from fastapi import HTTPException
from typing import Optional

DATABASE_URL = "sqlite:///./todos.db"
engine = create_engine(DATABASE_URL)#, connect_args={"check_same_thread":False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# -db dependency -> creates and closes db session for each request
def get_db():
    db = SessionLocal()    
    try:
        yield db
    finally:
        db.close()

def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            hashed_password TEXT NOT NULL,
            full_name TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(username: str) -> Optional[dict]:
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT username, hashed_password, full_name FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()
    if row:
        return {"username": row["username"], "hashed_password": row["hashed_password"], "full_name": row["full_name"]}
    return None

def create_user(username: str, hashed_password: str, full_name: str = ""):
    conn = sqlite3.connect(DATABASE_URL)
    try:
        conn.execute(
            "INSERT INTO users (username, hashed_password, full_name) VALUES (?, ?, ?)",
            (username, hashed_password, full_name)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already taken")
    finally:
        conn.close()
