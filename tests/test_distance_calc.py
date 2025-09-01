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

import math
import numpy as np
import pytest

import trackshapeutils as tsu
from trackshapeutils import Trackcenter
from shapeio.shape import Point


def test_find_closest_centerpoint_returns_point():
    centerpoint_array = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]])
    trackcenter = Trackcenter(centerpoint_array)
    reference_point = Point(1.1, 0, 0)
    closest_point = tsu.find_closest_centerpoint(reference_point, trackcenter, plane="xz")
    assert isinstance(closest_point, Point)
    np.testing.assert_array_almost_equal(closest_point.to_numpy(), [1, 0, 0])


def test_find_closest_centerpoint_invalid_plane_raises():
    trackcenter = Trackcenter(np.array([[0, 0, 0], [1, 1, 1]]))

    with pytest.raises(ValueError):
        tsu.find_closest_centerpoint(Point(0, 0, 0), trackcenter, plane="bad")


def test_find_closest_trackcenter_selects_nearest_trackcenter():
    trackcenter_near = Trackcenter(np.array([[0, 0, 0], [1, 0, 0]]))
    trackcenter_far = Trackcenter(np.array([[10, 0, 0], [11, 0, 0]]))
    reference_point = Point(0.5, 0, 0)
    closest_trackcenter = tsu.find_closest_trackcenter(reference_point, [trackcenter_near, trackcenter_far])
    assert closest_trackcenter is trackcenter_near


@pytest.mark.parametrize("plane", ["x", "y", "z", "xy", "xz", "zy", "xyz"])
def test_signed_distance_between_returns_float(plane):
    point1 = Point(0, 0, 0)
    point2 = Point(1, 1, 1)
    distance = tsu.signed_distance_between(point1, point2, plane=plane)
    assert isinstance(distance, float)


def test_signed_distance_between_xyz_is_always_positive():
    point1 = Point(0, 0, 0)
    point2 = Point(3, 4, 0)
    distance = tsu.signed_distance_between(point1, point2, plane="xyz")
    assert math.isclose(distance, 5.0)


def test_signed_distance_between_invalid_plane_raises():
    with pytest.raises(ValueError):
        tsu.signed_distance_between(Point(0, 0, 0), Point(1, 0, 0), plane="bad")


def test_distance_between_matches_absolute_signed_distance():
    point1 = Point(0, 0, 0)
    point2 = Point(1, 0, 0)
    signed_distance = tsu.signed_distance_between(point1, point2, "xz")
    absolute_distance = tsu.distance_between(point1, point2, "xz")
    assert absolute_distance == abs(signed_distance)


def test_distance_along_curve_positive_angle():
    distance = tsu.distance_along_curve(180, 2.0)
    assert math.isclose(distance, math.pi * 2.0)


def test_distance_along_curve_negative_angle_returns_positive():
    distance = tsu.distance_along_curve(-90, 4.0)
    assert math.isclose(distance, math.pi / 2 * 4.0)


def test_distance_along_trackcenter_straight_line():
    centerpoint_array = np.array([[x, 0, 0] for x in range(11)])
    trackcenter = Trackcenter(centerpoint_array)
    target_point = Point(10, 2, 0)
    distance = tsu.distance_along_trackcenter(target_point, trackcenter, start_point=Point(0, 0, 0), max_neighbor_dist=1.1)
    assert math.isclose(distance, 10.0, rel_tol=1e-5)


def test_distance_along_trackcenter_returns_none_if_not_found():
    trackcenter = Trackcenter(np.array([[0, 0, 0], [1, 0, 0]]))
    target_point = Point(1, 0, 0)
    distance = tsu.distance_along_trackcenter(target_point, trackcenter, max_neighbor_dist=1e-6)
    assert math.isnan(distance)
