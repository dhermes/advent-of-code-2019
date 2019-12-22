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

import bisect
import pathlib


HERE = pathlib.Path(__file__).resolve().parent
NUM_CARDS = 119315717514047


def transform_index_new_stack(index):
    return (NUM_CARDS - 1) - index


def transform_index_cut(index, cut):
    # 3
    # 3, ..., N - 1, 0, 1, 2
    # WAS
    # 0, ...., N,
    return (index - cut) % NUM_CARDS


# 0 1 2 3 4 5 6 7 8 9
# 0 3 6 9 2 5 8 1 4 7
# 0 7 4 1 8 5 2 9 6 3
#
# (0 + 3 * 4) % 10 --> 2
# (2 + 3 * 3) % 10 --> 1

# [0, 3, 5, 1, 4, 6, 2, 5, 7, 3]

# 0 mod 3 --> (10 - 1) // 3 + 1 = 3 values
CACHE = {}


def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)


def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception("modular inverse does not exist")
    else:
        return x % m


def transform_index_increment(index, increment):
    # (increment * k) % NUM_CARDS --> index
    # # SOLVE increment * k == index mod NUM_CARDS
    inverse = modinv(increment, NUM_CARDS)
    return (index * inverse) % NUM_CARDS
    # assert increment > 0
    # if increment not in CACHE:
    #     boundaries = [0]
    #     residues = [0]
    #     for _ in range(increment - 1):
    #         curr_residue = residues[-1]
    #         num_values = (NUM_CARDS - 1 - curr_residue) // increment + 1

    #         new_boundary = boundaries[-1] + num_values
    #         boundaries.append(new_boundary)

    #         new_residue = (curr_residue + increment * num_values) % NUM_CARDS
    #         assert 0 <= new_residue < increment, (
    #             new_residue,
    #             increment,
    #             boundaries,
    #             residues,
    #         )
    #         assert new_residue not in residues, (
    #             new_residue,
    #             increment,
    #             boundaries,
    #             residues,
    #         )
    #         residues.append(new_residue)

    #     CACHE[increment] = boundaries, residues

    # boundaries, residues = CACHE[increment]
    # X = [bisect.bisect(boundaries, ii) for ii in range(10)]
    # where = bisect.bisect(boundaries, index)
    # assert where >= 1
    # before_boundary = boundaries[where - 1]
    # assert before_boundary <= index
    # if where < len(boundaries):
    #     assert index < boundaries[where]
    # within_index = index - before_boundary
    # before_residue = residues[where - 1]
    # return before_residue + increment * within_index
    # # # 0 mod increment -->
    # # within_residue, residue = divmod(index, increment)

    # base_index = 0
    # for before_residue in range(residue):
    #     num_values = (NUM_CARDS - 1 - before_residue) // increment
    #     base_index += num_values

    # return base_index + within_residue

    # (NUM_CARDS - 1 - residue)
    # 0 mod (increment) --> FIRST GROUP
    # 1 mod (increment) --> SECOND GROUP

    # E.g. 6 mod 3 == 0 --> (0, 1, 2, 3)
    # 6 = 2 * 3 + 0
    # E.g. 6 mod 3 == 0 --> (0, 1, 2, 3)
    # 6 = 2 * 3 + 0

    raise NotImplementedError(within_residue, residue)
    # num_cards = len(cards)
    # new_cards = [None] * num_cards

    # index = 0
    # for i in range(num_cards):
    #     assert new_cards[index] is None
    #     new_cards[index] = cards[i]
    #     index = (index + increment) % num_cards

    # assert None not in new_cards
    # return new_cards


def transform_index(cards, line):
    if line == "deal into new stack":
        return transform_index_new_stack(cards)

    if line.startswith("deal with increment "):
        increment = int(line[20:])
        return transform_index_increment(cards, increment)

    if line.startswith("cut "):
        cut = int(line[4:])
        return transform_index_cut(cards, cut)

    raise NotImplementedError(line)


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    index = 2020
    lines = content.strip().split("\n")
    for line in lines[::-1]:
        index = transform_index(index, line)

    print(index)


if __name__ == "__main__":
    main()

# https://adventofcode.com/2019/day/21/input

# 5136534201680
