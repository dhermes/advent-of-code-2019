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

import copy
import itertools
import pathlib
import threading
import time


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
    99: ("HALT", 0),
}
POSITION_MODE = "0"
IMMEDIATE_MODE = "1"
ALL_MODES = set("01")


def do_add(modes, params, program):
    mode1, mode2, mode3 = modes
    assert mode3 == POSITION_MODE
    param1, param2, param3 = params
    if mode1 == POSITION_MODE:
        assert 0 <= param1 < len(program)
        value1 = program[param1]
    elif mode1 == IMMEDIATE_MODE:
        value1 = param1
    else:
        raise ValueError("Bad mode 1", modes, params, program)

    if mode2 == POSITION_MODE:
        assert 0 <= param2 < len(program)
        value2 = program[param2]
    elif mode2 == IMMEDIATE_MODE:
        value2 = param2
    else:
        raise ValueError("Bad mode 2", modes, params, program)

    assert 0 <= param3 < len(program)
    program[param3] = value1 + value2

    return -1


def do_multiply(modes, params, program):
    # TODO: Re-factor into `do_add()`
    mode1, mode2, mode3 = modes
    assert mode3 == POSITION_MODE
    param1, param2, param3 = params
    if mode1 == POSITION_MODE:
        assert 0 <= param1 < len(program)
        value1 = program[param1]
    elif mode1 == IMMEDIATE_MODE:
        value1 = param1
    else:
        raise ValueError("Bad mode 1", modes, params, program)

    if mode2 == POSITION_MODE:
        assert 0 <= param2 < len(program)
        value2 = program[param2]
    elif mode2 == IMMEDIATE_MODE:
        value2 = param2
    else:
        raise ValueError("Bad mode 2", modes, params, program)

    assert 0 <= param3 < len(program)
    program[param3] = value1 * value2

    return -1


def do_input(modes, params, program, std_input):
    assert modes == (POSITION_MODE,), modes
    param, = params

    assert 0 <= param < len(program)
    program[param] = next(std_input)

    return -1


def do_output(modes, params, program, std_output):
    mode, = modes
    param, = params

    if mode == POSITION_MODE:
        assert 0 <= param < len(program)
        value = program[param]
    elif mode == IMMEDIATE_MODE:
        value = param
    else:
        raise ValueError("Bad mode", modes, params, program)

    std_output.append(value)

    return -1


def next_instruction(index, program):
    assert 0 <= index < len(program)
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

    params = tuple(program[index + 1 : next_index])
    assert len(params) == num_params  # No partial slice

    return instruction, modes, params, next_index


def do_jump_if_true(modes, params, program):
    mode1, mode2 = modes
    param1, param2 = params

    # TODO: This may be incorrect interpretation.
    if mode1 == POSITION_MODE:
        assert 0 <= param1 < len(program)
        value1 = program[param1]
    elif mode1 == IMMEDIATE_MODE:
        value1 = param1
    else:
        raise ValueError("Bad mode 1", modes, params, program)

    if mode2 == POSITION_MODE:
        assert 0 <= param2 < len(program)
        value2 = program[param2]
    elif mode2 == IMMEDIATE_MODE:
        value2 = param2
    else:
        raise ValueError("Bad mode 2", modes, params, program)

    if value1 != 0:
        return value2

    return -1


def do_jump_if_false(modes, params, program):
    # TODO: Fold this into `do_jump_if_true`
    mode1, mode2 = modes
    param1, param2 = params

    # TODO: This may be incorrect interpretation.
    if mode1 == POSITION_MODE:
        assert 0 <= param1 < len(program)
        value1 = program[param1]
    elif mode1 == IMMEDIATE_MODE:
        value1 = param1
    else:
        raise ValueError("Bad mode 1", modes, params, program)

    if mode2 == POSITION_MODE:
        assert 0 <= param2 < len(program)
        value2 = program[param2]
    elif mode2 == IMMEDIATE_MODE:
        value2 = param2
    else:
        raise ValueError("Bad mode 2", modes, params, program)

    if value1 == 0:  # Only difference from `do_jump_if_true`
        return value2

    return -1


def do_less_than(modes, params, program):
    mode1, mode2, mode3 = modes
    assert mode3 == POSITION_MODE
    param1, param2, param3 = params
    if mode1 == POSITION_MODE:
        assert 0 <= param1 < len(program)
        value1 = program[param1]
    elif mode1 == IMMEDIATE_MODE:
        value1 = param1
    else:
        raise ValueError("Bad mode 1", modes, params, program)

    if mode2 == POSITION_MODE:
        assert 0 <= param2 < len(program)
        value2 = program[param2]
    elif mode2 == IMMEDIATE_MODE:
        value2 = param2
    else:
        raise ValueError("Bad mode 2", modes, params, program)

    if value1 < value2:
        to_store = 1
    else:
        to_store = 0

    assert 0 <= param3 < len(program)
    program[param3] = to_store
    return -1


