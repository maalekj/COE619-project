import json
import base64
import boto3
import uuid

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='me-south-1')
table = dynamodb.Table('my-private-table')

# Initialize the Lambda client
lambda_client = boto3.client('lambda', region_name='me-south-1')

def lambda_handler(event, context):
    try:
        # Validate and parse the request body
        body = validate_and_parse_body(event)

        # Generate a unique id for the item
        item_id = str(uuid.uuid4())

        # Base64 encode the image
        image = body.get("image")

        # Call the event_validate_lambda function
        validation_response = call_event_validate_lambda(image)

        # Check the validation response
        if not validation_response.get("validation_result"):
            return create_response(400, {"error": "Image validation failed"})

        # Create the item to be stored in DynamoDB
        item = create_dynamodb_item(item_id, body, image)

        # Store the item in DynamoDB
        store_item_in_dynamodb(item)

        # Return a successful response
        return create_response(200, {
            "message": "Item successfully inserted"
        })

    except Exception as e:
        # Return an error response
        return create_response(500, {"error": str(e)})

def validate_and_parse_body(event):
    if "body" not in event or not event["body"]:
        raise ValueError("Invalid request, 'body' key is missing or empty")
    return json.loads(event["body"])

def base64_encode_image(image):
    if image:
        return base64.b64encode(image.encode()).decode()
    return ""

def create_dynamodb_item(item_id, body, image):
    return {
        "id": item_id,
        "event_type": body.get("event_type"),
        "event_location": body.get("event_location"),
        "event_timestamp": body.get("event_timestamp"),
        "image": image
    }

def store_item_in_dynamodb(item):
    table.put_item(Item=item)

def call_event_validate_lambda(image):
    response = lambda_client.invoke(
        FunctionName='event_validate_lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({"image": image})
    )
    response_payload = json.loads(response['Payload'].read())
    return json.loads(response_payload['body'])

def create_response(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
