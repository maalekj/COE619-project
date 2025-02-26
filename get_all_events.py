import json
import boto3
import os
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["EVENT_TABLE_NAME"])


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    try:
        response = table.scan()

        if "Items" in response:
            return {
                "statusCode": 200,
                "body": json.dumps(response["Items"], cls=DecimalEncoder),
            }
        else:
            return {"statusCode": 404, "body": json.dumps("No events found")}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"An error occurred: {str(e)}")}
