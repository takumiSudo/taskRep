#!/usr/bin/env python3
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.ext.declarative import declarative_base


class User(Base):

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashedPassword = Column(String)
    phoneNumber = Column(String)


class UserRegister(BaseModel):

    username: str
    password: str
    phoneNumber : str

class SMSRequest(BaseModel):

    phoneNumber : str
    message : str
    pinpoint_project_id: str
