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
import doctest
import pathlib


HERE = pathlib.Path(__file__).resolve().parent
OPCODE_ADD = 1
OPCODE_MULTIPLY = 2
OPCODE_HALT = 99
EXPECTED_OUTPUT = 19690720


def validate_index(value, length):
    if value != int(value):
        raise ValueError("Non-integer encountered", value)

    if value < 0 or value >= length:
        raise ValueError("Index outside of range", value, length)


def binary_operation_info(instruction, running_program):
    if len(instruction) != 4:
        raise ValueError("Invalid program", running_program)

    input_index1 = instruction[1]
    input_index2 = instruction[2]
    output_index = instruction[3]

    length = len(running_program)
    validate_index(input_index1, length)
    validate_index(input_index2, length)
    validate_index(output_index, length)

    return (
        running_program[input_index1],
        running_program[input_index2],
        output_index,
    )


def run_intcode(program):
    """Run a program as a series of quartet instructions.

    The first value in the quartet is the opcode (ADD, MULTIPLY or HALT),
    the second and third values are the input locations and the fourth value
    is the output location.

    >>> run_intcode([1, 9, 10, 3, 2, 3, 11, 0, 99, 30, 40, 50])
    [3500, 9, 10, 70, 2, 3, 11, 0, 99, 30, 40, 50]
    >>> run_intcode([1, 0, 0, 0, 99])
    [2, 0, 0, 0, 99]
    >>> run_intcode([2, 3, 0, 3, 99])
    [2, 3, 0, 6, 99]
    >>> run_intcode([2, 4, 4, 5, 99, 0])
    [2, 4, 4, 5, 99, 9801]
    >>> run_intcode([1, 1, 1, 4, 99, 5, 6, 0, 99])
    [30, 1, 1, 4, 2, 5, 6, 0, 99]
    """
    running_program = copy.deepcopy(program)
    length = len(program)

    for start in range(0, length, 4):
        instruction = running_program[start : start + 4]
        opcode = instruction[0]
        if opcode == OPCODE_HALT:
            return running_program

        input_value1, input_value2, output_index = binary_operation_info(
            instruction, running_program
        )
        if opcode == OPCODE_ADD:
            running_program[output_index] = input_value1 + input_value2
        elif opcode == OPCODE_MULTIPLY:
            running_program[output_index] = input_value1 * input_value2
        else:
            raise RuntimeError("Invalid program", program)

    return running_program


def run_parameterized_program(program, noun, verb):
    # NOTE: This modifies `program` but probably doesn't need to.
    program[1] = noun
    program[2] = verb
    program_output = run_intcode(program)
    return program_output[0]


def inputs_search(program, expected_output):
    for noun in range(100):
        for verb in range(100):
            output = run_parameterized_program(program, noun, verb)
            if output == expected_output:
                return noun, verb

    raise RuntimeError("No match found")


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    program = [int(value) for value in content.split(",")]
    output1202 = run_parameterized_program(program, 12, 2)
    print(f"Program output at position 0: {output1202}")

    noun, verb = inputs_search(program, EXPECTED_OUTPUT)
    print(f"{noun:02}{verb:02} produces {EXPECTED_OUTPUT}")


if __name__ == "__main__":
    doctest.testmod()
    main()
