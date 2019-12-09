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


def add(a, b):
    return a + b


def _do_binary_op(modes, params, relative_base, program, fn):
    mode1, mode2, mode3 = modes
    param1, param2, param3 = params
    if mode1 == POSITION_MODE:
        assert 0 <= param1
        value1 = program[param1]
    elif mode1 == IMMEDIATE_MODE:
        value1 = param1
    elif mode1 == RELATIVE_MODE:
        index = relative_base + param1
        assert 0 <= index
        value1 = program[index]
    else:
        raise ValueError("Bad mode 1", modes, params, program)

    if mode2 == POSITION_MODE:
        assert 0 <= param2
        value2 = program[param2]
    elif mode2 == IMMEDIATE_MODE:
        value2 = param2
    elif mode2 == RELATIVE_MODE:
        index = relative_base + param2
        assert 0 <= index
        value2 = program[index]
    else:
        raise ValueError("Bad mode 2", modes, params, program)

    to_store = fn(value1, value2)
    if mode3 == POSITION_MODE:
        assert 0 <= param3
        program[param3] = to_store
    elif mode3 == RELATIVE_MODE:
        index = relative_base + param3
        assert 0 <= index
        program[index] = to_store
    else:
        raise ValueError("Bad mode 3", modes, params, program)

    return -1


def do_add(modes, params, relative_base, program):
    return _do_binary_op(modes, params, relative_base, program, operator.add)


def do_multiply(modes, params, relative_base, program):
    return _do_binary_op(modes, params, relative_base, program, operator.mul)


def do_input(modes, params, relative_base, program, std_input):
    mode, = modes
    param, = params

    if mode == POSITION_MODE:
        assert 0 <= param
        program[param] = next(std_input)
    elif mode == RELATIVE_MODE:
        index = relative_base + param
        assert 0 <= index
        program[index] = next(std_input)
    else:
        raise NotImplementedError("Invalid mode", mode)

    return -1


def do_output(modes, params, relative_base, program, std_output):
    mode, = modes
    param, = params

    if mode == POSITION_MODE:
        assert 0 <= param
        value = program[param]
    elif mode == IMMEDIATE_MODE:
        value = param
    elif mode == RELATIVE_MODE:
        index = relative_base + param
        assert 0 <= index
        value = program[index]
    else:
        raise ValueError("Bad mode", modes, params, program)

    std_output.append(value)

    return -1


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


def do_jump_if_true(modes, params, relative_base, program):
    mode1, mode2 = modes
    param1, param2 = params

    # TODO: This may be incorrect interpretation.
    if mode1 == POSITION_MODE:
        assert 0 <= param1
        value1 = program[param1]
    elif mode1 == IMMEDIATE_MODE:
        value1 = param1
    elif mode1 == RELATIVE_MODE:
        index = relative_base + param1
        assert 0 <= index
        value1 = program[index]
    else:
        raise ValueError("Bad mode 1", modes, params, program)

    if mode2 == POSITION_MODE:
        assert 0 <= param2
        value2 = program[param2]
    elif mode2 == IMMEDIATE_MODE:
        value2 = param2
    elif mode2 == RELATIVE_MODE:
        index = relative_base + param2
        assert 0 <= index
        value2 = program[index]
    else:
        raise ValueError("Bad mode 2", modes, params, program)

    if value1 != 0:
        return value2

    return -1


def do_jump_if_false(modes, params, relative_base, program):
    # TODO: Fold this into `do_jump_if_true`
    mode1, mode2 = modes
    param1, param2 = params

    # TODO: This may be incorrect interpretation.
    if mode1 == POSITION_MODE:
        assert 0 <= param1
        value1 = program[param1]
    elif mode1 == IMMEDIATE_MODE:
        value1 = param1
    elif mode1 == RELATIVE_MODE:
        index = relative_base + param1
        assert 0 <= index
        value1 = program[index]
    else:
        raise ValueError("Bad mode 1", modes, params, program)

    if mode2 == POSITION_MODE:
        assert 0 <= param2
        value2 = program[param2]
    elif mode2 == IMMEDIATE_MODE:
        value2 = param2
    elif mode2 == RELATIVE_MODE:
        index = relative_base + param2
        assert 0 <= index
        value2 = program[index]
    else:
        raise ValueError("Bad mode 2", modes, params, program)

    if value1 == 0:  # Only difference from `do_jump_if_true`
        return value2

    return -1


