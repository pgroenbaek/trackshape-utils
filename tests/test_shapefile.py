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
        "shape": tsu.load_shape("DK10f_A1tPnt5dLft.s", "./tests/data"),
        "compressed_shape": tsu.load_shape("DK10f_A1tPnt5dLft_compressed.s", "./tests/data")
    }

def test_load_shape():
    filename = "DK10f_A1tPnt5dLft.s"
    shape = tsu.load_shape(filename, "./tests/data")
    assert shape.filename == filename

def test_shape_compression():
    shape = tsu.load_shape("DK10f_A1tPnt5dLft.s", "./tests/data")
    copied_shape = shape.copy(new_filename="DK10f_A1tPnt5dLft_compressed.s")
    copied_shape.compress("./ffeditc_unicode.exe")
    assert copied_shape.is_compressed()

def test_shape_decompression():
    shape = tsu.load_shape("DK10f_A1tPnt5dLft_compressed.s", "./tests/data")
    copied_shape = shape.copy(new_filename="DK10f_A1tPnt5dLft_decompressed.s")
    copied_shape.decompress("./ffeditc_unicode.exe")
    assert not copied_shape.is_compressed()

def test_shape_is_compressed(global_storage):
    shape = global_storage["compressed_shape"]
    assert shape.is_compressed()

def test_shape_is_not_compressed(global_storage):
    shape = global_storage["shape"]
    assert not shape.is_compressed()

def test_shape_repl_uncompressed(global_storage):
    shape = global_storage["shape"]
    shape_string = str(shape)
    assert 'compressed=False' in shape_string
    assert 'lines' in shape_string

def test_shape_repl_compressed(global_storage):
    shape = global_storage["compressed_shape"]
    shape_string = str(shape)
    assert 'compressed=True' in shape_string

def test_lines_access(global_storage):
    shape = global_storage["shape"]
    try:
        lines = shape.lines
    except Exception as e:
        pytest.fail(f"An unexpected exception occurred: {e}")
    assert isinstance(lines, list) and len(lines) > 0

def test_lines_access_denied(global_storage):
    shape = global_storage["compressed_shape"]
    with pytest.raises(AttributeError) as exc_info:
        lines = shape.lines

# TODO Test remaining methods as I make them