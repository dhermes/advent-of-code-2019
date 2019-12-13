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
import copy
import json
import operator
import pathlib
import uuid

import numpy as np


HERE = pathlib.Path(__file__).resolve().parent
OPCODES = {
    1: ("ADD", 3),
    2: ("MULTIPLY", 3),
    3: ("INPUT", 1),
    4: ("OUTPUT", 1),
    5: ("JUMP-IF-TRUE", 2),
    6: ("JUMP-IF-FALSE", 2),
    7: ("LESS-THAN", 3),
    8: ("EQUALS", 3),
    9: ("ADJUST_BASE", 1),
    99: ("HALT", 0),
}
POSITION_MODE = "0"
IMMEDIATE_MODE = "1"
RELATIVE_MODE = "2"
ALL_MODES = set("012")
NO_JUMP_JUMP_INDEX = uuid.uuid4()
TERMINAL_JUMP_INDEX = uuid.uuid4()
TILE_DEFAULT = -1
TILE_BLOCK = 2
TILE_PADDLE = 3
TILE_BALL = 4
TILE_IDS = {
    0: " ",  # "EMPTY"
    1: "#",  # "WALL"
    TILE_BLOCK: "B",  # "BLOCK"
    TILE_PADDLE: "X",  # "PADDLE"
    TILE_BALL: "o",  # "BALL"
}
JOYSTICK_NEUTRAL = 0
JOYSTICK_LEFT = -1
JOYSTICK_RIGHT = 1
NUM_QUARTERS = 2


class AdjustBase:
    def __init__(self, value):
        self.value = value


def less_than_binary_op(value1, value2):
    if value1 < value2:
        to_store = 1
    else:
        to_store = 0

    return to_store


def equal_binary_op(value1, value2):
    if value1 == value2:
        to_store = 1
    else:
        to_store = 0

    return to_store


def get_value(mode, param, relative_base, program):
    if mode == POSITION_MODE:
        index = param
        assert 0 <= index
        return program[index]

    if mode == IMMEDIATE_MODE:
        return param

    if mode == RELATIVE_MODE:
        index = relative_base + param
        assert 0 <= index
        return program[index]

    raise ValueError("Invalid mode", mode)


def set_value(mode, param, to_store, relative_base, program):
    if mode == POSITION_MODE:
        index = param
        assert 0 <= index
        program[index] = to_store
        return

    if mode == RELATIVE_MODE:
        index = relative_base + param
        assert 0 <= index
        program[index] = to_store
        return

    raise ValueError("Invalid mode", mode)


def _do_binary_op(modes, params, relative_base, program, fn):
    mode1, mode2, mode3 = modes
    param1, param2, param3 = params
    value1 = get_value(mode1, param1, relative_base, program)
    value2 = get_value(mode2, param2, relative_base, program)

    to_store = fn(value1, value2)
    set_value(mode3, param3, to_store, relative_base, program)

    return NO_JUMP_JUMP_INDEX


def do_add(modes, params, relative_base, program):
    return _do_binary_op(modes, params, relative_base, program, operator.add)


def do_multiply(modes, params, relative_base, program):
    return _do_binary_op(modes, params, relative_base, program, operator.mul)


def do_input(modes, params, relative_base, program, std_input):
    mode, = modes
    param, = params

    to_store = next(std_input)
    set_value(mode, param, to_store, relative_base, program)

    return NO_JUMP_JUMP_INDEX


def do_output(modes, params, relative_base, program, std_output):
    mode, = modes
    param, = params

    value = get_value(mode, param, relative_base, program)
    std_output.append(value)

    return NO_JUMP_JUMP_INDEX


def _do_jump_unary_predicate(modes, params, relative_base, program, fn):
    mode1, mode2 = modes
    param1, param2 = params

    value1 = get_value(mode1, param1, relative_base, program)
    value2 = get_value(mode2, param2, relative_base, program)

    if fn(value1):
        return value2

    return NO_JUMP_JUMP_INDEX


def do_jump_if_true(modes, params, relative_base, program):
    return _do_jump_unary_predicate(
        modes, params, relative_base, program, operator.truth
    )


