import pathlib

import numpy as np


HERE = pathlib.Path(__file__).resolve().parent
SCAFFOLD = "#"
OPEN_SPACE = "."
VACUUM_ROBOT_UP = "^"
VACUUM_ROBOT_DOWN = "v"
VACUUM_ROBOT_LEFT = "<"
VACUUM_ROBOT_RIGHT = ">"
VACUUM_ROBOT_POSITIONS = {
    VACUUM_ROBOT_UP: np.array([-1, 0]),  # Visual up is "down" in row
    VACUUM_ROBOT_DOWN: np.array([1, 0]),  # Visual down is "up" in row
    VACUUM_ROBOT_LEFT: np.array([0, -1]),  # Visual left is "left" in col
    VACUUM_ROBOT_RIGHT: np.array([0, 1]),  # Visual right is "right" in col
}
POSITIONS_REVERSE = {tuple(v): k for k, v in VACUUM_ROBOT_POSITIONS.items()}
TURNS = {"L": np.array([[0, -1], [1, 0]]), "R": np.array([[0, 1], [-1, 0]])}
PAIRS = {
    ("L", 6): "V",
    ("L", 8): "W",
    ("L", 10): "X",
    ("R", 10): "Y",
    ("R", 12): "Z",
}


def find_exact(grid, value):
    match_rows, match_cols = np.where(grid == value)
    if match_rows.size == 0:
        assert match_cols.size == 0
        return None

    assert match_rows.size == match_cols.size == 1
    return match_rows[0], match_cols[0]


def display_grid(grid):
    _, cols = grid.shape
    print("-" * cols)
    for row in grid:
        print("".join(row))


def _apply_steps(grid, value, direction, robot_position):
    robot_char = POSITIONS_REVERSE[tuple(direction)]
    assert value > 0
    new_position = robot_position
    row, col = robot_position
    for _ in range(value):
        new_position += direction
        row, col = new_position
        if grid[row, col] in VACUUM_ROBOT_POSITIONS:
            grid[row, col] = SCAFFOLD
        else:
            if grid[row, col] != SCAFFOLD:
                raise RuntimeError("Fell off the scaffold")
            grid[row, col] = robot_char

    return direction, new_position


def apply_command(grid, command, direction, robot_position):
    if isinstance(command, int):
        return _apply_steps(grid, command, direction, robot_position)

    turn = TURNS[command]
    new_direction = turn.dot(direction)
    robot_char = POSITIONS_REVERSE[tuple(new_direction)]
    row, col = robot_position
    grid[row, col] = robot_char
    return new_direction, robot_position


def main():
    with open(HERE / "part1_output.txt", "r") as file_obj:
        display = file_obj.read()

    rows = display.strip().split("\n")
    assert set(len(row) for row in rows) == set([51])
    grid = np.array([list(row) for row in rows])
    # 0. Location the robot
    matches = []
    for direction_char, direction in VACUUM_ROBOT_POSITIONS.items():
        match = find_exact(grid, direction_char)
        if match is not None:
            matches.append((direction, match))
    assert len(matches) == 1
    match = matches[0]
    direction, robot_position = match
    robot_position = np.array(robot_position)
    # V:L06
    # W:L08
    # X:L10
    # Y:R10
    # Z:R12
    # Start moving
    path = ("R", 12, "L", 6, "R", 12, "L", 8, "L", 6, "L", 10, "R", 12)
    path += ("L", 6, "R", 12, "R", 12, "L", 10, "L", 6, "R", 10, "L", 8)
    path += ("L", 6, "L", 10, "R", 12, "L", 10, "L", 6, "R", 10, "L", 8)
    path += ("L", 6, "L", 10, "R", 12, "L", 10, "L", 6, "R", 10, "R", 12)
    path += ("L", 6, "R", 12, "R", 12, "L", 10, "L", 6, "R", 10)
    for command in path:
        direction, robot_position = apply_command(
            grid, command, direction, robot_position
        )

    display_grid(grid)

    print("".join(PAIRS[pair] for pair in zip(path[::2], path[1::2])))
    # ZVZWVXZVZZXVYWVXZXVYWVXZXVYZVZZXVY
    # [ZVZ][WVX][ZVZ][ZXVY][WVX][ZXVY][WVX][ZXVY][ZVZ][ZXVY]
    A = ("R", 12, "L", 6, "R", 12)  # ZVZ
    B = ("L", 8, "L", 6, "L", 10)  # WVX
    C = ("R", 12, "L", 10, "L", 6, "R", 10)  # ZXVY
    MAIN = A + B + A + C + B + C + B + C + A + C
    assert MAIN == path


if __name__ == "__main__":
    main()
