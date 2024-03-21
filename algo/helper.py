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
        p_state = states[i - 1]
        cur_state = states[i]

        is_forward_x = (cur_state.x - p_state.x) * (3 - p_state.direction) > 0
        is_forward_y = (cur_state.y - p_state.y) * (3 - p_state.direction) > 0

        # by direction convention, 2 mod 8
        is_clockwise = (cur_state.direction - p_state.direction - 2) % 8 == 0
        # by direction convention, 6 mod 8
        is_counter_clockwise = (cur_state.direction - p_state.direction - 6) % 8 == 0

        if cur_state.direction == p_state.direction:
            f_cmd = "FW010" if (is_forward_x or is_forward_y) else "BW010"
            commands.append(f_cmd)
        else:
            # Assume there are 4 turning command: FR, FL, BL, BR (the turn command will turn the robot 90 degrees)
            def generate_turn_command() -> str:
                is_forward = (
                    is_forward_x and (p_state.direction == 2 or p_state.direction == 6)
                ) or (
                    is_forward_y and (p_state.direction == 0 or p_state.direction == 4)
                )
                if is_clockwise:
                    # y value increased -> Forward Right
                    if is_forward:
                        return "FR000"
                    # y value decreased -> Backward Left
                    else:
                        return "BL000"
                elif is_counter_clockwise:
                    # y value increased -> Forward Left
                    if is_forward:
                        return "FL000"
                    # y value decreased -> Backward Right
                    else:
                        return "BR000"
                else:
                    raise Exception(
                        f"Invalid turing direction: previous - {p_state.direction} current - {cur_state.direction}"
                    )

            turn_command = generate_turn_command()
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
        if cur_state.screenshot_id != -1:
            obstacle = obstacles_dict[cur_state.screenshot_id]

            snap_command = generate_snap_command(cur_state, obstacle)
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
            dist_str = f"{value}" if value >= 100 else f"0{value}"
            compressed_commands[-1] = f"{cmd[:2]}{dist_str}"

            continue

        # Otherwise, just add as usual
        compressed_commands.append(cmd)

    return compressed_commands
