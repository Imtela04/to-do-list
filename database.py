# from fastapi import Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# from pydantic import BaseModel
# from dotenv import load_dotenv
# import os

# load_dotenv()
# SQLALCHEMY_DATABASE_URL = ""
DATABASE_URL = "sqlite:///./todos.db"
engine = create_engine(DATABASE_URL)#, connect_args={"check_same_thread":False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
# class Base(declarative_base):
#     pass

# -db dependency -> creates and closes db session for each request
def get_db():
    db = SessionLocal()    
    try:
        yield db
    finally:
        db.close()

