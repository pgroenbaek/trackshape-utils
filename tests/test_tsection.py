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

import numpy as np
import pytest

import trackshapeutils as tsu


def test_straight_trackcenters_from_global_tsection():
    trackcenters = tsu.trackcenters_from_global_tsection("A4t50mStrt.s", num_points_per_meter=10)
    assert len(trackcenters) == 4
    assert trackcenters[0].centerpoints.shape == (500, 3)
    assert trackcenters[0].centerpoints.size == 1500
    assert np.array_equal(trackcenters[0].centerpoints[0], np.array([-7.4775, 0, 0]))
    assert np.array_equal(trackcenters[0].centerpoints[-1], np.array([-7.4775, 0, 50]))
    assert trackcenters[1].centerpoints.shape == (500, 3)
    assert trackcenters[1].centerpoints.size == 1500
    assert np.array_equal(trackcenters[1].centerpoints[0], np.array([-2.4925, 0, 0]))
    assert np.array_equal(trackcenters[1].centerpoints[-1], np.array([-2.4925, 0, 50]))
    assert trackcenters[2].centerpoints.shape == (500, 3)
    assert trackcenters[2].centerpoints.size == 1500
    assert np.array_equal(trackcenters[2].centerpoints[0], np.array([2.4925, 0, 0]))
    assert np.array_equal(trackcenters[2].centerpoints[-1], np.array([2.4925, 0, 50]))
    assert trackcenters[3].centerpoints.shape == (500, 3)
    assert trackcenters[3].centerpoints.size == 1500
    assert np.array_equal(trackcenters[3].centerpoints[0], np.array([7.4775, 0, 0]))
    assert np.array_equal(trackcenters[3].centerpoints[-1], np.array([7.4775, 0, 50]))


def test_switch_trackcenters_from_global_tsection():
    trackcenters = tsu.trackcenters_from_global_tsection("A1tPnt5dLft.s", num_points_per_meter=10)
    assert len(trackcenters) == 2
    assert trackcenters[0].centerpoints.shape == (749, 3)
    assert trackcenters[0].centerpoints.size == 2247
    assert np.array_equal(trackcenters[0].centerpoints[0], np.array([0, 0, 0]))
    np.testing.assert_allclose(trackcenters[0].centerpoints[-1], np.array([-2.49249939, 0, 74.99998559]), atol=1e-6)
    assert trackcenters[1].centerpoints.shape == (800, 3)
    assert trackcenters[1].centerpoints.size == 2400
    assert np.array_equal(trackcenters[1].centerpoints[0], np.array([0, 0, 0]))
    assert np.array_equal(trackcenters[1].centerpoints[-1], np.array([0, 0, 80]))


# def test_trackcenter_from_local_tsection(global_storage):
#     local_tsection_path = global_storage["local_tsection_path"]
#     trackcenter = tsu.trackcenter_from_local_tsection("A4t50mStrt.s", tsection_file_path=local_tsection_path, num_points_per_meter=10)
#     assert trackcenters[0].centerpoints.shape == (500, 3)
#     assert trackcenters[0].centerpoints.size == 1500
#     assert np.array_equal(trackcenters[0].centerpoints[0], np.array([-7.4775, 0, 0]))
#     assert np.array_equal(trackcenters[0].centerpoints[-1], np.array([-7.4775, 0, 50]))
#     assert trackcenters[1].centerpoints.shape == (500, 3)
#     assert trackcenters[1].centerpoints.size == 1500
#     assert np.array_equal(trackcenters[1].centerpoints[0], np.array([-2.4925, 0, 0]))
#     assert np.array_equal(trackcenters[1].centerpoints[-1], np.array([-2.4925, 0, 50]))
#     assert trackcenters[2].centerpoints.shape == (500, 3)
#     assert trackcenters[2].centerpoints.size == 1500
#     assert np.array_equal(trackcenters[2].centerpoints[0], np.array([2.4925, 0, 0]))
#     assert np.array_equal(trackcenters[2].centerpoints[-1], np.array([2.4925, 0, 50]))
#     assert trackcenters[3].centerpoints.shape == (500, 3)
#     assert trackcenters[3].centerpoints.size == 1500
#     assert np.array_equal(trackcenters[3].centerpoints[0], np.array([7.4775, 0, 0]))
#     assert np.array_equal(trackcenters[3].centerpoints[-1], np.array([7.4775, 0, 50]))