import requests
import sys

if __name__ == '__main__':
    # Open the image file in binary mode
    img_name = sys.argv[1]
    with open(f'tests/input/{img_name}', 'rb') as file:
        # Read the binary data
        image_data = file.read()
        response = requests.post(
            "http://localhost:5000/image", 
            files={"file": (f"{img_name}", image_data)}
        )

        print("response", response.json())

