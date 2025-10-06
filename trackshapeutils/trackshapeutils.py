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

import os
import re
import math
import heapq
import codecs
import pathlib
import numpy as np
from typing import List, Optional
from scipy.interpolate import splprep, splev
from scipy.spatial import KDTree

from shapeio import shape


class Trackcenter:
    """
    Represents the centerline points of a track.

    Provides functionality for combining, comparing, and averaging
    track centerline representations.
    """

    def __init__(self, centerpoints: np.ndarray):
        """
        Initialize a Trackcenter.

        Args:
            centerpoints (np.ndarray): A 2D NumPy array of shape (N, 2) or (N, M)
                representing the coordinates of the track's centerline points.
        """
        self.centerpoints = centerpoints

    def __repr__(self):
        """
        Return a string representation of the Trackcenter object.

        The string shows the class name and the `centerpoints` array, which
        can be useful for debugging and logging.

        Returns:
            str: A string of the form "Trackcenter(centerpoints=<array>)".
        """
        return f"Trackcenter(centerpoints={self.centerpoints})"
    
    def __add__(self, other):
        """
        Combine two Trackcenter objects into a new Trackcenter.

        The method stacks the centerpoints of both objects, removes duplicates,
        and preserves the order of first appearance.

        Args:
            other (Trackcenter): Another Trackcenter instance to combine with.

        Returns:
            Trackcenter: A new Trackcenter containing the merged centerpoints.

        Raises:
            TypeError: If `other` is not a Trackcenter.
        """
        if not isinstance(other, Trackcenter):
            raise TypeError(f"Cannot add Trackcenter with {type(other).__name__}")
        
        combined_centerpoints = np.vstack((self.centerpoints, other.centerpoints))
        combined_centerpoints, idx = np.unique(combined_centerpoints, axis=0, return_index=True)
        combined_centerpoints = combined_centerpoints[np.argsort(idx)]

        return Trackcenter(combined_centerpoints)
    
    def __eq__(self, other):
        """
        Check equality between two Trackcenter objects.

        Two Trackcenters are equal if their centerpoints arrays are identical.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if `other` is a Trackcenter with identical centerpoints,
            False otherwise.
        """
        if isinstance(other, Trackcenter):
            return np.array_equal(self.centerpoints, other.centerpoints)
        return False
    
    @classmethod
    def average(cls, trackcenters: List["Trackcenter"]) -> "Trackcenter":
        """
        Compute the elementwise average of multiple Trackcenter objects.

        All Trackcenters must have centerpoints of the same shape.

        Args:
            trackcenters (List[Trackcenter]): A list of Trackcenter objects to average.

        Returns:
            Trackcenter: A new Trackcenter with centerpoints equal to the mean
            of the input centerpoints.

        Raises:
            ValueError: If the input list is empty or if Trackcenters have
            mismatched shapes.
        """
        if not isinstance(trackcenters, list):
            raise TypeError(f"""Parameter 'trackcenters' must be of type list, but got 
                {type(trackcenters).__name__}""")

        if not trackcenters:
            raise ValueError("Cannot average an empty list of Trackcenters")
        
        for trackcenter in trackcenters:
            if not isinstance(trackcenter, Trackcenter):
                raise TypeError(
                    f"""All elements of list in parameter 'trackcenters' must be Trackcenter 
                    objects, but got {type(trackcenter).__name__}"""
                )

        first_shape = trackcenters[0].centerpoints.shape
        for trackcenter in trackcenters:
            if trackcenter.centerpoints.shape != first_shape:
                raise ValueError("All Trackcenters must have the same shape to average")

        stacked = np.stack([trackcenter.centerpoints for trackcenter in trackcenters])
        averaged = np.mean(stacked, axis=0)

        return cls(averaged)


def generate_empty_centerpoints() -> Trackcenter:
    """
    Generate an empty Trackcenter with no centerline points.

    Returns:
        Trackcenter: A Trackcenter with an empty (0, 3) array of centerpoints.
    """
    centerpoints = np.empty((0, 3))

    return Trackcenter(centerpoints)


