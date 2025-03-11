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
    }

def test_combine_trackcenters():
    trackcenter1 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=tsu.Point(-2.5, 0, 0))
    trackcenter2 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=tsu.Point(2.5, 0, 0))
    combined_trackcenters = trackcenter1 + trackcenter2
    assert combined_trackcenters.centerpoints.shape == (20, 3)
    assert combined_trackcenters.centerpoints.size == 60
