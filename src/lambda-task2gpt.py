#!/usr/bin/env python3
import json
import os
import requests
from urllib.parse import unquote

def lambda_function(event, context):

	openai_key = os.getenv("OPENAI_API_KEY")

	print("Recieved Event : " + json.dumps(event, indent=2))

	message = json.loads(event['Records'][0]['Sns']['Message'])
	text = unquote(message['text'])

	headers = {
		'Content-Type': 'application/json',
		'Authorization': f'Bearer {openai_key}',
	}

	data = {
		"model": "gpt-4o-mini",
		"prompt": text,
		"max_tokens":150,
	}

	response_url = 'https://api.openai.com/v1/engines/davinci/completions'

	response = requests.post(response_url, headers=headers, json=data)
	response_data = response.json()


	if response.status_code != 200:
		print("Error in API response:", response_data)

		return {
			'statusCode': response.status_code,
			'body':json.dumps("Failed to get a valid response from GPT")
		}

	chat_response = response_data['choices'][0]['text'].strip()

	return {
		'statusCode': 200,
		'body': json.dumps(chat_response)
	}

if __name__ == "__main__":

	with open('test-incoming-sms.json', 'r') as file:
		test_event = json.load(file)
		context = {}

	# Test Lambda
	try :
		response = lambda_function(test_event, context)
		print("Lambda Function Response: ", response)

	except FileNotFoundError:
		print("Error: The json file was not found.")
	except json.JSONDecodeError:
		print("Error: Failed to decode JSON file")
	except Exception as e:
		print(f"An error occured: {e}")
