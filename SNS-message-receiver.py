from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)


# Endpoint to handle SNS notifications
@app.route("/sns", methods=["POST"])
def sns_handler():
    # Parse the incoming JSON payload
    payload = request.get_json()
    if not payload:
        try:
            payload = json.loads(request.data.decode("utf-8"))
        except Exception as e:
            print(f"Error parsing JSON payload: {e}")
            return jsonify({"message": "Invalid JSON payload"}), 400
    print("Received SNS message:", payload)

    # Handle SubscriptionConfirmation
    if payload.get("Type") == "SubscriptionConfirmation":
        subscribe_url = payload.get("SubscribeURL")
        print("Subscription confirmation received. Confirming subscription...")
        confirm_subscription(subscribe_url)
        return jsonify({"message": "Subscription confirmed"}), 200

    # Handle Notification
    elif payload.get("Type") == "Notification":
        message = payload.get("Message")
        print("Notification received:", message)
        return jsonify({"message": "Notification received"}), 200

    # Handle other message types
    else:
        print("Unknown message type received")
        return jsonify({"message": "Unknown message type"}), 400


# Function to confirm the subscription
def confirm_subscription(subscribe_url):
    try:
        response = requests.get(subscribe_url)
        if response.status_code == 200:
            print("Subscription confirmed successfully!")
        else:
            print(
                "Failed to confirm subscription. Status code: {}".format(
                    response.status_code
                )
            )
    except Exception as e:
        print("Error confirming subscription: {}".format(e))


if __name__ == "__main__":
    # Run the Flask server on port 5000
    app.run(host="0.0.0.0", port=5000)
