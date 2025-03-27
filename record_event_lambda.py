import json
import boto3
import os
import uuid
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
event_table = dynamodb.Table(os.environ["EVENT_TABLE_NAME"])
node_table = dynamodb.Table(os.environ["EDGE_NODE_TABLE_NAME"])
lambda_client = boto3.client("lambda")


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
            "node_id",
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

        # Check if node_id exists
        node_id = body["node_id"]
        node_response = node_table.get_item(Key={"node_id": node_id})
        if "Item" not in node_response:
            print(f"Node {node_id} not found in the table")
            return {"statusCode": 404, "body": json.dumps("Edge node not found")}

        # Perform validation by calling event_validate_lambda
        validation_result = validate_image(body["image"])
        print("Validation result:", validation_result)

        # Update event_status based on validation result
        if not validation_result.get("accident"):
            body["event_status"] = "invalid"
            event_details = "Validation failed"
            # Update the node's status to "online" for invalid events
            update_node_attributes(node_id, "online")
        else:
            body["event_status"] = "validated"
            event_details = validation_result.get(
                "event_details", "No details available"
            )
            # Update the node's status to "accident" for validated events
            update_node_attributes(node_id, "accident")

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
            node_id,
            body["event_status"],
        )

        # Store the item in DynamoDB
        store_item_in_dynamodb(item)

        # Publish the event ID and type to the SNS topic if validation succeeded
        if body["event_status"] == "validated":
            publish_to_sns(event_id, body["event_type"])

        # Return a consistent response structure
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"event_id": event_id, "event_status": body["event_status"]}
            ),
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"An error occurred: {str(e)}")}


def validate_image(image):
    try:
        response = lambda_client.invoke(
            FunctionName=os.environ["EVENT_VALIDATE_LAMBDA_NAME"],
            InvocationType="RequestResponse",
            Payload=json.dumps({"image": image}),
        )
        response_payload = json.loads(response["Payload"].read())
        validation_result_raw = response_payload["body"]
        print(f"Raw validation result: {validation_result_raw}")

        # Parse the JSON string returned by the validation Lambda
        validation_result = json.loads(validation_result_raw)
        print(f"Parsed validation result: {validation_result}")

        return validation_result
    except Exception as e:
        print(f"Error invoking event_validate_lambda: {e}")
        return {"accident": False, "event_details": None}


def create_dynamodb_item(
    event_id,
    event_type,
    event_timestamp,
    latitude,
    longitude,
    image,
    event_details,
    node_id,
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
        "node_id": node_id,
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


def update_node_attributes(node_id, status=None):
    """
    Update the attributes (status and last_seen) of a node in the DynamoDB table.
    """
    try:
        # Get the current timestamp and convert it to Decimal
        current_timestamp = Decimal(str(datetime.utcnow().timestamp()))

        # Build the update expression
        update_expression = "SET last_seen = :last_seen"
        expression_attribute_values = {":last_seen": current_timestamp}

        # Check the current node_status if a status update is requested
        if status:
            # Fetch the current node_status
            node_response = node_table.get_item(Key={"node_id": node_id})
            current_status = node_response.get("Item", {}).get("node_status")

            # Only update the status if it's not already "accident"
            if current_status != "accident":
                update_expression += ", node_status = :status"
                expression_attribute_values[":status"] = status
            else:
                print(
                    f"Node {node_id} already has status 'accident'. Skipping status update."
                )

        print(
            f"Attempting to update node {node_id} with status: {status} and last_seen: {current_timestamp}"
        )

        # Perform the update
        response = node_table.update_item(
            Key={"node_id": node_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="UPDATED_NEW",  # Return the updated values for debugging
        )
        print(f"Node {node_id} successfully updated. Response: {response}")
    except Exception as e:
        print(f"Error updating node {node_id}: {e}")
