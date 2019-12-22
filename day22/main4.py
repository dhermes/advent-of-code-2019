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

import math
import pathlib


HERE = pathlib.Path(__file__).resolve().parent


def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)


def modinv(a, m):
    g, x, _ = egcd(a, m)
    if g != 1:
        raise Exception("modular inverse does not exist")
    else:
        return x % m


class ModN:
    """Represents (aX + b) mod N."""

    def __init__(self, a, b, n):
        self.a = a
        self.b = b
        self.n = n

    def __mul__(self, other):
        assert isinstance(other, int)
        new_a = (self.a * other) % self.n
        new_b = (self.b * other) % self.n
        return ModN(new_a, new_b, self.n)

    def __rmul__(self, other):
        assert isinstance(other, int)
        return self.__mul__(other)

    def __add__(self, other):
        assert isinstance(other, int)
        new_b = (self.b + other) % self.n
        return ModN(self.a, new_b, self.n)

    def __sub__(self, other):
        assert isinstance(other, int)
        new_b = (self.b - other) % self.n
        return ModN(self.a, new_b, self.n)

    def __rsub__(self, other):
        assert isinstance(other, int)
        new_a = (-self.a) % self.n
        new_b = (other - self.b) % self.n
        return ModN(new_a, new_b, self.n)

    def __mod__(self, other):
        assert other == self.n
        return self

    def __repr__(self):
        return f"{self.a} X + {self.b} mod {self.n}"


def transform_index_new_stack(index, num_cards):
    # What happens to the **location** of a given card?
    return (num_cards - 1) - index


def transform_index_cut(index, cut, num_cards):
    # What happens to the **location** of a given card?
    return (index - cut) % num_cards


def transform_index_increment(index, increment, num_cards):
    # What happens to the **location** of a given card?
    #     i: 0,  1,  2,  3,  4,  5,  6,  7,  8,  9
    # * inc: 0,  3,  6,  9, 12, 15, 18, 21, 24, 27
    # mod n: 0,  3,  6,  9,  2,  5,  8,  1,  4,  7
    # (inv): 0,  7,  4,  1,  8,  5,  2,  9,  6,  3
    return (increment * index) % num_cards


def transform_index(cards, line, num_cards):
    if line == "deal into new stack":
        return transform_index_new_stack(cards, num_cards)

    if line.startswith("deal with increment "):
        increment = int(line[20:])
        return transform_index_increment(cards, increment, num_cards)

    if line.startswith("cut "):
        cut = int(line[4:])
        return transform_index_cut(cards, cut, num_cards)

    raise NotImplementedError(line)


def factors_below_sqrt(n):
    max_factor = math.sqrt(n)
    factor = 1
    while factor < max_factor:
        if n % factor == 0:
            yield factor
        # Next iteration
        factor += 1


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    num_cards = 119315717514047
    if False:
        num_cards = 10
        content = """\
deal into new stack
cut -2
deal with increment 7
cut 8
cut -4
deal with increment 7
cut 3
deal with increment 9
deal with increment 3
cut -1
"""

    # factors = list(factors_below_sqrt(num_cards))
    # # KNOWN TO BE: [1] i.e. num_cards = p, p prime
    # print(f"num cards factors: {factors}")
    # # KNOWN TO BE: [1, 2] i.e. num_cards = 2 * q + 1, q prime
    # factors = list(factors_below_sqrt(num_cards - 1))
    # print(f"(num cards - 1) factors: {factors}")

    # index = ModN(1, 0, num_cards)
    # lines = content.strip().split("\n")
    # for line in lines:
    #     index = transform_index(index, line, num_cards)

    index = ModN(93922407988235, 117473918147102, num_cards)

    num_applications = 101741582076661
    # a^N <-- repeated squaring

    # # a X + b
    # a = index.a
    # p = index.n
    # q, remainder = divmod(p, 2)
    # assert remainder == 1
    # print(f"q: {q}")
    # # a^(p - 1) == 1 mod p
    # # <==> a^(2q) == 1 mod p
    # # ==> a^2 == 1 (CHECKED NOPE) || a^q == 1 (MAYBE) || a^(2q) == 1 (BIG)
    # assert (a * a) % p != 1

    # a^2 X + b (a + 1)
    # a^3 X + b (a^2 + a + 1)
    # a^4 X + b (a^3 + a^2 + a + 1)
    # a^S X + b (a^S - 1) / (a - 1)
    a_S = pow(index.a, num_applications, index.n)
    assert math.gcd(index.a - 1, index.n) == 1  # PRIME, duh
    a_minus_1_inverse = modinv(index.a - 1, index.n)
    new_a = a_S
    new_b = (index.b * (a_S - 1) * a_minus_1_inverse) % index.n
    new_index = ModN(new_a, new_b, index.n)
    print(f"new_index: {new_index}")

    # aX + b == i mod n
    # X == (i - b)/a mod n
    a_inv = modinv(new_index.a, new_index.n)
    coeff_i = a_inv
    const_i = (-a_inv * new_index.b) % new_index.n
    print(f"i = {new_index}")
    print(f"X = {coeff_i} i + {const_i} mod {new_index.n}")
    position = 2020
    # what_in = (new_index.a * position + new_index.b) % new_index.n
    what_in = (coeff_i * position + const_i) % new_index.n
    print(what_in)
    # 13224103523662


if __name__ == "__main__":
    main()

# i == 7 X + 7 mod 10 <==> X == 3 i + 9 mod 10

# What position is card X in: 7 X + 7 (i.e. solve for i)
# What card is in position i: 3 i + 9 (i.e. solve for X)
# Position 3? 8
# 7(3) + 7 == 28 mod 10 (FUCK)
# 3(3) + 9 == 18 mod 10 (FUCK)
