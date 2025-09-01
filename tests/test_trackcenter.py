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
from trackshapeutils import Trackcenter
from shapeio.shape import Point


def test_trackcenters_equal():
    trackcenter1 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(0, 0, 0))
    trackcenter2 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(0, 0, 0))
    assert trackcenter1 == trackcenter2


def test_trackcenter_values_not_equal():
    trackcenter1 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(-2.5, 0, 0))
    trackcenter2 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(2.5, 0, 0))
    assert trackcenter1 != trackcenter2


def test_trackcenter_lengths_not_equal():
    trackcenter1 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(0, 0, 0))
    trackcenter2 = tsu.generate_straight_centerpoints(length=11, num_points=10, start_point=Point(0, 0, 0))
    assert trackcenter1 != trackcenter2


def test_trackcenter_num_points_not_equal():
    trackcenter1 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(0, 0, 0))
    trackcenter2 = tsu.generate_straight_centerpoints(length=10, num_points=11, start_point=Point(0, 0, 0))
    assert trackcenter1 != trackcenter2


def test_combine_trackcenters():
    trackcenter1 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(-2.5, 0, 0))
    trackcenter2 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(2.5, 0, 0))
    combined_trackcenters = trackcenter1 + trackcenter2
    assert combined_trackcenters.centerpoints.shape == (20, 3)
    assert combined_trackcenters.centerpoints.size == 60
    assert np.array_equal(combined_trackcenters.centerpoints[0], np.array([-2.5, 0, 0]))
    assert np.array_equal(combined_trackcenters.centerpoints[9], np.array([-2.5, 0, 10]))
    assert np.array_equal(combined_trackcenters.centerpoints[10], np.array([2.5, 0, 0]))
    assert np.array_equal(combined_trackcenters.centerpoints[-1], np.array([2.5, 0, 10]))


@pytest.mark.parametrize("bad_value", [
    [1, 2.0],
    "not a trackcenter",
    Point(1.0, 2.0, 3.0)
])
def test_combine_trackcenter_with_invalid_type_raises(bad_value):
    trackcenter = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(-2.5, 0, 0))
    with pytest.raises(TypeError):
        trackcenter + bad_value


def test_average_trackcenters():
    trackcenter1 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(-2.5, 0, 0))
    trackcenter2 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(2.5, 0, 0))
    combined_trackcenters = Trackcenter.average([trackcenter1, trackcenter2])
    assert combined_trackcenters.centerpoints.shape == (10, 3)
    assert combined_trackcenters.centerpoints.size == 30
    assert np.array_equal(combined_trackcenters.centerpoints[0], np.array([0, 0, 0]))
    assert np.array_equal(combined_trackcenters.centerpoints[-1], np.array([0, 0, 10]))


@pytest.mark.parametrize("bad_input", [
    [1, 2.0],
    "not a list",
    [Point(1.0, 2.0, 3.0), Point(3.0, 2.0, 1.0)]
])
def test_average_trackcenters_invalid_type_raises(bad_input):
    with pytest.raises(TypeError):
        Trackcenter.average(bad_input)


def test_average_trackcenters_empty_list_raises():
    with pytest.raises(ValueError):
        Trackcenter.average([])


def test_average_trackcenters_different_num_points_raises():
    trackcenter1 = tsu.generate_straight_centerpoints(length=10, num_points=10, start_point=Point(-2.5, 0, 0))
    trackcenter2 = tsu.generate_straight_centerpoints(length=10, num_points=11, start_point=Point(2.5, 0, 0))

    with pytest.raises(ValueError):
        Trackcenter.average([trackcenter1, trackcenter2])

