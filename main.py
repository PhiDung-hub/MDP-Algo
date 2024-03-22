import time
from algo.algo import MazeSolver
from algo.helper import command_generator
from flask import Flask, request, jsonify
from consts import Direction, WIDTH, HEIGHT

# from flask_cors import CORS
import model as ModelModule
from typing import Any
import cv2

app = Flask(__name__)

# model = ModelModule.load_model('Week_8.pt')
model = ModelModule.YoloV8("best_v8.pt")


@app.route("/status", methods=["GET"])
def status():
    """
    This is a health check endpoint to check if the server is running
    :return: a json object with a key "result" and value "ok"
    """
    return jsonify({"result": "ok"})


@app.route("/path", methods=["POST"])
def path_finding():
    """
    This is the main endpoint for the path finding algorithm
    :return: a json object with a key "data" and value a dictionary with keys "distance", "path", and "commands"
    """
    # Get the json data from the request
    content: Any = request.json

    # Get the obstacles, big_turn, retrying, robot_x, robot_y, and robot_direction from the json data
    obstacles = content["obstacles"]
    # big_turn = int(content['big_turn'])
    retrying = content["retrying"]
    robot_x, robot_y = content["robot_x"], content["robot_y"]
    robot_direction = Direction(content["robot_dir"])

    # Initialize MazeSolver object with robot size of 20x20, bottom left corner of robot at (1,1), facing north, and whether to use a big turn or not.
    maze_solver = MazeSolver(
        WIDTH, HEIGHT, robot_x, robot_y, robot_direction, big_turn=0
    )

    # Add each obstacle into the MazeSolver. Each obstacle is defined by its x,y positions, its direction, and its id
    for ob in obstacles:
        maze_solver.add_obstacle(ob["x"], ob["y"], ob["d"], ob["id"])

    start = time.time()
    # Get shortest path
    optimal_path, distance = maze_solver.get_optimal_order_dp(retrying=retrying)

    print(f"Time taken to find shortest path using A* search: {time.time() - start}s")
    print(f"Distance to travel: {distance} units")

    # Based on the shortest path, generate commands for the robot
    commands = command_generator(optimal_path, obstacles)

    # Get the starting location and add it to path_results
    path_results = [optimal_path[0].get_dict()]
    # Process each command individually and append the location the robot should be after executing that command to path_results
    i = 0
    for command in commands:
        if command.startswith("SNAP") or command.startswith("SSSSS"):
            continue
        elif command.startswith("FW") or command.startswith("BW"):
            compressed = int(command[-3:]) // 10
            i += compressed
        else:
            i += 1
        path_results.append(optimal_path[i].get_dict())
    return jsonify(
        {
            "data": {"distance": distance, "path": path_results, "commands": commands},
            "error": None,
        }
    )


@app.route("/image", methods=["POST"])
def image_predict():
    """
    This is the main endpoint for the image prediction algorithm
    :return: a json object with a key "result" and value a dictionary with keys "obstacle_id" and "image_id"
    """
    # Get the file from the request
    image_file = request.files["file"]

    # Get the file name
    filename = image_file.filename

    # Read the bytes data from the file
    file_data: bytes = image_file.read()

    (image_id, response_obj, image_instance) = ModelModule.rec_img(model, file_data)

    # Write the image
    cv2.imwrite(filename=f"tests/result/{filename}", img=image_instance)

    # filename format: "<timestamp>_<obstacle_id>_<signal>.jpeg"
    # constituents = file.filename.split("_")
    # obstacle_id = constituents[1]

    ## Week 8 ##
    # signal = constituents[2].strip(".jpg")
    # image_id = predict_image(filename, model, signal)

    ## Week 9 ##
    # We don't need to pass in the signal anymore
    # image_id = predict_image_week_9(filename,model)

    # Return the obstacle_id and image_id
    # result = {
    #     # "obstacle_id": obstacle_id,
    #     "image_id": image_id
    # }

    return jsonify({"image_id": image_id, "detected": response_obj})


@app.route("/stitch", methods=["GET"])
def stitch():
    """
    This is the main endpoint for the stitching command. Stitches the images using two different functions,
    in effect creating two stitches, just for redundancy purposes
    """
    # img = ModelModule.stitch_image()
    # img.show()
    img2 = ModelModule.stitch_image_own()
    img2.show()
    return jsonify({"result": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
