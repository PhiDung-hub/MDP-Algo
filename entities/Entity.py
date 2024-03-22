from typing import List
from consts import Direction, EXPANDED_CELL, SCREENSHOT_COST
from consts import WIDTH, HEIGHT, Direction


def is_valid_cell(center_x: int, center_y: int):
    return (
        center_x > 0 and center_y > 0 and center_x < WIDTH - 1 and center_y < HEIGHT - 1
    )


class CellState:
    """Base class for all objects on the arena, such as cells, obstacles, etc"""

    def __init__(
        self,
        x: int,
        y: int,
        direction: Direction = Direction.NORTH,
        screenshot_id=-1,
        penalty=0,
    ):
        self.x = x
        self.y = y
        self.direction = direction
        # If screenshot_od != -1, the snapshot is taken at that position is for the obstacle with id = screenshot_id
        self.screenshot_id = screenshot_id
        self.penalty = penalty  # Penalty for the view point of taking picture

    def cmp_position(self, x: int, y: int) -> bool:
        """
        Compare given (x,y) position with cell state's position
        """
        return self.x == x and self.y == y

    def is_eq(self, x: int, y: int, direction: Direction):
        """
        Compare given x, y, direction with cell state's position and direction
        """
        return self.x == x and self.y == y and self.direction == direction


    def __repr__(self):
        return "Cell(x: {}, y: {}, d: {}, screenshot_id: {})".format(
            self.x, self.y, self.direction, self.screenshot_id
        )

    def get_dict(self) -> dict[str, int]:
        """Returns a dictionary representation of the cell

        Returns:
            dict: {x,y,d,s}
        """
        return {"x": self.x, "y": self.y, "d": self.direction, "s": self.screenshot_id}


class Obstacle(CellState):
    """Obstacle class, inherited from CellState"""

    def __init__(self, x: int, y: int, direction: Direction, obstacle_id: int):
        super().__init__(x, y, direction)
        self.obstacle_id = obstacle_id

    def __eq__(self, other):
        """Checks if this obstacle is the same as input in terms of x, y, and direction

        Args:
            other (Obstacle): input obstacle to compare to

        Returns:
            bool: True if same, False otherwise
        """
        return (
            self.x == other.x
            and self.y == other.y
            and self.direction == other.direction
        )

    def get_view_state(self, retrying=False) -> List[CellState]:
        """Constructs the list of CellStates from which the robot can view the symbol on the obstacle

        Returns:
            List[CellState]: Valid cell states where robot can be positioned to view the symbol on the obstacle
        """
        cells = []

        observable = range(4, 7)

        exp = 2

        # If the obstacle is facing north, then robot's cell state must be facing south
        if self.direction == Direction.NORTH:
            for y in observable:
                (cell_x, cell_y) = (self.x, self.y + y)
                if is_valid_cell(cell_x, cell_y):
                    cells.append(CellState(cell_x, cell_y, Direction.SOUTH, self.obstacle_id, -y ** exp))


        # If obstacle is facing south, then robot's cell state must be facing north
        elif self.direction == Direction.SOUTH:
            for y in observable:
                (cell_x, cell_y) = (self.x, self.y - y)
                if is_valid_cell(cell_x, cell_y):
                    cells.append(CellState(cell_x, cell_y, Direction.NORTH, self.obstacle_id, -y ** exp))

        # If obstacle is facing east, then robot's cell state must be facing west
        elif self.direction == Direction.EAST:
            for x in observable:
                (cell_x, cell_y) = (self.x + x, self.y)
                if is_valid_cell(cell_x, cell_y):
                    cells.append(CellState(cell_x, cell_y, Direction.WEST, self.obstacle_id, -x ** exp))

        # If obstacle is facing west, then robot's cell state must be facing east
        elif self.direction == Direction.WEST:
            for x in observable:
                (cell_x, cell_y) = (self.x - x, self.y)
                if is_valid_cell(cell_x, cell_y):
                    cells.append(CellState(cell_x, cell_y, Direction.EAST, self.obstacle_id, -x ** exp))

        return cells


