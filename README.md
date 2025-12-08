# trackshape-utils

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/pgroenbaek/trackshape-utils?style=flat&label=Latest%20Version)](https://github.com/pgroenbaek/trackshape-utils/releases)
[![Python 3.7+](https://img.shields.io/badge/Python-3.7%2B-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License GNU GPL v3](https://img.shields.io/badge/License-%20%20GNU%20GPL%20v3%20-lightgrey?style=flat&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2NDAgNTEyIj4KICA8IS0tIEZvbnQgQXdlc29tZSBGcmVlIDYuNy4yIGJ5IEBmb250YXdlc29tZSAtIGh0dHBzOi8vZm9udGF3ZXNvbWUuY29tIExpY2Vuc2UgLSBodHRwczovL2ZvbnRhd2Vzb21lLmNvbS9saWNlbnNlL2ZyZWUgQ29weXJpZ2h0IDIwMjUgRm9udGljb25zLCBJbmMuIC0tPgogIDxwYXRoIGZpbGw9IndoaXRlIiBkPSJNMzg0IDMybDEyOCAwYzE3LjcgMCAzMiAxNC4zIDMyIDMycy0xNC4zIDMyLTMyIDMyTDM5OC40IDk2Yy01LjIgMjUuOC0yMi45IDQ3LjEtNDYuNCA1Ny4zTDM1MiA0NDhsMTYwIDBjMTcuNyAwIDMyIDE0LjMgMzIgMzJzLTE0LjMgMzItMzIgMzJsLTE5MiAwLTE5MiAwYy0xNy43IDAtMzItMTQuMy0zMi0zMnMxNC4zLTMyIDMyLTMybDE2MCAwIDAtMjk0LjdjLTIzLjUtMTAuMy00MS4yLTMxLjYtNDYuNC01Ny4zTDEyOCA5NmMtMTcuNyAwLTMyLTE0LjMtMzItMzJzMTQuMy0zMiAzMi0zMmwxMjggMGMxNC42LTE5LjQgMzcuOC0zMiA2NC0zMnM0OS40IDEyLjYgNjQgMzJ6bTU1LjYgMjg4bDE0NC45IDBMNTEyIDE5NS44IDQzOS42IDMyMHpNNTEyIDQxNmMtNjIuOSAwLTExNS4yLTM0LTEyNi03OC45Yy0yLjYtMTEgMS0yMi4zIDYuNy0zMi4xbDk1LjItMTYzLjJjNS04LjYgMTQuMi0xMy44IDI0LjEtMTMuOHMxOS4xIDUuMyAyNC4xIDEzLjhsOTUuMiAxNjMuMmM1LjcgOS44IDkuMyAyMS4xIDYuNyAzMi4xQzYyNy4yIDM4MiA1NzQuOSA0MTYgNTEyIDQxNnpNMTI2LjggMTk1LjhMNTQuNCAzMjBsMTQ0LjkgMEwxMjYuOCAxOTUuOHpNLjkgMzM3LjFjLTIuNi0xMSAxLTIyLjMgNi43LTMyLjFsOTUuMi0xNjMuMmM1LTguNiAxNC4yLTEzLjggMjQuMS0xMy44czE5LjEgNS4zIDI0LjEgMTMuOGw5NS4yIDE2My4yYzUuNyA5LjggOS4zIDIxLjEgNi43IDMyLjFDMjQyIDM4MiAxODkuNyA0MTYgMTI2LjggNDE2UzExLjcgMzgyIC45IDMzNy4xeiIvPgo8L3N2Zz4=&logoColor=%23ffffff)](https://github.com/pgroenbaek/trackshape-utils/blob/master/LICENSE)

A collection of utilities for working with MSTS and ORTS track shapes.

List of companion modules:
- [shapeio](https://github.com/pgroenbaek/shapeio) - offers functions to convert shapes between structured text format and Python objects.
- [shapeedit](https://github.com/pgroenbaek/shapeedit) - provides a wrapper for modifying the shape data structure safely.
- [pyffeditc](https://github.com/pgroenbaek/pyffeditc) - handles compression and decompression of shape files through the `ffeditc_unicode.exe` utility found in MSTS installations.
- [pytkutils](https://github.com/pgroenbaek/pytkutils) - handles compression and decompression of shape files through the `TK.MSTS.Tokens.dll` library by Okrasa Ghia.

## Installation

### Install from PyPI

```sh
pip install --upgrade trackshapeutils
```

### Install from wheel

If you have downloaded a `.whl` file from the [Releases](https://github.com/pgroenbaek/trackshape-utils/releases) page, install it with:

```sh
pip install path/to/trackshapeutils‑<version>‑py3‑none‑any.whl
```

Replace `<version>` with the actual version number in the filename.

### Install from source

```sh
git clone https://github.com/pgroenbaek/trackshape-utils.git
pip install --upgrade ./trackshape-utils
```

## Capabilities

This Python module provides additional utilities which, when used alongside [shapeedit](https://github.com/pgroenbaek/shapeedit), enable the creation of scripts to edit both straight and curved track shapes.

![DB1s to V4hs1t_RKL](https://github.com/pgroenbaek/trackshape-utils/blob/master/images/V4hs1t_RKL.png)

![DB1s curve to V4hs1t_RKL](https://github.com/pgroenbaek/trackshape-utils/blob/master/images/V4hs1t_RKL_Curve.png)


## Usage

The functionality in this module largely relies on the concept of trackcenters. These can be loaded from either a global `tsection.dat`, a local `tsection.dat` or be created manually to match whatever shape you are working on.

![Trackcenters](https://github.com/pgroenbaek/trackshape-utils/blob/master/images/Trackcenters.png)

Using trackcenters as a reference makes it easy to determine which part of the track a given vertex belongs to, which side of the track it is on, and how far from the start of the track the vertex is positioned.

Finally, trackcenters allow for calculating new positions of vertices relative to the trackcenter.

### Loading trackcenters

#### From the included global tsection.dat

Loading trackcenters is straightforward. You need to specify the shape name exactly as it appears in the global `tsection.dat`. This is not case-sensitive, but any prefixes or suffixes must be removed from shape names, e.g., `DB2f_a1t10mStrt.s` must be `a1t10mStrt.s`.

The function returns a list of trackcenters. For single-track shapes, such as `a1t10mStrt.s`, the list will contain only one item.

Additionally, the fidelity of the generated trackcenters can be controlled using the `num_points_per_meter` parameter. Smaller values make calculations faster but less accurate. This is a tradeoff that may require experimentation. Typically, 7-12 points per meter provides good results without being too slow.

```python
import trackshapeutils as tsu

trackcenters = tsu.trackcenters_from_global_tsection(
    "a1t10mStrt.s",
    num_points_per_meter=8
)
```

#### From your own global tsection.dat

If you want to use your own global `tsection.dat`, you can specify it using the `tsection_file_path` parameter.

```python
import trackshapeutils as tsu

trackcenters = tsu.trackcenters_from_global_tsection(
    "a1t10mStrt.s",
    tsection_file_path="/path/to/your/global/tsection.dat",
    num_points_per_meter=8
)
```

If you specify a _global tsection extension file_, for example from the `/OpenRails/tsection.dat` directory of a route, then set the `include_global_tsection` parameter to `True`. Otherwise, any tracksections from the standardised global `tsection.dat` cannot be found because this Python module currently does not resolve any `include (...)` statements.

Doing this appends the standardised global `tsection.dat` build \#60 to your extension file, so that any track section references within it can be found.

```python
import trackshapeutils as tsu

trackcenters = tsu.trackcenters_from_global_tsection(
    "a1t10mStrt.s",
    tsection_file_path="/path/to/your/global/extension/tsection.dat",
    include_global_tsection=True,
    num_points_per_meter=8
)
```

#### From a local tsection.dat

For any track shapes that rely on dynamic track sections, for example those created using tools like DynaTrax, you need to load the trackcenter from the local `tsection.dat`.

Here, it is not shape names but the TrackPath index that must be specified (**NOT** the TrackSection index). In other words, this refers to the number used as SectionIdx within world files.

This function returns a single trackcenter rather than a list, as these are always single-track.

```python
import trackshapeutils as tsu

trackcenter = tsu.trackcenter_from_local_tsection(
    41023,
    tsection_file_path="/path/to/your/local/tsection.dat",
    num_points_per_meter=8
)
```

#### Manual creation of trackcenters

If needed, trackcenters can also be created manually.  

These two functions normally do not need to be called directly, as they are invoked within `trackcenters_from_global_tsection` and `trackcenter_from_local_tsection`.

Trackcenters can be combined using the `+` operator or the `Trackcenter.average()` class method. The `+` operator appends points from one trackcenter to another, while `Trackcenter.average()` computes the average of corresponding points to create a new trackcenter.

```python
import trackshapeutils as tsu

# Generate a straight trackcenter
straight_trackcenter = tsu.generate_straight_centerpoints(
    length=10,
    start_angle=0,
    start_point=Point(0.0, 0.0, 0.0),
    num_points=80
)

# Generate a curved trackcenter
curved_trackcenter = tsu.generate_curve_centerpoints(
    curve_radius=1500,
    curve_angle=10,
    start_angle=0,
    start_point=Point(0.0, 0.0, 10.0),
    num_points=80
)

# Combine trackcenters by appending points from the curved trackcenter
combined_trackcenter = straight_trackcenter + curved_trackcenter

# Note: The '+' operator appends points from the second trackcenter to the first,
# preserving the order without modifying the original trackcenters.
```

If needed, trackcenters can also be averaged, for example to compute the centerline between two parallel tracks.

```python
import trackshapeutils as tsu
from trackshapeutils import Trackcenter

# Generate two parallel straight trackcenters, e.g., representing parallel tracks
straight_trackcenter1 = tsu.generate_straight_centerpoints(
    length=10,
    start_angle=0,
    start_point=Point(2.5, 0.0, 0.0),
    num_points=80
)
straight_trackcenter2 = tsu.generate_straight_centerpoints(
    length=10,
    start_angle=0,
    start_point=Point(-2.5, 0.0, 0.0),
    num_points=80
)

# Create a new trackcenter by averaging corresponding points from the two trackcenters
averaged_trackcenter = Trackcenter.average([straight_trackcenter1, straight_trackcenter2])

# Note: The averaged_trackcenter contains points located at the midpoint between
# corresponding points from straight_trackcenter1 and straight_trackcenter2.
```

### Calculating distances

#### Distance to closest trackcenter



```python
import trackshapeutils as tsu
from shapeio.shape import Point

point_along_track = Point(1.0, 1.0, 1.0)

trackcenters = tsu.trackcenters_from_global_tsection(
    "a4t10mStrt.s",
    num_points_per_meter=8
)

closest_trackcenter = tsu.find_closest_trackcenter(point_along_track, trackcenters, plane="xz")
closest_centerpoint = tsu.find_closest_centerpoint(point_along_track, closest_trackcenter, plane="xz")
distance_from_center = tsu.distance_between(point_along_track, closest_centerpoint, plane="xz")
```

Or, you can use `signed_distance_between` to be able to determine which side of the trackcenter the point is located at:

```python
signed_distance_from_center = tsu.signed_distance_between(point_along_track, closest_centerpoint, plane="xz")
```

#### Distance along the length of the track

```python
import trackshapeutils as tsu
from shapeio.shape import Point

point_along_track = Point(1.0, 1.0, 1.0)

trackcenters = tsu.trackcenters_from_global_tsection(
    "a4t10mStrt.s",
    num_points_per_meter=8
)

closest_trackcenter = tsu.find_closest_trackcenter(point_along_track, trackcenters, plane="xz")
closest_centerpoint = tsu.find_closest_centerpoint(point_along_track, closest_trackcenter, plane="xz")
distance_from_start = tsu.distance_along_trackcenter(point_along_track, closest_centerpoint, start_point=Point(0.0, 0.0, 0.0))
```

### Calculating new vertex positions

#### Perpendicular to a trackcenter

Recalculates position of `point_along_track` to be one meter further away from the closest track center.

```python
import trackshapeutils as tsu
from shapeio.shape import Point

point_along_track = Point(1.0, 1.0, 1.0)

trackcenters = tsu.trackcenters_from_global_tsection(
    "a4t10mStrt.s",
    num_points_per_meter=8
)

closest_trackcenter = tsu.find_closest_trackcenter(point_along_track, trackcenters, plane="xz")
closest_centerpoint = tsu.find_closest_centerpoint(point_along_track, closest_trackcenter, plane="xz")
signed_distance_from_center = tsu.signed_distance_between(point_along_track, closest_centerpoint, plane="xz")

if signed_distance_from_center > 0:
    new_distance = signed_distance_from_center + 1
else:
    new_distance = signed_distance_from_center - 1

new_point = tsu.get_new_position_from_trackcenter(new_distance, point_along_track, closest_trackcenter)
```

#### Along the length of a trackcenter

Move `point_along_track` 5 meters back along the track center from the original point. Keeping the XYZ offset between the original point and what was previously the closest point of the track center.

```python
import trackshapeutils as tsu
from shapeio.shape import Point

point_along_track = Point(7.0, 7.0, 1.0)

trackcenters = tsu.trackcenters_from_global_tsection(
    "a4t10mStrt.s",
    num_points_per_meter=8
)

closest_trackcenter = tsu.find_closest_trackcenter(point_along_track, trackcenters, plane="xz")
closest_centerpoint = tsu.find_closest_centerpoint(point_along_track, closest_trackcenter, plane="xz")

new_point = tsu.get_new_position_along_trackcenter(-5, closest_centerpoint, closest_trackcenter)
```

## Example Scripts

### Conversion of DB1z to V4hs_RKL slab track ([script](https://github.com/pgroenbaek/dbtracks-extras/blob/master/scripts/V4hs1t_RKL/convert_db1z1t_to_v4hs1trkl.py))

![DB1s to V4hs1t_RKL](https://github.com/pgroenbaek/trackshape-utils/blob/master/images/V4hs1t_RKL.png)

### Modifying NR_Emb with XTracks rails to fit ATracks ([script](https://github.com/pgroenbaek/nremb-atracks/blob/master/scripts/NR_Emb_AT/change_nrembrails_to_atracksrails.py))

![DB1s to V4hs1t_RKL](https://github.com/pgroenbaek/trackshape-utils/blob/master/images/NR_Emb_AT.png)

The edited NR_Emb shapes with ATracks rails are available for download at [trainsim.com](https://www.trainsim.com/forums/filelib/search-fileid?fid=90029).

## Running Tests

You can run tests manually or use `tox` to test across multiple Python versions.

### Run Tests Manually
First, install the required dependencies:

```sh
pip install pytest
```

Then, run tests with:

```sh
pytest
```

### Run Tests with `tox`

First, install the required dependencies:

```sh
pip install tox pytest
```

Then, run tests with:

```sh
tox
```

This will execute tests for all Python versions specified in `tox.ini`.


## Contributing

Contributions of all kinds are welcome. These could be suggestions, issues, bug fixes, documentation improvements, or new features.

For more details see the [contribution guidelines](https://github.com/pgroenbaek/trackshape-utils/blob/master/CONTRIBUTING.md).

## License

This Python module was created by Peter Grønbæk Andersen and is licensed under [GNU GPL v3](https://github.com/pgroenbaek/trackshape-utils/blob/master/LICENSE).

The module includes the standardized global [tsection.dat build #60](https://www.trainsim.com/forums/filelib-search-fileid?fid=88841) by Derek Morton. This file is also distributed under the GNU General Public License.