def do_jump_if_false(modes, params, relative_base, program):
    return _do_jump_unary_predicate(
        modes, params, relative_base, program, operator.not_
    )


def do_less_than(modes, params, relative_base, program):
    return _do_binary_op(
        modes, params, relative_base, program, less_than_binary_op
    )


def do_equal(modes, params, relative_base, program):
    return _do_binary_op(
        modes, params, relative_base, program, equal_binary_op
    )


def do_adjust_base(modes, params, relative_base, program):
    mode, = modes
    param, = params

    value = get_value(mode, param, relative_base, program)
    return AdjustBase(value)


def do_halt():
    return TERMINAL_JUMP_INDEX


def next_instruction(index, program):
    assert 0 <= index
    op_code_with_extra = program[index]
    assert op_code_with_extra >= 0

    mode_as_int, op_code = divmod(op_code_with_extra, 100)
    instruction, num_params = OPCODES[op_code]
    next_index = index + 1 + num_params
    if num_params == 0:
        assert mode_as_int == 0
        return instruction, (), (), next_index

    mode_chars = str(mode_as_int).zfill(num_params)
    assert len(mode_chars) == num_params, (mode_chars, num_params)
    assert set(mode_chars) <= ALL_MODES
    modes = tuple(reversed(mode_chars))

    params = tuple(program[i] for i in range(index + 1, next_index))
    assert len(params) == num_params  # No partial slice

    return instruction, modes, params, next_index


def execute_instruction(
    instruction, modes, params, relative_base, program, std_input, std_output
):
    if instruction == "ADD":
        return do_add(modes, params, relative_base, program)

    if instruction == "MULTIPLY":
        return do_multiply(modes, params, relative_base, program)

    if instruction == "INPUT":
        return do_input(modes, params, relative_base, program, std_input)

    if instruction == "OUTPUT":
        return do_output(modes, params, relative_base, program, std_output)

    if instruction == "JUMP-IF-TRUE":
        return do_jump_if_true(modes, params, relative_base, program)

    if instruction == "JUMP-IF-FALSE":
        return do_jump_if_false(modes, params, relative_base, program)

    if instruction == "LESS-THAN":
        return do_less_than(modes, params, relative_base, program)

    if instruction == "EQUALS":
        return do_equal(modes, params, relative_base, program)

    if instruction == "ADJUST_BASE":
        return do_adjust_base(modes, params, relative_base, program)

    if instruction == "HALT":
        return do_halt()

    raise ValueError("Bad instruction", instruction, modes, params, program)


def run_intcode(program, std_input, std_output):
    relative_base = 0
    running_program = copy.deepcopy(program)

    jump_index = NO_JUMP_JUMP_INDEX
    index = 0
    while jump_index != TERMINAL_JUMP_INDEX:
        instruction, modes, params, index = next_instruction(
            index, running_program
        )
        jump_index = execute_instruction(
            instruction,
            modes,
            params,
            relative_base,
            running_program,
            std_input,
            std_output,
        )
        if isinstance(jump_index, AdjustBase):
            relative_base += jump_index.value
        elif jump_index in (NO_JUMP_JUMP_INDEX, TERMINAL_JUMP_INDEX):
            # Nothing to do here, all good.
            pass
        elif jump_index >= 0:
            index = jump_index
        else:
            raise ValueError("Invalid jump index", jump_index)

    return running_program


def print_board(board):
    for row in board.T:
        for tile in row:
            print(TILE_IDS[tile], end=" ")
        print("\n", end="")


