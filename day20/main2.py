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
import itertools
import operator
import pathlib

import networkx as nx
import numpy as np


HERE = pathlib.Path(__file__).resolve().parent
VOID = (" ", "#")
CAN_TRAVERSE = "."
INFINITY = float("infinity")


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


def in_graphs(node, graphs):
    return any(node in g for g in graphs)


def locate_graph(node, graphs):
    match, = [i for i, gg in graphs.items() if node in gg]
    return match


def can_reach_exit(level, gg_id, exit_graph):
    if level != 0:
        return False

    return gg_id == exit_graph


def is_outside(node, rows, cols):
    row, col = node
    if row in (0, 1, rows - 2, rows - 1):
        return True

    return col in (0, 1, cols - 2, cols - 1)


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    if False:
        content = """\
         A        |
         A        |
  #######.#########
  #######.........#
  #######.#######.#
  #######.#######.#
  #######.#######.#
  #####  B    ###.#
BC...##  C    ###.#
  ##.##       ###.#
  ##...DE  F  ###.#
  #####    G  ###.#
  #########.#####.#
DE..#######...###.#
  #.#########.###.#
FG..#########.....#
  ###########.#####
             Z    |
             Z    |
"""
    if False:
        content = """\
                   A              |
                   A              |
  #################.############# |
  #.#...#...................#.#.# |
  #.#.#.###.###.###.#########.#.# |
  #.#.#.......#...#.....#.#.#...# |
  #.#########.###.#####.#.#.###.# |
  #.............#.#.....#.......# |
  ###.###########.###.#####.#.#.# |
  #.....#        A   C    #.#.#.# |
  #######        S   P    #####.# |
  #.#...#                 #......VT
  #.#.#.#                 #.##### |
  #...#.#               YN....#.# |
  #.###.#                 #####.# |
DI....#.#                 #.....# |
  #####.#                 #.###.# |
ZZ......#               QG....#..AS
  ###.###                 ####### |
JO..#.#.#                 #.....# |
  #.#.#.#                 ###.#.# |
  #...#..DI             BU....#..LF
  #####.#                 #.##### |
YN......#               VT..#....QG
  #.###.#                 #.###.# |
  #.#...#                 #.....# |
  ###.###    J L     J    #.#.### |
  #.....#    O F     P    #.#...# |
  #.###.#####.#.#####.#####.###.# |
  #...#.#.#...#.....#.....#.#...# |
  #.#####.###.###.#.#.#########.# |
  #...#.#.....#...#.#.#.#.....#.# |
  #.###.#####.###.###.#.#.####### |
  #.#.........#...#.............# |
  #########.###.###.############# |
           B   J   C              |
           U   P   P              |
"""
    if False:
        content = """\
             Z L X W       C                |
             Z P Q B       K                |
  ###########.#.#.#.#######.############### |
  #...#.......#.#.......#.#.......#.#.#...# |
  ###.#.#.#.#.#.#.#.###.#.#.#######.#.#.### |
  #.#...#.#.#...#.#.#...#...#...#.#.......# |
  #.###.#######.###.###.#.###.###.#.####### |
  #...#.......#.#...#...#.............#...# |
  #.#########.#######.#.#######.#######.### |
  #...#.#    F       R I       Z    #.#.#.# |
  #.###.#    D       E C       H    #.#.#.# |
  #.#...#                           #...#.# |
  #.###.#                           #.###.# |
  #.#....OA                       WB..#.#..ZH
  #.###.#                           #.#.#.# |
CJ......#                           #.....# |
  #######                           ####### |
  #.#....CK                         #......IC
  #.###.#                           #.###.# |
  #.....#                           #...#.# |
  ###.###                           #.#.#.# |
XF....#.#                         RF..#.#.# |
  #####.#                           ####### |
  #......CJ                       NM..#...# |
  ###.#.#                           #.###.# |
RE....#.#                           #......RF
  ###.###        X   X       L      #.#.#.# |
  #.....#        F   Q       P      #.#.#.# |
  ###.###########.###.#######.#########.### |
  #.....#...#.....#.......#...#.....#.#...# |
  #####.#.###.#######.#######.###.###.#.#.# |
  #.......#.......#.#.#.#.#...#...#...#.#.# |
  #####.###.#####.#.#.#.#.###.###.#.###.### |
  #.......#.....#.#...#...............#...# |
  #############.#.#.###.################### |
               A O F   N                    |
               A A D   M                    |
"""

    lines = content.replace("|", " ").split("\n")
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

    graphs = {
        i: gg for i, gg in enumerate(nx.connected_component_subgraphs(g))
    }

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

        nearby_node, = nearby_traversible
        nodes_outside = [is_outside(node, rows, cols) for node in nodes]
        if all(nodes_outside):
            # Outside portals go "down" a level
            level_delta = -1
        else:
            # Inside portals go "up" a level
            level_delta = 1
            assert nodes_outside == [False, False], (
                matches,
                rows,
                cols,
                nodes,
            )

        portals[pair].append((nearby_node, level_delta))

    (entrance, _), = portals.pop("AA")
    (exit_, _), = portals.pop("ZZ")

    entrance_graph = locate_graph(entrance, graphs)
    print(f"entrance: {entrance}")
    print(f"entrance_graph: {entrance_graph}")
    exit_graph = locate_graph(exit_, graphs)
    print(f"exit_: {exit_}")
    print(f"exit_graph: {exit_graph}")

    jump_points_by_graph = collections.defaultdict(set)
    jump_points_by_graph[entrance_graph].add((entrance, None))
    jump_points_by_graph[exit_graph].add((exit_, None))
    graph_portals = collections.defaultdict(dict)
    for portal_nodes in portals.values():
        (node1, level_delta1), (node2, level_delta2) = portal_nodes
        node1_graph = locate_graph(node1, graphs)
        node2_graph = locate_graph(node2, graphs)
        assert node1_graph != node2_graph

        jump_points_by_graph[node1_graph].add((node1, level_delta1))
        jump_points_by_graph[node2_graph].add((node2, level_delta2))

        jump_to = graph_portals[node1_graph]
        assert node1 not in jump_to
        jump_to[node1] = node2_graph, node2
        jump_to = graph_portals[node2_graph]
        assert node2 not in jump_to
        jump_to[node2] = node1_graph, node1

    within_graph_moves = {}
    for gg_id, nodes_with_delta in jump_points_by_graph.items():
        nodes = [node for node, _ in nodes_with_delta]
        assert len(nodes) >= 2
        gg = graphs[gg_id]
        for node1, node2 in itertools.combinations(nodes, 2):
            distance = nx.shortest_path_length(gg, node1, node2)
            key1 = (node1, node2)
            key2 = (node2, node1)
            if key1 in within_graph_moves:
                assert within_graph_moves[key1] == distance
            else:
                within_graph_moves[key1] = distance
            if key2 in within_graph_moves:
                assert within_graph_moves[key2] == distance
            else:
                within_graph_moves[key2] = distance

    # graph_id, node, level, distance
    shortest_distance = INFINITY
    locations = [(entrance_graph, entrance, 0, 0)]
    for index in range(10000):
        print(f"{index} -> {len(locations)}")
        new_locations = []

        for location in locations:
            gg_id, node, level, distance = location
            gg = graphs[gg_id]
            # 0. If ``jump`` is even, try to exit
            if can_reach_exit(level, gg_id, exit_graph):
                pair = node, exit_
                assert node in gg  # Sanity
                assert exit_ in gg  # Sanity
                jump_distance = within_graph_moves[pair]
                new_distance = distance + jump_distance
                if new_distance < shortest_distance:
                    msg = (
                        f"shortest_distance: {new_distance} (replacing "
                        f"{shortest_distance})"
                    )
                    print(msg)
                    shortest_distance = new_distance

                continue

            # 1. Find all **other** jump points in ``gg`` via ``jump_points_by_graph``
            for other_node, level_delta in jump_points_by_graph[gg_id]:
                if other_node in (node, entrance, exit_):
                    continue
                # 2. Use ``within_graph_moves`` to get distances to those points
                pair = node, other_node
                jump_distance = within_graph_moves[pair]
                new_distance = distance + jump_distance
                new_level = level + level_delta
                if level < 0:
                    # This step is invalid because we cannot go negative.
                    continue
                # 3. Use ``graph_portals`` to actually jump (add 1 step)
                new_gg_id, new_node = graph_portals[gg_id][other_node]
                new_distance += 1
                # 4. Give up when distance exceeds established minimum
                if new_distance < shortest_distance:
                    new_locations.append(
                        (new_gg_id, new_node, new_level, new_distance)
                    )
                else:
                    print(f"Rejected {new_distance}")

        # Update for next iteration.
        locations = new_locations
        if not locations:
            break

    print(f"shortest_distance: {shortest_distance}")


