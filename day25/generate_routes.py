import itertools
import json
import pathlib

import networkx as nx


HERE = pathlib.Path(__file__).resolve().parent


def powerset(values):
    num_values = len(values)
    return itertools.chain.from_iterable(
        itertools.combinations(values, subset_size)
        for subset_size in range(num_values + 1)
    )


def main():
    g = nx.Graph()
    g.add_edges_from(
        (
            ("a", "b"),
            ("a", "c"),
            ("b", "d"),
            ("b", "e"),
            ("d", "f"),
            ("f", "g"),
            ("e", "h"),
            ("c", "i"),
            ("c", "j"),
            ("i", "k"),
            ("i", "l"),
            ("k", "m"),
            ("m", "n"),
            ("m", "o"),
            ("l", "p"),
            ("p", "q"),
            ("j", "r"),
            ("r", "s"),
            ("r", "t"),
            ("b", "a"),
            ("c", "a"),
            ("d", "b"),
            ("e", "b"),
            ("f", "d"),
            ("g", "f"),
            ("h", "e"),
            ("i", "c"),
            ("j", "c"),
            ("k", "i"),
            ("l", "i"),
            ("m", "k"),
            ("n", "m"),
            ("o", "m"),
            ("p", "l"),
            ("q", "p"),
            ("r", "j"),
            ("s", "r"),
            ("t", "r"),
        )
    )
    items = {
        # BAD
        "d": "photons",
        "e": "escape pod",
        "h": "molten lava",
        "n": "giant electromagnet",
        "o": "infinite loop",
        # GOOD
        "b": "wreath",
        "c": "loom",
        "i": "ornament",
        "j": "fixed point",
        "p": "candy cane",
        "r": "spool of cat6",
        "s": "weather machine",
        "t": "shell",
    }
    g_directions = {
        ("a", "b"): "north",
        ("a", "c"): "east",
        ("b", "d"): "north",
        ("b", "e"): "east",
        ("d", "f"): "east",
        ("f", "g"): "south",
        ("e", "h"): "east",
        ("c", "i"): "south",
        ("c", "j"): "east",
        ("i", "k"): "east",
        ("i", "l"): "west",
        ("k", "m"): "south",
        ("m", "n"): "south",
        ("m", "o"): "east",
        ("l", "p"): "north",
        ("p", "q"): "north",
        ("j", "r"): "north",
        ("r", "s"): "north",
        ("r", "t"): "west",
        ("b", "a"): "south",
        ("c", "a"): "west",
        ("d", "b"): "south",
        ("e", "b"): "west",
        ("f", "d"): "west",
        ("g", "f"): "north",
        ("h", "e"): "west",
        ("i", "c"): "north",
        ("j", "c"): "west",
        ("k", "i"): "west",
        ("l", "i"): "east",
        ("m", "k"): "north",
        ("n", "m"): "north",
        ("o", "m"): "west",
        ("p", "l"): "south",
        ("q", "p"): "south",
        ("r", "j"): "south",
        ("s", "r"): "south",
        ("t", "r"): "east",
    }
    good_nodes = ("b", "c", "i", "j", "p", "r", "s", "t")

    all_possible = []
    subset_index = 0
    for node_subset in powerset(good_nodes):
        curr_node = "a"
        route = [curr_node]
        remaining = set(node_subset)
        while remaining:
            next_node = remaining.pop()
            path = nx.shortest_path(g, curr_node, next_node)
            route.extend(path[1:])
            # Remove any nodes that we pick up along the way
            for also_node in remaining.intersection(path):
                remaining.remove(also_node)
            # Update the current node for the next loop iteration
            curr_node = next_node

        next_node = "g"
        path = nx.shortest_path(g, curr_node, next_node)
        route.extend(path[1:])

        # Make sure to pick them all up.
        for node in node_subset:
            item = items[node]
            index = route.index(node)
            route = route[: index + 1] + [f"take {item}"] + route[index + 1 :]

        commands = []
        # for prev_node, curr_node in zip(route, route[1:]):
        route_size = len(route)
        for i in range(1, route_size):
            prev_node = route[i - 1]
            curr_node = route[i]
            if curr_node.startswith("take "):
                commands.append(curr_node)
                continue
            if prev_node.startswith("take "):
                assert i >= 2
                prev_node = route[i - 2]

            key = (prev_node, curr_node)
            direction = g_directions[key]
            commands.append(direction)

        all_possible.append(
            {
                "route": route,
                "commands": commands,
                "subset_index": subset_index,
            }
        )
        # For the next loop
        subset_index += 1  # Should just use ``enumerate()``

    with open(HERE / "all_possible.json", "w") as file_obj:
        json.dump(all_possible, file_obj, indent=4)
        file_obj.write("\n")


if __name__ == "__main__":
    main()
