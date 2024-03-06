from entities.Entity import CellState

def command_generator(
    states: list[CellState], obstacles: list[dict[str, int]]
) -> list[str]:
    """
    @Inputs
    --
    states: list of State objects
    obstacles: list of obstacles, each obstacle is a dictionary with keys "x", "y", "d", and "id"

    -------
    @Returns
    --
    commands: list of commands for the robot to follow
    """

    # Convert the list of obstacles into a dictionary with key as the obstacle id and value as the obstacle
    obstacles_dict = {ob["id"]: ob for ob in obstacles}

    # Initialize commands list
    commands = []

    # Iterate through each state in the list of states
    for i in range(1, len(states)):
        previous_state = states[i - 1]
        current_state = states[i]

        def generate_forward_command(cur_state: CellState, pre_state: CellState) -> str:
            d = cur_state.direction

            is_forward_x = (cur_state.x - pre_state.x) * (3 - d) > 0
            is_forward_y = (cur_state.y - pre_state.y) * (3 - d) > 0
            if is_forward_x or is_forward_y:
                return "FW010"
            else:
                return "BW010"

        # If previous state and current state are not the same direction, it means that there will be a turn command involved
        # Assume there are 4 turning command: FR, FL, BL, BR (the turn command will turn the robot 90 degrees)
        def generate_turn_command(
            current_state: CellState, previous_state: CellState
        ) -> str:
            # Facing north previously
            pd = previous_state.direction
            cd = current_state.direction

            # by direction convention, 2 mod 8
            is_clockwise = (cd - pd - 2) % 8 == 0
            # by direction convention, 6 mod 8
            is_counter_clockwise = (cd - pd - 6) % 8 == 0

            if is_clockwise:
                # y value increased -> Forward Right
                if current_state.y > previous_state.y:
                    return "FR000"
                # y value decreased -> Backward Left
                else:
                    return "BL000"
            elif is_counter_clockwise:
                # y value increased -> Forward Left
                if current_state.y > previous_state.y:
                    return "FL000"
                # y value decreased -> Backward Right
                else:
                    return "BR000"
            else:
                raise Exception(
                    f"Invalid turing direction: previous - {pd} current - {cd}"
                )

        if current_state.direction == previous_state.direction:
            f_cmd = generate_forward_command(current_state, previous_state)
            commands.append(f_cmd)
        else:
            turn_command = generate_turn_command(current_state, previous_state)
            commands.append(turn_command)

        def generate_snap_command(
            current_state: CellState, obstacle: dict[str, int]
        ) -> str:
            # NOTE: robot and obstacle should be facing each other
            snap_cmd = f"SNAP{current_state.screenshot_id}"

            robot_d = current_state.direction
            obstacle_d = obstacle["d"]

            is_EW = (robot_d + obstacle_d) % 8 == 0
            is_NS = (robot_d + obstacle_d) % 8 == 4

            EW_factor = (current_state.y - obstacle["y"]) * (robot_d - obstacle_d)
            NS_factor = (current_state.x - obstacle["x"]) * (robot_d - obstacle_d)

            if is_EW:
                if EW_factor > 0:
                    snap_cmd += "_L"
                elif EW_factor < 0:
                    snap_cmd += "_R"
                else:
                    snap_cmd += "_C"

            elif is_NS:
                if NS_factor < 0:
                    snap_cmd += "_L"
                elif NS_factor > 0:
                    snap_cmd += "_R"
                else:
                    snap_cmd += "_C"
            else:
                raise Exception(
                    f"Invalid direction: robot - {robot_d} obstacle - {obstacle_d}"
                )

            return snap_cmd

        # If any of these states has a valid screenshot ID, then add a SNAP command as well to take a picture
        if current_state.screenshot_id != -1:
            obstacle = obstacles_dict[current_state.screenshot_id]

            snap_command = generate_snap_command(current_state, obstacle)
            commands.append(snap_command)

    # Final command is the stop command (SSSSS)
    commands.append("SSSSS")

    # Compress commands if there are consecutive forward or backward commands
    compressed_commands = [commands[0]]

    for cmd in commands[1:]:
        ccmd = compressed_commands[-1]
        # If both commands are BW
        if cmd[1] == "W" and ccmd[:2] == cmd[:2]:
            # Get the number of steps of previous command
            steps = int(compressed_commands[-1][-3:])
            value = steps + 10
            dist_str = f"{value}" if value > 100 else f"0{value}"
            compressed_commands[-1] = f"{cmd[:2]}{dist_str}"

            continue

        # Otherwise, just add as usual
        compressed_commands.append(cmd)

    return compressed_commands