def generate_straight_centerpoints(
    length: float,
    num_points: int = 1000,
    start_angle: float = 0,
    start_point: shape.Point = shape.Point(0, 0, 0)
) -> Trackcenter:
    """
    Generate a straight Trackcenter defined by length.

    Args:
        length (float): The total length of the straight segment.
        num_points (int, optional): Number of points to generate along the line.
            Defaults to 1000.
        start_angle (float, optional): Rotation angle in degrees, applied in the X-Z plane.
            Defaults to 0.
        start_point (shape.Point, optional): Starting position of the line in 3D space.
            Defaults to shape.Point(0, 0, 0).

    Returns:
        Trackcenter: A Trackcenter containing the generated straight centerline points.
    """
    angle_radians = np.radians(start_angle)

    local_z = np.linspace(0, length, num_points)
    local_x = np.zeros_like(local_z)
    local_y = np.zeros_like(local_z)

    x_rotated = local_x * np.cos(angle_radians) - local_z * np.sin(angle_radians)
    z_rotated = local_x * np.sin(angle_radians) + local_z * np.cos(angle_radians)

    x_final = x_rotated + start_point.x
    y_final = local_y + start_point.y
    z_final = z_rotated + start_point.z

    centerpoints = np.vstack((x_final, y_final, z_final)).T

    return Trackcenter(centerpoints)


def generate_curve_centerpoints(
    curve_radius: float,
    curve_angle: float,
    num_points: int = 1000,
    start_angle: float = 0,
    start_point: shape.Point = shape.Point(0, 0, 0)
) -> Trackcenter:
    """
    Generate a curved Trackcenter segment defined by radius and angle.

    Args:
        curve_radius (float): Radius of the curve.
        curve_angle (float): Angle of the curve in degrees. Positive values
            produce a left-hand turn, negative values produce a right-hand turn.
        num_points (int, optional): Number of points to generate along the curve.
            Defaults to 1000.
        start_angle (float, optional): Initial heading angle in degrees.
            Defaults to 0.
        start_point (shape.Point, optional): Starting position of the curve in 3D space.
            Defaults to shape.Point(0, 0, 0).

    Returns:
        Trackcenter: A Trackcenter containing the generated curved centerline points.
    """
    theta = np.radians(np.linspace(0, abs(curve_angle), num_points))
    direction = -1 if curve_angle < 0 else 1

    local_x = direction * curve_radius * (1 - np.cos(theta))
    local_z = curve_radius * np.sin(theta)
    local_y = np.zeros_like(local_x)

    angle_radians = np.radians(start_angle) * direction
    cos_a = np.cos(angle_radians)
    sin_a = np.sin(angle_radians)

    x_rotated = cos_a * local_x - sin_a * local_z
    z_rotated = sin_a * local_x + cos_a * local_z

    x_final = x_rotated + start_point.x
    y_final = local_y + start_point.y
    z_final = z_rotated + start_point.z

    centerpoints = np.vstack((x_final, y_final, z_final)).T
    
    return Trackcenter(centerpoints)


