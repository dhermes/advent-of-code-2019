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

import itertools
import pathlib

import networkx as nx
import numpy as np


HERE = pathlib.Path(__file__).resolve().parent
ENTRANCE = "@"
OPEN_PASSAGE = "."
STONE_WALL = "#"
DOORS = tuple(chr(i) for i in range(65, 91))
KEYS = tuple(chr(i) for i in range(97, 123))
INFINITY = float("infinity")


def add_neighors(g, grid, node):
    g.add_node(node)
    row, col = node

    neighors = (
        (row - 1, col),  # UP
        (row + 1, col),  # DOWN
        (row, col - 1),  # LEFT
        (row, col + 1),  # RIGHT
    )
    for neighor_node in neighors:
        neighor_row, neighor_col = neighor_node
        cell_neighor = grid[neighor_row, neighor_col]
        if cell_neighor == STONE_WALL:
            continue

        g.add_edge(node, neighor_node)


def get_shortest_path(g, node1, node2, node_to_obstacle):
    all_paths = nx.all_shortest_paths(g, node1, node2)
    # Handle the first path.
    path = next(all_paths)
    obstacles_on_path = tuple(
        node_to_obstacle[node] for node in path if node in node_to_obstacle
    )

    # **IMPORTANT** We assume the "shortest" path uniquely determines which
    # landmarks are on the path.
    # Make sure all the other paths have the same landmarks.
    for other_path in all_paths:
        other_obstacles = tuple(
            node_to_obstacle[node]
            for node in other_path
            if node in node_to_obstacle
        )
        if other_obstacles != obstacles_on_path:
            missing_elements = set(obstacles_on_path).symmetric_difference(
                other_obstacles
            )
            # Allow a mismatch if it only involves the ENTRANCE.
            assert missing_elements == set([ENTRANCE]), (
                other_obstacles,
                obstacles_on_path,
            )

    return path, obstacles_on_path


class PairwiseDistance:
    def __init__(self):
        self.values = {}

    def insert(self, a, b, value):
        assert a < b
        key = (a, b)
        assert key not in self.values
        self.values[key] = value

    def get(self, a, b):
        if a > b:
            a, b = b, a

        key = (a, b)
        return self.values[key]


def greedy_route(g, keys, doors, pairwise_distance):
    route = [ENTRANCE]
    num_keys = len(keys) - 1
    total_distance = 0
    for _ in range(num_keys):
        # print(f"stage: {stage}")
        # if stage == 2:
        #     raise RuntimeError
        curr_key = route[-1]

        # Use greedy algorithm to pick the best choice.
        min_distance = INFINITY
        min_distance_key = None
        for key in keys.keys():
            if key in route:
                continue

            distance, obstacles = pairwise_distance.get(curr_key, key)
            remaining_obstacles = [
                obstacle
                for obstacle in obstacles
                if obstacle in DOORS and obstacle.lower() not in route
            ]
            if remaining_obstacles:
                # print((curr_key, key, obstacles, remaining_obstacles))
                continue

            if distance < min_distance:
                min_distance = distance
                min_distance_key = key

        assert min_distance_key is not None
        route.append(min_distance_key)
        # print(f"min_distance_key: {min_distance_key}")
        total_distance += min_distance

    # print(route)
    return total_distance


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    if True:
        content = """\
########################
#@..............ac.GI.b#
###d#e#f################
###A#B#C################
###g#h#i################
########################"""

    grid = content.strip().split("\n")
    rows = len(grid)
    cols = len(grid[0])
    assert set(len(row) for row in grid) == set([cols])
    grid = np.array([list(row) for row in grid])
    assert grid.shape == (rows, cols)

    # Make sure boundaries are all walls
    assert np.all(grid[:, 0] == STONE_WALL)
    assert np.all(grid[:, -1] == STONE_WALL)
    assert np.all(grid[0, :] == STONE_WALL)
    assert np.all(grid[-1, :] == STONE_WALL)

    entrance = None
    keys = {}
    doors = {}
    g = nx.Graph()
    for row in range(1, rows - 1):
        for col in range(1, cols - 1):
            node = (row, col)
            cell = grid[row, col]
            if cell == STONE_WALL:
                continue
            elif cell in DOORS:
                assert node not in doors
                doors[cell] = node
            elif cell in KEYS:
                assert cell not in keys
                keys[cell] = node
            elif cell == ENTRANCE:
                assert entrance is None
                entrance = node
            else:
                assert cell == OPEN_PASSAGE, cell

            add_neighors(g, grid, node)

    assert nx.is_connected(g)
    keys[ENTRANCE] = entrance

    all_keys = sorted(keys.keys())
    node_to_obstacle = {node: key for key, node in keys.items()}
    for door, node in doors.items():
        node_to_obstacle[node] = door

    pairwise_distance = PairwiseDistance()
    for key1, key2 in itertools.combinations(all_keys, 2):
        node1 = keys[key1]
        node2 = keys[key2]
        path, obstacles_on_path = get_shortest_path(
            g, node1, node2, node_to_obstacle
        )
        assert obstacles_on_path[0] == key1
        assert obstacles_on_path[-1] == key2
        pairwise_distance.insert(
            key1, key2, (len(path) - 1, obstacles_on_path)
        )

    greedy_distance = greedy_route(g, keys, doors, pairwise_distance)
    print(greedy_distance)
    # partial_routes = [(ENTRANCE,)]
    # num_keys = len(keys) - 1
    # for stage in range(num_keys):
    #     pass


if __name__ == "__main__":
    main()
