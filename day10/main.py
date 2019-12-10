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

import collections
import math
import pathlib

import numpy as np


HERE = pathlib.Path(__file__).resolve().parent
ASTEROID = 1
VACANT = 0


def to_int(value):
    if value == "#":  # Asteroid
        return ASTEROID
    if value == ".":  # Empty
        return VACANT
    raise ValueError("Unexpected element", value)


def parse_asteroids(content):
    lines = content.strip().split("\n")
    rows = len(lines)
    columns = len(lines[0])

    values = np.zeros((rows, columns), dtype=np.uint8)
    for row, line in enumerate(lines):
        assert len(line) == columns
        values[row, :] = [to_int(char) for char in line]

    return values


def normalize_direction(a, b):
    if a == 0 and b == 0:
        return 1, (0, 0)

    common_factor = abs(math.gcd(a, b))
    a_without, remainder = divmod(a, common_factor)
    assert remainder == 0
    b_without, remainder = divmod(b, common_factor)
    assert remainder == 0
    return common_factor, (a_without, b_without)


def line_of_sight(values, target_row, target_column):
    rows, columns = values.shape
    asteroids = collections.defaultdict(list)

    for row in range(rows):
        delta_row = target_row - row  # points down
        for column in range(columns):
            if row == target_row and column == target_column:
                continue

            delta_column = column - target_column  # points right
            if values[row, column] != ASTEROID:
                continue

            factor, direction = normalize_direction(delta_row, delta_column)
            asteroids[direction].append(factor)

    return asteroids


def all_line_of_sight(values):
    rows, columns = values.shape
    counts = np.zeros((rows, columns), dtype=np.uint64)

    for row in range(rows):
        for column in range(columns):
            if values[row, column] != ASTEROID:
                counts[row, column] = 0
                continue

            asteroids = line_of_sight(values, row, column)
            counts[row, column] = len(asteroids)

    return counts


def all_vaporized(values, target_row, target_column):
    rows, columns = values.shape
    asteroids = line_of_sight(values, target_row, target_column)
    directions_theta = {}

    for direction, multipliers in asteroids.items():
        # Row indices **increase** in the downward y direction.
        d_row, d_column = direction
        theta = np.arctan2(d_row, d_column)  # Row indices are y, columns are x
        directions_theta[theta] = (direction, sorted(multipliers))

    removed = []
    sorted_theta = np.array(sorted(directions_theta.keys(), reverse=True))
    # This is in the range [-pi, pi] (but reverse, since we go counter clockwise)
    in_first_quadrant, = np.where(
        np.logical_and(0 < sorted_theta, sorted_theta <= np.pi / 2)
    )
    start_index = min(in_first_quadrant)
    laser_theta = np.array(
        list(sorted_theta[start_index:]) + list(sorted_theta[:start_index])
    )

    updated = True
    while updated:
        updated = False

        for theta in laser_theta:
            direction, multipliers = directions_theta[theta]
            if not multipliers:
                continue

            multiplier = multipliers[0]
            delta_row, delta_column = direction
            delta_row *= multiplier  # Un-normalize
            delta_column *= multiplier  # Un-normalize
            # Undo delta_row = target_row - row
            row = target_row - delta_row
            assert 0 <= row < rows
            # Undo delta_column = column - target_column
            column = target_column + delta_column
            assert 0 <= column < columns, (column, columns)
            removed.append((row, column))
            updated = True

            # Update for next iteration.
            multipliers[:] = multipliers[1:]

    return removed


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read().strip()

    values = parse_asteroids(content)
    all_counts = all_line_of_sight(values)
    best_count = max(all_counts.flatten())
    print(best_count)

    row_matches, col_matches = np.where(all_counts == best_count)
    row_match, = row_matches
    col_match, = col_matches
    removed = all_vaporized(values, row_match, col_match)
    print(removed[200 - 1][::-1])


if __name__ == "__main__":
    main()
