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
        print(f"Raw validation result (repr): {repr(validation_result)}")

        # Clean up the response to remove any extra formatting
        # Normalize the string by stripping leading/trailing whitespace
        validation_result = validation_result.strip()

        # Remove the prefix ```json and suffix ```
        if validation_result.startswith("```json"):
            validation_result = validation_result[len("```json") :].strip()
        if validation_result.endswith("```"):
            validation_result = validation_result[: -len("```")].strip()

        print(f"Cleaned validation result: {repr(validation_result)}")

        # Parse the cleaned JSON string returned by OpenAI
        try:
            validation_data = json.loads(validation_result)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from OpenAI response: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {"error": "Invalid JSON format from OpenAI response"}
                ),
            }

        # Extract fields from the parsed JSON
        is_valid = validation_data.get("accident")
        category = validation_data.get("category")
        event_details = validation_data.get("eventdetails")

        # Construct the result
        result = {
            "accident": is_valid,
            "category": category,
            "event_details": event_details,
        }

    except Exception as e:
        print(f"Request to OpenAI API failed: {e}")
        result = {
            "accident": False,
            "error": f"Failed to get response from ChatGPT: {e}",
        }

    # Return the validation result
    return {
        "statusCode": 200,
        "body": json.dumps(result),
    }
