#!/usr/bin/env python3

from twilio.rest import Client
import os
import time

ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
twilio_number = os.environ["TWILIO_NUMBER"]
target_number = os.environ["INDIVIDUAL_NUMBER"]

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def poll_messages():
    last_message_sid = None

    while True:
        try:
            messages = client.messages.list(from_= TWILIO_NUMBER, limit=10)

            if not messages:
                continue
            for message in reversed(messages):
                if last_message_sid is None or message.sid != last_message_sid:
                    print(f"Recieved message from {message.from_}: {message.body}")
                    last_message_sid = message.sid

                    try:
                        process_message(message.body)
                    except Exception as e:
                        raise "Error occured as {e}"
        finally:

            time.sleep(10)


def process_message(message):

    data = message.body
    # Log Message to database
    # log_message_to_db(data)

    # Call GPT to analyze the task
    api_response = _call_openai_api(data)
    print(f"API Response: {api_response}")

    # Send back to Number
    response = api_response['body']
    _send_2_user(response)

def send_message(send_message):
    message = client.messages.create(
        to=target_number,
        from_=twilio_number,
        body=send_message
    )

    print(message.sid)


def log_message_to_db(data):
    raise NotImplementedError

def _call_openai_api(message):

    """
    Simple Handle Function that connects to external openai api that can calculate the task difficulty.

    IN : Message[str]
    OUT: Respones[str]
    """
    assert isinstance(message, str), "Message must be String Format"
    print("Received Event: " + message)

    # Unpacks the Message to extract the text portion of the package
    client = OPENAI()

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
			'statusCode': completion.status_code,
			'body':json.dumps("Failed to get a valid response from GPT")
		}

    return {
		'statusCode': 200,
		'body': completion.choices[0].message
    }

if __name__ == "__main__":
    # poll_messages()

    send_message()
