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

import itertools
import pathlib
import time


HERE = pathlib.Path(__file__).resolve().parent
BASE_PATTERN = (0, 1, 0, -1)
LEN_BASE_PATTERN = len(BASE_PATTERN)


# def index_slices(n):
#     # -1   0      n - 2  n - 1       2n - 2  2n - 1       3n - 2, 3n - 1,       4n - 2
#     #  1   2      n      n + 1       2n      2n + 1       3n    , 3n + 1,       4n
#     #  0 | 0, ... 0    , 1    , ..., 1     , 0     , ..., 0     , -1     , ..., -1
#     window_size = 4 * n
#     positive_slices = [slice(n - 1 + i, None, window_size) for i in range(n)]
#     negative_slices = [
#         slice(2 * n - 1 + i, None, window_size) for i in range(n)
#     ]
#     return positive_slices, negative_slices


def pattern(n):
    pattern_index = 0
    within_number_index = 0
    current_value = BASE_PATTERN[pattern_index]
    while True:
        within_number_index += 1
        if within_number_index >= n:
            within_number_index = 0
            pattern_index = (pattern_index + 1) % LEN_BASE_PATTERN
            current_value = BASE_PATTERN[pattern_index]

        # NOTE: It's crucial we increment first, this way the "first"
        #       value gets jumped over in only the first iteration.
        yield current_value


def indices_positive(n, num_values):
    # n = 2
    #   S E             S E             S E             S E             S E
    # 0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,
    # 0,1,1,0,0,-,-,0,0,1,1,0,0,-,-,0,0,1,1,0,0,-,-,0,0,1,1,0,0,-,-,0,0,1,1,0,
    # n = 3
    #     S   E                   S   E                   S   E
    # 0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,
    # 0,0,1,1,1,0,0,0,-,-,-,0,0,0,1,1,1,0,0,0,-,-,-,0,0,0,1,1,1,0,0,0,-,-,-,0,
    # n = 4
    #       S     E                         S     E                         S
    # 0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,
    # 0,0,0,1,1,1,1,0,0,0,0,-,-,-,-,0,0,0,0,1,1,1,1,0,0,0,0,-,-,-,-,0,0,0,0,1,

    global_index = n - 1
    local_index = 0
    while True:
        if global_index >= num_values:
            return

        yield global_index

        local_index += 1
        global_index += 1
        if local_index >= n:
            local_index = 0
            global_index += n * (LEN_BASE_PATTERN - 1)


def indices_negative(n, num_values):
    # n = 2
    #           S E             S E             S E             S E
    # 0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,
    # 0,1,1,0,0,-,-,0,0,1,1,0,0,-,-,0,0,1,1,0,0,-,-,0,0,1,1,0,0,-,-,0,0,1,1,0,
    # n = 3
    #                 S   E                   S   E                   S   E
    # 0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,
    # 0,0,1,1,1,0,0,0,-,-,-,0,0,0,1,1,1,0,0,0,-,-,-,0,0,0,1,1,1,0,0,0,-,-,-,0,
    # n = 4
    #                       S     E                         S     E
    # 0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,6,7,8,9,0,1,2,3,4,5,
    # 0,0,0,1,1,1,1,0,0,0,0,-,-,-,-,0,0,0,0,1,1,1,1,0,0,0,0,-,-,-,-,0,0,0,0,1,

    global_index = 3 * n - 1
    local_index = 0
    while True:
        if global_index >= num_values:
            return

        yield global_index

        local_index += 1
        global_index += 1
        if local_index >= n:
            local_index = 0
            global_index += n * (LEN_BASE_PATTERN - 1)


def n_times(values, n):
    repeat_index = 0
    within_values_index = 0
    num_values = len(values)
    while True:
        yield values[within_values_index]
        # Increment for the next iteration
        within_values_index += 1
        if within_values_index >= num_values:
            within_values_index = 0
            repeat_index += 1
            if repeat_index >= n:
                return


def apply(input_values):
    size = len(input_values)
    output_values = []
    for n in range(1, size + 1):
        window = pattern(n)
        multiply_full = sum(a * b for a, b in zip(input_values, window))
        output_values.append(abs(multiply_full) % 10)

    assert len(output_values) == len(input_values)
    return tuple(output_values)


# def apply_slices(input_values):
#     size = len(input_values)
#     output_values = []
#     for n in range(1, size + 1):
#         positive_slices, negative_slices = index_slices(n)
#         multiply_full = 0
#         for positive_slice in positive_slices:
#             multiply_full += sum(input_values[positive_slice])
#         for negative_slice in negative_slices:
#             multiply_full -= sum(input_values[negative_slice])
#         output_values.append(abs(multiply_full) % 10)

