import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["EVENT_TABLE_NAME"])


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"], parse_float=Decimal)

        # Validate required fields
        required_fields = ["event_id"]
        for field in required_fields:
            if field not in body:
                return {
                    "statusCode": 400,
                    "body": json.dumps(f"Missing required field: {field}"),
                }

        event_id = body["event_id"]

        update_expression = "SET"
        expression_attribute_values = {}

        if "event_type" in body:
            update_expression += " event_type = :event_type,"
            expression_attribute_values[":event_type"] = body["event_type"]

        if "event_timestamp" in body:
            update_expression += " event_timestamp = :event_timestamp,"
            expression_attribute_values[":event_timestamp"] = body["event_timestamp"]

        if "latitude" in body:
            update_expression += " latitude = :latitude,"
            expression_attribute_values[":latitude"] = body["latitude"]

        if "longitude" in body:
            update_expression += " longitude = :longitude,"
            expression_attribute_values[":longitude"] = body["longitude"]

        if "image" in body:
            update_expression += " image = :image,"
            expression_attribute_values[":image"] = body["image"]

        if "event_status" in body:
            update_expression += " event_status = :event_status,"
            expression_attribute_values[":event_status"] = body["event_status"]

        # Remove trailing comma
        if update_expression.endswith(","):
            update_expression = update_expression[:-1]

        if not expression_attribute_values:
            return {"statusCode": 400, "body": json.dumps("No valid fields to update")}

        response = table.update_item(
            Key={"id": event_id},
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
