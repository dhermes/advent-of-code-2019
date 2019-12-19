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
DEBUG = True
INFINITY = float("infinity")


def debug(value, **kwargs):
    if not DEBUG:
        return
    print(value, **kwargs)


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


class Intcode:
    def __init__(self, program, std_input, std_output):
        self.running_program = copy.deepcopy(program)
        self.std_input = std_input
        self.std_output = std_output

        self.relative_base = 0
        self.index = 0
        self.done = False

    def advance_one(self):
        assert not self.done

        instruction, modes, params, index = next_instruction(
            self.index, self.running_program
        )
        jump_index = execute_instruction(
            instruction,
            modes,
            params,
            self.relative_base,
            self.running_program,
            self.std_input,
            self.std_output,
        )
        if isinstance(jump_index, AdjustBase):
            self.relative_base += jump_index.value
        elif jump_index in (NO_JUMP_JUMP_INDEX, TERMINAL_JUMP_INDEX):
            # Nothing to do here, all good.
            pass
        elif jump_index >= 0:
            index = jump_index
        else:
            raise ValueError("Invalid jump index", jump_index)

        self.index = index
        self.done = jump_index == TERMINAL_JUMP_INDEX

    def run(self):
        while not self.done:
            self.advance_one()


def in_tractor_beam(program, row, col):
    std_input_list = [row, col]
    std_input = iter(std_input_list)
    std_output = []
    intcode = Intcode(program, std_input, std_output)
    intcode.run()

    predicate, = std_output
    return predicate


def find_edges(program, row, left_guess, right_guess):
    left_col = left_guess
    right_col = right_guess

    # Move left until we are **for sure** outside.
    yes_left = in_tractor_beam(program, row, left_col)
    while yes_left:
        left_col -= 5
        assert left_col > 0
        yes_left = in_tractor_beam(program, row, left_col)

    # Now that we are outside the left edge, start incrementing by 1.
    while not yes_left:
        left_col += 1
        yes_left = in_tractor_beam(program, row, left_col)

    # Move right until we are **for sure** outside.
    yes_right = in_tractor_beam(program, row, right_col)
    while yes_right:
        # NOTE: This **SHOULD** have a bounded number of iterations
        right_col += 5
        yes_right = in_tractor_beam(program, row, right_col)

    # Now that we are outside the right edge, start decrementing by 1.
    while not yes_right:
        right_col -= 1
        yes_right = in_tractor_beam(program, row, right_col)

    return left_col, right_col


