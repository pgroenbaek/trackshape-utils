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

import os
import pytest
import trackshapeutils as tsu

@pytest.fixture(scope="module")
def global_storage():
    return {
        "shape": tsu.load_shape("DK10f_A1tPnt5dLft.s", "./tests/data"),
        "shape_compressed": tsu.load_shape("DK10f_A1tPnt5dLft_compressed.s", "./tests/data")
    }

@pytest.mark.skipif(not os.path.exists("./ffeditc_unicode.exe"), reason="requires ffeditc_unicode.exe to be present in the file system")
def test_shape_compression(global_storage):
    shape = global_storage["shape"]
    copied_shape = shape.copy(new_filename="DK10f_A1tPnt5dLft_compressed.s")
    copied_shape.compress("./ffeditc_unicode.exe")
    assert copied_shape.is_compressed()

@pytest.mark.skipif(not os.path.exists("./ffeditc_unicode.exe"), reason="requires ffeditc_unicode.exe to be present in the file system")
def test_shape_decompression(global_storage):
    shape = global_storage["shape_compressed"]
    copied_shape = shape.copy(new_filename="DK10f_A1tPnt5dLft_decompressed.s")
    copied_shape.decompress("./ffeditc_unicode.exe")
    assert not copied_shape.is_compressed()