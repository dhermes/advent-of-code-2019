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
import operator
import pathlib
import uuid

import networkx as nx
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
SCAFFOLD = "#"
OPEN_SPACE = "."
VACUUM_ROBOT_UP = "^"
VACUUM_ROBOT_DOWN = "v"
VACUUM_ROBOT_LEFT = "<"
VACUUM_ROBOT_RIGHT = ">"
VACUUM_ROBOT_POSITIONS = (
    VACUUM_ROBOT_UP,
    VACUUM_ROBOT_DOWN,
    VACUUM_ROBOT_LEFT,
    VACUUM_ROBOT_RIGHT,
)
VACUUM_ROBOT_TUMBLING = "X"
# Main: {A,B,C}...   at most 20 w/o newline
# A: {L,R,0,...,9}... at most 20 w/o newline
# B: {L,R,0,...,9}... at most 20 w/o newline
# C: {L,R,0,...,9}... at most 20 w/o newline
# continuous video feed: {y,n}


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


def part1(program):
    std_input_list = []
    std_input = iter(std_input_list)
    std_output = []
    intcode = Intcode(program, std_input, std_output)
    intcode.run()

    display = "".join(chr(value) for value in std_output)
    display = display.rstrip() + "\n"
    with open(HERE / "part1_output.txt", "w") as file_obj:
        file_obj.write(display)

    rows = display.strip().split("\n")
    assert set(len(row) for row in rows) == set([51])
    grid = np.array([list(row) for row in rows])

    g = nx.Graph()
    rows, cols = grid.shape
    match_rows, match_cols = np.where(grid == SCAFFOLD)
    scaffold_intersections = set()
    for row, col in zip(match_rows, match_cols):
        all_neighors_scaffold = True
        if row > 0 and grid[row - 1, col] == SCAFFOLD:
            g.add_edge((row, col), (row - 1, col))
        else:
            all_neighors_scaffold = False

        if row < rows - 1 and grid[row + 1, col] == SCAFFOLD:
            g.add_edge((row, col), (row + 1, col))
        else:
            all_neighors_scaffold = False

        if col > 0 and grid[row, col - 1] == SCAFFOLD:
            g.add_edge((row, col), (row, col - 1))
        else:
            all_neighors_scaffold = False

        if col < cols - 1 and grid[row, col + 1] == SCAFFOLD:
            g.add_edge((row, col), (row, col + 1))
        else:
            all_neighors_scaffold = False

        if all_neighors_scaffold:
            scaffold_intersections.add((row, col))

    print(sum(row * col for row, col in scaffold_intersections))

    return g, grid


class VacuumRobot:
    def __init__(self, g, grid, direction, position):
        self.std_input = []
        self.std_output = []
        self.index = 0

        self.g = g
        self.grid = grid
        self.direction = direction
        self.position = np.array(position)
        self.visited = set()

    def __iter__(self):
        return self

    def __next__(self):
        curr_index = self.index
        self.index = curr_index + 1
        return self.std_input[curr_index]

    def append(self, value):
        self.std_output.append(value)

    def send_command(self, ascii_str):
        # num_fns = len(movement_fns)
        # partners = [","] * (num_fns - 1) + ["\n"]
        # assert len(partners) == num_fns
        # for movement_fn, partner in zip(movement_fns, partners):
        #     assert movement_fn in ("A", "B", "C", "L", "R")
        #     self.std_input.extend([ord(movement_fn), ord(partner)])
        self.std_input.extend([ord(c) for c in ascii_str])


def find_exact(grid, value):
    match_rows, match_cols = np.where(grid == value)
    if match_rows.size == 0:
        assert match_cols.size == 0
        return None

    assert match_rows.size == match_cols.size == 1
    return match_rows[0], match_cols[0]


def part2(program, g, grid):
    matches = []
    for direction in VACUUM_ROBOT_POSITIONS:
        match = find_exact(grid, direction)
        if match is not None:
            matches.append((direction, match))

    assert len(matches) == 1
    match = matches[0]
    direction, robot_position = match

    # Force the vacuum robot to wake up by changing the value in your ASCII
    # program at address 0 from 1 to 2
    assert program[0] == 1
    program[0] = 2

    robot = VacuumRobot(g, grid, direction, robot_position)
    # A = ("R", 12, "L", 6, "R", 12)  # ZVZ
    # B = ("L", 8, "L", 6, "L", 10)  # WVX
    # C = ("R", 12, "L", 10, "L", 6, "R", 10)  # ZXVY
    robot.send_command("A,B,A,C,B,C,B,C,A,C\n")  # MAIN
    robot.send_command("R,12,L,6,R,12\n")  # A
    robot.send_command("L,8,L,6,L,10\n")  # B
    robot.send_command("R,12,L,10,L,6,R,10\n")  # C
    robot.send_command("n\n")  # video feed
    intcode = Intcode(program, robot, robot)
    intcode.run()

    print(robot.std_output)


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    program = collections.defaultdict(int)
    for index, value in enumerate(content.strip().split(",")):
        program[index] = int(value)

    g, grid = part1(program)
    part2(program, g, grid)


if __name__ == "__main__":
    main()