def find_edges_vertical(program, col, above_guess, below_guess):
    above_row = above_guess
    below_row = below_guess

    # Move above until we are **for sure** outside.
    yes_above = in_tractor_beam(program, above_row, col)
    while yes_above:
        above_row -= 5
        assert above_row > 0
        yes_above = in_tractor_beam(program, above_row, col)

    # Now that we are outside the above edge, start incrementing by 1.
    while not yes_above:
        above_row += 1
        yes_above = in_tractor_beam(program, above_row, col)

    # Move below until we are **for sure** outside.
    yes_below = in_tractor_beam(program, below_row, col)
    while yes_below:
        # NOTE: This **SHOULD** have a bounded number of iterations
        below_row += 5
        yes_below = in_tractor_beam(program, below_row, col)

    # Now that we are outside the below edge, start decrementing by 1.
    while not yes_below:
        below_row -= 1
        yes_below = in_tractor_beam(program, below_row, col)

    return above_row, below_row


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    program = collections.defaultdict(int)
    for index, value in enumerate(content.strip().split(",")):
        program[index] = int(value)

    # grid = np.zeros((50, 50), dtype=int)
    # for row in range(50):
    #     for col in range(50):
    #         grid[row, col] = in_tractor_beam(program, row, col)

    # # print(grid)
    # print(np.sum(grid))
    # # print(np.count_nonzero(grid))

    # left_edge = []
    # right_edge = []
    # for row in range(50):
    #     in_beam_indices, = np.where(grid[row, :] == 1)
    #     if in_beam_indices.size == 0:
    #         continue
    #     left_col = in_beam_indices[0]
    #     right_col = in_beam_indices[-1]
    #     assert np.all(in_beam_indices == np.arange(left_col, right_col + 1))
    #     left_edge.append((row, left_col))
    #     right_edge.append((row, right_col))

    # left_edge = np.array(left_edge)
    # coeffs, residuals, _, _, _ = np.polyfit(
    #     left_edge[:, 0], left_edge[:, 1], 1, full=True
    # )
    # residual_left, = residuals
    # coeff_row_left, const_left = coeffs

    # right_edge = np.array(right_edge)
    # coeffs, residuals, _, _, _ = np.polyfit(
    #     right_edge[:, 0], right_edge[:, 1], 1, full=True
    # )
    # residual_right, = residuals
    # coeff_row_right, const_right = coeffs
    # print((coeff_row_left, const_left, residual_left))
    # print((coeff_row_right, const_right, residual_right))

    # display = {0: " ", 1: "#"}
    # img = "\n".join("".join(display[value] for value in row) for row in grid)
    # print(img)

    # row = 543
    # left_col = 395
    # yes_left = in_tractor_beam(program, row, left_col)
    # assert not yes_left
    # while not yes_left:
    #     left_col += 1
    #     yes_left = in_tractor_beam(program, row, left_col)

    # right_col = 500
    # yes_right = in_tractor_beam(program, row, right_col)
    # assert not yes_right
    # while not yes_right:
    #     right_col -= 1
    #     yes_right = in_tractor_beam(program, row, right_col)

    # print((row, left_col, right_col))
    # # for col in range(395, 405):
    # #     print((row, col, in_tractor_beam(program, row, col)))
    # # for col in range(495, 505):
    # #     print((row, col, in_tractor_beam(program, row, col)))

    # BEGIN: DJH row
    row = 530
    left_col = 395
    right_col = 500
    left_edges = {}
    right_edges = {}
    min_col = 388  # INFINITY
    max_col = 915  # -INFINITY
    grid = np.empty((470, 528), dtype=str)
    grid.fill(" ")
    for row in range(530, 1000):
        left_col, right_col = find_edges(program, row, left_col, right_col)
        grid[row - 530, left_col - min_col : right_col - min_col + 1] = "#"
        # min_col = min(min_col, left_col)
        # max_col = max(max_col, right_col)
        assert left_col >= min_col
        assert right_col <= max_col
        width = right_col - left_col + 1
        # print(f"{row} -> {width}")
        if width < 100:
            continue
        left_edges[row] = left_col
        right_edges[row] = right_col

    # print((min_col, max_col))
    img = "\n".join("".join(value for value in row) for row in grid)
    with open(HERE / "img.txt", "w") as fh:
        fh.write(img)
    # END: DJH row

    # BEGIN: DJH col
    above_row = 368
    below_row = 470
    above_edges = {}
    below_edges = {}
    min_row = 371  # INFINITY
    max_row = 1252  # -INFINITY
    for col in range(340, 916):
        above_row, below_row = find_edges_vertical(
            program, col, above_row, below_row
        )
        # min_row = min(min_row, above_row)
        # max_row = max(max_row, below_row)
        assert above_row >= min_row
        assert below_row <= max_row
        height = below_row - above_row + 1
        # print(f"{col} -> {height}")
        if height < 100:
            continue
        above_edges[col] = above_row
        below_edges[col] = below_row
    # END: DJH col

    # print((min_row, max_row))
    # img = "\n".join("".join(value for value in row) for row in grid)
    # with open(HERE / "img.txt", "w") as fh:
    #     fh.write(img)
    X = {
        "left_edges": left_edges,
        "right_edges": right_edges,
        "above_edges": above_edges,
        "below_edges": below_edges,
    }
    with open(HERE / "X.json", "w") as fh:
        json.dump(X, fh)


if __name__ == "__main__":
    main()
