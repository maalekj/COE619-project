import json
import boto3
import os
from decimal import Decimal

# Initialize the DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name="me-south-1")
table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])


def lambda_handler(event, context):
    try:
        # Extract the event ID from the query parameters
        event_id = event["queryStringParameters"]["event_id"]

        # Fetch the event from DynamoDB
        response = table.get_item(Key={"id": event_id})

        # Check if the item exists
        if "Item" not in response:
            return create_response(404, {"error": "Event not found"})

        # Convert the item to a JSON serializable format
        item = response["Item"]
        item = convert_decimal_to_float(item)

        # Return the event details
        return create_response(200, item)

    except Exception as e:
        print(f"Exception: {e}")
        return create_response(500, {"error": str(e)})


def convert_decimal_to_float(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = convert_decimal_to_float(obj[i])
    elif isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = convert_decimal_to_float(v)
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


def create_response(status_code, body):
    return {"statusCode": status_code, "body": json.dumps(body)}
