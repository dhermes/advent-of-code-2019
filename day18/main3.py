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
import pickle

import colors
import networkx as nx
import numpy as np


HERE = pathlib.Path(__file__).resolve().parent
ENTRANCE = "@"
OPEN_PASSAGE = "."
STONE_WALL = "#"
DOORS = tuple(chr(i) for i in range(65, 91))
KEYS = tuple(chr(i) for i in range(97, 123))


def reachable_keys(g, entrance, keys):
    for key, node in keys.items():
        if nx.has_path(g, entrance, node):
            yield key


def visit_key(g, grid, key, keys, doors):
    # Z = [f"key: {key}"]
    door = key.upper()
    # Remove key and door from inventory.
    keys.pop(key)
    if door in doors:
        door_node = doors.pop(door)
        # Z.append(f"door_node: {door_node}")
        add_neighors(g, grid, door_node, doors)
    # print(Z)


def add_neighors(g, grid, node, doors):
    # In case no neighbors, e.g. a key trapped behind a door
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
        if cell_neighor == STONE_WALL or cell_neighor in doors:
            continue

        g.add_edge(node, neighor_node)


def collect_keys(g, grid, entrance, keys, doors):
    if not keys:
        assert not doors
        # print("Base case")
        return [()]

    combined_paths = []
    for key in reachable_keys(g, entrance, keys):
        g_copy = g.copy()
        keys_copy = keys.copy()
        doors_copy = doors.copy()
        # Modify g_copy, keys_copy, doors_copy
        visit_key(g_copy, grid, key, keys_copy, doors_copy)

        paths = collect_keys(g_copy, grid, entrance, keys_copy, doors_copy)
        # print(f"paths: {paths}")
        combined_paths.extend((key,) + path for path in paths)

    assert combined_paths
    return combined_paths


def new_filenames(filename):
    pre, score, prefix = filename.split("_")
    assert pre == "distance"
    score = int(score)
    prefix, post = prefix.split(".txt")
    assert post == ""

    with open(HERE / filename, "r") as file_obj:
        content = file_obj.read()

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
    # g = nx.DiGraph()
    g = nx.Graph()
    for row in range(1, rows - 1):
        for col in range(1, cols - 1):
            node = (row, col)
            cell = grid[row, col]
            if cell == STONE_WALL:
                continue
            if cell in DOORS:
                assert node not in doors
                doors[cell] = node
                continue

            # For ENTRANCE / OPEN_PASSAGE / KEYS, we add to graph neighbors.
            if cell in KEYS:
                assert cell not in keys
                keys[cell] = node
            elif cell == ENTRANCE:
                assert entrance is None
                entrance = node
            else:
                assert cell == OPEN_PASSAGE, cell

            add_neighors(g, grid, node, DOORS)

    assert entrance is not None
    assert len(set(keys.values())) == len(keys)
    assert len(set(doors.values())) == len(doors)

    reachable = list(reachable_keys(g, entrance, keys))
    reachable_nodes = [keys[key] for key in reachable]

    filenames = []
    for key in reachable:
        node = keys[key]
        path = nx.shortest_path(g, entrance, node)
        # Filter out nodes that have other reachable nodes "on the way"
        matching_nodes = [
            reachable_node
            for reachable_node in reachable_nodes
            if reachable_node in path
        ]
        if matching_nodes != [node]:
            continue

        new_grid = grid.copy()
        new_grid[new_grid == ENTRANCE] = OPEN_PASSAGE
        new_grid[new_grid == key] = ENTRANCE
        new_grid[new_grid == key.upper()] = OPEN_PASSAGE
        new_score = score + len(path) - 1
        new_prefix = f"{prefix}{key}"
        filename = f"distance_{new_score}_{new_prefix}.txt"
        with open(HERE / filename, "w") as file_obj:
            file_obj.write("\n".join("".join(row) for row in new_grid) + "\n")

        filenames.append(filename)

    return filenames


def next_stage(filenames):
    result = []
    for filename in filenames:
        result.extend(new_filenames(filename))
    return tuple(result)


def main():
    stage = 0
    filenames = ("distance_0_.txt",)
    while filenames:
        print(f"{stage}: {len(filenames)}")
        stage += 1
        filenames = next_stage(filenames)


if __name__ == "__main__":
    main()
