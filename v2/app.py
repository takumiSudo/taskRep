import boto3
import requests
from urllib.parse import unquote
from openai import OpenAI
import json
import pymysq



sqs = boto3.client('sqs')
queue_url = 'PLACE_HOLDER'
# Database connection parameters
db_params = {
    'host': 'your-rds-instance.rds.amazonaws.com',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database'
}

phone_number = "123456789"

def connect_to_database():
    return pymysql.connect(**db_params)

def log_message_to_db(message_text):
    conn = connect_to_database()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO message_log (message_text) VALUES (%s)"
            cursor.execute(sql, (message_text,))
            conn.commit()
    finally:
        conn.close()

    return {
		'statusCode': 200
	}

# Listner for SQS 
def poll_sqs_messages():
    while True:
        try:
            response = sqs.receive_message(
                QueueUrl = queue_url,
                AttributeName = ['All'],
                MaxNumberOfMessages = 10,
                WaitTimeSeconds = 20
            )
    
            messages = response.get('Messages', [])
            if not messages:
                continue

            for message in messages:
                try:
                    process_message(message)
                finally:
                    sqs.delete_message(
                        QueueUrl = queue_url,
                        ReceiptHandle = message['ReceiptHandle'] 
                )

        except Exception as e:
            print(f"An error occurred: {e}")


def process_message(message):

    data = message['Body']
    # Log Message to database
    log_message_to_db(data)
    
    # Call GPT to analyze the task
    api_response = _call_openai_api(data)
    print(f"API Response: {api_response}")

    # Send back to Number
    response = api_response['body']
    _send_2_user(response)


def _send_2_user(message):

    assert isinstance(message, str), "Message must be String Format"

    sns = boto3.client('sns')
    response = sns.publish(
        PhoneNumber = phone_number,
        Message = message,
        MessageAttributes = {
            'AWS.SNS.SMS.SMSType': {
                'DataType': 'String',
                'StringValue': 'Transactional'
            }
        }
    )

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

def send_sms_message(text):
    raise NotImplementedError



if __name__ == "__main__":
    poll_sqs_messages()
