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

import numpy as np
import PIL.Image


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
COLOR_BLACK = 0
COLOR_WHITE = 1
MAX_PIXEL = 255
TURN_LEFT = np.array([[0, -1], [1, 0]])
TURN_RIGHT = np.array([[0, 1], [-1, 0]])


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


class Robot:
    def __init__(self, start_color):
        assert start_color in (COLOR_BLACK, COLOR_WHITE)
        self.input_index = 0
        self.std_input = [start_color]  # Seed first panel
        self.std_output = []
        self.panels = collections.defaultdict(list)
        self.position = np.array([[0], [0]])
        self.direction = np.array([[0], [1]])

    def __iter__(self):
        return self

    def __next__(self):
        # NOTE: This is not thread-safe
        curr_index = self.input_index
        self.input_index = curr_index + 1
        return self.std_input[curr_index]

    def append(self, value):
        # NOTE: This is not thread-safe
        self.std_output.append(value)
        if len(self.std_output) % 2 == 0:
            color, direction_int = self.std_output[-2:]
            assert color in (COLOR_BLACK, COLOR_WHITE)
            # Paint the current panel.
            self.panels[tuple(self.position.flatten())].append(color)
            # Turn the robot
            if direction_int == 0:
                self.direction = TURN_LEFT.dot(self.direction)
            elif direction_int == 1:
                self.direction = TURN_RIGHT.dot(self.direction)
            else:
                raise ValueError("Invalid direction", direction_int)
            # Advance the robot
            self.position += self.direction
            # Get current paint color of new position
            colors = self.panels[tuple(self.position.flatten())]
            if colors:
                curr_color = colors[-1]
            else:
                curr_color = COLOR_BLACK
            # Add the color to inputs.
            self.std_input.append(curr_color)


def paint_hull(program, start_color):
    robot = Robot(start_color)
    run_intcode(program, robot, robot)
    return robot


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    program = collections.defaultdict(int)
    for index, value in enumerate(content.strip().split(",")):
        program[index] = int(value)

    robot = paint_hull(program, COLOR_BLACK)
    count = sum(1 for colors in robot.panels.values() if colors)
    print(f"Number of painted panels when starting with Black: {count}")

    robot = paint_hull(program, COLOR_WHITE)
    all_indices = np.array(list(robot.panels.keys()))
    min_x = min(all_indices[:, 0])
    max_x = max(all_indices[:, 0])
    min_y = min(all_indices[:, 1])
    max_y = max(all_indices[:, 1])
    width_x = max_x - min_x + 1
    width_y = max_y - min_y + 1

    painted = COLOR_BLACK * np.ones((width_x, width_y), dtype=np.uint8)
    for position, colors in robot.panels.items():
        if not colors:
            continue
        assert len(colors) == 1
        color = colors[0]
        assert color in (COLOR_BLACK, COLOR_WHITE)
        x, y = position
        shifted_x = x - min_x
        shifted_y = y - min_y
        assert 0 <= shifted_x < width_x
        assert 0 <= shifted_y < width_y
        painted[shifted_x, shifted_y] = color

    # Swap rows and columns
    painted = painted.T
    # Invert rows
    painted = painted[::-1, :]

    # Swap white and black and scale up to highest pixel intensity.
    image = PIL.Image.fromarray(MAX_PIXEL - MAX_PIXEL * painted)
    image.save(HERE / "image.png")


if __name__ == "__main__":
    main()
