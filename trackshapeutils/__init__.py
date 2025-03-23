"""
Track Shape Utils

This module provides various utility functions for working with track shape files, 
including file handling, shape processing, and geometric calculations for track 
center points and curves. It includes functions for:

- File operations (reading, writing, ensuring directory existence)
- Shape file processing (finding track shape files, compression, and decompression)
- String and text manipulation (case-insensitive replacement)
- Geometric calculations for track center points (straight and curved track segments)
- Closest point searches and signed distance calculations
- Linking points to UV values and prim_state names
- Modification of UV values

This module is intended for use with existing track shapes to adjust them. Points in the
shape geometry can be repositioned, for example relative to the track center or along the track
for both curved and straight track shapes. This code cannot add/remove shape geometry, but you can
hide things underneath the trackbed. It will also not edit how vertices are connected.


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

__version__ = '0.2.0'
__all__ = [
    'find_directory_files', 'load_file', 'load_shape',
    'generate_empty_centerpoints', 'generate_straight_centerpoints', 'generate_curve_centerpoints',
    'generate_centerpoints_from_tsection', 'find_closest_centerpoint', 'signed_distance_between', 'distance_between',
    'distance_along_curved_track', 'distance_along_straight_track', 'distance_along_nearest_trackcenter', 'get_curve_centerpoint_from_angle',
    'get_straight_centerpoint_from_length', 'get_new_position_from_angle',
    'get_new_position_from_length', 'get_new_position_from_trackcenter',
    'PrimState', 'Point', 'UVPoint', 'Normal', 'Vertex', 'IndexedTrilist', 'File', 'Shapefile', 'Trackcenter'
]

__author__ = 'Peter Grønbæk Andersen <peter@grnbk.io>'


from .trackshapeutils import find_directory_files
from .trackshapeutils import load_file, load_shape
from .trackshapeutils import generate_empty_centerpoints, generate_straight_centerpoints, generate_curve_centerpoints
from .trackshapeutils import generate_centerpoints_from_tsection, find_closest_centerpoint, signed_distance_between, distance_between
from .trackshapeutils import distance_along_curved_track, distance_along_straight_track, distance_along_nearest_trackcenter, get_curve_centerpoint_from_angle
from .trackshapeutils import get_straight_centerpoint_from_length, get_new_position_from_angle
from .trackshapeutils import get_new_position_from_length, get_new_position_from_trackcenter
from .trackshapeutils import PrimState, Point, UVPoint, Normal, Vertex, IndexedTrilist, File, Shapefile, Trackcenter
