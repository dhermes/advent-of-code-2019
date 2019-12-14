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
import pathlib


HERE = pathlib.Path(__file__).resolve().parent
MAX_ITERATIONS = 10000
FUEL = "FUEL"
ORE = "ORE"
DEBUG = False
TRILLION = 1000000000000
EXAMPLE_CONTENT1 = """\
10 ORE => 10 A
1 ORE => 1 B
7 A, 1 B => 1 C
7 A, 1 C => 1 D
7 A, 1 D => 1 E
7 A, 1 E => 1 FUEL"""
EXAMPLE_CONTENT2 = """\
9 ORE => 2 A
8 ORE => 3 B
7 ORE => 5 C
3 A, 4 B => 1 AB
5 B, 7 C => 1 BC
4 C, 1 A => 1 CA
2 AB, 3 BC, 4 CA => 1 FUEL"""
EXAMPLE_CONTENT3 = """\
157 ORE => 5 NZVS
165 ORE => 6 DCFZ
44 XJWVT, 5 KHKGT, 1 QDVJ, 29 NZVS, 9 GPVTF, 48 HKGWZ => 1 FUEL
12 HKGWZ, 1 GPVTF, 8 PSHF => 9 QDVJ
179 ORE => 7 PSHF
177 ORE => 5 HKGWZ
7 DCFZ, 7 PSHF => 2 XJWVT
165 ORE => 2 GPVTF
3 DCFZ, 7 NZVS, 5 HKGWZ, 10 PSHF => 8 KHKGT"""
EXAMPLE_CONTENT4 = """\
2 VPVL, 7 FWMGM, 2 CXFTF, 11 MNCFX => 1 STKFG
17 NVRVD, 3 JNWZP => 8 VPVL
53 STKFG, 6 MNCFX, 46 VJHF, 81 HVMC, 68 CXFTF, 25 GNMV => 1 FUEL
22 VJHF, 37 MNCFX => 5 FWMGM
139 ORE => 4 NVRVD
144 ORE => 7 JNWZP
5 MNCFX, 7 RFSQX, 2 FWMGM, 2 VPVL, 19 CXFTF => 3 HVMC
5 VJHF, 7 MNCFX, 9 VPVL, 37 CXFTF => 6 GNMV
145 ORE => 6 MNCFX
1 NVRVD => 8 CXFTF
1 VJHF, 6 MNCFX => 4 RFSQX
176 ORE => 6 VJHF"""
EXAMPLE_CONTENT5 = """\
171 ORE => 8 CNZTR
7 ZLQW, 3 BMBT, 9 XCVML, 26 XMNCP, 1 WPTQ, 2 MZWV, 1 RJRHP => 4 PLWSL
114 ORE => 4 BHXH
14 VRPVC => 6 BMBT
6 BHXH, 18 KTJDG, 12 WPTQ, 7 PLWSL, 31 FHTLT, 37 ZDVW => 1 FUEL
6 WPTQ, 2 BMBT, 8 ZLQW, 18 KTJDG, 1 XMNCP, 6 MZWV, 1 RJRHP => 6 FHTLT
15 XDBXC, 2 LTCX, 1 VRPVC => 6 ZLQW
13 WPTQ, 10 LTCX, 3 RJRHP, 14 XMNCP, 2 MZWV, 1 ZLQW => 1 ZDVW
5 BMBT => 4 WPTQ
189 ORE => 9 KTJDG
1 MZWV, 17 XDBXC, 3 XCVML => 2 XMNCP
12 VRPVC, 27 CNZTR => 2 XDBXC
15 KTJDG, 12 BHXH => 5 XCVML
3 BHXH, 2 VRPVC => 7 MZWV
121 ORE => 7 VRPVC
7 XCVML => 6 RJRHP
5 BHXH, 4 VRPVC => 5 LTCX"""


def debug(value, **kwargs):
    if not DEBUG:
        return
    print(value, **kwargs)


def parse_reagent(reagent):
    count, compound = reagent.split(" ")
    return int(count), compound


def parse_line(line):
    inputs_str, result = line.split(" => ")
    inputs = tuple(
        parse_reagent(command) for command in inputs_str.split(", ")
    )
    return inputs, parse_reagent(result)


def unparse_reagent(pair):
    count, compound = pair
    return f"{count} {compound}"


def unparse_reaction(inputs, output):
    output_str = unparse_reagent(output)
    input_str = ", ".join(unparse_reagent(pair) for pair in inputs)
    return f"{output_str} <= {input_str}"


