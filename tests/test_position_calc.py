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


def test_get_curve_centerpoint_from_angle_quarter_circle_left():
    result = tsu.get_curve_centerpoint_from_angle(curve_radius=1.0, curve_angle=90)
    expected = Point(1.0, 0.0, 1.0)
    np.testing.assert_allclose(result.to_numpy(), expected.to_numpy(), atol=1e-6)


def test_get_curve_centerpoint_from_angle_quarter_circle_right():
    result = tsu.get_curve_centerpoint_from_angle(curve_radius=1.0, curve_angle=-90)
    expected = Point(-1.0, 0.0, 1.0)
    np.testing.assert_allclose(result.to_numpy(), expected.to_numpy(), atol=1e-6)


def test_get_curve_centerpoint_from_angle_with_start_angle():
    result = tsu.get_curve_centerpoint_from_angle(curve_radius=2.0, curve_angle=90, start_angle=90)
    assert math.isclose(result.x, -2.0, rel_tol=1e-6)
    assert math.isclose(result.z, 2.0, rel_tol=1e-6)


def test_get_straight_centerpoint_from_length_zero_angle():
    result = tsu.get_straight_centerpoint_from_length(10.0)
    expected = Point(10.0, 0.0, 0.0)
    np.testing.assert_allclose(result.to_numpy(), expected.to_numpy())


def test_get_straight_centerpoint_from_length_ninety_angle():
    result = tsu.get_straight_centerpoint_from_length(5.0, start_angle=90)
    expected = Point(0.0, 0.0, 5.0)
    np.testing.assert_allclose(result.to_numpy(), expected.to_numpy(), atol=1e-6)


def test_get_straight_centerpoint_from_length_with_start_point():
    start_point = Point(1.0, 0.0, 1.0)
    result = tsu.get_straight_centerpoint_from_length(3.0, start_angle=0, start_point=start_point)
    expected = Point(4.0, 0.0, 1.0)
    np.testing.assert_allclose(result.to_numpy(), expected.to_numpy())


def test_get_new_position_from_angle_preserves_offset():
    trackcenter = Trackcenter(np.array([[0, 0, 0], [0, 0, 10]]))
    original_point = Point(1.0, 0.0, 5.0)
    new_point = tsu.get_new_position_from_angle(5.0, 90, original_point, trackcenter)
    assert math.isclose(new_point.x - (new_point.x - 1.0), 1.0, rel_tol=1e-6)


def test_get_new_position_from_length_preserves_offset():
    trackcenter = Trackcenter(np.array([[0, 0, 0], [10, 0, 0]]))
    original_point = Point(0.0, 0.0, 1.0)
    new_point = tsu.get_new_position_from_length(5.0, original_point, trackcenter)
    offset = new_point.z - original_point.z
    assert math.isclose(offset, 0.0, rel_tol=1e-6)


def test_get_new_position_from_length_preserves_offset():
    points = np.array([[0,0,0],[5,0,0],[10,0,0],[15,0,0]])
    trackcenter = Trackcenter(points)
    original_point = Point(0.0, 0.0, 1.0)
    new_point = tsu.get_new_position_from_length(5.0, original_point, trackcenter)
    offset = new_point.z - trackcenter.centerpoints[0, 2]
    assert math.isclose(offset, 1.0, rel_tol=1e-6)


def test_get_new_position_from_trackcenter_positive_offset():
    points = np.array([[0,0,0],[5,0,0],[10,0,0],[15,0,0]])
    trackcenter = Trackcenter(points)
    original_point = Point(0.0, 0.0, 1.0)
    new_point = tsu.get_new_position_from_trackcenter(1.0, original_point, trackcenter)
    assert new_point.z > 0


def test_get_new_position_from_trackcenter_negative_offset():
    points = np.array([[0,0,0],[5,0,0],[10,0,0],[15,0,0]])
    trackcenter = Trackcenter(points)
    original_point = Point(0.0, 0.0, -1.0)
    new_point = tsu.get_new_position_from_trackcenter(-1.0, original_point, trackcenter)
    assert new_point.z < 0


def test_get_new_position_along_trackcenter_moves_forward():
    points = np.array([[0,0,0],[5,0,0],[10,0,0],[15,0,0]])
    trackcenter = Trackcenter(points)
    original_point = Point(0.0, 0.0, 1.0)
    result_points = tsu.get_new_position_along_trackcenter(5.0, original_point, trackcenter)
    assert isinstance(result_points, list)
    assert len(result_points) == 1
    new_point = result_points[0]
    assert new_point.x > original_point.x


def test_get_new_position_along_trackcenter_preserves_lateral_offset():
    points = np.array([[0,0,0],[5,0,0],[10,0,0],[15,0,0]])
    trackcenter = Trackcenter(points)
    original_point = Point(5.0, 0.0, 2.0)
    result_points = tsu.get_new_position_along_trackcenter(5.0, original_point, trackcenter)
    new_point = result_points[0]
    assert math.isclose(new_point.z, 2.0, rel_tol=1e-6)