#     pre_jump = []
#     for location in locations:
#         gg_id, node, distance = location
#         gg = graphs[gg_id]
#         jump_points = jump_points_by_graph[gg_id]
#         for jump_graph, jump_node in jump_points:
#             jump_distance = nx.shortest_path_length(gg, node, jump_node)
#             new_distance = distance + jump_distance
#             pre_jump.append((jump_graph, jump_node, new_distance))

#     if True:
#         breakpoint()
#         raise RuntimeError

#     print(f"jump: {jump}")

# levels = collections.defaultdict(list)
# graphs = list(nx.connected_component_subgraphs(g))
# component, = [gg for gg in graphs if entrance in gg]
# levels[0] = [component]
# graphs.remove(component)

# level = 0
# cross_level = {}
# while portals:
#     print(f"level: {level}")
#     keys_matched = []
#     for key, portal_nodes in portals.items():
#         assert len(portal_nodes) == 2
#         on_level = [
#             node for node in portal_nodes if in_graphs(node, levels[level])
#         ]
#         if not on_level:
#             continue

#         keys_matched.append(key)

#         same_side, = on_level
#         other_side, = [node for node in portal_nodes if node != same_side]
#         # Find the component containing the ``other_side``
#         components = [gg for gg in graphs if other_side in gg]
#         if len(components) == 0:
#             raise NotImplementedError

