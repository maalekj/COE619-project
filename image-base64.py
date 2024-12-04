import base64


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        return encoded_string.decode("utf-8")


if __name__ == "__main__":
    image_path = "res/car-accident.jpeg"
    base64_string = image_to_base64(image_path)
    print("Base64 encoding of the image:")
    print(base64_string)
