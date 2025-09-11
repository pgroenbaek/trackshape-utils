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


def test_trackcenters_from_straight_section_in_global_tsection():
    trackcenters = tsu.trackcenters_from_global_tsection(
        "A4t50mStrt.s",
        num_points_per_meter=10
    )
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


def test_trackcenters_from_straight_section_in_global_tsection():
    trackcenters = tsu.trackcenters_from_global_tsection(
        "A4t50mStrt.s",
        num_points_per_meter=10
    )
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


def test_trackcenters_from_switch_in_global_tsection():
    trackcenters = tsu.trackcenters_from_global_tsection(
        "A1tPnt5dLft.s",
        num_points_per_meter=10
    )
    assert len(trackcenters) == 2
    assert trackcenters[0].centerpoints.shape == (749, 3)
    assert trackcenters[0].centerpoints.size == 2247
    assert np.array_equal(trackcenters[0].centerpoints[0], np.array([0, 0, 0]))
    np.testing.assert_allclose(trackcenters[0].centerpoints[-1], np.array([-2.49249939, 0, 74.99998559]), atol=1e-6)
    assert trackcenters[1].centerpoints.shape == (800, 3)
    assert trackcenters[1].centerpoints.size == 2400
    assert np.array_equal(trackcenters[1].centerpoints[0], np.array([0, 0, 0]))
    assert np.array_equal(trackcenters[1].centerpoints[-1], np.array([0, 0, 80]))


def test_trackcenters_from_custom_global_tsection(global_storage):
    custom_global_tsection_path = global_storage["global_tsection_extension_path"]
    trackcenters = tsu.trackcenters_from_global_tsection(
        "DB22f_A1t30000r0_25d_o.s",
        tsection_file_path=custom_global_tsection_path,
        num_points_per_meter=10
    )
    assert len(trackcenters) == 1
    assert trackcenters[0].centerpoints.shape == (1309, 3)
    assert trackcenters[0].centerpoints.size == 3927
    assert np.array_equal(trackcenters[0].centerpoints[0], np.array([0, 0, 0]))
    np.testing.assert_allclose(trackcenters[0].centerpoints[-1], np.array([-0.28573243, 0, 130.94003415]), atol=1e-6)


def test_trackcenters_from_nonexistant_custom_global_tsection_raises(global_storage):
    doesnotexist_path = global_storage["doesnotexist_path"]
    with pytest.raises(FileNotFoundError):
        tsu.trackcenters_from_global_tsection(
            "DB22f_A1t30000r0_25d_o.s",
            tsection_file_path=doesnotexist_path,
            num_points_per_meter=10
        )


def test_trackcenters_from_global_tsection_with_nonexistant_shapename_raises(global_storage):
    with pytest.raises(ValueError):
        tsu.trackcenters_from_global_tsection(
            "doesnotexist.s",
            num_points_per_meter=10
        )


def test_trackcenter_from_local_tsection(global_storage):
    local_tsection_path = global_storage["local_tsection_path"]
    trackcenter = tsu.trackcenter_from_local_tsection(
        50759,
        tsection_file_path=local_tsection_path,
        num_points_per_meter=10
    )
    assert trackcenter.centerpoints.shape == (257, 3)
    assert trackcenter.centerpoints.size == 771
    assert np.array_equal(trackcenter.centerpoints[0], np.array([0, 0, 0]))
    np.testing.assert_allclose(trackcenter.centerpoints[-1], np.array([0.03248401, 0, 25.89449892]), atol=1e-6)


def test_trackcenters_from_nonexistant_local_tsection_raises(global_storage):
    doesnotexist_path = global_storage["doesnotexist_path"]
    with pytest.raises(FileNotFoundError):
        tsu.trackcenter_from_local_tsection(
            50759,
            tsection_file_path=doesnotexist_path,
            num_points_per_meter=10
        )


def test_trackcenters_from_local_tsection_with_nonexistant_trackpathidx_raises(global_storage):
    local_tsection_path = global_storage["local_tsection_path"]
    with pytest.raises(ValueError):
        tsu.trackcenter_from_local_tsection(
            100000000,
            tsection_file_path=local_tsection_path,
            num_points_per_meter=10
        )
