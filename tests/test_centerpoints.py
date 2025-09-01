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


def test_generate_empty_centerpoints_returns_trackcenter():
    trackcenter = tsu.generate_empty_centerpoints()
    assert isinstance(trackcenter, Trackcenter)


def test_generate_empty_centerpoints_shape_is_zero_by_three():
    trackcenter = tsu.generate_empty_centerpoints()
    assert trackcenter.centerpoints.shape == (0, 3)


def test_generate_straight_returns_trackcenter():
    trackcenter = tsu.generate_straight_centerpoints(10.0, num_points=5)
    assert isinstance(trackcenter, Trackcenter)
    assert trackcenter.centerpoints.shape == (5, 3)


def test_generate_straight_starts_at_start_point():
    start = Point(1, 2, 3)
    trackcenter = tsu.generate_straight_centerpoints(10.0, num_points=2, start_point=start)
    np.testing.assert_array_almost_equal(trackcenter.centerpoints[0], start.to_numpy())


def test_generate_straight_zero_length_is_constant_point():
    trackcenter = tsu.generate_straight_centerpoints(0.0, num_points=5)
    assert np.allclose(trackcenter.centerpoints, np.zeros((5, 3)))


def test_generate_straight_line_is_collinear():
    trackcenter = tsu.generate_straight_centerpoints(10.0, num_points=100, start_angle=45)
    diffs = np.diff(trackcenter.centerpoints, axis=0)
    cross_products = np.cross(diffs[:-1], diffs[1:])
    assert np.allclose(cross_products, 0, atol=1e-6)


def test_generate_curve_returns_trackcenter():
    trackcenter = tsu.generate_curve_centerpoints(5.0, 90.0, num_points=50)
    assert isinstance(trackcenter, Trackcenter)
    assert trackcenter.centerpoints.shape == (50, 3)


def test_generate_curve_starts_at_start_point():
    start = Point(2, 1, -3)
    trackcenter = tsu.generate_curve_centerpoints(5.0, 90.0, num_points=2, start_point=start)
    np.testing.assert_array_almost_equal(trackcenter.centerpoints[0], start.to_numpy())


def test_generate_curve_zero_angle_is_constant_point():
    trackcenter = tsu.generate_curve_centerpoints(5.0, 0.0, num_points=10)
    assert np.allclose(trackcenter.centerpoints, np.zeros((10, 3)))


def test_generate_curve_negative_angle_mirrors_direction():
    trackcenter_positive_curve = tsu.generate_curve_centerpoints(5.0, 90.0, num_points=50)
    trackcenter_negative_curve = tsu.generate_curve_centerpoints(5.0, -90.0, num_points=50)
    assert np.allclose(trackcenter_positive_curve.centerpoints[:, 0], -trackcenter_negative_curve.centerpoints[:, 0], atol=1e-6)
    assert np.allclose(trackcenter_positive_curve.centerpoints[:, 2], trackcenter_negative_curve.centerpoints[:, 2], atol=1e-6)


def test_generate_curve_points_are_on_circle():
    radius = 5.0
    trackcenter = tsu.generate_curve_centerpoints(radius, 180.0, num_points=200)
    x = trackcenter.centerpoints[:, 0]
    z = trackcenter.centerpoints[:, 2]
    distances = np.sqrt((x - radius) ** 2 + z**2)
    assert np.allclose(distances, radius, atol=1e-2)