class Grid:
    """
    Grid object that contains the size of the grid and a list of obstacles
    """

    def __init__(self, size_x: int, size_y: int):
        """
        Args:
            size_x (int): Size of the grid in the x direction
            size_y (int): Size of the grid in the y direction
        """
        self.size_x = size_x
        self.size_y = size_y
        self.obstacles: List[Obstacle] = []

    def add_obstacle(self, obstacle: Obstacle):
        """Add a new obstacle to the Grid object, ignores if duplicate obstacle

        Args:
            obstacle (Obstacle): Obstacle to be added
        """
        # Loop through the existing obstacles to check for duplicates
        to_add = True
        for ob in self.obstacles:
            if ob == obstacle:
                to_add = False
                break

        if to_add:
            self.obstacles.append(obstacle)

    def reset_obstacles(self):
        self.obstacles = []

    def reachable(self, x: int, y: int, turn=False, preTurn=False) -> bool:
        """Checks whether the given x,y coordinate is reachable/safe. Criterion is as such:
        - Must be at least 4 units away in total (x+y) from the obstacle
        - Greater distance (x or y distance) must be at least 3 units away from obstacle

        Args:
            x (int): _description_
            y (int): _description_

        Returns:
            bool: _description_
        """

        if not self.is_valid_coord(x, y):
            return False

        for ob in self.obstacles:
            # print(f"Looking at position x:{x} y:{y} against ob: {ob.x} {ob.y}")
            if ob.x == 4 and ob.y <= 4 and x < 4 and y < 4:
                # print(f"ob.x: {ob.x} ob.y: {ob.y} x: {x} y:{y} Triggered four bypass")
                continue

            # Must be at least 4 units away in total (x+y)
            if abs(ob.x - x) + abs(ob.y - y) >= 4:
                # print(f"ob.x: {ob.x} ob.y: {ob.y} x: {x} y:{y} Triggered more than 3 units bypass")
                continue

            # If max(x,y) is less than 3 units away, consider not reachable
            if turn and max(abs(ob.x - x), abs(ob.y - y)) < EXPANDED_CELL * 2 + 1:
                # if ob.x == 0 and ob.y == 10 and x == 1 and y == 12:
                #     print(f"ob.x: {ob.x} ob.y: {ob.y} x: {x} y:{y} Triggered less than 3 max units trap")
                return False
            if preTurn and max(abs(ob.x - x), abs(ob.y - y)) < EXPANDED_CELL * 2 + 1:
                # if ob.x == 0 and ob.y == 10 and x == 1 and y == 12:
                #     print(f"ob.x: {ob.x} ob.y: {ob.y} x: {x} y:{y} Triggered less than 3 max units trap")
                return False
            elif max(abs(ob.x - x), abs(ob.y - y)) < 2:
                # print(f"ob.x: {ob.x} ob.y: {ob.y} x: {x} y:{y} Triggered less than 3 max units trap")
                return False

        return True

    def is_valid_coord(self, x: int, y: int) -> bool:
        return x > 0 and y > 0 and x < self.size_x - 1 and y < self.size_y - 1

    def get_view_obstacle_positions(self, retrying) -> List[List[CellState]]:
        """
        This function return a list of desired states for the robot to achieve based on the obstacle position and direction.
        The state is the position that the robot can see the image of the obstacle and is safe to reach without collision
        :return: [[CellState]]
        """
        optimal_positions = []
        for obstacle in self.obstacles:
            if obstacle.direction == 8:
                continue
            else:
                view_states = [
                    view_state
                    for view_state in obstacle.get_view_state(retrying)
                    if self.reachable(view_state.x, view_state.y)
                ]
            optimal_positions.append(view_states)

        return optimal_positions