def trackcenters_from_global_tsection(
    shape_name: str,
    tsection_file_path: str = None,
    include_global_tsection: bool = False,
    num_points_per_meter: int = 5,
    start_offset: shape.Point = shape.Point(0, 0, 0)
) -> List[Trackcenter]:
    """
    Generate one or more Trackcenters from a global `tsection.dat` file.

    This function parses MSTS / Open Rails style track section definitions (`tsection.dat`)
    and constructs the corresponding centerline geometry for the given track
    shape name.

    Args:
        shape_name (str): The name of the track shape to search for in `tsection.dat`.
        tsection_file_path (str, optional): Path to a `tsection.dat` file. If not
            provided, the function defaults to using the global `tsection.dat` build 60
            included with the module. Defaults to None.
        include_global_tsection (bool, optional): Whether to append the global `tsection.dat` build 60
            included with the module to the contents of the `tsection_file_path` file. Necessary only if `tsection_file_path`
            is a `tsection.dat` extension file that refers to sections in the standardised global `tsection.dat`.
            Defaults to False.
        num_points_per_meter (int, optional): Density of generated points along each
            section. Higher values produce smoother curves at the cost of performance.
            Defaults to 5.
        start_offset (shape.Point, optional): A translation applied to the starting
            point of the generated Trackcenter(s). Defaults to `shape.Point(0, 0, 0)`.

    Returns:
        List[Trackcenter]: A list of Trackcenter objects representing the full
            centerline(s) of the specified track shape.

    Raises:
        FileNotFoundError: If the file at `tsection_file_path` is missing.
        ValueError: If the specified shape is not found, or if any referenced TrackSection cannot be parsed.
    """
    tsection_text = ""

    if tsection_file_path is not None:
        if not os.path.exists(tsection_file_path):
            raise FileNotFoundError(f"""Unable to create trackcenters: Specified file '{tsection_file_path}'
                in parameter 'tsection_file_path' does not exist.""")

        with open(tsection_file_path, "r", encoding=_detect_encoding(tsection_file_path)) as f:
            tsection_text += f.read()

    if tsection_file_path is None or include_global_tsection:
        module_directory = pathlib.Path(__file__).parent
        default_tsection_file_path = f"{module_directory}/tsection.dat"

        with open(default_tsection_file_path, "r", encoding=_detect_encoding(default_tsection_file_path)) as f:
            tsection_text += "\n" + f.read()

    trackshape_pattern = re.compile(r"TrackShape\s*\(\s*\d+\s*\n(.*?)\n\s*\)", re.DOTALL)
    sectionidx_pattern = re.compile(r"SectionIdx\s*\(\s*([^\)]*?)\s*\)")

    trackshape_matches = trackshape_pattern.findall(tsection_text)

    for trackshape_match in trackshape_matches:
        if re.search(rf'FileName\s*\(\s*{re.escape(shape_name)}\s*\)', trackshape_match, re.IGNORECASE):
            trackcenters = []

            sectionidx_matches = sectionidx_pattern.findall(trackshape_match)
            section_idxs = [s.strip() for s in sectionidx_matches]

            for section_idx in section_idxs:
                trackcenter = generate_empty_centerpoints()

                values = section_idx.split()
                num_idxs = int(values[0])
                start_x, start_y, start_z = map(float, values[1:4])
                start_angle = float(values[4])
                tracksection_idxs = list(map(int, values[5:5 + num_idxs]))

                for idx, tracksection_idx in enumerate(tracksection_idxs):
                    tracksection_pattern = tracksection_pattern = re.compile(
                        rf"TrackSection\s*\(\s*({tracksection_idx})\s*\n"
                        r"\s*SectionSize\s*\(\s*([\d.]+)\s+([\d.]+)\s*\)\s*\n"
                        r"(\s*SectionCurve\s*\(\s*([\d.-]+)\s+([\d.-]+)\s*\)\s*\n)?"
                        r"\s*\)",
                        re.MULTILINE | re.DOTALL
                    )
                    tracksection_match = tracksection_pattern.search(tsection_text)

                    if not tracksection_match:
                        raise ValueError(f"""Unable to create trackcenters: Could not find TrackSection
                            '{tracksection_idx}' defined by TrackShape '{shape_name}'. Instead create 
                            the trackcenters manually using the methods 'generate_straight_centerpoints'
                            and 'generate_curve_centerpoints'.""")
                    
                    length = float(tracksection_match.group(3))
                    radius = float(tracksection_match.group(5)) if tracksection_match.group(5) else None
                    angle = float(tracksection_match.group(6)) if tracksection_match.group(6) else None

                    if idx == 0:
                        x = start_x + start_offset.x
                        y = start_y + start_offset.y
                        z = start_z + start_offset.z
                        current_path_point = shape.Point(x, y, z)
                        current_path_angle = start_angle
                    
                    if radius is not None and angle is not None:
                        curve_length = distance_along_curve(curve_angle=angle, curve_radius=radius)
                        num_points = int(curve_length * num_points_per_meter)
                        num_points = max(num_points, 10)
                        section_trackcenter = generate_curve_centerpoints(
                            curve_radius=radius,
                            curve_angle=angle,
                            start_angle=current_path_angle,
                            start_point=current_path_point,
                            num_points=num_points
                        )
                        current_path_angle += angle
                    else:
                        num_points = int(length * num_points_per_meter)
                        num_points = max(num_points, 10)
                        section_trackcenter = generate_straight_centerpoints(
                            length=length,
                            start_angle=current_path_angle,
                            start_point=current_path_point,
                            num_points=num_points
                        )
                    
                    section_endpoint = shape.Point.from_numpy(section_trackcenter.centerpoints[-1])
                    current_path_point.x = section_endpoint.x
                    current_path_point.z = section_endpoint.z

                    trackcenter += section_trackcenter
                
                trackcenters.append(trackcenter)

            return trackcenters

    raise ValueError(f"""Unable to create trackcenters: Unknown shape '{shape_name}'. Instead create 
        the trackcenters manually using the functions 'generate_straight_centerpoints'
        and 'generate_curve_centerpoints'.""")


