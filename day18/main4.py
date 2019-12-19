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

    def insert(self, a, b, path_len, obstacles):
        assert a < b
        key = (a, b)
        assert key not in self.values
        self.values[key] = path_len, obstacles

    def get(self, a, b):
        if a > b:
            path_len, obstacles = self.values[(b, a)]
            return path_len, obstacles[::-1]

        return self.values[(a, b)]


def greedy_route(g, keys, doors, pairwise_distance):
    route = [ENTRANCE]
    num_keys = len(keys) - 1
    total_distance = 0
    for _ in range(num_keys):
        # Use greedy algorithm to pick the best choice.
        min_distance = INFINITY
        min_distance_key = None

        choices = valid_choices(g, route, keys, doors, pairwise_distance)
        for key, distance in choices:
            if distance < min_distance:
                min_distance = distance
                min_distance_key = key

        assert min_distance_key is not None, (route,)
        route.append(min_distance_key)
        # print(f"min_distance_key: {min_distance_key}")
        total_distance += min_distance

    # print(route)
    return total_distance


def is_impediment(obstacle, route):
    if obstacle == ENTRANCE:
        return False

    if obstacle in KEYS:
        return obstacle not in route

    assert obstacle in DOORS
    return obstacle.lower() not in route


def valid_choices(g, route, keys, doors, pairwise_distance):
    # print(f"route: {route}")
    curr_key = route[-1]
    for key in keys.keys():
        if key in route:
            continue

        distance, obstacles = pairwise_distance.get(curr_key, key)
        remaining_obstacles = [
            obstacle
            for obstacle in obstacles[1:-1]
            if is_impediment(obstacle, route)
        ]
        # print(
        #     f"key: {key} | obstacles: {list(obstacles[1:-1])} | "
        #     f"remaining_obstacles: {remaining_obstacles}"
        # )
        if remaining_obstacles:
            continue

        yield key, distance


def consolidate_by_visited(routes):
    by_visited = {}
    for route, distance in routes:
        last_one = route[-1]
        visited = tuple(sorted(route[:-1]))
        key = (last_one, visited)

        if key not in by_visited:
            by_visited[key] = route, distance

        _, compare_distance = by_visited[key]
        if distance < compare_distance:
            by_visited[key] = route, distance

    return list(by_visited.values())


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    if False:
        content = """\
########################
#...............b.C.D.f#
#.######################
#.....@.a.B.c.d.A.e.F.g#
########################"""
    if False:
        content = """\
#################
#i.G..c...e..H.p#
########.########
#j.A..b...f..D.o#
########@########
#k.E..a...g..B.n#
########.########
#l.F..d...h..C.m#
#################"""
    if False:
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
    print("Done creating graph")

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
        pairwise_distance.insert(key1, key2, len(path) - 1, obstacles_on_path)

    print("Done computing pairwise distances")
    # print(content.strip())

    greedy_distance = greedy_route(g, keys, doors, pairwise_distance)
    print(f"greedy_distance: {greedy_distance}")

    route_start = (ENTRANCE,)
    distance_start = 0
    partial_routes = [(route_start, distance_start)]
    num_keys = len(keys) - 1
    for stage in range(num_keys):
        partial_routes_new = []
        for route, partial_distance in partial_routes:
            choices = valid_choices(g, route, keys, doors, pairwise_distance)
            for key, distance in choices:
                new_distance = partial_distance + distance
                if new_distance > greedy_distance:
                    # msg = (
                    #     f"Got rid of route at stage {stage} for "
                    #     f"{new_distance} exceeding greedy distance "
                    #     f"{greedy_distance}"
                    # )
                    # print(msg)
                    continue

                new_route = route + (key,)
                partial_routes_new.append((new_route, new_distance))

        # Consolidate for any paths that have led to the same point.
        partial_routes_new = consolidate_by_visited(partial_routes_new)
        # Update for next iteration.
        partial_routes = partial_routes_new
        # print(f"{stage}: {partial_routes}")
        print(f"{stage}: {len(partial_routes)}")

    min_distance = INFINITY
    min_distance_route = None
    for route, distance in partial_routes:
        if distance < min_distance:
            min_distance = distance
            min_distance_route = route

    print(f"min_distance: {min_distance}")
    print(f"min_distance_route: {min_distance_route}")


if __name__ == "__main__":
    main()
