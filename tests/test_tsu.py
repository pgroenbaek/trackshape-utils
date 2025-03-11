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