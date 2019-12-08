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

import pathlib

import numpy as np
import PIL.Image


HERE = pathlib.Path(__file__).resolve().parent


def main():
    filename = HERE / "input.txt"
    with open(filename, "r") as file_obj:
        content = file_obj.read().strip()

    width = 25
    height = 6
    layer_size = width * height
    num_layers, remainder = divmod(len(content), layer_size)
    assert remainder == 0

    visible = 7 * np.ones((height, width), dtype=np.uint8)

    best_layer = -1
    fewest_zeros = layer_size + 1
    for i in range(num_layers):
        layer = content[layer_size * i : layer_size * (i + 1)]
        num_zeros = layer.count("0")
        if num_zeros < fewest_zeros:
            fewest_zeros = num_zeros
            best_layer = i

        cell_index = 0
        for row in range(height):
            for col in range(width):
                if visible[row, col] == 7:
                    pixel = int(layer[cell_index])
                    if pixel in (0, 1):
                        visible[row, col] = pixel
                    elif pixel != 2:
                        raise ValueError("Bad layer", layer)
                # For next iteration
                cell_index += 1

        assert cell_index == len(layer), (cell_index, len(layer))

    layer = content[layer_size * best_layer : layer_size * (best_layer + 1)]
    num_ones = layer.count("1")
    num_twos = layer.count("2")
    print(num_ones * num_twos)

    assert np.all(visible != 7)
    image = PIL.Image.fromarray(255 - 255 * visible)
    image.save(HERE / "image.png")


if __name__ == "__main__":
    main()
