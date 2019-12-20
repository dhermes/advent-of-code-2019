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
import operator
import pathlib

import networkx as nx
import numpy as np


HERE = pathlib.Path(__file__).resolve().parent
VOID = (" ", "#")
CAN_TRAVERSE = "."


def get_neighbors(row, col, rows, cols):
    neighbors = (
        (row - 1, col),
        (row + 1, col),
        (row, col - 1),
        (row, col + 1),
    )
    for neighbor_key in neighbors:
        if not 0 <= neighbor_key[0] < rows:
            continue
        if not 0 <= neighbor_key[1] < cols:
            continue

        yield neighbor_key


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    lines = content.split("\n")
    assert lines[-1] == ""
    lines = lines[:-1]
    rows = len(lines)
    cols = len(lines[0])
    assert set(len(line) for line in lines) == set([cols])

    grid = np.array([list(line) for line in lines])
    assert grid.shape == (rows, cols), (grid.shape, rows, cols)

    g = nx.Graph()
    second_pass = {}
    for row in range(rows):
        for col in range(cols):
            curr_key = (row, col)
            cell = grid[row, col]
            if cell in VOID:
                continue

            if cell != CAN_TRAVERSE:
                second_pass[curr_key] = cell

            for neighbor_key in get_neighbors(row, col, rows, cols):
                neighbor_row, neighbor_col = neighbor_key
                neighbor_cell = grid[neighbor_row, neighbor_col]
                if neighbor_cell == ".":
                    g.add_edge(curr_key, neighbor_key)

    portals = collections.defaultdict(list)
    while second_pass:
        assert len(second_pass) % 2 == 0
        curr_key, cell = second_pass.popitem()

        matches = [(cell, curr_key)]
        row, col = curr_key
        for neighbor_key in get_neighbors(row, col, rows, cols):
            if neighbor_key not in second_pass:
                continue

            neighbor_cell = second_pass.pop(neighbor_key)
            matches.append((neighbor_cell, neighbor_key))

        assert len(matches) == 2, matches
        matches.sort(key=operator.itemgetter(0))
        pair = "".join(match[0] for match in matches)
        nodes = [match[1] for match in matches]

        nearby_traversible = []
        for node in nodes:
            node_row, node_col = node
            for neighbor_key in get_neighbors(node_row, node_col, rows, cols):
                neighbor_row, neighbor_col = neighbor_key
                neighbor_cell = grid[neighbor_row, neighbor_col]
                if neighbor_cell != CAN_TRAVERSE:
                    continue

                nearby_traversible.append(neighbor_key)

        assert len(nearby_traversible) == 1, nearby_traversible
        portals[pair].append(nearby_traversible[0])

    entrance, = portals.pop("AA")
    exit_, = portals.pop("ZZ")

    for portal_nodes in portals.values():
        assert len(portal_nodes) == 2
        in_node, out_node = portal_nodes
        g.add_edge(in_node, out_node)

    print(nx.shortest_path_length(g, entrance, exit_))
    # print(entrance)
    # print(g.size())


if __name__ == "__main__":
    main()
