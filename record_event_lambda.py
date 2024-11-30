import json
import base64
import boto3
import uuid
from datetime import datetime, timezone, timedelta

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='me-south-1')
table = dynamodb.Table('my-private-table')

def lambda_handler(event, context):
    # Check if 'body' key exists in the event and is not empty
    if "body" not in event or not event["body"]:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "Invalid request, 'body' key is missing or empty"}
            ),
        }

    # Parse the body
    body = json.loads(event["body"])

    # Generate a unique id for the item
    item_id = str(uuid.uuid4())

    # Add the id to the item
    item = {
        "id": item_id,
        "event_type": body.get("event_type"),
        "event_location": body.get("event_location"),
        "event_timestamp": body.get("event_timestamp"),
        "image": body.get("image")
    }

    # Put the item into the DynamoDB table
    try:
        table.put_item(Item=item)
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Item successfully inserted"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