def do_equal(modes, params, program):
    # TODO: Factor into `do_less_than`
    mode1, mode2, mode3 = modes
    assert mode3 == POSITION_MODE
    param1, param2, param3 = params
    if mode1 == POSITION_MODE:
        assert 0 <= param1 < len(program)
        value1 = program[param1]
    elif mode1 == IMMEDIATE_MODE:
        value1 = param1
    else:
        raise ValueError("Bad mode 1", modes, params, program)

    if mode2 == POSITION_MODE:
        assert 0 <= param2 < len(program)
        value2 = program[param2]
    elif mode2 == IMMEDIATE_MODE:
        value2 = param2
    else:
        raise ValueError("Bad mode 2", modes, params, program)

    if value1 == value2:  # Only difference from `do_less_than`
        to_store = 1
    else:
        to_store = 0

    assert 0 <= param3 < len(program)
    program[param3] = to_store
    return -1


def do_halt():
    return -2


def execute_instruction(
    instruction, modes, params, program, std_input, std_output
):
    if instruction == "ADD":
        return do_add(modes, params, program)

    if instruction == "MULTIPLY":
        return do_multiply(modes, params, program)

    if instruction == "INPUT":
        return do_input(modes, params, program, std_input)

    if instruction == "OUTPUT":
        return do_output(modes, params, program, std_output)

    if instruction == "JUMP-IF-TRUE":
        return do_jump_if_true(modes, params, program)

    if instruction == "JUMP-IF-FALSE":
        return do_jump_if_false(modes, params, program)

    if instruction == "JUMP-IF-FALSE":
        return do_jump_if_false(modes, params, program)

    if instruction == "LESS-THAN":
        return do_less_than(modes, params, program)

    if instruction == "EQUALS":
        return do_equal(modes, params, program)

    if instruction == "HALT":
        return do_halt()

    raise ValueError("Bad instruction", instruction, modes, params, program)


def run_intcode(program, std_input, std_output):
    running_program = copy.deepcopy(program)

    jump_index = -1
    index = 0
    while jump_index != -2:
        assert jump_index >= -1
        instruction, modes, params, index = next_instruction(
            index, running_program
        )
        jump_index = execute_instruction(
            instruction, modes, params, running_program, std_input, std_output
        )
        if jump_index >= 0:
            index = jump_index

    return running_program


def run_it(program, input_, std_output=None):
    std_input = iter(input_)
    if std_output is None:
        std_output = []
    run_intcode(program, std_input, std_output)
    return std_output


def run_sequence(program, sequence):
    output_value = 0
    for sequence_value in sequence:
        output_value, = run_it(program, [sequence_value, output_value])
    return output_value


class BlockingStream:
    def __init__(self, initial_values):
        self.lock = threading.Lock()
        self.values = [value for value in initial_values]
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            curr_index = self.index
            self.index = curr_index + 1

        # NOTE: This spinlock is suboptimal, but it could be worse.
        while curr_index >= len(self.values):
            time.sleep(1e-3)

        return self.values[curr_index]

    def append(self, value):
        with self.lock:
            self.values.append(value)


def run_sequence_connected(program, sequence):
    vA, vB, vC, vD, vE = sequence
    sA = BlockingStream([vA, 0])
    sB = BlockingStream([vB])
    sC = BlockingStream([vC])
    sD = BlockingStream([vD])
    sE = BlockingStream([vE])

    tAB = threading.Thread(target=run_it, args=(program, sA, sB))
    tBC = threading.Thread(target=run_it, args=(program, sB, sC))
    tCD = threading.Thread(target=run_it, args=(program, sC, sD))
    tDE = threading.Thread(target=run_it, args=(program, sD, sE))
    tEA = threading.Thread(target=run_it, args=(program, sE, sA))
    tAB.start()
    tBC.start()
    tCD.start()
    tDE.start()
    tEA.start()

    tAB.join()
    tBC.join()
    tCD.join()
    tDE.join()
    tEA.join()

    return sA.values[-1]


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    program = [int(value) for value in content.strip().split(",")]

    max_value = 0
    max_permutation = None
    for permutation in itertools.permutations((0, 1, 2, 3, 4)):
        value = run_sequence(program, permutation)
        if value > max_value:
            max_value = value
            max_permutation = permutation

    print(f"Serial I/O: {max_permutation} -> {max_value}")

    max_value = 0
    max_permutation = None
    for permutation in itertools.permutations((5, 6, 7, 8, 9)):
        value = run_sequence_connected(program, permutation)
        if value > max_value:
            max_value = value
            max_permutation = permutation

    print(f"Feedback I/O: {max_permutation} -> {max_value}")


if __name__ == "__main__":
    main()
