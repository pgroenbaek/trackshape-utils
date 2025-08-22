# trackshape-utils

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/pgroenbaek/trackshape-utils?style=flat&label=Latest%20Version)](https://github.com/pgroenbaek/trackshape-utils/releases)
[![Python 3.6+](https://img.shields.io/badge/Python-3.6%2B-blue?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License GNU GPL v3](https://img.shields.io/badge/License-%20%20GNU%20GPL%20v3%20-lightgrey?style=flat&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2NDAgNTEyIj4KICA8IS0tIEZvbnQgQXdlc29tZSBGcmVlIDYuNy4yIGJ5IEBmb250YXdlc29tZSAtIGh0dHBzOi8vZm9udGF3ZXNvbWUuY29tIExpY2Vuc2UgLSBodHRwczovL2ZvbnRhd2Vzb21lLmNvbS9saWNlbnNlL2ZyZWUgQ29weXJpZ2h0IDIwMjUgRm9udGljb25zLCBJbmMuIC0tPgogIDxwYXRoIGZpbGw9IndoaXRlIiBkPSJNMzg0IDMybDEyOCAwYzE3LjcgMCAzMiAxNC4zIDMyIDMycy0xNC4zIDMyLTMyIDMyTDM5OC40IDk2Yy01LjIgMjUuOC0yMi45IDQ3LjEtNDYuNCA1Ny4zTDM1MiA0NDhsMTYwIDBjMTcuNyAwIDMyIDE0LjMgMzIgMzJzLTE0LjMgMzItMzIgMzJsLTE5MiAwLTE5MiAwYy0xNy43IDAtMzItMTQuMy0zMi0zMnMxNC4zLTMyIDMyLTMybDE2MCAwIDAtMjk0LjdjLTIzLjUtMTAuMy00MS4yLTMxLjYtNDYuNC01Ny4zTDEyOCA5NmMtMTcuNyAwLTMyLTE0LjMtMzItMzJzMTQuMy0zMiAzMi0zMmwxMjggMGMxNC42LTE5LjQgMzcuOC0zMiA2NC0zMnM0OS40IDEyLjYgNjQgMzJ6bTU1LjYgMjg4bDE0NC45IDBMNTEyIDE5NS44IDQzOS42IDMyMHpNNTEyIDQxNmMtNjIuOSAwLTExNS4yLTM0LTEyNi03OC45Yy0yLjYtMTEgMS0yMi4zIDYuNy0zMi4xbDk1LjItMTYzLjJjNS04LjYgMTQuMi0xMy44IDI0LjEtMTMuOHMxOS4xIDUuMyAyNC4xIDEzLjhsOTUuMiAxNjMuMmM1LjcgOS44IDkuMyAyMS4xIDYuNyAzMi4xQzYyNy4yIDM4MiA1NzQuOSA0MTYgNTEyIDQxNnpNMTI2LjggMTk1LjhMNTQuNCAzMjBsMTQ0LjkgMEwxMjYuOCAxOTUuOHpNLjkgMzM3LjFjLTIuNi0xMSAxLTIyLjMgNi43LTMyLjFsOTUuMi0xNjMuMmM1LTguNiAxNC4yLTEzLjggMjQuMS0xMy44czE5LjEgNS4zIDI0LjEgMTMuOGw5NS4yIDE2My4yYzUuNyA5LjggOS4zIDIxLjEgNi43IDMyLjFDMjQyIDM4MiAxODkuNyA0MTYgMTI2LjggNDE2UzExLjcgMzgyIC45IDMzNy4xeiIvPgo8L3N2Zz4=&logoColor=%23ffffff)](/LICENSE)

> 🚧 **Version 0.5.0 Status: In Development**  
> This version is not feature-complete and is still being actively developed.  
> Expect missing functionality, incomplete features, and frequent changes.

A collection of utilities for working with MSTS/ORTS track shapes. 

List of companion modules:
- [shapeio](https://github.com/pgroenbaek/shapeio) - offers functions to convert shapes between structured text format and Python objects.
- [shapeedit](https://github.com/pgroenbaek/shapeedit) - provides a wrapper for modifying the shape data structure safely.
- [pytkutils](https://github.com/pgroenbaek/pytkutils) - handles compression and decompression of shape files through the `TK.MSTS.Tokens.dll` library by Okrasa Ghia.

## Installation

<!-- ### Install from PyPI

```sh
pip install --upgrade trackshapeutils
```

### Install from wheel

If you have downloaded a `.whl` file from the [Releases](https://github.com/pgroenbaek/trackshape-utils/releases) page, install it with:

```sh
pip install path/to/trackshapeutils‑<version>‑py3‑none‑any.whl
```

Replace `<version>` with the actual version number in the filename. For example:

```sh
pip install path/to/trackshapeutils-0.5.0b0-py3-none-any.whl
``` -->

### Install from source

```sh
git clone https://github.com/pgroenbaek/trackshape-utils.git
pip install --upgrade ./trackshape-utils
```

## Usage

<!-- See [shapeio](https://github.com/pgroenbaek/shapeio) for loading shapes into Python. See [shapeedit](https://github.com/pgroenbaek/shapeedit) for functions to modify shapes while keeping them error-free and usable in MSTS/ORTS. -->

TODO

<!-- ### Loading trackcenters

#### From the included global tsection.dat

#### From your own global tsection.dat

#### From a local tsection.dat


### Manual creation of trackcenters



### Combining trackcenters


### Calculating distance to trackcenter


### Calculating new positions

#### Perpendicular to a trackcenter

#### Along the length of a trackcenter





### Working with trackcenters

Trackcenters make it easy to work with track shapes using the same generalized scripting logic, no matter if the track shapes are curved, straight, or have multiple parallel tracks.

The trackcenters can be loaded using the `generate_trackcenters_from_global_tsection` function, either from the global *tsection.dat* Build \#60 included with the Python module or from a file you provide. The function returns a list of trackcenters, each corresponding to a parallel track. For single-track sections, there will be only one item in the list.

You can also use `generate_trackcenters_from_local_tsection` to load data from a local *tsection.dat* file if you want to, for example, modify dynamic track section shapes generated with DynaTrax.

If needed, trackcenters can also be created manually using `generate_curve_centerpoints` and `generate_straight_centerpoints`. The functions that load from *tsection.dat* files use these internally.

The example below shows how to use `find_closest_trackcenter`, `find_closest_centerpoint`, and `signed_distance_between` to calculate the distance from a vertex to the nearest trackcenter. This is essential for generalizing your scripting logic. 

By using the distance from the center, you can easily determine which part of the track a vertex belongs to, regardless of whether the track section is curved, straight, or has multiple parallel tracks.

To calculate new vertex positions relative to the trackcenter, you can use `get_new_position_from_trackcenter` to adjust the distance from the center, and `get_new_position_along_trackcenter` to adjust the position along the trackcenter.


```python
import trackshapeutils as tsu

shape_load_path = "./examples/data"
shape_processed_path = "./examples/data/processed"

sfile_name = 'DB1s_a2t500r20d.s'
new_sfile_name = 'DB1s_a2t500r20d_modified.s'

sfile = tsu.load_shape(sfile_name, shape_load_path)
new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)

# Create trackcenter objects based on data in the global tsection.dat
# Name must match the names defined within the global tsection.dat, so replace 'DB1s_' with nothing.
tsection_sfile_name = sfile_name.replace('DB1s_', '')
trackcenters = tsu.generate_trackcenters_from_global_tsection(shape_name=tsection_sfile_name, num_points_per_meter=7)

# Get all vertices in lod_dlevel 500.
lod_dlevel = 500
subobject_idxs = new_sfile.get_subobject_idxs_in_lod_dlevel(lod_dlevel)

for subobject_idx in subobject_idxs:
    vertices_in_subobject = new_sfile.get_vertices_in_subobject(lod_dlevel, subobject_idx)

    for vertex in vertices_in_subobject:
        # Calculate distance from the closest track center to the vertex point in the xz-plane.
        closest_trackcenter = tsu.find_closest_trackcenter(vertex.point, trackcenters, plane="xz")
        closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, closest_trackcenter, plane="xz")
        distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")

        # Calculate and set a new position based on distance to the closest track center (perpendicular to the closest track center).
        new_distance_from_center = -1.4125
        new_position_from_center = tsu.get_new_position_from_trackcenter(new_distance_from_center, vertex.point, closest_trackcenter)
        vertex.point.x = new_position_from_center.x
        vertex.point.y = new_position_from_center.y
        vertex.point.z = new_position_from_center.z
        new_sfile.update_vertex(vertex)

        # Calculate and set a new position based on distance along closest track center from Point(0.0, 0.0, 0.0).
        new_distance_along_track = 10
        new_position_along_track = tsu.get_new_position_along_trackcenter(new_distance_along_track, vertex.point, closest_trackcenter)
        vertex.point.x = new_position_along_track.x
        vertex.point.y = new_position_along_track.y
        vertex.point.z = new_position_along_track.z
        new_sfile.update_vertex(vertex)

new_sfile.save()
```

## Example Scripts

### Converting DB1s to DB1fb ([script](./examples/convert_db1s_to_db1fb.py))

The DBTracks track system includes many track variants, such as with different textures, various types of sleepers, and other differences like the presence or absence of overhead wires and the German LZB cable. For some variants, such as DB1fb, not all track sections are available.

However, DB1fb sections can easily be created from DB1s sections by changing the textures and removing the LZB cable.

That is exactly what this simple script does for both curved and straight track. The script was created before the functionality to remove triangles was added, so the LZB cable is hidden by moving it below the track bed. -->

<!-- Image showing a shape before and after running the script: -->

<!-- ![Before and after running the script](./examples/images/convert_db1s_to_db1fb.png) -->

<!-- ### Creating ATracks railheads from NR_Emb railheads ([script](./examples/change_nrembrails_to_atracksrails.py))

The old XTracks track system was created in the early 2000s and features completely square railheads. More modern track systems, such as ATracks, do not. The difference is very noticeable if you try to combine the two.

Norbert Rieger's old NR_Emb shapes with integrated railheads have railhead geometry that matches that of XTracks, making those shapes visually incompatible with ATracks.

This script adjusts the XTracks-style railheads in the NR_Emb shapes to match the geometry of ATracks. The script is fairly advanced and supports both straight and curved track sections, as well as multiple parallel tracks. Within the script, new geometry is quite literally being built and appended to the existing railheads. -->

<!-- Image showing a shape before and after running the script: -->

<!-- ![Before and after running the script](./examples/images/change_nrembrails_to_atracksrails.png) -->

<!-- The edited NR_Emb shapes are available for download at [trainsim.com](https://www.trainsim.com/forums/filelib/search-fileid?fid=90029).

### Copying overhead wire from one shape to another ([script](./examples/make_ohw_dblslip7_5d.py))

This is another fairly advanced script that copies the overhead wire from one of Norbert Rieger's **DblSlip7\_5d** shapes into the animated **DblSlip7\_5d** shapes created by Laci1959.

Shapes can use different internal coordinate systems. These coordinate systems are transformed into world space using the `matrix ( ... )` definitions found inside the shape files.

The script handles remapping the points and normals to align with the internal coordinate system of Laci1959's shapes. Without this step, the copied geometry would appear in the wrong position when the edited shape is rendered.

<!-- Image showing a shape before and after running the script: -->

<!-- ![Before and after running the script](./examples/images/make_ohw_dblslip7_5d.png) -->

<!-- The edited DblSlip7\_5d shapes are available for download at [the-train.de](https://the-train.de/downloads/entry/11283-dbtracks-doppelte-kreuzungsweiche-dkw-7-5/).

### Additional examples

There are further example scripts available in [this repository](https://github.com/pgroenbaek/openrails-route-dk24-objects/tree/master/Scripts/DBTracks). -->


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


## Run Tests with `tox`

`tox` allows you to test across multiple Python environments.

### **1. Install `tox`**
```sh
pip install tox
```

### **2. Run Tests**
```sh
tox
```

This will execute tests in all specified Python versions.

### **3. `tox.ini` Configuration**
The `tox.ini` file should be in your project root:

```ini
[tox]
envlist = py36, py37, py38, py39, py310

[testenv]
deps = pytest
commands = pytest
```

Modify `envlist` to match the Python versions you want to support.

## License

This Python module was created by Peter Grønbæk Andersen and is licensed under [GNU GPL v3](/LICENSE).

The module includes the standardized global [tsection.dat build #60](https://www.trainsim.com/forums/filelib-search-fileid?fid=88841) by Derek Morton. This file is also distributed under the GNU General Public License.
