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

import doctest
import pathlib

import numpy as np


HERE = pathlib.Path(__file__).resolve().parent


def parse_move(move):
    """Convert a directional text move into a vector and distance.

    >>> parse_move("R8")
    (array([1, 0, 1]), 8)
    >>> parse_move("L5")
    (array([-1,  0,  1]), 5)
    >>> parse_move("D3")
    (array([ 0, -1,  1]), 3)
    >>> parse_move("U4")
    (array([0, 1, 1]), 4)
    """
    direction = move[:1]  # Avoid IndexError using [0]
    distance = int(move[1:])
    if str(distance) != move[1:]:
        raise ValueError("Unexpected move", move)
    if distance < 1:
        raise ValueError("Unexpected move", move)

    if direction == "U":
        return np.array([0, 1, 1]), distance
    if direction == "D":
        return np.array([0, -1, 1]), distance
    if direction == "R":
        return np.array([1, 0, 1]), distance
    if direction == "L":
        return np.array([-1, 0, 1]), distance

    raise ValueError("Unexpected move", move)


def wire_to_points(turns):
    """Convert a series of turns into a list of points on a lattice.

    >>> wire_to_points("R8,U5,L5,D3")
    [(0, 0, 0), (1, 0, 1), (2, 0, 2), (3, 0, 3), (4, 0, 4), (5, 0, 5), (6, 0, 6), (7, 0, 7), (8, 0, 8), (8, 1, 9), (8, 2, 10), (8, 3, 11), (8, 4, 12), (8, 5, 13), (7, 5, 14), (6, 5, 15), (5, 5, 16), (4, 5, 17), (3, 5, 18), (3, 4, 19), (3, 3, 20), (3, 2, 21)]
    >>> wire_to_points("U7,R6,D4,L4")
    [(0, 0, 0), (0, 1, 1), (0, 2, 2), (0, 3, 3), (0, 4, 4), (0, 5, 5), (0, 6, 6), (0, 7, 7), (1, 7, 8), (2, 7, 9), (3, 7, 10), (4, 7, 11), (5, 7, 12), (6, 7, 13), (6, 6, 14), (6, 5, 15), (6, 4, 16), (6, 3, 17), (5, 3, 18), (4, 3, 19), (3, 3, 20), (2, 3, 21)]
    """
    moves = turns.split(",")
    current_point = np.array([0, 0, 0])
    points = [tuple(current_point)]
    for move in moves:
        direction, distance = parse_move(move)
        for _ in range(distance):
            current_point += direction
            points.append(tuple(current_point))

    return points


def find_intersections(turns1, turns2):
    points1 = wire_to_points(turns1)
    points2 = wire_to_points(turns2)

    distance_mapping1 = {}
    for x_val, y_val, steps in points1:
        key = (x_val, y_val)
        if key in distance_mapping1:
            distance_mapping1[key] = min(steps, distance_mapping1[key])
        else:
            distance_mapping1[key] = steps

    common_points = {}
    for x_val, y_val, steps in points2:
        key = (x_val, y_val)
        if key == (0, 0):
            continue

        if key not in distance_mapping1:
            continue

        if key in common_points:
            steps1, steps2 = common_points[key]
            steps2 = min(steps, steps2)
            common_points[key] = steps1, steps2
        else:
            common_points[key] = distance_mapping1[key], steps

    if len(common_points) == 0:
        raise RuntimeError("Expected at least 1 intersection", turns1, turns2)

    return common_points


def minimal_distance(turns1, turns2):
    """Compute the minimal Manhattan distance to a point where wires cross.

    >>> minimal_distance("R8,U5,L5,D3", "U7,R6,D4,L4")
    6
    >>> minimal_distance(
    ...     "R75,D30,R83,U83,L12,D49,R71,U7,L72",
    ...     "U62,R66,U55,R34,D71,R55,D58,R83",
    ... )
    159
    >>> minimal_distance(
    ...     "R98,U47,R26,D63,R33,U87,L62,D20,R33,U53,R51",
    ...     "U98,R91,D20,R16,D67,R40,U7,R15,U6,R7",
    ... )
    135
    """
    common_points = find_intersections(turns1, turns2)
    common_iter = iter(common_points.keys())
    x_val, y_val = next(common_iter)
    min_distance = abs(x_val) + abs(y_val)
    for x_val, y_val in common_iter:
        min_distance = min(min_distance, abs(x_val) + abs(y_val))

    return min_distance


def minimal_distance_by_steps(turns1, turns2):
    """Compute the minimal sum of steps to a point where wires cross.

    >>> minimal_distance_by_steps("R8,U5,L5,D3", "U7,R6,D4,L4")
    30
    >>> minimal_distance_by_steps(
    ...     "R75,D30,R83,U83,L12,D49,R71,U7,L72",
    ...     "U62,R66,U55,R34,D71,R55,D58,R83",
    ... )
    610
    >>> minimal_distance_by_steps(
    ...     "R98,U47,R26,D63,R33,U87,L62,D20,R33,U53,R51",
    ...     "U98,R91,D20,R16,D67,R40,U7,R15,U6,R7",
    ... )
    410
    """
    common_points = find_intersections(turns1, turns2)
    common_iter = iter(common_points.values())
    steps1, steps2 = next(common_iter)
    min_distance = steps1 + steps2
    for steps1, steps2 in common_iter:
        min_distance = min(min_distance, steps1 + steps2)

    return min_distance


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    turns1, turns2 = content.strip().split("\n")
    distance_manhattan = minimal_distance(turns1, turns2)
    print(f"Minimal Manhattan Distance: {distance_manhattan}")
    distance_by_steps = minimal_distance_by_steps(turns1, turns2)
    print(f"Minimal Total Steps: {distance_by_steps}")


if __name__ == "__main__":
    doctest.testmod()
    main()
