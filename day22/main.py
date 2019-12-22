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


HERE = pathlib.Path(__file__).resolve().parent
NUM_CARDS = 10007


def do_move_new_stack(cards):
    return cards[::-1]


def do_move_cut(cards, cut):
    return cards[cut:] + cards[:cut]


def do_move_increment(cards, increment):
    num_cards = len(cards)
    new_cards = [None] * num_cards
    assert increment > 0

    index = 0
    for i in range(num_cards):
        assert new_cards[index] is None
        new_cards[index] = cards[i]
        index = (index + increment) % num_cards

    assert None not in new_cards
    return new_cards


def do_move(cards, line):
    if line == "deal into new stack":
        return do_move_new_stack(cards)

    if line.startswith("deal with increment "):
        increment = int(line[20:])
        return do_move_increment(cards, increment)

    if line.startswith("cut "):
        cut = int(line[4:])
        return do_move_cut(cards, cut)

    raise NotImplementedError(line)


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    cards = list(range(NUM_CARDS))
    lines = content.strip().split("\n")
    for line in lines:
        cards = do_move(cards, line)

    print(cards.index(2019))


if __name__ == "__main__":
    main()

# https://adventofcode.com/2019/day/21/input
