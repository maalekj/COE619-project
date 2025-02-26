import json
import boto3
import os
import uuid
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
event_table = dynamodb.Table(os.environ["EVENT_TABLE_NAME"])
node_table = dynamodb.Table(os.environ["EDGE_NODE_TABLE_NAME"])


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"], parse_float=Decimal)

        # Validate required fields
        required_fields = [
            "event_type",
            "event_timestamp",
            "latitude",
            "longitude",
            "image",
            "edge_node_id",
            "event_status",
        ]
        for field in required_fields:
            if field not in body:
                return {
                    "statusCode": 400,
                    "body": json.dumps(f"Missing required field: {field}"),
                }

        # Check if event_status is 'reported'
        if body["event_status"] != "reported":
            return {
                "statusCode": 400,
                "body": json.dumps("Invalid event status. Must be 'reported'"),
            }

        # Check if edge_node_id exists
        edge_node_id = body["edge_node_id"]
        node_response = node_table.get_item(Key={"node_id": edge_node_id})
        if "Item" not in node_response:
            return {"statusCode": 404, "body": json.dumps("Edge node not found")}

        # Perform validation (assuming validation_result is obtained from some validation function)
        validation_result = validate_image(
            body["image"]
        )  # Placeholder for actual validation logic
        print("Validation result:", validation_result)

        # Update event_status based on validation result
        if not validation_result.get("accident"):
            body["event_status"] = "verification failed"
            return create_response(400, {"error": "Image validation failed"})
        else:
            body["event_status"] = "validated"

        # Extract event details from the validation response
        event_details = validation_result.get("event_details")

        # Generate a unique event_id
        event_id = str(uuid.uuid4())

        # Create the item to be stored in DynamoDB
        item = create_dynamodb_item(
            event_id,
            body["event_type"],
            body["event_timestamp"],
            body["latitude"],
            body["longitude"],
            body["image"],
            event_details,
            edge_node_id,
            body["event_status"],
        )

        # Store the item in DynamoDB
        store_item_in_dynamodb(item)

        # Publish the event ID and type to the SNS topic if validation succeeded
        if body["event_status"] == "validated":
            publish_to_sns(event_id, body["event_type"])

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"event_id": event_id, "event_status": body["event_status"]}
            ),
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"An error occurred: {str(e)}")}


def validate_image(image):
    # Placeholder for actual validation logic
    return {"accident": True, "event_details": "Sample details"}


def create_dynamodb_item(
    event_id,
    event_type,
    event_timestamp,
    latitude,
    longitude,
    image,
    event_details,
    edge_node_id,
    event_status,
):
    return {
        "id": event_id,  # Ensure the primary key 'id' is included
        "event_id": event_id,
        "event_type": event_type,
        "event_timestamp": event_timestamp,
        "latitude": latitude,
        "longitude": longitude,
        "image": image,
        "event_details": event_details,
        "edge_node_id": edge_node_id,
        "event_status": event_status,
    }


def store_item_in_dynamodb(item):
    event_table.put_item(Item=item)


def publish_to_sns(event_id, event_type):
    sns = boto3.client("sns")
    topic_arn = os.environ["SNS_TOPIC_ARN"]
    message = json.dumps({"event_id": event_id, "event_type": event_type})
    sns.publish(TopicArn=topic_arn, Message=message)


def create_response(status_code, body):
    return {"statusCode": status_code, "body": json.dumps(body)}