def update_compounds(all_compounds, extra, reactions_by_output):
    all_compounds_next = collections.defaultdict(int)
    extra_next = copy.deepcopy(extra)
    for compound, count in all_compounds.items():
        if compound == ORE:
            all_compounds_next[compound] += count
            continue

        inputs, output = reactions_by_output[compound]
        debug(
            f"{unparse_reaction(inputs, output)} to satisfy "
            f"({count} {compound})"
        )
        output_count, output_compound = output
        assert output_compound == compound
        reaction_multiple, remainder = divmod(count, output_count)
        if remainder != 0:
            reaction_multiple += 1
            leftover = output_count - remainder
            assert reaction_multiple * output_count - leftover == count
            extra_next[output_compound] += leftover
            debug(f"++: extra_next        : {dict(extra_next)}")

        for input_count, input_compound in inputs:
            all_compounds_next[input_compound] += (
                input_count * reaction_multiple
            )
            debug(f"++: all_compounds_next: {dict(all_compounds_next)}")

    # Convert to list so we can modify `extra_next` in the loop.
    extra_pairs = list(extra_next.items())
    for compound, count in extra_pairs:
        if compound not in all_compounds_next:
            continue
        to_remove = min(all_compounds_next[compound], count)
        all_compounds_next[compound] -= to_remove
        if all_compounds_next[compound] == 0:
            all_compounds_next.pop(compound)
        extra_next[compound] -= to_remove
        debug(f"--: all_compounds_next: {dict(all_compounds_next)}")
        debug(f"--: extra_next        : {dict(extra_next)}")

    return all_compounds_next, extra_next


def just_ore(all_compounds):
    if len(all_compounds) != 1:
        return False

    return ORE in all_compounds


def determine_ore(reactions_by_output, fuel):
    all_compounds = collections.defaultdict(int)
    all_compounds[FUEL] = fuel
    extra = collections.defaultdict(int)
    debug("================")
    debug(f"-1: all_compounds    : {dict(all_compounds)}")
    debug(f"-1: extra            : {dict(extra)}")
    for i in range(MAX_ITERATIONS):
        debug("================")
        all_compounds, extra = update_compounds(
            all_compounds, extra, reactions_by_output
        )
        debug(f"{i:02}: all_compounds     : {dict(all_compounds)}")
        debug(f"{i:02}: extra             : {dict(extra)}")
        if just_ore(all_compounds):
            break

    return all_compounds[ORE]


def binary_search(predicate, start, end):
    assert predicate(start)
    if start == end:
        return start

    assert start < end
    assert not predicate(end)
    if start + 1 == end:
        return start

    midpoint = (start + end) // 2
    if predicate(midpoint):
        debug(f"new_start: {midpoint} | new_end: {end}")
        return binary_search(predicate, midpoint, end)

    debug(f"new_start: {start} | new_end: {midpoint}")
    return binary_search(predicate, start, midpoint)


class EnoughFuelPredicate:
    def __init__(self, reactions_by_output, total_ore):
        self.reactions_by_output = reactions_by_output
        self.total_ore = total_ore

    def __call__(self, fuel):
        ore_for_fuel = determine_ore(self.reactions_by_output, fuel)
        return ore_for_fuel <= self.total_ore


def how_much_fuel_under(reactions_by_output, total_ore):
    predicate = EnoughFuelPredicate(reactions_by_output, total_ore)
    min_fuel = 1
    max_fuel = 2
    # Find an upper bound on how much fuel can be produced, doubling the
    # interval at every step.
    while predicate(max_fuel):
        min_fuel = max_fuel
        max_fuel *= 2
    # Perform a binary search.
    debug(f"min_fuel: {min_fuel} | max_fuel: {max_fuel}")
    return binary_search(predicate, min_fuel, max_fuel)


def parse_content(content):
    lines = content.strip().split("\n")
    reactions_by_output = {}
    for line in lines:
        inputs, output = parse_line(line)
        _, compound = output
        if compound in reactions_by_output:
            raise KeyError(
                f"Expected exactly one reaction to produce {compound}"
            )
        reactions_by_output[compound] = inputs, output

    return reactions_by_output


def test():
    reactions_by_output1 = parse_content(EXAMPLE_CONTENT1)
    assert determine_ore(reactions_by_output1, 1) == 31

    reactions_by_output2 = parse_content(EXAMPLE_CONTENT2)
    assert determine_ore(reactions_by_output2, 1) == 165

    reactions_by_output3 = parse_content(EXAMPLE_CONTENT3)
    assert determine_ore(reactions_by_output3, 1) == 13312
    assert how_much_fuel_under(reactions_by_output3, TRILLION) == 82892753

    reactions_by_output4 = parse_content(EXAMPLE_CONTENT4)
    assert determine_ore(reactions_by_output4, 1) == 180697
    assert how_much_fuel_under(reactions_by_output4, TRILLION) == 5586022

    reactions_by_output5 = parse_content(EXAMPLE_CONTENT5)
    assert determine_ore(reactions_by_output5, 1) == 2210736
    assert how_much_fuel_under(reactions_by_output5, TRILLION) == 460664


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    reactions_by_output = parse_content(content)
    part1 = determine_ore(reactions_by_output, 1)
    print(f"ORE for 1 Fuel: {part1}")
    part2 = how_much_fuel_under(reactions_by_output, TRILLION)
    part2_ore = determine_ore(reactions_by_output, part2)
    part2_ore_over = determine_ore(reactions_by_output, part2 + 1)
    print(f"{part2_ore:,} ORE is needed for {part2} Fuel,")
    print(f"  {part2_ore_over:,} ORE is needed for {part2 + 1} Fuel")


if __name__ == "__main__":
    test()
    main()
