#!/usr/bin/env python3
from sqlalchemy import create_engine, Column, Integer, String, select


class User(Base):

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    phoneNumber = Column(String)