def trackcenter_from_local_tsection(
    trackpath_idx: int,
    tsection_file_path: str,
    num_points_per_meter: int = 5,
    start_offset: shape.Point = shape.Point(0, 0, 0),
    start_angle: int = 0
) -> Trackcenter:
    """
    Generate a Trackcenter from a track path defined in a local `tsection.dat` file.

    This function parses a specific TrackPath index in the provided `tsection.dat` file
    and constructs the corresponding centerline geometry as a single `Trackcenter`.
    Use this function for shapes that rely on dyntrack tracksections, e.g. shapes created
    using DynaTrax.

    Args:
        trackpath_idx (int): The TrackPath index to read from the `tsection.dat` file.
        tsection_file_path (str): Path to the local `tsection.dat` file containing track definitions.
        num_points_per_meter (int, optional): Number of points generated per meter of track.
            Higher values produce smoother curves at the cost of performance. Defaults to 5.
        start_offset (shape.Point, optional): Translation applied to the starting point
            of the Trackcenter. Defaults to `shape.Point(0, 0, 0)`.
        start_angle (int, optional): Initial heading angle in degrees for the start of the track.
            Defaults to 0.

    Returns:
        Trackcenter: A Trackcenter object representing the reconstructed centerline for
            the specified TrackPath.

    Raises:
        FileNotFoundError: If the file at `tsection_file_path` is missing.
        ValueError: If the specified TrackPath is not found, or if any referenced SectionCurve cannot be parsed.
    """
    tsection_text = ""

    if not os.path.exists(tsection_file_path):
        raise FileNotFoundError(f"""Unable to create trackcenter: Specified file '{tsection_file_path}' in parameter
        'tsection_file_path' does not exist.""")

    with open(tsection_file_path, "r", encoding=_detect_encoding(tsection_file_path)) as f:
        tsection_text += f.read()

    trackpath_pattern = re.compile(rf"TrackPath\s*\(\s*{trackpath_idx}\s+\d+(?:\s+\d+)*\s*\)", re.DOTALL)
    trackpath_match = trackpath_pattern.search(tsection_text)

    if not trackpath_match:
        raise ValueError(f"""Unable to create trackcenter: Unknown TrackPath '{trackpath_idx}'. Instead create 
            the trackcenter manually using the functions 'generate_straight_centerpoints'
            and 'generate_curve_centerpoints'.""")

    numbers = re.findall(r'\d+', trackpath_match.group())
    tracksection_idxs = [int(n) for n in numbers[2:]]

    trackcenter = generate_empty_centerpoints()

    for idx, tracksection_idx in enumerate(tracksection_idxs):
        sectioncurve_pattern = re.compile(
            r'SectionCurve\s*\(\s*\d+\s*\)\s+'
            rf'{tracksection_idx}\s+'
            r'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s+'
            r'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)'
        )
        sectioncurve_match = re.search(sectioncurve_pattern, tsection_text)

        if not sectioncurve_match:
            raise ValueError(f"""Unable to create trackcenter: Could not find SectionCurve '{tracksection_idx}'
                defined by TrackPath '{trackpath_idx}'. Instead create the trackcenter manually using the methods
                'generate_straight_centerpoints' and 'generate_curve_centerpoints'.""")

        sectioncurve_value1 = float(sectioncurve_match.group(1))
        sectioncurve_value2 = float(sectioncurve_match.group(2))

        if idx == 0:
            current_path_point = shape.Point(start_offset.x, start_offset.y, start_offset.z)
            current_path_angle = start_angle
        
        if sectioncurve_value2 == 0:
            length = sectioncurve_value1
            num_points = int(length * num_points_per_meter)
            num_points = max(num_points, 10)
            section_trackcenter = generate_straight_centerpoints(
                length=length,
                start_angle=current_path_angle,
                start_point=current_path_point,
                num_points=num_points
            )
        else:
            angle = sectioncurve_value1
            radius = sectioncurve_value2
            curve_length = distance_along_curve(curve_angle=angle, curve_radius=radius)
            num_points = int(curve_length * num_points_per_meter)
            num_points = max(num_points, 10)
            section_trackcenter = generate_curve_centerpoints(
                curve_radius=radius,
                curve_angle=angle,
                start_angle=current_path_angle,
                start_point=current_path_point,
                num_points=num_points
            )
            current_path_angle += angle

        section_endpoint = shape.Point.from_numpy(section_trackcenter.centerpoints[-1])
        current_path_point.x = section_endpoint.x
        current_path_point.z = section_endpoint.z

        trackcenter += section_trackcenter
    
    return trackcenter


