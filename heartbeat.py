import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["EDGE_NODE_TABLE_NAME"])


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])

        # Validate required fields
        required_fields = ["node_id"]
        for field in required_fields:
            if field not in body:
                return {
                    "statusCode": 400,
                    "body": json.dumps(f"Missing required field: {field}"),
                }

        node_id = body["node_id"]
        last_seen = int(datetime.utcnow().timestamp())

        # Get the current node status
        response = table.get_item(Key={"node_id": node_id})
        if "Item" not in response:
            return {"statusCode": 404, "body": json.dumps("Node not found")}

        node_status = response["Item"].get("node_status", "offline")

        # Update the last_seen and node_status if necessary
        update_expression = "SET last_seen = :last_seen"
        expression_attribute_values = {":last_seen": last_seen}

        if node_status == "offline":
            update_expression += ", node_status = :node_status"
            expression_attribute_values[":node_status"] = "online"

        table.update_item(
            Key={"node_id": node_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Heartbeat received successfully!",
                    "node_id": node_id,
                    "last_seen": last_seen,
                    "node_status": (
                        "online" if node_status == "offline" else node_status
                    ),
                }
            ),
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"An error occurred: {str(e)}")}
