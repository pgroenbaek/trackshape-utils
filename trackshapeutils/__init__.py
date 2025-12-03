"""
Track Shape Utils

This module provides various utility functions for working with track shape files, 
including loading data from tsection.dat, and geometric calculations related to track 
center points and curves.

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

__version__ = '0.5.0b3'
__all__ = [
    'generate_empty_centerpoints', 'generate_straight_centerpoints', 'generate_curve_centerpoints',
    'trackcenters_from_global_tsection', 'trackcenter_from_local_tsection',
    'find_closest_centerpoint', 'find_closest_trackcenter',
    'signed_distance_between', 'distance_between', 'distance_along_curve', 'distance_along_trackcenter',
    'get_curve_centerpoint_from_angle', 'get_straight_centerpoint_from_length', 'get_new_position_from_angle',
    'get_new_position_from_length', 'get_new_position_from_trackcenter', 'get_new_position_along_trackcenter',
    'Trackcenter'
]

__author__ = 'Peter Grønbæk Andersen <peter@grnbk.io>'


from .trackshapeutils import generate_empty_centerpoints, generate_straight_centerpoints, generate_curve_centerpoints
from .trackshapeutils import trackcenters_from_global_tsection, trackcenter_from_local_tsection
from .trackshapeutils import find_closest_centerpoint, find_closest_trackcenter
from .trackshapeutils import signed_distance_between, distance_between, distance_along_curve, distance_along_trackcenter
from .trackshapeutils import get_curve_centerpoint_from_angle, get_straight_centerpoint_from_length, get_new_position_from_angle
from .trackshapeutils import get_new_position_from_length, get_new_position_from_trackcenter, get_new_position_along_trackcenter
from .trackshapeutils import Trackcenter
