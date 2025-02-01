import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["EDGE_NODE_TABLE_NAME"])


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"], parse_float=Decimal)

        # Check for required fields
        required_fields = ["longitude", "latitude", "node_status"]
        for field in required_fields:
            if field not in body:
                return {
                    "statusCode": 400,
                    "body": json.dumps(f"Missing required field: {field}"),
                }

        # Validate data
        longitude = body["longitude"]
        latitude = body["latitude"]
        node_status = body["node_status"]
        node_name = body.get("node_name", "unnamed node")

        if not isinstance(longitude, Decimal) or not isinstance(latitude, Decimal):
            return {
                "statusCode": 400,
                "body": json.dumps("Longitude and latitude must be numbers"),
            }

        if not isinstance(node_status, str) or not isinstance(node_name, str):
            return {
                "statusCode": 400,
                "body": json.dumps("Node status and node name must be strings"),
            }

        # Save to DynamoDB
        item = {
            "node_id": context.aws_request_id,
            "longitude": longitude,
            "latitude": latitude,
            "node_status": node_status,
            "node_name": node_name,
        }
        table.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps("Edge node registered successfully!"),
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"An error occurred: {str(e)}")}
