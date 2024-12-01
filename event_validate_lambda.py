import json
import urllib.request


def lambda_handler(event, context):
    # Log the received event
    print("Received event:", json.dumps(event))

    # Extract the image from the event
    image = event.get("image", "")

    # Determine the validation result based on the ability to hit google.com
    try:
        response = urllib.request.urlopen("https://www.google.com")
        if response.status == 200:
            validation_result = True
        else:
            validation_result = False
    except Exception as e:
        print(f"Request to google.com failed: {e}")
        validation_result = False

    # Return the validation result
    return {
        "statusCode": 200,
        "body": json.dumps({"validation_result": validation_result}),
    }
