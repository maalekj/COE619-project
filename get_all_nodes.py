import json
import boto3
import os
from decimal import Decimal
from datetime import datetime, timedelta

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["EDGE_NODE_TABLE_NAME"])

# Global variable for the time threshold (in minutes)
TIME_THRESHOLD_MINUTES = 15


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    try:
        response = table.scan()

        if "Items" in response:
            items = response["Items"]
            current_time = int(datetime.utcnow().timestamp())
            threshold_time = current_time - TIME_THRESHOLD_MINUTES * 60

            for item in items:
                last_seen = item.get("last_seen", 0)
                if last_seen < threshold_time:
                    item["node_status"] = "offline"
                    table.update_item(
                        Key={"node_id": item["node_id"]},
                        UpdateExpression="SET node_status = :node_status",
                        ExpressionAttributeValues={":node_status": "offline"},
                    )

            return {
                "statusCode": 200,
                "body": json.dumps(items, cls=DecimalEncoder),
            }
        else:
            return {"statusCode": 404, "body": json.dumps("No nodes found")}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps(f"An error occurred: {str(e)}")}
