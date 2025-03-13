"""
This file is part of Track Shape Utils.

Copyright (C) 2025 Peter Grønbæk Andersen <peter@grnbk.io>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import pytest
import trackshapeutils as tsu

@pytest.fixture(scope="module")
def global_storage():
    return {
        "file": tsu.load_file("DK10f_A1tPnt5dLft.sd", "./tests/data"),
        "shape": tsu.load_shape("DK10f_A1tPnt5dLft.s", "./tests/data"),
        "compressed_shape": tsu.load_shape("DK10f_A1tPnt5dLft_compressed.s", "./tests/data")
    }

def test_find_directory_files():
    files = tsu.find_directory_files("./tests/data", ["*.s"], ["*.sd"])
    assert not any([line.endswith(".sd") for line in files])
    assert all([line.endswith(".s") for line in files])

def test_load_file():
    file = tsu.load_file("DK10f_A1tPnt5dLft.sd", "./tests/data")

def test_load_shape():
    filename = "DK10f_A1tPnt5dLft.s"
    shape = tsu.load_shape(filename, "./tests/data")
    assert shape.filename == filename

def test_generate_empty_centerpoints():
    trackcenter = tsu.generate_empty_centerpoints()
    assert trackcenter.centerpoints.size == 0

def test_generate_straight_centerpoints():
    trackcenter = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=tsu.Point(0, 0, 0))
    assert trackcenter.centerpoints.shape == (10, 3)
    assert trackcenter.centerpoints.size == 30

def test_generate_curve_centerpoints():
    trackcenter = tsu.generate_curve_centerpoints(curve_angle=20, curve_radius=500, num_points=10, start_point=tsu.Point(0, 0, 0))
    assert trackcenter.centerpoints.shape == (10, 3)
    assert trackcenter.centerpoints.size == 30