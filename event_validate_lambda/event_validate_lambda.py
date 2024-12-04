import json
import boto3
from botocore.exceptions import ClientError
import openai


def get_openai_api_key():
    ssm = boto3.client("ssm")
    try:
        parameter = ssm.get_parameter(Name="/openai/api_key", WithDecryption=True)
        return parameter["Parameter"]["Value"]
    except ClientError as e:
        print(f"Error retrieving parameter: {e}")
        return None


def lambda_handler(event, context):
    prompt = (
        "Analyze the given image and confirm if it depicts an accident. Respond in JSON format only. Use the following structure:\n"
        "- If there is no accident:\n"
        "  {\n"
        '    "accident": false,\n'
        '    "category": null,\n'
        '    "eventdetails": null\n'
        "  }\n"
        "- If there is an accident:\n"
        "  {\n"
        '    "accident": true,\n'
        '    "category": "<category>",\n'
        '    "eventdetails": "<details for responders review>"\n'
        "  }\n"
        'Replace <category> with one of these options: "fire", "traffic", "crime", or "other". Replace <details about the event> with a short description of the event (e.g., "details for responders review"). Respond with valid JSON and no additional text.'
    )
    # Log the received event
    print("Received event:", json.dumps(event))

    # Extract the image from the event
    base64_image = event.get("image", "")

    # Get the OpenAI API key
    openai_api_key = get_openai_api_key()
    if not openai_api_key:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to retrieve OpenAI API key"}),
        }

    # Set the OpenAI API key
    openai.api_key = openai_api_key

    # Ask ChatGPT about the image
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
        )
        validation_result = response.choices[0].message.content

        # Assuming the response content is a JSON string with validation, category, and event details
        validation_data = json.loads(validation_result)
        is_valid = validation_data.get("accident")
        category = validation_data.get("category")
        event_details = validation_data.get("eventdetails")

        if is_valid:
            result = {
                "validation_result": "true",
                "category": category,
                "event_details": event_details,
            }
        else:
            result = {"validation_result": "false"}

    except Exception as e:
        print(f"Request to OpenAI API failed: {e}")
        result = {
            "validation_result": "false",
            "error": f"Failed to get response from ChatGPT, Request to OpenAI API failed: {e}",
        }

    # Return the validation result
    return {
        "statusCode": 200,
        "body": json.dumps(result),
    }
