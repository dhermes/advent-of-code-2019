import collections
import itertools

import numpy as np

# import sympy


Factors = collections.namedtuple("Factors", "exponent2 exponent5 residue5")


def exponent_residue(value, p):
    assert value > 0
    exponent = 0
    quotient, remainder = divmod(value, p)
    # value = p * quotient + remainder
    # quotient = (value - remainder) / p
    while remainder == 0:
        exponent += 1
        quotient, remainder = divmod(quotient, p)

    # # Here remainder != 0, so we have
    # >>> value == p**exponent * (remainder + p * quotient)
    # We'd want residue equal to (remainder + p * quotient) mod p, but
    # that is already equal to `remainder` for us.
    return exponent, remainder


def to_mod10_multiplier(factors):
    residue2 = 1
    if factors.exponent2 > 0:
        residue2 = 0

    residue5 = factors.residue5
    if factors.exponent5 > 0:
        residue5 = 0

    if residue2 == 0 and residue5 == 0:
        return 0

    if residue5 % 2 == residue2:
        return residue5

    return residue5 + 5


def mod10_series(stages):
    # (n + stages - 1) C n
    # (n + stages) C (n + 1) = [(n + stages - 1) C n] (n + stages) / (n + 1)
    n = 0
    factors = Factors(exponent2=0, exponent5=0, residue5=1)
    while True:
        yield to_mod10_multiplier(factors)
        # Update for next iteration
        n += 1
        numerator = n + stages - 1
        # NOTE: residue mod 2 must always be 1.
        numerator_exponent2, _ = exponent_residue(numerator, 2)
        numerator_exponent5, numerator_residue5 = exponent_residue(
            numerator, 5
        )
        denominator = n
        denominator_exponent2, _ = exponent_residue(denominator, 2)
        denominator_exponent5, denominator_residue5 = exponent_residue(
            denominator, 5
        )
        # since a^4 == 1 mod 5, a^{-1} == a^3 mod 5.
        residue5 = numerator_residue5 * denominator_residue5 ** 3
        residue5 %= 5

        new_exponent2 = (
            factors.exponent2 + numerator_exponent2 - denominator_exponent2
        )
        new_exponent5 = (
            factors.exponent5 + numerator_exponent5 - denominator_exponent5
        )
        assert new_exponent2 >= 0
        assert new_exponent5 >= 0
        new_residue5 = (factors.residue5 * residue5) % 5
        factors = Factors(
            exponent2=new_exponent2,
            exponent5=new_exponent5,
            residue5=new_residue5,
        )


def main():
    # expected = "84462026"
    values = tuple(int(c) for c in "03036732577212944063491565474664")
    # expected = "78725270"
    values = tuple(int(c) for c in "02935109699940807407585447034323")
    # expected = "53553731"
    values = tuple(int(c) for c in "03081770884921959731165446850517")
    # ...
    values = tuple(
        int(c)
        for c in "59702216318401831752516109671812909117759516365269440231257788008453756734827826476239905226493589006960132456488870290862893703535753691507244120156137802864317330938106688973624124594371608170692569855778498105517439068022388323566624069202753437742801981883473729701426171077277920013824894757938493999640593305172570727136129712787668811072014245905885251704882055908305407719142264325661477825898619802777868961439647723408833957843810111456367464611239017733042717293598871566304020426484700071315257217011872240492395451028872856605576492864646118292500813545747868096046577484535223887886476125746077660705155595199557168004672030769602168262"
    )

    start_index = int("".join(map(str, values[:7])))
    relative_index = start_index % len(values)
    final_index = len(values) * 10000 - 1
    # final_index = start_index + 14
    # values = sympy.symbols(" ".join(f"c{i:02}" for i in range(len(values))))

    values_repeated = itertools.cycle(values)
    # Consume until we are at ``relative_index``
    curr_cycle_index = 0
    while curr_cycle_index < relative_index:
        next(values_repeated)
        curr_cycle_index += 1

    # print(f"len(values): {len(values)}")
    # print(f"start_index: {start_index}")
    # print(f"relative_index: {relative_index}")
    # print(f"...: {values[relative_index:relative_index + 10]}")

    digits_out = np.zeros(8, dtype=int)
    multipliers = np.zeros(8, dtype=int)
    multiplier_iter = mod10_series(100)
    for index in range(start_index, final_index + 1):
        value = next(values_repeated)
        multipliers[1:] = multipliers[:-1]
        multipliers[0] = next(multiplier_iter)

        digits_out += value * multipliers
        if index % 1000 == 0:
            digits_out = np.mod(digits_out, 10)
        # print("===============")
        # print(f"value: {value}")
        # print(f"digits_out: {digits_out}")
        # print(f"multipliers: {multipliers}")

    # print("===============")
    digits_out = np.mod(digits_out, 10)
    print(digits_out)


if __name__ == "__main__":
    main()


# Stage   1: (n + 0 ) C 0
# Stage   2: (n + 1 ) C 1
# Stage   3: (n + 2 ) C 2
# Stage   4: (n + 3 ) C 3
# ...
# Stage 100: (n + 99) C 99
