#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, select, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Json, ValidationError
import bcrypt
from typing import Union, Dict, Any
import datetime
import enum
import boto3
import sqlite3
import json
import os
import requests
from urllib.parse import unquote
from openai import OpenAI
import hashlib


app = FastAPI()


DATABASE_URL = "sqlite:///./taskRep.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Reset applied for testing purposes only; remove when moving into production
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# CORS for front end interactions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Status(enum.Enum):
    COMPLETE = "COMPLETE"
    INPROGRESS = "IN PROGRESS"
    NOT_STARTED = "NOT STARTED"

class User(Base):

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    phoneNumber = Column(String)
    hashedPassword = Column(String)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    phoneNumber = Column(String)
    message = Column(String)
    response = Column(String)
    status = Column(Enum(Status))


class UserRegister(BaseModel):
    username: str
    password: str
    phoneNumber : str

class SMSRequest(BaseModel):
    username: str
    phoneNumber : str
    message : str
    pinpoint_project_id: str

class SMSRecieve(BaseModel):
    username: str
    phoneNumber: str
    message: Json


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/user/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegister):

    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    db_user = User(username = user.username, hashedPassword = hashed_password, phoneNumber = user.phoneNumber)
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

@app.post("/send/send-sms", status_code=status.HTTP_200_OK)
def send_sms_api(sms_request: SMSRequest):

    try:
        response = send_sms(sms_request.phone_number, sms_request.message, sms_request.pinpoint_project_id)
        return {"message": "SMS sent successfully", "response":response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def send_sms(phoneNumber, message, pinpoint_project_id):
    import boto3
    client = boto3.client('pinpoint')
    response = client.send_messages(
        ApplicationId=pinpoint_project_id,
        MessageRequest={
            'Addresses': {
                phoneNumber: {
                    'ChannelType': 'SMS'
                }
            },
            'MessageConfiguration': {
                'SMSMessage': {
                    'Body': message,
                    'MessageType': 'TRANSACTIONAL',
                }
            }
        }
    )
    return response

@app.post("/receive/receive-sms", status_code=status.HTTP_200_OK)
async def receive_sms_api(sms_receive: SMSRecieve):

    # Chat GPT Integration:
    try:
        response = send2gpt(message)
        if response['statusCode'] == 200:
            response_message = response['body']
    except ValidationError as e:
        print(e)

    db_texts = Task(
        username = sms_receive.username,
        phoneNumber = sms_receive.phoneNumber,
        message = sms_receive.message,
        respones = response_message,
        status = "INPROGRESS"
    )
    db = SessionLocal()

    # Integrate incoming SMS to Tasks Database
    try:
        db.add(db_texts)
        db.commit()
        print("message : Text Registered Successfully")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Message Already Exists")
    finally:
        db.close()

    # Send back the SMS the response
    response = client.post("/send/send-sms", json = {"username": sms_receive.username, "phoneNumber": sms_receive.phoneNumber, "message": response_message, "pinpoint_project_id": "TEST_ID"})
    if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Internal Send API call failed")





def send2gpt(event, context):

	print("Recieved Event : " + json.dumps(event, indent=2))

	# Unpacks the Message to extract the text portion of the package
	message = json.loads(event['Records'][0]['Sns']['Message'])
	text = unquote(message['text'])

	# Text Completion : API connection with OPENAI
	client = OpenAI()

	completion = client.chat.completions.create(
		model="gpt-4o-mini",
		messages=[
			{"role": "system", "content": "You are a scheduling assistant, skilled in analyzing how time a task would take. You should give out an estimate ranging from 30 mins to 3 hours with 30 minute increments."},
			{"role": "user", "content": "Analyze how much time a typical person will take to complete the following task:" + text},
		]
	)

	if completion is None:
		print("Error in API response:", completion)

		return {
			'statusCode': response.status_code,
			'body':json.dumps("Failed to get a valid response from GPT")
		}

	return {
		'statusCode': 200,
		'body': completion.choices[0].message
	}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