#     assert len(output_values) == len(input_values)
#     return tuple(output_values)


def part1(values):
    for _ in range(100):
        values = apply(values)
        # values = apply_slices(values)

    print("".join(map(str, values[:8])))


def compute_dependencies(num_values, index, result=None):
    if result is None:
        result = set()

    n = index + 1
    dependency_index = n - 1
    within_number_index = 0

    while dependency_index < num_values:
        result.add(dependency_index)

        within_number_index += 1
        dependency_index += 1
        if within_number_index >= n:
            within_number_index = 0
            # Skip ``n`` zeros
            dependency_index += n

    return result


def part2_failedA():
    # real_signal = n_times(values, 10000)
    real_signal = values * 10000
    for c in range(100):
        print(f"Starting {c} ({time.time()})")
        real_signal = apply(real_signal)
        print(f"Finished {c} ({time.time()})")


def part2_failedB():
    num_values = 650 * 10000  # len(values) * 10000
    dependencies_by_stage = {100: set([0, 1, 2, 3, 4, 5, 6])}
    last_stage = 98
    for stage in range(99, last_stage - 1, -1):
        previous_dependencies = dependencies_by_stage[stage + 1]
        current_dependencies = set()
        for index in previous_dependencies:
            compute_dependencies(
                num_values, index, result=current_dependencies
            )

        dependencies_by_stage[stage] = current_dependencies


class RepeatedList:
    def __init__(self, values, repeat):
        self.values = values
        self.num_values = len(values)
        self.repeated_length = repeat * self.num_values

    def __getitem__(self, index):
        if isinstance(index, slice):
            raise IndexError("slicing not supported")
        if index < 0:
            raise IndexError("list index out of range; negative not supported")
        if index >= self.repeated_length:
            raise IndexError("list index out of range")

        actual_index = index % self.num_values
        return self.values[actual_index]

    def __len__(self):
        return self.repeated_length


class OnDemandCompute:
    def __init__(self, values):
        self.values = values
        self.num_values = len(values)
        self.cache = {}

    def compute(self, stage, index):
        if stage == 0:
            return self.values[index]

        key = (stage, index)
        if key in self.cache:
            return self.cache[key]

        n = index + 1
        multiply_full = 0
        for dependency_index in indices_positive(n, self.num_values):
            multiply_full += self.compute(stage - 1, dependency_index)
        for dependency_index in indices_negative(n, self.num_values):
            multiply_full -= self.compute(stage - 1, dependency_index)

        result = abs(multiply_full) % 10
        self.cache[key] = result
        return result


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    if False:
        content = "12345678\n"
    if False:
        # 24176176
        content = "80871224585914546619083218645595\n"
    if False:
        # 73745418
        content = "19617804207202209144916044189917\n"
    if False:
        # 52432133 (part 1)
        content = "69317163492948606335995924319873\n"
    if False:
        # 84462026 (part 2)
        content = "03036732577212944063491565474664\n"

    values = tuple(int(c) for c in content.strip())
    part1(values)

    start_index = int("".join(map(str, values[:7])))
    values_repeated = RepeatedList(values, 10000)
    # At least past 50% + a buffer of 10
    assert 2 * start_index >= len(values_repeated) + 20

    on_demand = OnDemandCompute(values_repeated)
    v1 = on_demand.compute(100, start_index)
    print(v1)


if __name__ == "__main__":
    main()

# 12345678
# 48226158 | 48226158
# 34040438 | 34040438
# 03415518 | 03415518
# 01029498 | 01029498

# n = 10
# ======
#  1: c00 - c02 + c04 - c06 + c08 (10 / 4  == 2.5)
#  2: c01 + c02 - c05 - c06 + c09 (10 / 8  == 1.25)
#  3: c02 + c03 + c04 - c08 - c09 (10 / 12 == 0.8333)
#  4: c03 + c04 + c05 + c06       (10 / 16 == 0.625)
#  5: c04 + c05 + c06 + c07 + c08 (10 / 20 == 0.5)
# ------------------------------------------------------------------------------
#  6: c05 + c06 + c07 + c08 + c09 (10 / 24 == 0.416...)
#  7: c06 + c07 + c08 + c09       (10 / 28 == 0.357...)
#  8: c07 + c08 + c09             (10 / 32 == 0.3125)
#  9: c08 + c09                   (10 / 36 == 0.277...)
# 10: c09                         (10 / 40 == 0.25)

