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

import numpy as np


HERE = pathlib.Path(__file__).resolve().parent
MOON_NAMES = ("Io", "Europa", "Ganymede", "Callisto")
MAX_CYCLE_LENGTH = 1000000


class Moon:
    def __init__(self, name, position):
        self.name = name
        self.position = np.array(position, dtype=int)
        self.num_values, = self.position.shape
        self.velocity = np.zeros([self.num_values], dtype=int)

    @classmethod
    def from_line_3d(cls, name, line):
        pre, value = line.split("<")
        assert pre == ""
        value, post = value.split(">")
        assert post == ""
        x_eq, y_eq, z_eq = value.split(", ")
        pre, x_val = x_eq.split("x=")
        assert pre == ""
        pre, y_val = y_eq.split("y=")
        assert pre == ""
        pre, z_val = z_eq.split("z=")
        assert pre == ""
        position = int(x_val), int(y_val), int(z_val)
        return cls(name, position)

    def update_position(self):
        self.position += self.velocity

    def potential_energy(self):
        return np.sum(np.abs(self.position))

    def kinetic_energy(self):
        return np.sum(np.abs(self.velocity))

    def total_energy(self):
        return self.potential_energy() * self.kinetic_energy()

    def as_tuple(self):
        assert self.position.ndim == 1
        assert self.velocity.ndim == 1
        return tuple(self.position) + tuple(self.velocity)

    def prune(self, index):
        name = f"{self.name}:{index}"
        return Moon(name, [self.position[index]])


def update_velocities(moon1, moon2):
    assert moon1.num_values == moon2.num_values
    for i in range(moon1.num_values):
        if moon1.position[i] < moon2.position[i]:
            moon1.velocity[i] += 1
            moon2.velocity[i] += -1
        elif moon1.position[i] > moon2.position[i]:
            moon1.velocity[i] += -1
            moon2.velocity[i] += 1


def perform_timestep(moons):
    for moon1, moon2 in itertools.combinations(moons, 2):
        update_velocities(moon1, moon2)

    for moon in moons:
        moon.update_position()


def total_energy(moons):
    return sum(moon.total_energy() for moon in moons)


def prune_moons(moons, index):
    return [moon.prune(index) for moon in moons]


def as_tuple(moons):
    result = ()
    for moon in moons:
        result += moon.as_tuple()
    return result


def cycle_length(moons):
    seen = set()
    state0 = as_tuple(moons)
    seen.add(state0)
    for step in range(2, MAX_CYCLE_LENGTH):
        perform_timestep(moons)
        seen.add(as_tuple(moons))
        if len(seen) != step:
            assert as_tuple(moons) == state0
            return len(seen)

    raise RuntimeError("Did not complete", [moon.name for moon in moons])


def part1(moons, num_steps):
    moons = copy.deepcopy(moons)
    for _ in range(num_steps):
        perform_timestep(moons)
    result = total_energy(moons)
    print(f"Total energy: {result}")


def part2(moons):
    moons = copy.deepcopy(moons)
    just_x = prune_moons(moons, 0)
    just_y = prune_moons(moons, 1)
    just_z = prune_moons(moons, 2)
    cycle_lengths = []
    for moons_reduced in (just_x, just_y, just_z):
        cycle_lengths.append(cycle_length(moons_reduced))
    print(f"Universe repeats after: {np.lcm.reduce(cycle_lengths)}")


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read()

    lines = content.strip().split("\n")
    assert len(lines) == len(MOON_NAMES)

    moons = []
    for name, line in zip(MOON_NAMES, lines):
        moon = Moon.from_line_3d(name, line)
        moons.append(moon)

    part1(moons, 1000)
    part2(moons)


if __name__ == "__main__":
    main()
