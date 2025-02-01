import json


def lambda_handler(event, context):
    # For now, just return a success message
    return {"statusCode": 200, "body": json.dumps("Edge node registered successfully!")}
