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
