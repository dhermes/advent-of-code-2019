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
import pathlib


HERE = pathlib.Path(__file__).resolve().parent


def fuel_needed(mass):
    """Compute fuel required for a module given the mass.

    Fuel required to launch a given module is based on its mass. Specifically,
    to find the fuel required for a module, take its mass, divide by three,
    round down, and subtract 2.

    For example:

    * For a mass of 12, divide by 3 and round down to get 4, then subtract 2
      to get 2.
    * For a mass of 14, dividing by 3 and rounding down still yields 4, so the
      fuel required is also 2.
    * For a mass of 1969, the fuel required is 654.
    * For a mass of 100756, the fuel required is 33583.

    >>> fuel_needed(12)
    2
    >>> fuel_needed(14)
    2
    >>> fuel_needed(1969)
    654
    >>> fuel_needed(100756)
    33583
    """
    return max(mass // 3 - 2, 0)


def fuel_needed_account_for_fuel(mass):
    """Compute fuel required for a module (and its fuel) given the mass.

    So, for each module mass, calculate its fuel and add it to the total.
    Then, treat the fuel amount you just calculated as the input mass and
    repeat the process, continuing until a fuel requirement is zero or
    negative. For example:

    * A module of mass 14 requires 2 fuel. This fuel requires no further fuel
      (2 divided by 3 and rounded down is 0, which would call for a negative
      fuel), so the total fuel required is still just 2.
    * At first, a module of mass 1969 requires 654 fuel. Then, this fuel
      requires 216 more fuel (654 / 3 - 2). 216 then requires 70 more fuel,
      which requires 21 fuel, which requires 5 fuel, which requires no further
      fuel. So, the total fuel required for a module of mass 1969 is
      654 + 216 + 70 + 21 + 5 = 966.
    * The fuel required by a module of mass 100756 and its fuel is:
      33583 + 11192 + 3728 + 1240 + 411 + 135 + 43 + 12 + 2 = 50346.

    >>> fuel_needed_account_for_fuel(14)
    2
    >>> fuel_needed_account_for_fuel(1969)
    966
    >>> fuel_needed_account_for_fuel(100756)
    50346
    """
    total_fuel = 0
    last_used = fuel_needed(mass)
    while last_used > 0:
        total_fuel += last_used
        last_used = fuel_needed(last_used)

    return total_fuel


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    total_fuel = 0
    total_fuel_with_accounting = 0
    for line in content.strip().split("\n"):
        mass = int(line)
        total_fuel += fuel_needed(mass)
        total_fuel_with_accounting += fuel_needed_account_for_fuel(mass)

    print(f"Total fuel: {total_fuel}")
    print(f"Total fuel with accounting: {total_fuel_with_accounting}")


if __name__ == "__main__":
    doctest.testmod()
    main()
