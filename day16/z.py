import sys

import colors


BASE_PATTERN = (0, 1, 0, -1)
LEN_BASE_PATTERN = len(BASE_PATTERN)
CIRCLE = "\u25cf"
BLUE_CIRCLE = colors.blue(CIRCLE)
RED_CIRCLE = colors.red(CIRCLE)


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


def main():
    first_nonzero = []
    if len(sys.argv) > 1:
        num_values = int(sys.argv[1])
    else:
        num_values = 20
    over_25 = False
    over_50 = False
    over_75 = False
    no_red = False
    # Red ceases to exist just after n = (#values / 3)
    #  20 --> 7 (6.666...)
    #  30 --> 11 (10)
    #  31 --> 11 (10.333...)
    #  32 --> 11 (10.666...)
    #  33 --> 12 (11)
    #  34 --> 11 (11.333...)
    #  40 --> 14 (13.333...)
    #  50 --> 17 (16.666...)
    #  60 --> 21 (20)
    #  70 --> 24 (23.333...)
    #  80 --> 27 (26.666...)
    # 100 --> 34 (33.333...)
    # 160 --> 54 (53.333...)
    # 320 --> 107 (106.666...)
    # Contiguous run of blue to the very end just after n = (#values / 2)
    #  20 --> 11 (10)
    #  30 --> 16 (15)
    #  31 --> 16 (15.5)
    #  32 --> 17 (16)
    #  33 --> 17 (16.5)
    #  34 --> 18 (17)
    #  40 --> 21 (20)
    #  80 --> 41 (40)
    for n in range(1, num_values + 1):
        if not over_25 and 4 * n >= num_values:
            over_25 = True
            # print(f"Over 25% ({n} / {num_values} = {n / num_values})")
        if not over_50 and 2 * n >= num_values:
            over_50 = True
            # print(f"Over 50% ({n} / {num_values} = {n / num_values})")
        if not over_75 and 4 * n >= 3 * num_values:
            over_75 = True
            # print(f"Over 75% ({n} / {num_values} = {n / num_values})")

        print(f"{n:2}: ", end="")
        values_iter = pattern(n)
        seen_nonzero = False
        red_count = 0
        for index in range(num_values):
            value = next(values_iter)
            if not seen_nonzero and value != 0:
                first_nonzero.append((n, index))
                seen_nonzero = True
            if value == 0:
                print(" ", end="")
            elif value == 1:
                print(BLUE_CIRCLE, end="")
            elif value == -1:
                red_count += 1
                print(RED_CIRCLE, end="")
            else:
                raise RuntimeError
        print("\n", end="")

        if not no_red and red_count == 0:
            # print(f"No red ({n} / {num_values} = {n / num_values})")
            no_red = True

    for n, index in first_nonzero:
        assert n - index == 1


def apply_no_modulus(input_values):
    size = len(input_values)
    output_values = []

    first_all_blue, _ = divmod(size, 2)
    first_all_blue += 1  # Always round up, even if ``remainder == 0``.

    for n in range(1, size + 1):
        # 50% mark
        if n < first_all_blue:
            output_values.append(0)
            continue

        window = pattern(n)
        multiply_full = sum(a * b for a, b in zip(input_values, window))
        output_values.append(multiply_full)

    assert len(output_values) == len(input_values)
    return tuple(output_values)


if __name__ == "__main__":
    main()
