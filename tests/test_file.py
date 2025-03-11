import pytest
import trackshapeutils as tsu

@pytest.fixture(scope="module")
def global_storage():
    return {
        "file": tsu.load_file("DK10f_A1tPnt5dLft.sd", "./tests/data"),
        "file_copied": tsu.load_file("DK10f_A1tPnt5dLft_copied.sd", "./tests/data")
    }

def test_load_file():
    file = tsu.load_file("DK10f_A1tPnt5dLft.sd", "./tests/data")

def test_copy_file(global_storage):
    file = global_storage["file"]
    copied_file = file.copy(new_filename="DK10f_A1tPnt5dLft_copied.sd")
    assert copied_file.filename == "DK10f_A1tPnt5dLft_copied.sd"

def test_replace(global_storage):
    file = global_storage["file_copied"]
    file.replace("DK10f_A1tPnt5dLft.s", "DK10f_A1tPnt5dLft_copied.s")
    assert any(["DK10f_A1tPnt5dLft_copied.s" in line for line in file.lines])

def test_replace_ignorecase(global_storage):
    file = global_storage["file_copied"]
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