import json
import boto3
import os
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["EDGE_NODE_TABLE_NAME"])


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"], parse_float=Decimal)

        # Check for required fields
        required_fields = ["longitude", "latitude"]
        for field in required_fields:
            if field not in body:
                return {
                    "statusCode": 400,
                    "body": json.dumps(f"Missing required field: {field}"),
                }

        # Validate data
        longitude = body["longitude"]
        latitude = body["latitude"]
        node_name = body.get("node_name", "unnamed node")

        if not isinstance(longitude, Decimal) or not isinstance(latitude, Decimal):
            return {
                "statusCode": 400,
                "body": json.dumps("Longitude and latitude must be numbers"),
            }

        if not isinstance(node_name, str):
            return {
                "statusCode": 400,
                "body": json.dumps("Node name must be a string"),
            }

        # Generate a unique node_id
        node_id = context.aws_request_id

        # Set the last_seen value to the current timestamp
        last_seen = int(datetime.utcnow().timestamp())

        # Set the node_status to 'online'
        node_status = "online"

        # Save to DynamoDB
        item = {
            "node_id": node_id,
            "longitude": longitude,
            "latitude": latitude,
            "node_status": node_status,
            "node_name": node_name,
            "last_seen": last_seen,
        }
        table.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Edge node registered successfully!", "node_id": node_id}
            ),
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"An error occurred: {str(e)}")}
