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
    data = {
        "file": tsu.load_file("DK10f_A1tPnt5dLft.sd", "./tests/data"),
        "file_copied": tsu.load_file("DK10f_A1tPnt5dLft_copied.sd", "./tests/data")
    }
    data["file_changed"] = data["file"].copy(new_filename="DK10f_A1tPnt5dLft_changed.sd")
    return data

def test_copy_file(global_storage):
    file = global_storage["file"]
    copied_file = file.copy(new_filename="DK10f_A1tPnt5dLft_copied.sd")
    assert copied_file.filename == "DK10f_A1tPnt5dLft_copied.sd"

def test_replace(global_storage):
    file = global_storage["file_changed"]
    file.replace("DK10f_A1tPnt5dLft.s", "DK10f_A1tPnt5dLft_copied.s")
    assert any(["DK10f_A1tPnt5dLft_copied.s" in line for line in file.lines])

def test_replace_ignorecase(global_storage):
    file = global_storage["file_changed"]
    file.replace_ignorecase("DK10F_A1TPNT5dLFT.s", "DK10f_A1tPnt5dLft_copied.s")
    assert any(["DK10f_A1tPnt5dLft_copied.s" in line for line in file.lines])

def test_lines_access(global_storage):
    file = global_storage["file"]
    try:
        lines = file.lines
    except Exception as e:
        pytest.fail(f"An unexpected exception occurred: {e}")
    assert isinstance(lines, list) and len(lines) > 0

def test_filepath(global_storage):
    file = global_storage["file"]
    filepath = file.filepath
    assert filepath == f"{file.directory}/{file.filename}"