def find_closest_trackcenter(
    point_along_track: shape.Point,
    trackcenters: List[Trackcenter],
    plane: str = "xz"
) -> Trackcenter:
    """
    Find the Trackcenter whose centerline is closest to a given point.

    Args:
        point_along_track (shape.Point): The reference point along the track.
        trackcenters (List[Trackcenter]): A list of Trackcenter objects to search.
        plane (str, optional): Plane in which to measure distances. Can be "xz" or "xy".
            Defaults to "xz".

    Returns:
        Trackcenter: The Trackcenter object whose centerline has the closest point
        to the reference point.
    """
    closest_trackcenter = None
    min_distance = float('inf')

    for trackcenter in trackcenters:
        closest_centerpoint = find_closest_centerpoint(point_along_track, trackcenter, plane=plane)
        
        distance = distance_between(point_along_track, closest_centerpoint, plane=plane)

        if distance < min_distance:
            min_distance = distance
            closest_trackcenter = trackcenter

    return closest_trackcenter


def find_closest_centerpoint(
    point_along_track: shape.Point,
    trackcenter: Trackcenter,
    plane: str = "xz"
) -> shape.Point:
    """
    Find the point on a Trackcenter centerline closest to a given reference point.

    Args:
        point_along_track (shape.Point): The reference point along the track.
        trackcenter (Trackcenter): The Trackcenter to search.
        plane (str, optional): Plane in which to measure distances. Can be "xz" or "xy".
            Defaults to "xz".

    Returns:
        shape.Point: The centerline point of the Trackcenter closest to the reference point.

    Raises:
        ValueError: If `plane` is not "xz" or "xy".
    """
    point = point_along_track.to_numpy()
    centerpoints = trackcenter.centerpoints

    if plane == 'xz':
        centerpoints_2d = centerpoints[:, [0, 2]]
        point_2d = point[[0, 2]]
    elif plane == 'xy':
        centerpoints_2d = centerpoints[:, [0, 1]]
        point_2d = point[[0, 1]]
    else:
        raise ValueError("Invalid plane. Choose either 'xy' or 'xz'.")
    
    distances = np.linalg.norm(centerpoints_2d - point_2d, axis=1)
    closest_index = np.argmin(distances)

    return shape.Point.from_numpy(trackcenter.centerpoints[closest_index])


def signed_distance_between(
    point1: shape.Point,
    point2: shape.Point,
    plane: str = "xz"
) -> float:
    """
    Compute the signed distance between two points projected onto a specified plane.

    The sign of the distance depends on the relative orientation of the points
    with respect to a reference vector in the plane. For 'xyz', returns the
    standard Euclidean distance (always positive).

    Args:
        point1 (shape.Point): The first point.
        point2 (shape.Point): The second point.
        plane (str, optional): Plane onto which to project the points. Valid options:
            'x', 'y', 'z', 'xy', 'xz', 'zy', 'xyz'. Defaults to 'xz'.

    Returns:
        float: The signed distance between the points in the specified plane.
               If plane='xyz', returns the Euclidean distance (always positive).

    Raises:
        ValueError: If `plane` is not one of the allowed values.
    """
    point1 = point1.to_numpy()
    point2 = point2.to_numpy()

    if plane == "x":
        point1_proj = np.array([point1[0], 0, 0])
        point2_proj = np.array([point2[0], 0, 0])
        reference_vector = np.array([0, 1, 0])
    elif plane == "y":
        point1_proj = np.array([0, point1[1], 0])
        point2_proj = np.array([0, point2[1], 0])
        reference_vector = np.array([1, 0, 0])
    elif plane == "z":
        point1_proj = np.array([0, 0, point1[2]])
        point2_proj = np.array([0, 0, point2[2]])
        reference_vector = np.array([1, 0, 0])
    elif plane == "xy":
        point1_proj = np.array([point1[0], point1[1], 0])
        point2_proj = np.array([point2[0], point2[1], 0])
        reference_vector = np.array([1, 0, 0])
    elif plane == "xz":
        point1_proj = np.array([point1[0], 0, point1[2]])
        point2_proj = np.array([point2[0], 0, point2[2]])
        reference_vector = np.array([0, 1, 0])
    elif plane == "zy":
        point1_proj = np.array([0, point1[1], point1[2]])
        point2_proj = np.array([0, point2[1], point2[2]])
        reference_vector = np.array([1, 0, 0])
    elif plane == "xyz": # Euclidean distance, never signed.
        point1_proj = np.array([point1[0], point1[1], point1[2]])
        point2_proj = np.array([point2[0], point2[1], point2[2]])
        vector_to_point = point2_proj - point1_proj
        distance = np.linalg.norm(vector_to_point)
        return distance
    else:
        raise ValueError("Invalid plane. Choose 'x', 'y', 'z', 'xy', 'xz', 'zy', or 'xyz'.")

    vector_to_point = point1_proj - point2_proj
    cross = np.cross(reference_vector, vector_to_point)
    signed_distance = np.linalg.norm(vector_to_point[:2]) * np.sign(cross[-1])

    return signed_distance


