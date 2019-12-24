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
RECURSIVE = "?"
# (row, col) --> [(row, col, level_delta), ...]
# ABOVE, BELOW, LEFT, RIGHT
NEIGHBORS = {
    (0, 0): ((1, 2, -1), (1, 0, 0), (2, 1, -1), (0, 1, 0)),
    (0, 1): ((1, 2, -1), (1, 1, 0), (0, 0, 0), (0, 2, 0)),
    (0, 2): ((1, 2, -1), (1, 2, 0), (0, 1, 0), (0, 3, 0)),
    (0, 3): ((1, 2, -1), (1, 3, 0), (0, 2, 0), (0, 4, 0)),
    (0, 4): ((1, 2, -1), (1, 4, 0), (0, 3, 0), (2, 3, -1)),
    #
    (1, 0): ((0, 0, 0), (2, 0, 0), (2, 1, -1), (1, 1, 0)),
    (1, 1): ((0, 1, 0), (2, 1, 0), (1, 0, 0), (1, 2, 0)),
    (1, 2): (
        (0, 2, 0),
        (0, 0, 1),  # BELOW
        (0, 1, 1),  # BELOW
        (0, 2, 1),  # BELOW
        (0, 3, 1),  # BELOW
        (0, 4, 1),  # BELOW
        (1, 1, 0),
        (1, 3, 0),
    ),
    (1, 3): ((0, 3, 0), (2, 3, 0), (1, 2, 0), (1, 4, 0)),
    (1, 4): ((0, 4, 0), (2, 4, 0), (1, 3, 0), (2, 3, -1)),
    #
    (2, 0): ((1, 0, 0), (3, 0, 0), (2, 1, -1), (2, 1, 0)),
    (2, 1): (
        (1, 1, 0),
        (3, 1, 0),
        (2, 0, 0),
        (0, 0, 1),  # RIGHT
        (1, 0, 1),  # RIGHT
        (2, 0, 1),  # RIGHT
        (3, 0, 1),  # RIGHT
        (4, 0, 1),  # RIGHT
    ),
    # MISSING: (2, 2)
    (2, 3): (
        (1, 3, 0),
        (3, 3, 0),
        (0, 4, 1),  # LEFT
        (1, 4, 1),  # LEFT
        (2, 4, 1),  # LEFT
        (3, 4, 1),  # LEFT
        (4, 4, 1),  # LEFT
        (2, 4, 0),
    ),
    (2, 4): ((1, 4, 0), (3, 4, 0), (2, 3, 0), (2, 3, -1)),
    #
    (3, 0): ((2, 0, 0), (4, 0, 0), (2, 1, -1), (3, 1, 0)),
    (3, 1): ((2, 1, 0), (4, 1, 0), (3, 0, 0), (3, 2, 0)),
    (3, 2): (
        (4, 0, 1),  # ABOVE
        (4, 1, 1),  # ABOVE
        (4, 2, 1),  # ABOVE
        (4, 3, 1),  # ABOVE
        (4, 4, 1),  # ABOVE
        (4, 2, 0),
        (3, 1, 0),
        (3, 3, 0),
    ),
    (3, 3): ((2, 3, 0), (4, 3, 0), (3, 2, 0), (3, 4, 0)),
    (3, 4): ((2, 4, 0), (4, 4, 0), (3, 3, 0), (2, 3, -1)),
    #
    (4, 0): ((3, 0, 0), (3, 2, -1), (2, 1, -1), (4, 1, 0)),
    (4, 1): ((3, 1, 0), (3, 2, -1), (4, 0, 0), (4, 2, 0)),
    (4, 2): ((3, 2, 0), (3, 2, -1), (4, 1, 0), (4, 3, 0)),
    (4, 3): ((3, 3, 0), (3, 2, -1), (4, 2, 0), (4, 4, 0)),
    (4, 4): ((3, 4, 0), (3, 2, -1), (4, 3, 0), (2, 3, -1)),
}


def bug_count(grids, row, col, level):
    count = 0

    key = (row, col)
    for triple in NEIGHBORS[key]:
        neighbor_row, neighbor_col, level_delta = triple
        neighbor_level = level + level_delta
        neighbor_grid = grids.get(neighbor_level)
        if neighbor_grid is None:
            continue

        if neighbor_grid[neighbor_row, neighbor_col] == BUG:
            count += 1

    return count


def update_grids(grids):
    new_grids = {}
    min_level = min(grids.keys())
    max_level = max(grids.keys())

    # Go 1 level below and 1 level above, because bugs "ripple out".
    for level in range(min_level - 1, max_level + 2):
        grid = grids.get(level)
        if grid is None:
            grid = np.empty((5, 5), dtype=str)
            grid.fill(EMPTY)
            grid[2, 2] = RECURSIVE

        new_grid = np.empty((5, 5), dtype=str)
        new_grid.fill(EMPTY)
        new_grid[2, 2] = RECURSIVE
        for row in range(5):
            for col in range(5):
                if row == col == 2:
                    continue

                count = bug_count(grids, row, col, level)
                cell = grid[row, col]
                if cell == BUG:
                    if count == 1:
                        new_grid[row, col] = BUG
                elif cell == EMPTY:
                    if count in (1, 2):
                        new_grid[row, col] = BUG
                else:
                    raise ValueError("Invalid cell", locals())

        if np.any(new_grid == BUG):
            new_grids[level] = new_grid

    return new_grids


def display(grid):
    for row_of_str in grid:
        print("".join(row_of_str))


def main():
    filename = HERE / "input2.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    if False:
        content = """\
....#
#..#.
#.?##
..#..
#....
"""

    grid = np.array([list(row) for row in content.strip().split("\n")])
    assert grid.shape == (5, 5)

    grids = {0: grid}
    for index in range(200):
        grids = update_grids(grids)

    count = 0
    for grid in grids.values():
        count += np.count_nonzero(grid == BUG)
    print(f"count: {count}")


if __name__ == "__main__":
    main()

# counts = -np.ones((5, 5), dtype=int)
# for row in range(5):
#     for col in range(5):
#         if row == col == 2:
#             continue
#         counts[row, col] = bug_count({0: grid}, row, col, 0)
# counts1 = counts == 1
# bugs_still = np.logical_and(grid == BUG, counts1)
# counts2 = counts == 2
# bugs_new = np.logical_and(grid == EMPTY, np.logical_or(counts1, counts2))
# bugs = np.logical_or(bugs_still, bugs_new)
# g = np.empty((5, 5), dtype=str)
# g.fill(EMPTY)
# g[2, 2] = RECURSIVE
# g[bugs] = BUG
