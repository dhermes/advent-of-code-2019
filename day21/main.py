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
DEBUG = False
TEMPORARY_VALUE_REGISTER = "T"
JUMP_REGISTER = "J"
TILE_DISTANCE = {"A": 1, "B": 2, "C": 3, "D": 4}
FINISH = "WALK\n"
# AND X Y: Y <- X & Y | Y must always by T or J | X can be A,B,C,D,T,J
# OR  X Y: Y <- X | Y | Y must always by T or J | X can be A,B,C,D,T,J
# NOT X Y: Y <- ~X    | Y must always by T or J | X can be A,B,C,D,T,J


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


class SpringDroid:
    def __init__(self):
        self.std_input = []
        self.std_output = []
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        curr_index = self.index
        self.index = curr_index + 1
        return self.std_input[curr_index]

    def append(self, value):
        self.std_output.append(value)

    def send_command(self, ascii_str):
        self.std_input.extend([ord(c) for c in ascii_str])


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    program = collections.defaultdict(int)
    for index, value in enumerate(content.strip().split(",")):
        program[index] = int(value)

    droid = SpringDroid()
    # # Attempt 1
    # droid.send_command("NOT D J\n")
    # # Attempt 2
    # droid.send_command("NOT A J\n")
    # droid.send_command("NOT B T\n")
    # droid.send_command("AND T J\n")
    # droid.send_command("NOT C T\n")
    # droid.send_command("AND T J\n")
    # droid.send_command("AND D J\n")
    # # Attempt 3
    # droid.send_command("NOT A J\n")
    # # Attempt 4
    # droid.send_command("NOT D J\n")
    # droid.send_command("NOT J J\n")
    # # Attempt 5
    # droid.send_command("OR A J\n")
    # droid.send_command("NOT B T\n")
    # droid.send_command("AND T J\n")
    # droid.send_command("NOT C T\n")
    # droid.send_command("AND T J\n")
    # droid.send_command("AND D J\n")
    # droid.send_command("NOT A T\n")
    # droid.send_command("OR T J\n")
    # # Attempt 6
    # droid.send_command("NOT B J\n")
    # droid.send_command("NOT C T\n")
    # droid.send_command("OR T J\n")
    # droid.send_command("AND A J\n")
    # droid.send_command("AND D J\n")
    # Attempt 7
    droid.send_command("NOT B J\n")
    droid.send_command("NOT C T\n")
    droid.send_command("OR T J\n")
    droid.send_command("AND A J\n")
    droid.send_command("AND D J\n")
    droid.send_command("NOT A T\n")
    droid.send_command("OR T J\n")

    droid.send_command(FINISH)
    intcode = Intcode(program, droid, droid)
    intcode.run()

    print(f"Hull damage: {droid.std_output[-1]}")
    print(bytes(droid.std_output[:-1]).decode("ascii"))


if __name__ == "__main__":
    main()


#   @
#  @ @
# @   @
# 01234

# IF 1: (~A) & B
# IF 2: (~A) & (~B) & C
# IF 3: (~A) & (~B) & (~C) & D

# T: F, J: F
#         | T  | J
# ---------+----+---
#         | 0  | 0
# NOT A J |    | ~A
# NOT B T | ~B |
# AND T J |    | ~A & ~B
# NOT C T | ~C |
# AND T J |    | ~A & ~B & ~C
# AND D J |    | ~A & ~B & ~C & D

# JUMP (|#..#):   (A & (~B) & (~C) & D) | (~A)
#
#         | T  | J
# ---------+----+---
#         | 0  | 0
# OR  A J |    | A
# NOT B T | ~B |
# AND T J |    | A & ~B
# NOT C T | ~C |
# AND T J |    | A & ~B & ~C
# AND D J |    | A & ~B & ~C & D
# NOT A T | ~A |
# OR  T J |    | (A & ~B & ~C & D) | (~A)

#   #|.##. <-- shit
#  |# .##  <-- before:
#
# A & (~B | ~C) & D
# covers all of
# |#.##
# |##.#
# |#..#

#         | T  | J
# ---------+----+---
#         | 0  | 0
# NOT B J |    | ~B
# NOT C T | ~C |
# OR  T J |    | (~B | ~C)
# AND A J |    | (~B | ~C) & A
# AND D J |    | (~B | ~C) & A & D

#         | T  | J
# ---------+----+---
#         | 0  | 0
# NOT B J |    | ~B
# NOT C T | ~C |
# OR  T J |    | (~B | ~C)
# AND A J |    | (~B | ~C) & A
# AND D J |    | (~B | ~C) & A & D
# NOT A T | ~A |
# OR  T J |    | ((~B | ~C) & A & D) | (~A)
