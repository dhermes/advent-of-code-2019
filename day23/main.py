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
import threading
import time
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


class NIC:
    def __init__(self, address, by_address, nat):
        self.address = address
        self.by_address = by_address
        self.nat = nat
        self.spinlock = False

        self.std_input = [address, -1]
        self.std_output = []
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        curr_index = self.index
        self.index = curr_index + 1

        # NOTE: This spinlock is suboptimal, but it could be worse.
        while curr_index >= len(self.std_input):
            self.spinlock = True
            time.sleep(1e-3)

        self.spinlock = False
        return self.std_input[curr_index]

    def append(self, value):
        self.std_output.append(value)
        if len(self.std_output) % 3 != 0:
            return

        destination, x_val, y_val = self.std_output[-3:]
        if destination == 255:
            self.nat.send_two(self.address, x_val, y_val)
            return

        destination_nic = self.by_address[destination]
        destination_nic.std_input.extend([x_val, y_val])


class NAT:
    def __init__(self, by_address):
        self.by_address = by_address
        self.lock = threading.Lock()
        self.x_val = None
        self.y_val = None
        self.sent_y = []

    def send_two(self, from_nic, x_val, y_val):
        # NOTE: ``from_nic`` is (for now) ignored.
        with self.lock:
            self.x_val = x_val
            self.y_val = y_val

    def monitor(self):
        # Intended to run in a thread.
        consecutive_spinlocks = 0
        while True:
            # NOTE: This is subject to race conditions, lack of locks in this
            #       code is wild west.
            if all(nic.spinlock for nic in self.by_address.values()):
                consecutive_spinlocks += 1
            else:
                consecutive_spinlocks = 0

            if consecutive_spinlocks >= 100:
                consecutive_spinlocks = 0
                # Don't change x and y during this
                with self.lock:
                    if self.x_val is None or self.y_val is None:
                        raise RuntimeError("Have not received anything")
                    destination_nic = self.by_address[0]
                    if self.y_val in self.sent_y:
                        raise RuntimeError(
                            f"Sending y = {self.y_val} again", self.sent_y
                        )
                    else:
                        self.sent_y.append(self.y_val)

                    destination_nic.std_input.extend([self.x_val, self.y_val])

            # Sleep before next (infinite) loop iteration
            time.sleep(1e-3)


def run_intcode(intcode):
    # Intended to be run in a thread.
    nic = intcode.std_input
    assert nic is intcode.std_output
    try:
        intcode.run()
    except Exception as exc:
        msg = (
            f"Failed in thread {threading.current_thread().name}: {exc!r}, "
            f"Current state: {nic.__dict__}"
        )
        print(msg)
        raise


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    program = collections.defaultdict(int)
    for index, value in enumerate(content.strip().split(",")):
        program[index] = int(value)

    # NIC: 0, ..., 49
    # Packet: X, Y
    # dest. address / X / Y <-- e.g. 10, 20, 30
    #
    # it will request its network address via a single input instruction. Be
    # sure to give each computer a unique network address.
    by_address = {}
    nat = NAT(by_address)
    threads = []
    for address in range(50):
        nic = NIC(address, by_address, nat)
        by_address[address] = nic

        intcode = Intcode(program, nic, nic)
        thread = threading.Thread(target=run_intcode, args=(intcode,))
        threads.append(thread)

    # Add a thread for the NAT monitor
    thread = threading.Thread(target=nat.monitor)
    threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # # nic = NIC(0)
    # # nic.std_input.append(0)
    # # icc = Intcode(program, nic, nic)
    # X = [by_address[i].std_input.std_output for i in range(50)]
    # breakpoint()
    # # nic.std_input.extend([0, 1, 2, 3, 4])
    # # intcode = Intcode(program, nic, nic)
    # # try:
    # #     intcode.run()
    # # except Exception as exc:
    # #     print(repr(exc))

    # # print(nic.std_output)


if __name__ == "__main__":
    main()
