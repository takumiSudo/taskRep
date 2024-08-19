#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
import bcrypt
from typing import Union
from pydantic import BaseModel
import datetime
import boto3
import sqlite3

app = FastAPI()

DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# CORS for front end interactions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(Base):

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    phoneNumber = Column(String)


Base.metadata.create_all(bind=engine)

class UserRegister(BaseModel):

    username: str
    password: str
    phoneNumber : str



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/user/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegister):

    hashed_password = bcrypt.haspw(user.password.encode('utf-8'), bcrypt.gensalt())
    db_user = User(username = user.username)
    db = SessionLocal()

    try:
        db.add(db_user)
        db.commit()
        return {"message": "User registered successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