def distance_between(
    point1: shape.Point,
    point2: shape.Point,
    plane: str = "xz"
) -> float:
    """
    Compute the absolute distance between two points projected onto a specified plane.

    This is the absolute value of `signed_distance_between`, ignoring the sign.

    Args:
        point1 (shape.Point): The first point.
        point2 (shape.Point): The second point.
        plane (str, optional): Plane onto which to project the points. Valid options:
            'x', 'y', 'z', 'xy', 'xz', 'zy', 'xyz'. Defaults to 'xz'.

    Returns:
        float: The absolute distance between the two points in the specified plane.
    """
    signed_distance = signed_distance_between(point1, point2, plane=plane)
    
    distance = abs(signed_distance)

    return distance


def distance_along_curve(
    curve_angle: float,
    curve_radius: float
) -> float:
    """
    Compute the arc length of a circular curve segment.

    Args:
        curve_angle (float): The angle of the curve in degrees.
        curve_radius (float): The radius of the curve.

    Returns:
        float: The absolute distance along the curve.
    """
    angle_radians = math.radians(curve_angle)
    
    distance = curve_radius * angle_radians
    distance = abs(distance)
    
    return distance


def distance_along_trackcenter(
    point_along_track: shape.Point,
    trackcenter: Trackcenter,
    start_point: shape.Point = shape.Point(0, 0, 0),
    max_neighbor_dist: float = 0.2
) -> Optional[float]:
    """
    Compute the distance along a Trackcenter from a starting point to a given target point.

    Both `start_point` and `point_along_track` do not need to be exactly on the trackcenter.
    The distance is measured along the centerline points, considering neighbors within 
    `max_neighbor_dist`. Returns NaN if no valid path exists.

    Args:
        point_along_track (shape.Point): The target point along the track.
        trackcenter (Trackcenter): The Trackcenter to measure along.
        start_point (shape.Point, optional): The starting point along the Trackcenter.
            Defaults to `shape.Point(0, 0, 0)`.
        max_neighbor_dist (float, optional): Maximum distance to consider a centerpoint
            as a neighbor for path calculation. Defaults to 0.2.

    Returns:
        float: Distance along the Trackcenter from the starting point to the target point.
               Returns NaN if the distance cannot be computed.
    """
    centerpoints = trackcenter.centerpoints
    centerpoints_xz = centerpoints[:, [0, 2]]

    tree = KDTree(centerpoints_xz)

    start_point_np = start_point.to_numpy()[[0, 2]]
    target_point_np = point_along_track.to_numpy()[[0, 2]]

    _, start_idx = tree.query(start_point_np)
    _, target_idx = tree.query(target_point_np)

    neighbor_dict = {
        i: tree.query_ball_point(centerpoints_xz[i], r=max_neighbor_dist)
        for i in range(len(centerpoints_xz))
    }

    queue = [(0.0, target_idx)]
    visited = set()

    distances_to_start = np.linalg.norm(centerpoints_xz - start_point_np, axis=1)

    while queue:
        distance_so_far, current_idx = heapq.heappop(queue)
        if current_idx in visited:
            continue
        visited.add(current_idx)

        if current_idx == start_idx:
            return distance_so_far

        for neighbor in neighbor_dict[current_idx]:
            if neighbor not in visited:
                step_distance = np.linalg.norm(centerpoints_xz[current_idx] - centerpoints_xz[neighbor])
                heapq.heappush(queue, (distance_so_far + step_distance, neighbor))

    # No valid path found
    return math.nan


def get_curve_centerpoint_from_angle(
    curve_radius: float,
    curve_angle: float,
    start_angle: float = 0,
    start_point: shape.Point = shape.Point(0, 0, 0)
) -> shape.Point:
    """
    Compute the 3D end point of a circular curve segment from its radius and angle.

    Args:
        curve_radius (float): The radius of the curve.
        curve_angle (float): The angle of the curve in degrees. Positive for left turns,
            negative for right turns.
        start_angle (float, optional): Initial heading angle in degrees. Defaults to 0.
        start_point (shape.Point, optional): Starting point of the curve in 3D space.
            Defaults to `shape.Point(0, 0, 0)`.

    Returns:
        shape.Point: The 3D coordinates of the end point of the curve.
    """
    theta = np.radians(abs(curve_angle))
    
    local_z = curve_radius * np.sin(theta)
    local_x = curve_radius * (1 - np.cos(theta))
    y = start_point.y

    if curve_angle < 0:
        local_x = -local_x

    angle_rad = np.radians(start_angle)
    x = start_point.x + (local_x * np.cos(angle_rad) - local_z * np.sin(angle_rad))
    z = start_point.z + (local_x * np.sin(angle_rad) + local_z * np.cos(angle_rad))

    return shape.Point.from_numpy(np.array([x, y, z]))


