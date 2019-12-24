# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pathlib

import numpy as np


HERE = pathlib.Path(__file__).resolve().parent
BUG = "#"
EMPTY = "."


def bug_count(grid, row, col):
    count = 0

    if grid[row - 1, col] == BUG:
        count += 1

    if grid[row + 1, col] == BUG:
        count += 1

    if grid[row, col - 1] == BUG:
        count += 1

    if grid[row, col + 1] == BUG:
        count += 1

    return count


def update_grid(grid):
    assert grid.shape == (7, 7)
    new_grid = np.empty((7, 7), dtype=grid.dtype)
    new_grid.fill(EMPTY)

    for row in range(1, 6):
        for col in range(1, 6):
            count = bug_count(grid, row, col)
            cell = grid[row, col]
            if cell == BUG:
                if count == 1:
                    new_grid[row, col] = BUG
            elif cell == EMPTY:
                if count in (1, 2):
                    new_grid[row, col] = BUG
            else:
                raise ValueError("Invalid cell", locals())

    return new_grid


def to_int(grid):
    inside_grid = grid[1:-1, 1:-1]
    cells = inside_grid.flatten(order="C")
    as_ints = (cells == BUG).astype(int)
    as_bin_str = "".join(str(v) for v in as_ints[::-1])
    return int(as_bin_str, 2)


def display(grid):
    inside_grid = grid[1:-1, 1:-1]
    for row_of_str in inside_grid:
        print("".join(row_of_str))


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    if False:
        content = """\
....#
#..#.
#..##
..#..
#....
"""

    inside_grid = np.array([list(row) for row in content.strip().split("\n")])
    assert inside_grid.shape == (5, 5)

    grid = np.empty((7, 7), dtype=inside_grid.dtype)
    grid.fill(EMPTY)
    grid[1:-1, 1:-1] = inside_grid
    # print(grid)

    seen = set()
    seen.add(to_int(grid))
    while True:
        # print(grid[3, 3]) <-- recursion
        # print("=" * 40)
        # display(grid)
        grid = update_grid(grid)
        as_int = to_int(grid)
        if as_int in seen:
            # print("=" * 40)
            # display(grid)
            print(f"Repeated: {as_int}")
            break
        seen.add(as_int)


if __name__ == "__main__":
    main()


# counts = np.empty((7, 7), dtype=int)
# counts[:, :] = -1
# for row in range(1, 6):
#     for col in range(1, 6):
#         counts[row, col] = bug_count(grid, row, col)
