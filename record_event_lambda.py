import json
import base64
from datetime import datetime, timezone, timedelta


def lambda_handler(event, context):
    # Check if 'body' key exists in the event and is not empty
    if "body" not in event or not event["body"]:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "Invalid request, 'body' key is missing or empty"}
            ),
        }

    try:
        # Parse the incoming request
        body = json.loads(event["body"])
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON format in request body"}),
        }

    # Extract the image and event details
    image_data = body.get("image")
    event_type = body.get("event_type")
    event_timestamp = body.get("event_timestamp")
    event_location = body.get("event_location")

    # Check if all required fields are present and not empty
    if not all([image_data, event_type, event_timestamp, event_location]):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing required fields"}),
        }

    # Additional checks for empty strings
    if not all(
        [
            image_data.strip(),
            event_type.strip(),
            event_timestamp.strip(),
            event_location.strip(),
        ]
    ):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Fields cannot be empty"}),
        }

    # Decode the image if needed (assuming it's base64 encoded)
    try:
        image_bytes = base64.b64decode(image_data)
    except base64.binascii.Error:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid base64 encoding in image data"}),
        }

    # Convert the Unix timestamp to GMT+3
    try:
        event_time = datetime.fromtimestamp(int(event_timestamp), tz=timezone.utc)
        gmt_plus_3_time = event_time.astimezone(timezone(timedelta(hours=3)))
    except (ValueError, OSError):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid timestamp format"}),
        }

    # Format the time in a human-readable format
    human_readable_time = gmt_plus_3_time.strftime("%Y-%m-%d %H:%M:%S %Z")

    # Prepare the response
    response = {
        "statusCode": 200,
        "body": json.dumps(
            {
                "event_type": event_type,
                "event_location": event_location,
                "event_time_gmt_plus_3": human_readable_time,
            }
        ),
    }

    return response