#         component, = components
#         if component not in levels[level + 1]:
#             levels[level + 1].append(component)
#             graphs.remove(component)

#     # print(f"keys_matched: {keys_matched}")
#     for key in keys_matched:
#         node1, node2 = portals.pop(key)
#         assert node1 not in cross_level
#         cross_level[node1] = node2

#     # print(f"cross_level: {cross_level}")
#     level += 1

# keys_matched = []
# for key, portal_nodes in portals.items():
#     assert len(portal_nodes) == 2
#     on_level = [
#         node for node in portal_nodes if in_graphs(node, levels[0])
#     ]
#     if not on_level:
#         continue

#     keys_matched.append(key)

#     same_side, = on_level
#     other_side, = [node for node in portal_nodes if node != same_side]
#     # Find the component containing the ``other_side``
#     component, = [gg for gg in graphs if other_side in gg]
#     if component not in levels[1]:
#         levels[1].append(component)
#         graphs.remove(component)

# print(keys_matched)
# assert exit_ in levels[0]

# for portal_nodes in portals.values():
#     assert len(portal_nodes) == 2
#     in_node, out_node = portal_nodes
#     # g.add_edge(in_node, out_node)

# print(nx.shortest_path_length(g, entrance, exit_))
# # print(entrance)
# # print(g.size())


if __name__ == "__main__":
    main()

# Just need an even number of jumps
# (Pdb) {k: v for k, v in graph_portals.items() if len(v) != 2}
# {12: {(65, 98), (61, 132), (59, 132), (63, 98)}}
# (Pdb) entrance
# (55, 2)
# (Pdb) exit_
# (124, 67)