# >>> import sympy
# >>> variables = sympy.symbols(' '.join(f'c{i:02}' for i in range(15)))

# n = 15
# ======
#  1: c00 - c02 + c04 - c06 + c08 - c10 + c12 - c14 (15 / 4  == 3.75)
#  2: c01 + c02 - c05 - c06 + c09 + c10 - c13 - c14 (15 / 8  == 1.875)
#  3: c02 + c03 + c04 - c08 - c09 - c10 + c14       (15 / 12 == 1.25)
#  4: c03 + c04 + c05 + c06 - c11 - c12 - c13 - c14 (15 / 16 == 0.9375)
#  5: c04 + c05 + c06 + c07 + c08 - c14             (15 / 20 == 0.75)
#  6: c05 + c06 + c07 + c08 + c09 + c10             (15 / 24 == 0.625)
#  7: c06 + c07 + c08 + c09 + c10 + c11 + c12       (15 / 28 == 0.535...)
# ------------------------------------------------------------------------------
#  8: c07 + c08 + c09 + c10 + c11 + c12 + c13 + c14 (15 / 32 == 0.46875)
#  9: c08 + c09 + c10 + c11 + c12 + c13 + c14       (15 / 36 == 0.416...)
# 10: c09 + c10 + c11 + c12 + c13 + c14             (15 / 40 == 0.375)
# 11: c10 + c11 + c12 + c13 + c14                   (15 / 44 == 0.3409...)
# 12: c11 + c12 + c13 + c14                         (15 / 48 == 0.3125)
# 13: c12 + c13 + c14                               (15 / 52 == 0.288...)
# 14: c13 + c14                                     (15 / 56 == 0.267...)
# 15: c14                                           (15 / 60 == 0.25)

# values = [1, 2, 3, 4, 5, 6, 7, 8]
# odc = OnDemandCompute(values)

# n = 1: LCM( 4, 650) =  2 * 650 --> 5000 copies
# n = 2: LCM( 8, 650) =  4 * 650 --> 2500 copies
# n = 3: LCM(12, 650) =  6 * 650 --> 1666 copies, 4 leftover
# n = 4: LCM(16, 650) =  8 * 650 --> 1250 copies
# n = 5: LCM(20, 650) =  2 * 650 --> 5000 copies
# n = 6: LCM(24, 650) = 12 * 650 --> 833  copies, 4 leftover
# n = 7: LCM(28, 650) = 14 * 650 --> 714  copies, 4 leftover

# len(y) == 200; apply(n copies of y)[0]
#  1: 1|9|0|0|0
#  2: 2|8|3|0|0
#  3: 3|7|0|0|0
#  4: 4|6|0|0|0
#  5: 5|5|3|0|0
#  6: 6|4|0|0|0
#  7: 7|3|0|0|0
#  8: 8|2|7|0|0
#  9: 9|1|0|0|0
# 10: 0|0|0|0|0
# 11: 1|9|7|0|0
# 12: 2|8|0|0|0
# 13: 3|7|0|0|0
# 14: 4|6|7|0|0
# 15: 5|5|0|0|0
# 16: 6|4|0|0|0

# len(y) == 101; apply(n copies of y)[0]
#  1: 7|8|6|5|0
#  2: 1|7|0|9|1
#  3: 6|8|9|0|4
#  4: 0|8|0|9|0
#  5: 7|6|1|9|7
#  6: 1|5|7|2|8
#  7: 6|0|3|8|0
#  8: 0|0|7|4|2
#  9: 7|8|6|1|1
# 10: 1|7|3|5|9
# 11: 6|8|4|4|9
# 12: 0|8|0|5|0
# 13: 7|6|6|5|3
# 14: 1|5|0|6|9
# 15: 6|0|9|6|6
# 16: 0|0|0|0|1

# len(y) == 154; apply(n copies of y)[:5]
#  1: 7|5|6|1|2
#  2: 0|0|6|5|6
#  3: 7|5|9|8|7
#  4: 0|0|5|0|7
#  5: 7|5|3|1|9
#  6: 0|0|0|5|3
#  7: 7|5|6|8|3
#  8: 0|0|6|0|6
#  9: 7|5|9|1|2
# 10: 0|0|5|5|0
# 11: 7|5|3|8|2
# 12: 0|0|0|0|6
# 13: 7|5|6|1|7
# 14: 0|0|6|5|7
# 15: 7|5|9|8|9
# 16: 0|0|5|0|3
