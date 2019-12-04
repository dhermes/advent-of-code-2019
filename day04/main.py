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

import doctest


INPUT = "245318-765747"


def meets_criteria(value):
    """Determine if a number meets the criteria

    >>> meets_criteria(111111)
    True
    >>> meets_criteria(223450)
    False
    >>> meets_criteria(123789)
    False
    """
    digits = [int(d) for d in str(value)]
    if len(digits) != 6:
        return False

    # No repeats.
    if len(set(digits)) == len(digits):
        return False

    adjacent_same = False
    prev = -1
    for d in digits:
        if d == prev:
            adjacent_same = True
        if d < prev:
            return False
        # On to the next iteration.
        prev = d

    return adjacent_same


def meets_criteria_strict(value):
    """Determine if a number meets the criteria

    >>> meets_criteria_strict(112233)
    True
    >>> meets_criteria_strict(123444)
    False
    >>> meets_criteria_strict(111111)
    False
    >>> meets_criteria_strict(111122)
    True
    >>> meets_criteria_strict(223450)
    False
    >>> meets_criteria_strict(123789)
    False
    """
    digits = [int(d) for d in str(value)]
    if len(digits) != 6:
        return False

    # No repeats.
    if len(set(digits)) == len(digits):
        return False

    streak_counts = []
    prev = -1
    current_streak = 0
    for i, d in enumerate(digits):
        if d < prev:
            return False

        if d == prev:
            current_streak += 1
            # Account for final iteration.
            if i == len(digits) - 1:
                streak_counts.append(current_streak)
        else:
            if current_streak != 0:
                streak_counts.append(current_streak)
            current_streak = 1

        # On to the next iteration.
        prev = d

    return 2 in streak_counts


def main():
    start, end = map(int, INPUT.split("-"))
    count = sum(1 for value in range(start, end + 1) if meets_criteria(value))
    print(f"Meets criteria: {count}")
    count = sum(
        1 for value in range(start, end + 1) if meets_criteria_strict(value)
    )
    print(f"Meets criteria strict: {count}")


if __name__ == "__main__":
    doctest.testmod()
    main()
