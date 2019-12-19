import json


INFINITY = float("INFINITY")


def purview(row, col, left_edges, right_edges, above_edges, below_edges):
    max_col = right_edges[str(row)]
    max_row = below_edges[str(col)]

    for curr_col in range(col + 1, max_col + 1):
        above_row = above_edges[str(curr_col)]
        if above_row > row:
            max_col = curr_col - 1
            break

        below_row = below_edges[str(curr_col)]
        max_row = min(max_row, below_row)

    return max_row - row + 1, max_col - col + 1
    # left_col = left_edges.get(str(row), INFINITY)
    # max_col = right_edges.get(str(row), -INFINITY)
    # left_col = left_edges.get(str(row), INFINITY)
    # max_col = right_edges.get(str(row), -INFINITY)
    # if col < left_col or col > max_col:
    #     raise RuntimeError("Outside of tractor beam")

    # # Go until we find a row that doesn't include ``col``.
    # max_row = row
    # curr_row = row + 1
    # while True:
    #     # TODO: This loop should have an upper bound
    #     left_col = left_edges[curr_row]
    #     if col < left_col:
    #         break

    #     max_row = curr_row
    #     right_col = right_edges[curr_row]
    #     max_col = min(max_col, right_col)
    #     # Set up next iteration.
    #     curr_row += 1

    # return max_row - row + 1, max_col - col + 1


def main():
    with open("day19/X.json", "r") as fh:
        X = json.load(fh)

    left_edges = X["left_edges"]
    right_edges = X["right_edges"]
    above_edges = X["above_edges"]
    below_edges = X["below_edges"]

    rows = sorted(map(int, left_edges.keys()))
    assert rows == sorted(map(int, right_edges.keys()))
    cols = sorted(map(int, above_edges.keys()))
    assert cols == sorted(map(int, below_edges.keys()))

    # row = min(rows)
    # assert row == rows[0]
    # col = left_edges[str(row)]
    # print((row, col, right_edges[str(row)]))
    # p = purview(row, col, left_edges, right_edges, above_edges, below_edges)
    # print(p)
    done = False
    for row in rows:
        start_col = left_edges[str(row)]
        end_col = right_edges[str(row)]
        for col in range(start_col, end_col + 1):
            p = purview(
                row, col, left_edges, right_edges, above_edges, below_edges
            )
            p_row, p_col = p
            if p_row >= 100 and p_col >= 100:
                print((row, col))
                done = True
                break

        if done:
            break


if __name__ == "__main__":
    main()
