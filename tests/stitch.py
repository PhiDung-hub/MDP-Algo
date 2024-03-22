import requests

if __name__ == '__main__':
    # Open the image file in binary mode
    response = requests.get(
        "http://localhost:5000/stitch"
    )

