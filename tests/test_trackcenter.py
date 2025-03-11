import pytest
import trackshapeutils as tsu

@pytest.fixture(scope="module")
def global_storage():
    return {
    }

def test_combine_trackcenters():
    trackcenter1 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=tsu.Point(-2.5, 0, 0))
    trackcenter2 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=tsu.Point(2.5, 0, 0))
    combined_trackcenters = trackcenter1 + trackcenter2
    assert combined_trackcenters.centerpoints.shape == (20, 3)
    assert combined_trackcenters.centerpoints.size == 60