class Arcade:
    def __init__(self, seed_moves, program):
        self.program = copy.deepcopy(program)
        self.program[0] = NUM_QUARTERS
        self.index = 0
        self.std_input = [value for value in seed_moves]
        self.std_output = []
        self.score = None
        self.board = None
        self.ball_location = None
        self.paddle_location = None
        self.trajectory = None
        self.retired_output = []

    def __iter__(self):
        return self

    def __next__(self):
        curr_index = self.index
        self.index = curr_index + 1
        if self.board is None:
            assert curr_index == 0
            num_tiles, remainder = divmod(len(self.std_output), 3)
            assert remainder == 0
            # Set the score.
            assert self.std_output[-3:] == [-1, 0, 0]
            self.score = 0
            # Determine the board size.
            x_values = self.std_output[:-3:3]
            assert min(x_values) == 0
            width_x = max(x_values) + 1
            y_values = self.std_output[1:-3:3]
            assert min(y_values) == 0
            width_y = max(y_values) + 1
            # Populate the board.
            self.board = TILE_DEFAULT * np.ones((width_x, width_y), dtype=int)
            for i in range(num_tiles - 1):  # Ignore last triple (-1, 0, 1)
                x, y, tile = self.std_output[3 * i : 3 * i + 3]
                assert 0 <= x < width_x
                assert 0 <= y < width_y
                assert tile in TILE_IDS
                if self.board[x, y] != TILE_DEFAULT:
                    raise ValueError(x, y, self.board)
                self.board[x, y] = tile
            # Make sure the board is fully set.
            assert np.all(self.board != TILE_DEFAULT)
            # Set the location of the ball and paddle (and assert exactly one)
            self.ball_location = locate(self.board, TILE_BALL)
            self.paddle_location = locate(self.board, TILE_PADDLE)
            # Reset std_output
            self.reset_std_output()
            # Get the next move
            next_move(self.board, curr_index, self.std_input)
        else:
            new_score = update_board(self.board, self.std_output)
            if new_score is not None:
                self.score = new_score
                # Only print the new score if we are in "USER INPUT" mode.
                if curr_index >= len(self.std_input):
                    print(f"New score: {new_score}")
            self.reset_std_output()
            updated = next_move(self.board, curr_index, self.std_input)
            if updated:
                with open(HERE / "moves.json", "w") as file_obj:
                    json.dump(self.std_input, file_obj, indent=4)
                    file_obj.write("\n")

        return self.std_input[curr_index]

    def append(self, value):
        self.std_output.append(value)

    def reset_std_output(self):
        self.retired_output.append(self.std_output)
        self.std_output = []


def locate(board, tile):
    (x,), (y,) = np.where(board == tile)
    return x, y


def update_board(board, std_output):
    width_x, width_y = board.shape
    size = len(std_output)
    assert size % 3 == 0
    index = 0
    new_score = None
    while index < size:
        next_index = index + 3
        x, y, tile = std_output[index:next_index]
        # For next iteration.
        index = next_index

        if (x, y) == (-1, 0):
            if new_score is None:
                new_score = tile
            else:
                assert tile > new_score
                new_score = tile
            continue

        assert 0 <= x < width_x, (x, y, tile)
        assert 0 <= y < width_y, (x, y, tile)
        assert tile in TILE_IDS
        board[x, y] = tile

    return new_score


def next_move(board, index, std_input):
    if index < len(std_input):
        return False

    print_board(board)
    next_move = input("l/-/r? ")
    if next_move == "l":
        std_input.append(JOYSTICK_LEFT)
        return True

    if next_move == "-":
        std_input.append(JOYSTICK_NEUTRAL)
        return True

    if next_move == "r":
        std_input.append(JOYSTICK_RIGHT)
        return True

    raise ValueError("Invalid input", next_move)


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    program = collections.defaultdict(int)
    for index, value in enumerate(content.strip().split(",")):
        program[index] = int(value)

    std_input_list = []
    std_input = iter(std_input_list)
    std_output = []
    run_intcode(program, std_input, std_output)
    assert len(std_output) % 3 == 0
    tile_ids = std_output[2::3]
    tile_id_counts = collections.Counter(tile_ids)
    print(f"Number of blocks: {tile_id_counts[TILE_BLOCK]}")

    with open(HERE / "moves.json", "r") as file_obj:
        seed_moves = json.load(file_obj)
    arcade = Arcade(seed_moves, program)
    run_intcode(arcade.program, arcade, arcade)
    assert arcade.std_output
    new_score = update_board(arcade.board, arcade.std_output)
    assert new_score is not None
    arcade.score = new_score
    arcade.reset_std_output()

    print(f"Final score: {arcade.score}")


if __name__ == "__main__":
    main()
