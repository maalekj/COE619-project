import json

def lambda_handler(event, context):
    # Log the received event
    print("Received event:", json.dumps(event))

    # Extract the image from the event
    image = event.get("image", "")

    # Determine the validation result based on the first letter of the image
    if image and image[0].lower() == 'i':
        validation_result = True
    else:
        validation_result = False

    # Return the validation result
    return {
        "statusCode": 200,
        "body": json.dumps({"validation_result": validation_result})
    }