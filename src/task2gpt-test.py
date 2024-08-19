#!/usr/bin/env python3
import json
import os
import requests
from urllib.parse import unquote
from openai import OpenAI


def lambda_function(event, context):

	print("Recieved Event : " + json.dumps(event, indent=2))

	# Unpacks the Message to extract the text portion of the package
	message = json.loads(event['Records'][0]['Sns']['Message'])
	text = unquote(message['text'])


	# Text Completion : API connection with OPENAI
	client = OpenAI()

	completion = client.chat.completions.create(
		model="gpt-4o-mini",
		messages=[
			{"role": "system", "content": "You are a scheduling assistant, skilled in analyzing how time a task would take."},
			{"role": "user", "content": "Analyze how much time a human will take to complete the following task:" + text},
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
