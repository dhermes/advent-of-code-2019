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
import pickle
import random
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
MOVEMENT_NORTH = 1
MOVEMENT_SOUTH = 2
MOVEMENT_WEST = 3
MOVEMENT_EAST = 4
MOVEMENTS = {
    MOVEMENT_NORTH: np.array([0, 1]),  # North
    MOVEMENT_SOUTH: np.array([0, -1]),  # South
    MOVEMENT_WEST: np.array([-1, 0]),  # West
    MOVEMENT_EAST: np.array([1, 0]),  # East
}
STATUS_CODE_WALL = 0
STATUS_CODE_CAN_TRAVERSE = 1
STATUS_CODE_OXYGEN_SYSTEM = 2
WALL = "#"
CAN_TRAVERSE = "."
OXYGEN_SYSTEM = "S"
DROID = "D"
UNKNOWN = " "
DEBUG = False  # True
MAX_ITERATIONS = 2000000


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


class RepairDroid:
    def __init__(self):
        self.location = np.array([0, 0])
        self.pending = None
        self.map = {tuple(self.location): CAN_TRAVERSE}
        self.oxygen_system_location = None
        self.direction = MOVEMENT_NORTH
        # Grid information for pretty-printing.
        self.min_x = 0
        self.min_y = 0
        self.max_x = 0
        self.max_y = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.pending = MOVEMENTS[self.direction]
        return self.direction

    def append(self, status_code):
        assert self.pending is not None
        # Handle the information about the pending move.
        new_location = self.location + self.pending
        self.update_grid_information(new_location)
        key = tuple(new_location)
        if status_code == STATUS_CODE_WALL:
            self.map[key] = WALL
        elif status_code == STATUS_CODE_CAN_TRAVERSE:
            self.map[key] = CAN_TRAVERSE
            self.location = new_location
        elif status_code == STATUS_CODE_OXYGEN_SYSTEM:
            self.map[key] = OXYGEN_SYSTEM
            self.location = new_location

            if self.oxygen_system_location is None:
                self.oxygen_system_location = new_location
                debug(
                    f"x: [{self.min_x}, {self.max_x}], "
                    f"y: [{self.min_y}, {self.max_y}]"
                )
            else:
                assert np.all(self.oxygen_system_location == new_location), (
                    self.oxygen_system_location,
                    new_location,
                )
        else:
            raise ValueError("Invalid status code", status_code)

        # NOTE: This must be called **after** updating ``location``.
        self.update_direction()
        # Reset pending since the move has been applied.
        self.pending = None

    def update_grid_information(self, location):
        x, y = location
        self.min_x = min(self.min_x, x)
        self.max_x = max(self.max_x, x)
        self.min_y = min(self.min_y, y)
        self.max_y = max(self.max_y, y)

    def display(self):
        droid_at = tuple(self.location)
        width = self.max_x - self.min_x + 1
        assert width > 0
        header_footer = "+" + "-" * width + "+"
        print(header_footer)

        for y in range(self.min_y, self.max_y + 1):
            print("|", end="")
            for x in range(self.min_x, self.max_x + 1):
                key = (x, y)
                if key == droid_at:
                    print(DROID, end="")
                    continue

                value = self.map.get(key, UNKNOWN)
                print(value, end="")
            # Go next row.
            print("|\n", end="")

        print(header_footer)

    def to_unknown_neighbor(self):
        directions = []
        for direction, delta in MOVEMENTS.items():
            key = tuple(self.location + delta)
            if key not in self.map:
                directions.append(direction)

        if not directions:
            return None

        # value_up = self.map.get(key_up)
        # value_right = self.map.get(key_right)
        # value_down = self.map.get(key_down)
        # value_left = self.map.get(key_left)
        debug(f"Direction choices (to unknown): {directions}")
        return directions[0]

    def to_valid_neighbor(self):
        directions = []
        for direction, delta in MOVEMENTS.items():
            key = tuple(self.location + delta)
            # A key error here would mean the caller did not verify that
            # all neighbors are in the map.
            if self.map[key] != WALL:
                directions.append(direction)

        if not directions:
            raise ValueError("All neighbors are walls")

        debug(f"Direction choices (to valid): {directions}")
        return random.choice(directions)

    def update_direction(self):
        direction = self.to_unknown_neighbor()
        if direction is None:
            direction = self.to_valid_neighbor()

        self.direction = direction
        debug(f"New direction: {self.direction}")


def part1(droid):
    g = nx.Graph()
    for key, cell_type in droid.map.items():
        if cell_type == WALL:
            continue
        location = np.array(key)
        for delta in MOVEMENTS.values():
            neighbor_key = tuple(location + delta)
            neighbor_cell_type = droid.map.get(neighbor_key)
            if neighbor_cell_type not in (CAN_TRAVERSE, OXYGEN_SYSTEM):
                continue

            g.add_edge(key, neighbor_key)

    oxygen_system_location = tuple(droid.oxygen_system_location)
    print(nx.shortest_path_length(g, (0, 0), oxygen_system_location))


def has_unknown_cells(droid):
    for key, cell_type in droid.map.items():
        if cell_type == WALL:
            continue

        location = np.array(key)
        for delta in MOVEMENTS.values():
            neighbor_key = tuple(location + delta)
            if neighbor_key not in droid.map:
                return True

    return False


def main():
    # Make this computation deterministic, since we randomly choose neighbors.
    random.seed(9701239824)

    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    program = collections.defaultdict(int)
    for index, value in enumerate(content.strip().split(",")):
        program[index] = int(value)

    pickle_file = HERE / "intcode.pkl"
    if pickle_file.exists():
        with open(pickle_file, "rb") as file_obj:
            intcode = pickle.load(file_obj)

        assert isinstance(intcode, Intcode)
        droid = intcode.std_input
        assert intcode.std_output is droid
        assert isinstance(droid, RepairDroid)
    else:
        droid = RepairDroid()
        intcode = Intcode(program, droid, droid)
        while droid.oxygen_system_location is None:
            intcode.advance_one()

        assert droid.oxygen_system_location is not None
        with open(pickle_file, "wb") as file_obj:
            pickle.dump(intcode, file_obj)

    part1(droid)
    droid.display()
    # Sanity check before re-starting.
    assert droid.pending is None

    for index in range(MAX_ITERATIONS):
        if not has_unknown_cells(droid):
            break

        intcode.advance_one()
        if index > 0 and index % 1000 == 0:
            # debug(f"Count: {index}")
            print(f"Count: {index}")

    droid.display()
    assert not has_unknown_cells(droid)
    # global DEBUG
    # DEBUG = True
    # try:
    #     run_intcode(program, droid, droid)
    # except:
    #     droid.display()
    #     raise


if __name__ == "__main__":
    main()

# IDEA:
# Have an **OPTIONAL** std_input and use it to set forth a **known**
# path to the "maybe" ones via the graph (w00t networkx)!!
