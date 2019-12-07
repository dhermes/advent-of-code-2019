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

import networkx as nx


HERE = pathlib.Path(__file__).resolve().parent
COM = "COM"


def get_parent(g, node):
    if node == COM:
        return None

    predecessors = list(g.predecessors(node))
    if len(predecessors) != 1:
        raise ValueError("Unexpected parents", g, node, predecessors)
    return predecessors[0]


def all_predecessors(g, node):
    if node == COM:
        return []

    parents = []
    parent = get_parent(g, node)
    while parent is not None:
        parents.append(parent)
        parent = get_parent(g, parent)

    return parents


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    g = nx.DiGraph()
    for pair in content.strip().split("\n"):
        parent_name, name = pair.split(")")
        g.add_edge(parent_name, name)

    count = 0
    for node in g.nodes:
        count += len(all_predecessors(g, node))

    print(count)

    you_predecessors = all_predecessors(g, "YOU")[::-1]
    san_predecessors = all_predecessors(g, "SAN")[::-1]
    shared_you = [
        i
        for i, value in enumerate(you_predecessors)
        if value in san_predecessors
    ]
    assert shared_you == list(range(min(shared_you), max(shared_you) + 1))
    shared_san = [
        i
        for i, value in enumerate(san_predecessors)
        if value in you_predecessors
    ]
    assert shared_san == shared_you
    you_moves = len(you_predecessors[max(shared_you) :]) - 1
    san_moves = len(san_predecessors[max(shared_you) :]) - 1
    print(you_moves + san_moves)


if __name__ == "__main__":
    main()