def do_less_than(modes, params, relative_base, program):
    mode1, mode2, mode3 = modes
    param1, param2, param3 = params
    if mode1 == POSITION_MODE:
        assert 0 <= param1
        value1 = program[param1]
    elif mode1 == IMMEDIATE_MODE:
        value1 = param1
    elif mode1 == RELATIVE_MODE:
        index = relative_base + param1
        assert 0 <= index
        value1 = program[index]
    else:
        raise ValueError("Bad mode 1", modes, params, program)

    if mode2 == POSITION_MODE:
        assert 0 <= param2
        value2 = program[param2]
    elif mode2 == IMMEDIATE_MODE:
        value2 = param2
    elif mode2 == RELATIVE_MODE:
        index = relative_base + param2
        assert 0 <= index
        value2 = program[index]
    else:
        raise ValueError("Bad mode 2", modes, params, program)

    if value1 < value2:
        to_store = 1
    else:
        to_store = 0

    if mode3 == POSITION_MODE:
        assert 0 <= param3
        program[param3] = to_store
    elif mode3 == RELATIVE_MODE:
        index = relative_base + param3
        assert 0 <= index
        program[index] = to_store
    else:
        raise ValueError("Bad mode 3", modes, params, program)

    return -1


def do_equal(modes, params, relative_base, program):
    # TODO: Factor into `do_less_than`
    mode1, mode2, mode3 = modes
    param1, param2, param3 = params
    if mode1 == POSITION_MODE:
        assert 0 <= param1
        value1 = program[param1]
    elif mode1 == IMMEDIATE_MODE:
        value1 = param1
    elif mode1 == RELATIVE_MODE:
        index = relative_base + param1
        assert 0 <= index
        value1 = program[index]
    else:
        raise ValueError("Bad mode 1", modes, params, program)

    if mode2 == POSITION_MODE:
        assert 0 <= param2
        value2 = program[param2]
    elif mode2 == IMMEDIATE_MODE:
        value2 = param2
    elif mode2 == RELATIVE_MODE:
        index = relative_base + param2
        assert 0 <= index
        value2 = program[index]
    else:
        raise ValueError("Bad mode 2", modes, params, program)

    if value1 == value2:  # Only difference from `do_less_than`
        to_store = 1
    else:
        to_store = 0

    if mode3 == POSITION_MODE:
        assert 0 <= param3
        program[param3] = to_store
    elif mode3 == RELATIVE_MODE:
        index = relative_base + param3
        assert 0 <= index
        program[index] = to_store
    else:
        raise ValueError("Bad mode 3", modes, params, program)

    return -1


def do_adjust_base(modes, params, relative_base, program):
    mode, = modes
    param, = params

    if mode == POSITION_MODE:
        index = param
        assert 0 <= index
        value = program[index]
    elif mode == IMMEDIATE_MODE:
        value = param
    elif mode == RELATIVE_MODE:
        index = relative_base + param
        assert 0 <= index
        value = program[index]
    else:
        raise NotImplementedError("Invalid mode", mode)

    return AdjustBase(value)


def do_halt():
    return -2


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

    jump_index = -1
    index = 0
    while jump_index != -2:
        assert jump_index >= -1
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
            jump_index = -1
        elif jump_index >= 0:
            index = jump_index

    return running_program


class AdjustBase:
    def __init__(self, value):
        self.value = value


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    program = collections.defaultdict(int)
    for index, value in enumerate(content.strip().split(",")):
        program[index] = int(value)

    for input_val in (1, 2):
        std_input_list = [input_val]
        std_input = iter(std_input_list)
        std_output = []
        run_intcode(program, std_input, std_output)
        print(std_output)


if __name__ == "__main__":
    main()
