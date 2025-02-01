import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["EDGE_NODE_TABLE_NAME"])


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"], parse_float=Decimal)
        node_id = body.get("node_id")

        if not node_id:
            return {
                "statusCode": 400,
                "body": json.dumps("Missing required field: node_id"),
            }

        update_expression = "SET"
        expression_attribute_values = {}

        if "node_status" in body:
            update_expression += " node_status = :node_status,"
            expression_attribute_values[":node_status"] = body["node_status"]

        if "longitude" in body and "latitude" in body:
            update_expression += " longitude = :longitude, latitude = :latitude,"
            expression_attribute_values[":longitude"] = body["longitude"]
            expression_attribute_values[":latitude"] = body["latitude"]

        # Remove trailing comma
        if update_expression.endswith(","):
            update_expression = update_expression[:-1]

        if not expression_attribute_values:
            return {"statusCode": 400, "body": json.dumps("No valid fields to update")}

        response = table.update_item(
            Key={"node_id": node_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="UPDATED_NEW",
        )

        return {
            "statusCode": 200,
            "body": json.dumps(response["Attributes"], cls=DecimalEncoder),
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"An error occurred: {str(e)}")}


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)
