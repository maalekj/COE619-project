import json
import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["EDGE_NODE_TABLE_NAME"])


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    try:
        node_id = event["queryStringParameters"]["node_id"]

        response = table.get_item(Key={"node_id": node_id})

        if "Item" in response:
            return {
                "statusCode": 200,
                "body": json.dumps(response["Item"], cls=DecimalEncoder),
            }
        else:
            return {"statusCode": 404, "body": json.dumps("Node not found")}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"An error occurred: {str(e)}")}
