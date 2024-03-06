import os
import shutil
import time
import glob
import torch
from PIL import Image
import cv2
import numpy as np
from ultralytics import YOLO
import math

SPECIAL_LABELS = {
    'arrow-bullseye': 'id00',
    'bullseye-arrow': 'id01',
    'bullseye-arrow-bullseye': 'id02',
}

CLASSNAMES_MAP = {0: SPECIAL_LABELS['arrow-bullseye'], 1: SPECIAL_LABELS['bullseye-arrow'], 2: SPECIAL_LABELS['bullseye-arrow-bullseye'], 
              3: 'id11', 4: 'id12', 5: 'id13', 6: 'id14', 7: 'id15', 8: 'id16', 9: 'id17', 
              10: 'id18', 11: 'id19', 12: 'id20', 13: 'id21', 14: 'id22', 15: 'id23', 16: 'id24', 
              17: 'id25', 18: 'id26', 19: 'id27', 20: 'id28', 21: 'id29', 22: 'id30', 23: 'id31', 
              24: 'id32', 25: 'id33', 26: 'id34', 27: 'id35', 28: 'id36', 29: 'id37', 30: 'id38', 
              31: 'id39', 32: 'id40', 33: 'id99'}

def YoloV8(weight="best_v8.pt"):
    return YOLO(weight)

def rec_img(model: YOLO, file_data: bytes):
    np_data = np.frombuffer(file_data, dtype=np.uint8)

    # Open the file-like object as a PIL Image
    image_instance = cv2.imdecode(np_data, cv2.IMREAD_COLOR)

    result = model(image_instance)

    response_obj = {}

    for r in result:
        for index, box in enumerate(r.boxes):
            # Bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # Convert to int values

            # Draw box on the image
            cv2.rectangle(image_instance, (x1, y1), (x2, y2), (255, 0, 255), 3)

            # Confidence
            confidence = math.ceil((box.conf[0] * 100)) / 100
            print("Confidence --->", confidence)
            # Class name
            cls = int(box.cls[0])
            print("Class name -->", CLASSNAMES_MAP[cls])

            response_obj[index] = {
                "confidence": confidence,
                "bounds": [x1, y1, x2, y2],
                "id": int(CLASSNAMES_MAP[cls][-2:])
            }

            # Object details
            org = [x1, y1]
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 7
            color = (0, 255, 0)
            thickness = 12

            cv2.putText(image_instance, CLASSNAMES_MAP[cls], org, font, fontScale, color, thickness)

    # TODO: handle the case for multiple box detected (in response_obj)
    
    image_id = 0
    if response_obj[0]:
        image_id = response_obj[0]['id']

    return (image_id, response_obj, image_instance)

############################### LEGACY CODE ###################################
###############################################################################
def stitch_image():
    """
    Stitches the images in the folder together and saves it into runs/stitched folder
    """
    # Initialize path to save stitched image
    imgFolder = 'runs'
    stitchedPath = os.path.join(imgFolder, f'stitched-{int(time.time())}.jpeg')

    # Find all files that ends with ".jpg" (this won't match the stitched images as we name them ".jpeg")
    imgPaths = glob.glob(os.path.join(imgFolder+"/detect/*/", "*.jpg"))
    # Open all images
    images = [Image.open(x) for x in imgPaths]
    # Get the width and height of each image
    width, height = zip(*(i.size for i in images))
    # Calculate the total width and max height of the stitched image, as we are stitching horizontally
    total_width = sum(width)
    max_height = max(height)
    stitchedImg = Image.new('RGB', (total_width, max_height))
    x_offset = 0

    # Stitch the images together
    for im in images:
        stitchedImg.paste(im, (x_offset, 0))
        x_offset += im.size[0]
    # Save the stitched image to the path
    stitchedImg.save(stitchedPath)

    # Move original images to "originals" subdirectory
    for img in imgPaths:
        shutil.move(img, os.path.join(
            "runs", "originals", os.path.basename(img)))

    return stitchedImg

def stitch_image_own():
    """
    Stitches the images in the folder together and saves it into own_results folder

    Basically similar to stitch_image() but with different folder names and slightly different drawing of bounding boxes and text
    """
    imgFolder = 'own_results'
    stitchedPath = os.path.join(imgFolder, f'stitched-{int(time.time())}.jpeg')

    imgPaths = glob.glob(os.path.join(imgFolder+"/annotated_image_*.jpg"))
    imgTimestamps = [imgPath.split("_")[-1][:-4] for imgPath in imgPaths]
    
    sortedByTimeStampImages = sorted(zip(imgPaths, imgTimestamps), key=lambda x: x[1])

    images = [Image.open(x[0]) for x in sortedByTimeStampImages]
    width, height = zip(*(i.size for i in images))
    total_width = sum(width)
    max_height = max(height)
    stitchedImg = Image.new('RGB', (total_width, max_height))
    x_offset = 0

    for im in images:
        stitchedImg.paste(im, (x_offset, 0))
        x_offset += im.size[0]
    stitchedImg.save(stitchedPath)

    return stitchedImg