def get_straight_centerpoint_from_length(
    length: float,
    start_angle: float = 0,
    start_point: shape.Point = shape.Point(0, 0, 0)
) -> shape.Point:
    """
    Compute the 3D end point of a straight segment from its length.

    Args:
        length (float): Length of the straight segment.
        start_angle (float, optional): Initial heading angle in degrees. Defaults to 0.
        start_point (shape.Point, optional): Starting point of the segment in 3D space.
            Defaults to `shape.Point(0, 0, 0)`.

    Returns:
        shape.Point: The 3D coordinates of the end point of the straight segment.
    """
    theta = np.radians(start_angle)

    x = start_point.x + length * np.cos(theta)
    z = start_point.z + length * np.sin(theta)
    y = start_point.y

    return shape.Point.from_numpy(np.array([x, y, z]))


def get_new_position_from_angle(
    new_curve_radius: float,
    new_curve_angle: float,
    original_point: shape.Point,
    trackcenter: Trackcenter,
    start_angle: float = 0,
    start_point: shape.Point = shape.Point(0, 0, 0)
) -> shape.Point:
    """
    Compute a new 3D position by mapping an original point onto a new curved segment.

    The function preserves the lateral offset of the original point relative to the
    closest centerline point on the provided Trackcenter.

    Args:
        new_curve_radius (float): Radius of the new curve.
        new_curve_angle (float): Angle of the new curve in degrees.
        original_point (shape.Point): Original point to map onto the new curve.
        trackcenter (Trackcenter): Trackcenter representing the original centerline.
        start_angle (float, optional): Starting heading angle of the new curve. Defaults to 0.
        start_point (shape.Point, optional): Starting point of the new curve. Defaults to `shape.Point(0, 0, 0)`.

    Returns:
        shape.Point: The new 3D position corresponding to the original point's offset
        relative to the new curved segment.
    """
    closest_center = find_closest_centerpoint(original_point, trackcenter, plane='xz')
    offset = original_point.to_numpy() - closest_center.to_numpy()

    calculated_curve_point = get_curve_centerpoint_from_angle(new_curve_radius, new_curve_angle, start_angle)

    new_x = start_point.x + calculated_curve_point.x
    new_z = start_point.z + calculated_curve_point.z

    new_position = np.array([new_x, original_point.y, new_z]) + offset

    return shape.Point.from_numpy(new_position)


def get_new_position_from_length(
    new_length: float,
    original_point: shape.Point,
    trackcenter: Trackcenter,
    start_angle: float = 0,
    start_point: shape.Point = shape.Point(0, 0, 0)
) -> shape.Point:
    """
    Compute a new 3D position by mapping an original point onto a new straight segment.

    The function preserves the lateral offset of the original point relative to the
    closest centerline point on the provided Trackcenter.

    Args:
        new_length (float): Length of the new straight segment.
        original_point (shape.Point): Original point to map onto the new straight segment.
        trackcenter (Trackcenter): Trackcenter representing the original centerline.
        start_angle (float, optional): Starting heading angle of the new segment. Defaults to 0.
        start_point (shape.Point, optional): Starting point of the new segment. Defaults to `shape.Point(0, 0, 0)`.

    Returns:
        shape.Point: The new 3D position corresponding to the original point's offset
        relative to the new straight segment.
    """
    closest_center = find_closest_centerpoint(original_point, trackcenter, plane='xz')
    offset = original_point.to_numpy() - closest_center.to_numpy()

    calculated_straight_point = get_straight_centerpoint_from_length(new_length, start_angle)

    new_x = start_point.x + calculated_straight_point.x
    new_z = start_point.z + calculated_straight_point.z

    new_position = np.array([new_x, original_point.y, new_z]) + offset

    return shape.Point.from_numpy(new_position)


def get_new_position_from_trackcenter(
    new_signed_distance: float,
    original_point: shape.Point,
    trackcenter: Trackcenter
) -> shape.Point:
    """
    Compute a new 3D position laterally offset from a Trackcenter centerline.

    The function finds the closest point on the track center to the original point,
    computes the tangent of the centerline at that location, and applies a lateral
    offset from the track center in the plane perpendicular to the tangent to compute
    the new position.

    Args:
        new_signed_distance (float): Lateral distance to offset from the centerline.
            Positive values offset to the left, negative to the right (relative to
            the centerline tangent in the XZ plane).
        original_point (shape.Point): The original point to map from.
        trackcenter (Trackcenter): Trackcenter representing the centerline.

    Returns:
        shape.Point: New 3D position offset from the Trackcenter centerline.
    """
    centerpoints = trackcenter.centerpoints
    closest_center = find_closest_centerpoint(original_point, trackcenter, plane="xz")
    closest_center = closest_center.to_numpy()

    tck, _ = splprep(centerpoints.T, s=0)
    num_samples = 1000
    u_values = np.linspace(0, 1, num_samples)
    spline_points = np.array(splev(u_values, tck)).T

    tree = KDTree(spline_points)
    _, index = tree.query(closest_center)

    if index < len(spline_points) - 1:
        tangent_vector = spline_points[index + 1] - spline_points[index]
    else:
        tangent_vector = spline_points[index] - spline_points[index - 1]
    
    tangent_vector[1] = 0
    tangent_vector /= np.linalg.norm(tangent_vector)
    lateral_vector = np.array([-tangent_vector[2], 0, tangent_vector[0]])

    new_position = closest_center + new_signed_distance * lateral_vector

    return shape.Point.from_numpy(new_position)


def get_new_position_along_trackcenter(
    new_distance_along_track: float,
    original_point: shape.Point,
    trackcenter: Trackcenter,
    max_neighbor_dist: float = 0.2
) -> List[shape.Point]:
    """
    Compute a new 3D position along a Trackcenter centerline, preserving lateral offset.

    The function finds the closest point on the track center to the original point,
    computes the new position based on the distance along the track to the target
    location, and preserves the lateral offset of the original point relative to the centerline.

    Args:
        new_distance_along_track (float): Distance to move along the Trackcenter
            from the original point.
        original_point (shape.Point): The original point to map from.
        trackcenter (Trackcenter): Trackcenter representing the centerline.
        max_neighbor_dist (float, optional): Maximum neighbor distance used for
            computing distances along the track. Defaults to 0.2.

    Returns:
        List[shape.Point]: List containing a single 3D point at the new position
        along the Trackcenter, preserving the original lateral offset.
    """
    closest_center = find_closest_centerpoint(original_point, trackcenter, plane="xz")
    
    distance_from_start_to_closest_center = distance_along_trackcenter(
        closest_center,
        trackcenter,
        max_neighbor_dist=max_neighbor_dist
    )

    target_distance = distance_from_start_to_closest_center + new_distance_along_track

    centerpoints = trackcenter.centerpoints
    tck, _ = splprep(centerpoints.T, s=0)
    num_samples = 1000
    u_values = np.linspace(0, 1, num_samples)
    spline_points = np.array(splev(u_values, tck)).T

    distances = np.cumsum(np.linalg.norm(np.diff(spline_points, axis=0), axis=1))
    
    target_index = np.searchsorted(distances, target_distance)

    if target_index >= len(spline_points):
        target_index = len(spline_points) - 1

    new_position_on_track = spline_points[target_index]

    lateral_offset = original_point.to_numpy() - closest_center.to_numpy()
    lateral_offset[1] = 0

    new_position = new_position_on_track + lateral_offset

    return [shape.Point.from_numpy(new_position)]


def _detect_encoding(filepath: str) -> str:
    """
    Detect the text encoding of a file by inspecting its initial bytes (BOM or heuristics).

    Args:
        filepath (str): Path to the file to check.

    Returns:
        str: The detected encoding string suitable for use in `open()`.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be accessed.
        OSError: For other OS-related errors while reading the file.
    """
    with open(filepath, 'rb') as f:
        b = f.read(4)
        bstartswith = b.startswith
        if bstartswith((codecs.BOM_UTF32_BE, codecs.BOM_UTF32_LE)):
            return 'utf-32'
        if bstartswith((codecs.BOM_UTF16_BE, codecs.BOM_UTF16_LE)):
            return 'utf-16'
        if bstartswith(codecs.BOM_UTF8):
            return 'utf-8-sig'

        if len(b) >= 4:
            if not b[0]:
                return 'utf-16-be' if b[1] else 'utf-32-be'
            if not b[1]:
                return 'utf-16-le' if b[2] or b[3] else 'utf-32-le'
        elif len(b) == 2:
            if not b[0]:
                return 'utf-16-be'
            if not b[1]:
                return 'utf-16-le'
        return 'utf-8'

