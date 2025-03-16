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
import fnmatch
import subprocess
import re
import copy
import codecs
import shutil
import pathlib
import numpy as np
from scipy.interpolate import splprep, splev
from scipy.spatial import KDTree
from typing import List, Dict, Optional


def _detect_encoding(filepath):
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


class PrimState:
    def __init__(self, idx: int, name: str):
        self.idx = idx
        self.name = name
    
    def __repr__(self):
        return f"PrimState(idx={self.idx}, name={self.name})"


class Point:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z
    
    def __repr__(self):
        return f"Point(x={self.x}, y={self.y}, z={self.z})"
    
    def to_numpy(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    @classmethod
    def from_numpy(cls, array: np.ndarray):
        if array.shape != (3,):
            raise ValueError("Input array must have shape (3,).")
        return cls(array[0], array[1], array[2])


class UVPoint:
    def __init__(self, u: float, v: float):
        self.u = u
        self.v = v
    
    def __repr__(self):
        return f"UVPoint(u={self.u}, v={self.v})"
    
    def to_numpy(self) -> np.ndarray:
        return np.array([self.u, self.v])

    @classmethod
    def from_numpy(cls, array: np.ndarray):
        if array.shape != (2,):
            raise ValueError("Input array must have shape (2,).")
        return cls(array[0], array[1])


class Normal:
    def __init__(self, vec_x: float, vec_y: float, vec_z: float):
        self.vec_x = vec_x
        self.vec_y = vec_y
        self.vec_z = vec_z
    
    def __repr__(self):
        return f"Normal(vec_x={self.vec_x}, vec_y={self.vec_y}, vec_z={self.vec_z})"
    
    def to_numpy(self) -> np.ndarray:
        return np.array([self.vec_x, self.vec_y, self.vec_z])

    @classmethod
    def from_numpy(cls, array: np.ndarray):
        if array.shape != (3,):
            raise ValueError("Input array must have shape (3,).")
        return cls(array[0], array[1], array[2])


class Vertex:
    def __init__(self, vertex_idx: int, point: Point, uv_point: UVPoint, normal: Normal, point_idx: int, uv_point_idx: int, normal_idx: int, \
            lod_dlevel: int, subobject_idx: int):
        self.point = point
        self.uv_point = uv_point
        self.normal = normal
        self._vertex_idx = vertex_idx
        self._point_idx = point_idx
        self._uv_point_idx = uv_point_idx
        self._normal_idx = normal_idx
        self._lod_dlevel = lod_dlevel
        self._subobject_idx = subobject_idx
    
    def __repr__(self):
        return f"""Vertex(vertex_idx={self._vertex_idx}, point={self.point}, point_idx={self._point_idx}, uv_point={self.uv_point}, 
            uv_point_idx={self._uv_point_idx}, normal={self.normal}, normal_idx={self._normal_idx},
            lod_dlevel={self._lod_dlevel}, subobject_idx={self._subobject_idx})"""

    def __eq__(self, other):
        if isinstance(other, Vertex):
            return all([
                self._vertex_idx == other._vertex_idx,
                self._subobject_idx == other._subobject_idx,
                self._lod_dlevel == other._lod_dlevel
            ])
        return False
    
    @property
    def vertex_idx(self) -> int:
        return self._vertex_idx
    
    @property
    def point_idx(self) -> int:
        return self._point_idx
    
    @property
    def uv_point_idx(self) -> int:
        return self._uv_point_idx
    
    @property
    def normal_idx(self) -> int:
        return self._normal_idx
    
    @property
    def lod_dlevel(self) -> int:
        return self._lod_dlevel
    
    @property
    def subobject_idx(self) -> int:
        return self._subobject_idx


class IndexedTrilist:
    def __init__(self, trilist_idx: int, vertex_idxs: List[int], normal_idxs: List[int], flags: List[str], lod_dlevel: int, subobject_idx: int, prim_state_idx: int):
        self.vertex_idxs = vertex_idxs
        self.normal_idxs = normal_idxs
        self.flags = flags
        self._trilist_idx = trilist_idx
        self._lod_dlevel = lod_dlevel
        self._subobject_idx = subobject_idx
        self._prim_state_idx = prim_state_idx
    
    def __repr__(self):
        return f"""IndexedTrilist(trilist_idx={self._trilist_idx}, lod_dlevel={self._lod_dlevel}, subobject_idx={self._subobject_idx}, prim_state_idx={self._prim_state_idx},
            vertex_idxs={self.vertex_idxs}, normal_idxs={self.normal_idxs}, flags={self.flags})"""

    def __eq__(self, other):
        if isinstance(other, IndexedTrilist):
            return all([
                self._trilist_idx == other._trilist_idx,
                self._lod_dlevel == other._lod_dlevel,
                self._subobject_idx == other._subobject_idx,
                self._prim_state_idx == other._prim_state_idx
            ])
        return False
    
    @property
    def trilist_idx(self) -> int:
        return self._trilist_idx
    
    @property
    def lod_dlevel(self) -> int:
        return self._lod_dlevel
    
    @property
    def subobject_idx(self) -> int:
        return self._subobject_idx
    
    @property
    def prim_state_idx(self) -> int:
        return self._prim_state_idx


class File:
    def __init__(self, filename: str, directory: str, encoding: str = None, shouldRead: bool = True):
        self.filename = filename
        self.directory = directory
        self._ensure_exists()
        if encoding is None:
            self.encoding = _detect_encoding(self.filepath)
        else:
            self.encoding = encoding
        if shouldRead:
            self._lines = self._read()

    def __repr__(self) -> str:
        return f"File(filename={self.filename}, directory={self.directory}, lines={len(self._lines)})"
    
    def _ensure_exists(self) -> None:
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', encoding='utf-16-le') as f:
                pass

    def _read(self) -> List[str]:
        if self.encoding is None:
            self.encoding = _detect_encoding(self.filepath)
        with open(self.filepath, 'r', encoding=self.encoding) as f:
            return f.read().split('\n')
    
    def save(self, encoding: str = None) -> None:
        if encoding is not None:
            self.encoding = encoding
        with open(self.filepath, 'w', encoding=self.encoding) as f:
            text = '\n'.join(self.lines)
            f.write(text)

    def copy(self, new_filename: str = None, new_directory: str = None) -> "File":
        if new_filename is None and new_directory is None:
            raise ValueError("Either supply a new filename, a new directory or both.")
        if new_filename == self.filename and new_directory == self.directory:
            raise ValueError("Cannot copy the file to itself. Please specify either a new filename and/or a new directory.")

        copied_file = copy.deepcopy(self)
        copied_file.filename = new_filename

        if new_directory is not None:
            copied_file.directory = new_directory
        
        shutil.copyfile(self.filepath, copied_file.filepath)
        return copied_file

    def replace(self, search_exp: str, replace_str: str) -> None:
        pattern = re.compile(search_exp)
        text = '\n'.join(self.lines)
        text = pattern.sub(replace_str, text)
        self._lines = text.split('\n')
    
    def replace_ignorecase(self, search_exp: str, replace_str: str) -> None:
        pattern = re.compile(search_exp, re.IGNORECASE)
        text = '\n'.join(self.lines)
        text = pattern.sub(replace_str, text)
        self._lines = text.split('\n')
    
    @property
    def lines(self) -> List[str]:
        return self._lines
    
    @property
    def filepath(self) -> str:
        return f"{self.directory}/{self.filename}"


class Shapefile(File):
    def __init__(self, filename: str, directory: str, encoding: str = None):
        super().__init__(filename, directory, encoding=encoding, shouldRead=False)
        if not self.is_compressed():
            self._lines = super()._read()

    def __repr__(self) -> str:
        if self.is_compressed():
            return f"Shapefile(filename={self.filename}, directory={self.directory}, compressed=True)"
        return f"Shapefile(filename={self.filename}, directory={self.directory}, compressed=False, lines={len(self._lines)})"

    def save(self) -> None:
        if self.is_compressed():
            raise AttributeError("Cannot save the shapefile while it is compressed. Please use the 'save()' method before using 'compress(ffeditc_path: str)'.")
        super().save()

    def copy(self, new_filename: str, new_directory: str = None) -> "Shapefile":
        copied_file = super().copy(new_filename, new_directory)

        if isinstance(copied_file, File):
            copied_shapefile = Shapefile(
                copied_file.filename,
                copied_file.directory,
                encoding=copied_file.encoding
            )

            if not self.is_compressed():
                copied_shapefile._lines = copied_file._lines
            return copied_shapefile
        
        return copied_file

    def is_compressed(self) -> Optional[bool]:
        with open(self.filepath, 'r', encoding=_detect_encoding(self.filepath)) as f:
            try:
                header = f.read(32)
                if header.startswith("SIMISA@@@@@@@@@@JINX0s1t______"):
                    return False
                elif header == "":
                    return None
            except UnicodeDecodeError:
                pass
            
            return True

    def compress(self, ffeditc_path) -> None:
        if not self.is_compressed():
            subprocess.call([ffeditc_path, self.filepath, "/o:" + self.filepath])

    def decompress(self, ffeditc_path) -> None:
        if self.is_compressed():
            subprocess.call([ffeditc_path, self.filepath, "/u", "/o:" + self.filepath])
            self.encoding = _detect_encoding(self.filepath)
            if not self._lines:
                self._lines = super()._read()

    @property
    def lines(self) -> List[str]:
        if self.is_compressed():
            raise AttributeError("""Cannot access lines while the shapefile is compressed. Please use the 'decompress(ffeditc_path: str)' method first.""")
        return self._lines

    def get_lod_dlevels(self) -> List[int]:
        lod_dlevels = []

        for line in self.lines:
            if "dlevel_selection (" in line.lower():
                parts = line.split(' ')
                lod_dlevels.append(int(parts[2]))

        return sorted(lod_dlevels)
    
    def get_prim_states(self) -> Dict[int, PrimState]:
        current_prim_state_idx = 0
        prim_states = {}

        for line in self.lines:
            if "prim_state " in line.lower():
                parts = line.split(' ')
                prim_states[current_prim_state_idx] = PrimState(current_prim_state_idx, parts[1])
                current_prim_state_idx += 1

        return prim_states
    
    def get_prim_state_by_name(self, prim_state_name: str) -> Optional[PrimState]:
        current_prim_state_idx = 0

        for line in self.lines:
            if "prim_state " in line.lower():
                parts = line.split(' ')
                if parts[1] == prim_state_name:
                    return PrimState(current_prim_state_idx, parts[1])
                current_prim_state_idx += 1

        return None
    
    def get_prim_state_by_idx(self, prim_state_idx: int) -> Optional[PrimState]:
        current_prim_state_idx = 0

        for line in self.lines:
            if "prim_state " in line.lower():
                parts = line.split(' ')
                if current_prim_state_idx == prim_state_idx:
                    return PrimState(current_prim_state_idx, parts[1])
                current_prim_state_idx += 1

        return None

    def get_points(self) -> Dict[int, Point]:
        current_point_idx = 0
        points = {}

        for line in self.lines:
            if "point (" in line.lower() and "uv_point (" not in line.lower():
                parts = line.split(' ')
                points[current_point_idx] = Point(float(parts[2]), float(parts[3]), float(parts[4]))
                current_point_idx += 1

        return points

    def get_point_by_idx(self, point_idx: int) -> Optional[Point]:
        current_point_idx = 0

        for line in self.lines:
            if "point (" in line.lower() and "uv_point (" not in line.lower():
                parts = line.split(' ')
                if current_point_idx == point_idx:
                    return Point(float(parts[2]), float(parts[3]), float(parts[4]))
                current_point_idx += 1

        return None
    
    def set_point_value(self, point_idx: int, point: Point) -> bool:
        current_point_idx = 0

        for line_idx, line in enumerate(self.lines):
            if "point (" in line.lower() and "uv_point (" not in line.lower():
                if current_point_idx == point_idx:
                    parts = line.split(" ")
                    parts[2] = str(point.x)
                    parts[3] = str(point.y)
                    parts[4] = str(point.z)
                    line = " ".join(parts)
                    self.lines[line_idx] = line
                    return True
                
                current_point_idx += 1

        return False

    def set_point_count(self, point_count: int) -> bool:
        for line_idx, line in enumerate(self.lines):
            if "points (" in line.lower():
                parts = line.split(" ")
                parts[2] = str(point_count)
                line = " ".join(parts)
                self.lines[line_idx] = line
                return True

        return False
    
    def add_point(self, point: Point) -> Optional[int]:
        current_point_idx = 0
        processing_points = False

        for line_idx, line in enumerate(self.lines):
            if 'points (' in line.lower():
                processing_points = True

            if processing_points and ')' in line.lower() and 'point (' not in line.lower():
                processing_points = False
                self.lines[line_idx : line_idx] = [f"\t\tpoint ( {point.x} {point.y} {point.z} )"]
                self.set_point_count(current_point_idx + 1)
                return current_point_idx

            if processing_points and 'point (' in line.lower():
                current_point_idx += 1

        return None

    def get_uvpoints(self) -> Dict[int, UVPoint]:
        current_uv_point_idx = 0
        uv_points = {}

        for line in self.lines:
            if "uv_point (" in line.lower():
                parts = line.split(' ')
                uv_points[current_uv_point_idx] = UVPoint(float(parts[2]), float(parts[3]))
                current_uv_point_idx += 1

        return uv_points
    
    def get_uvpoint_by_idx(self, uv_point_idx: int) -> Optional[UVPoint]:
        current_uv_point_idx = 0

        for line in self.lines:
            if "uv_point (" in line.lower():
                parts = line.split(' ')
                if current_uv_point_idx == uv_point_idx:
                    return UVPoint(float(parts[2]), float(parts[3]))
                current_uv_point_idx += 1

        return None
    
    def set_uvpoint_value(self, uv_point_idx: int, uv_point: UVPoint) -> bool:
        current_uv_point_idx = 0

        for line_idx, line in enumerate(self.lines):
            if 'uv_point (' in line.lower():
                if current_uv_point_idx == uv_point_idx:
                    parts = line.split(" ")
                    parts[2] = str(uv_point.u)
                    parts[3] = str(uv_point.v)
                    line = " ".join(parts)
                    self.lines[line_idx] = line
                    return True

                current_uv_point_idx += 1

        return False

    def set_uvpoint_count(self, uv_point_count: int) -> bool:
        for line_idx, line in enumerate(self.lines):
            if "uv_points (" in line.lower():
                parts = line.split(" ")
                parts[2] = str(uv_point_count)
                line = " ".join(parts)
                self.lines[line_idx] = line
                return True

        return False
    
    def add_uvpoint(self, uv_point: UVPoint) -> Optional[int]:
        current_uv_point_idx = 0
        processing_uv_points = False

        for line_idx, line in enumerate(self.lines):
            if 'uv_points (' in line.lower():
                processing_uv_points = True

            if processing_uv_points and ')' in line.lower() and 'uv_point (' not in line.lower():
                processing_uv_points = False
                self.lines[line_idx : line_idx] = [f"\t\tuv_point ( {uv_point.u} {uv_point.v} )"]
                self.set_uvpoint_count(current_uv_point_idx + 1)
                return current_uv_point_idx

            if processing_uv_points and 'uv_point (' in line.lower():
                current_uv_point_idx += 1

        return None

    def get_normals(self) -> Dict[int, Normal]:
        current_normals_idx = 0
        processing_normals = False
        normals = {}

        for line in self.lines:
            if 'normals (' in line.lower():
                processing_normals = True

            if 'vector (' in line.lower() and processing_normals:
                parts = line.split(' ')
                normals[current_normals_idx] = Normal(float(parts[2]), float(parts[3]), float(parts[4]))
                current_normals_idx += 1

            if processing_normals and ')' in line.lower() and 'vector (' not in line.lower():
                processing_normals = False

        return normals

    def get_normal_by_idx(self, normal_idx: int) -> Optional[Normal]:
        current_normals_idx = 0
        processing_normals = False

        for line in self.lines:
            if 'normals (' in line.lower():
                processing_normals = True

            if 'vector (' in line.lower() and processing_normals:
                parts = line.split(' ')
                if current_normals_idx == normal_idx:
                    return Normal(float(parts[2]), float(parts[3]), float(parts[4]))
                current_normals_idx += 1

            if processing_normals and ')' in line.lower() and 'vector (' not in line.lower():
                processing_normals = False

        return None
    
    def set_normal_value(self, normal_idx: int, normal: Normal) -> bool:
        current_normal_idx = 0
        processing_normals = False

        for line_idx, line in enumerate(self.lines):
            if 'normals (' in line.lower():
                processing_normals = True

            if 'vector (' in line.lower() and processing_normals:
                if current_normal_idx == normal_idx:
                    parts = line.split(" ")
                    parts[2] = str(normal.vec_x)
                    parts[3] = str(normal.vec_y)
                    parts[4] = str(normal.vec_z)
                    line = " ".join(parts)
                    self.lines[line_idx] = line
                    return True
                
                current_normal_idx += 1

            if processing_normals and ')' in line.lower() and len(line.lower()) < 6:
                processing_normals = False
        
        return False

    def set_normal_count(self, normals_count: int) -> bool:
        for line_idx, line in enumerate(self.lines):
            if "normals (" in line.lower():
                parts = line.split(" ")
                parts[2] = str(normals_count)
                line = " ".join(parts)
                self.lines[line_idx] = line
                return True

        return False
    
    def add_normal(self, normal: Normal) -> Optional[int]:
        current_normal_idx = 0
        processing_normals = False

        for line_idx, line in enumerate(self.lines):
            if 'normals (' in line.lower():
                processing_normals = True

            if processing_normals and ')' in line.lower() and len(line.lower()) < 6:
                processing_normals = False
                self.lines[line_idx : line_idx] = [f"\t\tvector ( {normal.vec_x} {normal.vec_y} {normal.vec_z} )"]
                self.set_normal_count(current_normal_idx + 1)
                return current_normal_idx

            if processing_normals and 'vector (' in line.lower():
                current_normal_idx += 1

        return None
        
    def get_subobject_idxs_in_lod_dlevel(self, lod_dlevel: int) -> List[int]:
        subobject_idxs = []
        current_subobject_idx = 0
        current_dlevel = -1

        for line_idx, line in enumerate(self.lines):
            if "dlevel_selection (" in line.lower():
                parts = line.split(' ')
                current_dlevel = int(parts[2])

            if "sub_object (" in line.lower() and current_dlevel == lod_dlevel:
                subobject_idxs.append(current_subobject_idx)
                current_subobject_idx += 1

        return subobject_idxs
    
    def get_prim_state_idxs_in_subobject(self, lod_dlevel: int, subobject_idx: int):
        raise NotImplementedError()
    
    def get_indexed_trilists_in_subobject(self, lod_dlevel: int, subobject_idx: int) -> Dict[int, List[IndexedTrilist]]:
        indexed_trilists = {}
        current_dlevel = -1
        current_subobject_idx = -1
        current_trilist_idx = 0
        current_prim_state_idx = 0
        processing_trilist = False
        collecting_vertex_idxs = False
        vertex_idxs_in_trilist = []
        collecting_normal_idxs = False
        normal_idxs_in_trilist = []
        collecting_flags = False
        flags_in_trilist = []

        for line_idx, line in enumerate(self.lines):
            if "dlevel_selection (" in line.lower():
                parts = line.split(' ')
                current_dlevel = int(parts[2])

            if current_dlevel == lod_dlevel:
                if "sub_object (" in line.lower():
                    current_subobject_idx += 1
                
                if current_subobject_idx == subobject_idx:
                    if 'prim_state_idx (' in line.lower():
                        parts = line.split(' ')
                        current_prim_state_idx = int(parts[2])

                    if 'indexed_trilist (' in line.lower():
                        processing_trilist = True

                    if 'vertex_idxs (' in line.lower() or collecting_vertex_idxs:
                        parts = line.replace('vertex_idxs', '').replace('(', '').replace(')', '').split()
                        if parts:
                            if not collecting_vertex_idxs:
                                parts = parts[1:]
                            vertex_idxs = list(map(int, parts))
                            vertex_idxs_in_trilist.extend(vertex_idxs)
                        collecting_vertex_idxs = not line.endswith(')')

                    if 'normal_idxs (' in line.lower() or collecting_normal_idxs:
                        parts = line.replace('normal_idxs', '').replace('(', '').replace(')', '').split()
                        if parts:
                            if not collecting_normal_idxs:
                                parts = parts[1:]
                            normal_idxs = list(map(int, parts))
                            normal_idxs_in_trilist.extend(normal_idxs)
                        collecting_normal_idxs = not line.endswith(')')

                    if 'flags (' in line.lower() or collecting_flags:
                        parts = line.replace('flags', '').replace('(', '').replace(')', '').split()
                        if parts:
                            if not collecting_flags:
                                parts = parts[1:]
                            flags = list(map(str, parts))
                            flags_in_trilist.extend(flags)
                        collecting_flags = not line.endswith(')')

                    if processing_trilist and '\t)' in line.lower():
                        processing_trilist = False

                        indexed_trilist = IndexedTrilist(
                            trilist_idx=current_trilist_idx,
                            vertex_idxs=vertex_idxs_in_trilist,
                            normal_idxs=normal_idxs_in_trilist,
                            flags=flags_in_trilist,
                            lod_dlevel=current_dlevel,
                            subobject_idx=current_subobject_idx,
                            prim_state_idx=current_prim_state_idx
                        )

                        if current_prim_state_idx not in indexed_trilists:
                            indexed_trilists[current_prim_state_idx] = [indexed_trilist]
                        else:
                            indexed_trilists[current_prim_state_idx].append(indexed_trilist)
                        
                        current_trilist_idx += 1
                        vertex_idxs_in_trilist = []
                        normal_idxs_in_trilist = []
                        flags_in_trilist = []

        return indexed_trilists
    
    def update_indexed_trilist(self, indexed_trilist: IndexedTrilist) -> bool:
        current_dlevel = -1
        current_subobject_idx = -1
        current_trilist_idx = -1
        current_prim_state_idx = -1
        processing_trilist = False
        collecting_vertex_idxs = False
        collecting_normal_idxs = False
        collecting_flags = False
        lines_to_remove = []

        for line_idx, line in enumerate(self.lines):
            if "dlevel_selection (" in line.lower():
                parts = line.split(' ')
                current_dlevel = int(parts[2])

            if current_dlevel == indexed_trilist._lod_dlevel:
                if "sub_object (" in line.lower():
                    current_subobject_idx += 1
                
                if current_subobject_idx == indexed_trilist._subobject_idx:
                    if 'prim_state_idx (' in line.lower():
                        parts = line.split(' ')
                        current_prim_state_idx = int(parts[2])

                    if current_prim_state_idx == indexed_trilist._prim_state_idx:
                        if 'indexed_trilist (' in line.lower():
                            processing_trilist = True
                            current_trilist_idx += 1
                        
                        if current_trilist_idx == indexed_trilist._trilist_idx:
                            if 'vertex_idxs (' in line.lower() or collecting_vertex_idxs:
                                lines_to_remove.append(line_idx)
                                collecting_vertex_idxs = not line.endswith(')')

                            if 'normal_idxs (' in line.lower() or collecting_normal_idxs:
                                lines_to_remove.append(line_idx)
                                collecting_normal_idxs = not line.endswith(')')

                            if 'flags (' in line.lower() or collecting_flags:
                                lines_to_remove.append(line_idx)
                                collecting_flags = not line.endswith(')')

                        if processing_trilist and '\t)' in line.lower():
                            processing_trilist = False

        if lines_to_remove:
            new_vertex_trilist = indexed_trilist.vertex_idxs
            new_normals_trilist = indexed_trilist.normal_idxs
            new_flags_trilist = indexed_trilist.flags
            trilist_start_line_idx = min(lines_to_remove)
            lines_to_add = []
            
            self._lines = [line for idx, line in enumerate(self.lines) if idx not in lines_to_remove]
            
            if len(new_vertex_trilist) == 0:
                lines_to_add.append("vertex_idxs ( 0 )")
            
            vertex_trilist_chunks = [tuple(new_vertex_trilist[i : i + 197]) for i in range(0, len(new_vertex_trilist), 197)]
            for index, chunk in enumerate(vertex_trilist_chunks):
                line = "\t\t\t\t\t\t\t\t\t"
                if len(vertex_trilist_chunks) == 1:
                    line += f"vertex_idxs ( {len(new_vertex_trilist)} " + " ".join(map(str, chunk)) + " )"
                elif index == 0:
                    line += f"vertex_idxs ( {len(new_vertex_trilist)} " + " ".join(map(str, chunk))
                elif index == len(vertex_trilist_chunks) - 1:
                    line += " ".join(map(str, chunk)) + " )"
                else:
                    line += " ".join(map(str, chunk))
                lines_to_add.append(line)
            
            if len(new_normals_trilist) == 0:
                lines_to_add.append("normal_idxs ( 0 )")
            
            normals_trilist_chunks = [tuple(new_normals_trilist[i : i + 197]) for i in range(0, len(new_normals_trilist), 197)]
            for index, chunk in enumerate(normals_trilist_chunks):
                line = "\t\t\t\t\t\t\t\t\t"
                if len(normals_trilist_chunks) == 1:
                    line += f"normal_idxs ( {len(new_normals_trilist)} " + " ".join(map(str, chunk)) + " )"
                elif index == 0:
                    line += f"normal_idxs ( {len(new_normals_trilist)} " + " ".join(map(str, chunk))
                elif index == len(normals_trilist_chunks) - 1:
                    line += " ".join(map(str, chunk)) + " )"
                else:
                    line += " ".join(map(str, chunk))
                lines_to_add.append(line)
            
            if len(new_flags_trilist) == 0:
                lines_to_add.append("flags ( 0 )")
            
            flags_trilist_chunks = [tuple(new_flags_trilist[i : i + 197]) for i in range(0, len(new_flags_trilist), 197)]
            for index, chunk in enumerate(flags_trilist_chunks):
                line = "\t\t\t\t\t\t\t\t\t"
                if len(flags_trilist_chunks) == 1:
                    line += f"flags ( {len(new_flags_trilist)} " + " ".join(chunk) + " )"
                elif index == 0:
                    line += f"flags ( {len(new_flags_trilist)} " + " ".join(chunk)
                elif index == len(flags_trilist_chunks) - 1:
                    line += " ".join(chunk) + " )"
                else:
                    line += " ".join(chunk)
                lines_to_add.append(line)

            self.lines[trilist_start_line_idx : trilist_start_line_idx] = lines_to_add
            return True

        return False

    def get_vertices_in_subobject(self, lod_dlevel: int, subobject_idx: int) -> List[Vertex]:
        vertices_in_subobject = []
        current_dlevel = -1
        current_subobject_idx = -1
        current_vertex_idx = 0

        points = self.get_points()
        uv_points = self.get_uvpoints()
        normals = self.get_normals()

        for line_idx, line in enumerate(self.lines):
            if "dlevel_selection (" in line.lower():
                parts = line.split()
                current_dlevel = int(parts[2])

            if current_dlevel == lod_dlevel:
                if "sub_object (" in line.lower():
                    current_subobject_idx += 1
                    current_vertex_idx = 0
                
                if current_subobject_idx == subobject_idx:
                    if "vertex (" in line.lower():
                        parts = ' '.join(self.lines[line_idx : line_idx + 2]).split(' ')
                        vertex = Vertex(
                            vertex_idx=current_vertex_idx,
                            point=points[int(parts[3])],
                            uv_point=uv_points[int(parts[10])],
                            normal=normals[int(parts[4])],
                            point_idx=int(parts[3]),
                            uv_point_idx=int(parts[10]),
                            normal_idx=int(parts[4]),
                            lod_dlevel=current_dlevel,
                            subobject_idx=current_subobject_idx
                        )
                        vertices_in_subobject.append(vertex)
                        current_vertex_idx += 1

        return vertices_in_subobject

    def get_vertices_by_prim_state(self, lod_dlevel: int, prim_state: PrimState) -> List[Vertex]:
        points = self.get_points()
        uvpoints = self.get_uvpoints()
        normals = self.get_normals()
        prim_states = self.get_prim_states()
        subobject_idxs = self.get_subobject_idxs_in_lod_dlevel(lod_dlevel)

        vertices_by_prim_state = []
        for subobject_idx in subobject_idxs:
            vertices = self.get_vertices_in_subobject(lod_dlevel, subobject_idx)
            indexed_trilists = self.get_indexed_trilists_in_subobject(lod_dlevel, subobject_idx)
            for vertex in vertices:
                for prim_state_idx in indexed_trilists:
                    if prim_state_idx == prim_state.idx:
                        for indexed_trilist in indexed_trilists[prim_state_idx]:
                            if vertex._vertex_idx in indexed_trilist.vertex_idxs:
                                if vertex not in vertices_by_prim_state:
                                    vertices_by_prim_state.append(vertex)

        return vertices_by_prim_state

    def get_vertex_in_subobject_by_idx(self,  lod_dlevel: int, subobject_idx: int, vertex_idx: int) -> Optional[Vertex]:
        current_dlevel = -1
        current_subobject_idx = -1
        current_vertex_idx = 0

        points = self.get_points()
        uv_points = self.get_uvpoints()
        normals = self.get_normals()

        for line_idx, line in enumerate(self.lines):
            if "dlevel_selection (" in line.lower():
                parts = line.split(' ')
                current_dlevel = int(parts[2])

            if current_dlevel == lod_dlevel:
                if "sub_object (" in line.lower():
                    current_subobject_idx += 1
                    current_vertex_idx = 0
                
                if current_subobject_idx == subobject_idx:
                    if "vertex (" in line.lower():
                        if current_vertex_idx == vertex_idx:
                            parts = ' '.join(self.lines[line_idx : line_idx + 2]).split(' ')
                            vertex = Vertex(
                                vertex_idx=current_vertex_idx,
                                point=points[int(parts[3])],
                                uv_point=uv_points[int(parts[10])],
                                normal=normals[int(parts[4])],
                                point_idx=int(parts[3]),
                                uv_point_idx=int(parts[10]),
                                normal_idx=int(parts[4]),
                                lod_dlevel=current_dlevel,
                                subobject_idx=current_subobject_idx
                            )
                            return vertex
                    
                        current_vertex_idx += 1

        return None

    def get_prim_states_for_vertex(self):
        raise NotImplementedError()

    def get_connected_vertices(self, prim_state: PrimState, vertex: Vertex) -> List[Vertex]:
        find_vertex_idx = vertex._vertex_idx
        find_vertex_dlevel = vertex._lod_dlevel
        find_vertex_subobject_idx = vertex._subobject_idx
        find_vertex_prim_state_idx = prim_state.idx

        vertices = self.get_vertices_in_subobject(find_vertex_dlevel, find_vertex_subobject_idx)
        indexed_trilists = self.get_indexed_trilists_in_subobject(find_vertex_dlevel, find_vertex_subobject_idx)

        connected_vertices = []
        connected_vertex_idxs = []
        if find_vertex_prim_state_idx in indexed_trilists:
            indexed_trilists_for_prim_state = indexed_trilists[find_vertex_prim_state_idx]
            for indexed_trilist in indexed_trilists_for_prim_state:
                triangles = [tuple(indexed_trilist.vertex_idxs[i : i + 3]) for i in range(0, len(indexed_trilist.vertex_idxs), 3)]
                for tri in triangles:
                    if find_vertex_idx in tri:
                        for vertex_idx in tri:
                            if vertex_idx != find_vertex_idx:
                                connected_vertex_idxs.append(vertex_idx)
                                connected_vertex_idxs = list(set(connected_vertex_idxs))

            for vertex_idx in connected_vertex_idxs:
                connected_vertices.append(vertices[vertex_idx])

        return connected_vertices
    
    def update_vertex(self, vertex: Vertex) -> bool:
        point_idx = vertex._point_idx
        uv_point_idx = vertex._uv_point_idx
        normal_idx = vertex._normal_idx

        has_updated_point = self.set_point_value(point_idx, vertex.point)
        has_updated_uv_point = self.set_uv_point_value(uv_point_idx, vertex.uv_point)
        has_updated_normal = self.set_normal_value(normal_idx, vertex.normal)

        update_successful = all([has_updated_point, has_updated_uv_point, has_updated_normal])
        return update_successful

    def add_vertex_to_subobject(self, lod_dlevel: int, subobject_idx: int, point: Point, uv_point: UVPoint, normal: Normal) -> Optional[Vertex]:
        current_dlevel = -1
        current_subobject_idx = -1
        current_vertex_idx = 0
        processing_vertices = False

        new_point_idx = self.add_point(point)
        new_uv_point_idx = self.add_uvpoint(uv_point)
        new_normal_idx = self.add_normal(normal)

        new_vertex = Vertex(
            vertex_idx=-1,
            point=point,
            uv_point=uv_point,
            normal=normal,
            point_idx=new_point_idx,
            uv_point_idx=new_uv_point_idx,
            normal_idx=new_normal_idx,
            lod_dlevel=lod_dlevel,
            subobject_idx=subobject_idx
        )

        for line_idx, line in enumerate(self.lines):
            if "dlevel_selection (" in line.lower():
                parts = line.split(' ')
                current_dlevel = int(parts[2])

            if current_dlevel == lod_dlevel:
                if "sub_object (" in line.lower():
                    current_subobject_idx += 1
                
                if current_subobject_idx == subobject_idx:
                    if 'vertices (' in line.lower():
                        processing_vertices = True

                    if processing_vertices and ')' in line.lower() and 'vert' not in self.lines[line_idx - 1].lower():
                        processing_vertices = False
                        self.lines[line_idx : line_idx] = [
                            f"\t\t\t\t\t\t\t\tvertex ( 00000000 {new_vertex._point_idx} {new_vertex._normal_idx} ff969696 ff808080",
                            f"\t\t\t\t\t\t\t\t\tvertex_uvs ( 1 {new_vertex._uv_point_idx} )",
                            "\t\t\t\t\t\t\t\t)"
                        ]
                        self.set_vertices_count(lod_dlevel, subobject_idx, current_vertex_idx + 1)
                        new_vertex._vertex_idx = current_vertex_idx
                        return new_vertex
                    
                    if processing_vertices and 'vertex (' in line.lower():
                        current_vertex_idx += 1

        return None
    
    def set_vertices_count(self, lod_dlevel: int, subobject_idx: int, vertices_count: int) -> bool:
        current_dlevel = -1
        current_subobject_idx = -1

        for line_idx, line in enumerate(self.lines):
            if "dlevel_selection (" in line.lower():
                parts = line.split(' ')
                current_dlevel = int(parts[2])

            if current_dlevel == lod_dlevel:
                if "sub_object (" in line.lower():
                    current_subobject_idx += 1
                
                if current_subobject_idx == subobject_idx:
                    if "vertices (" in line.lower():
                        parts = line.split(" ")
                        parts[2] = str(vertices_count)
                        line = " ".join(parts)
                        self.lines[line_idx] = line
                        return True
        
        return False
    
    def get_subobject_header(self, lod_dlevel: int, subobject_idx: int, vertices_count: int) -> bool:
        raise NotImplementedError()

    def update_subobject_header(self, lod_dlevel: int, subobject_idx: int, vertices_count: int) -> bool:
        raise NotImplementedError()

    def get_vertex_sets(self, lod_dlevel: int, subobject_idx: int) -> bool:
        raise NotImplementedError()

    def update_vertex_sets(self, lod_dlevel: int, subobject_idx: int) -> bool:
        raise NotImplementedError()
    
    def calculate_point_midpoint(self, point1: Point, point2: Point) -> Point:
        return Point.from_numpy((point1.to_numpy() + point2.to_numpy()) / 2)
    
    def calculate_uvpoint_midpoint(self, uv_point1: UVPoint, uv_point2: UVPoint) -> UVPoint:
        return UVPoint.from_numpy((uv_point1.to_numpy() + uv_point2.to_numpy()) / 2)
        
    def calculate_surface_normal(self, point1: Point, point2: Point, point3: Point) -> Normal:
        edge1 = point2.to_numpy() - point1.to_numpy()
        edge2 = point3.to_numpy() - point1.to_numpy()

        normal = np.cross(edge1, edge2)
        normal = normal / np.linalg.norm(normal)

        return Normal.from_numpy(normal)
    
    def calculate_vertex_normal(self, point: Point, connected_points: List[Point]) -> Normal:
        vertex_normal_sum = np.zeros(3)

        if len(connected_points) < 2:
            return Normal(0, 0, 0)
        
        for i in range(len(connected_points) - 1):
            edge1 = connected_points[i].to_numpy() - point.to_numpy()
            edge2 = connected_points[i + 1].to_numpy() - point.to_numpy()

            normal = np.cross(edge1, edge2)
            vertex_normal_sum += np.linalg.norm(normal)
        
        return Normal.from_numpy(vertex_normal_sum)
    
    def insert_vertex_between(self, prim_state: PrimState, vertex1: Vertex, vertex2: Vertex) -> Optional[Vertex]:
        if vertex1._lod_dlevel != vertex2._lod_dlevel:
            raise AttributeError("Cannot insert a new vertex between vertices in two different LOD distance levels.")
        if vertex1._subobject_idx != vertex2._subobject_idx:
            raise AttributeError("Cannot insert a new vertex between vertices in two different subobjects.")

        lod_dlevel = vertex1._lod_dlevel
        subobject_idx = vertex1._subobject_idx

        new_point = self.calculate_point_midpoint(vertex1.point, vertex2.point)
        new_uv_point = self.calculate_uvpoint_midpoint(vertex1.uv_point, vertex2.uv_point)
        new_normal = Normal(0, 0, 0)

        new_vertex = self.add_vertex_to_subobject(vertex1._lod_dlevel, vertex1._subobject_idx, new_point, new_uv_point, new_normal)

        if new_vertex is not None:
            indexed_trilists = self.get_indexed_trilists_in_subobject(lod_dlevel, subobject_idx)
            for prim_state_idx in indexed_trilists:
                if prim_state_idx == prim_state.idx:
                    for indexed_trilist in indexed_trilists[prim_state_idx]:
                        changed_indexed_trilist = copy.deepcopy(indexed_trilist)
                        changed_indexed_trilist.vertex_idxs = []
                        changed_indexed_trilist.normal_idxs = []
                        changed_indexed_trilist.flags = []
                        
                        triangles = [tuple(indexed_trilist.vertex_idxs[i : i + 3]) for i in range(0, len(indexed_trilist.vertex_idxs), 3)]
                        for tri_idx, tri in enumerate(triangles):
                            if vertex1._vertex_idx not in tri and vertex2._vertex_idx not in tri:
                                changed_indexed_trilist.vertex_idxs.extend(tri)
                                changed_indexed_trilist.normal_idxs.append(indexed_trilist.normal_idxs[tri_idx])
                                changed_indexed_trilist.flags.append(indexed_trilist.flags[tri_idx])
                        
                        for tri_idx, tri in enumerate(triangles):
                            if vertex1._vertex_idx in tri and vertex2._vertex_idx in tri:
                                vertex3_idx = [v for v in tri if v not in (vertex1._vertex_idx, vertex2._vertex_idx)][0]
                                new_triangle1 = [vertex1._vertex_idx, new_vertex._vertex_idx, vertex3_idx]
                                new_triangle2 = [new_vertex._vertex_idx, vertex2._vertex_idx, vertex3_idx]

                                vertex3 = self.get_vertex_in_subobject_by_idx(lod_dlevel, subobject_idx, vertex3_idx)

                                new_normal1 = self.calculate_surface_normal(vertex1.point, new_vertex.point, vertex3.point)
                                new_normal2 = self.calculate_surface_normal(new_vertex.point, vertex2.point, vertex3.point)

                                new_normal_idx1 = self.add_normal(new_normal1)
                                new_normal_idx2 = self.add_normal(new_normal2)

                                changed_indexed_trilist.vertex_idxs.extend(new_triangle1)
                                changed_indexed_trilist.vertex_idxs.extend(new_triangle2)
                                changed_indexed_trilist.normal_idxs.append(new_normal_idx1)
                                changed_indexed_trilist.normal_idxs.append(new_normal_idx2)
                                changed_indexed_trilist.flags.append("00000000")
                                changed_indexed_trilist.flags.append("00000000")

                        # TODO Adjust subobject header / vertex sets as necessary
                        self.update_indexed_trilist(changed_indexed_trilist)

                        connected_vertex_points = [vertex.point for vertex in self.get_connected_vertices(prim_state, new_vertex)]
                        new_vertex_normal = self.calculate_vertex_normal(new_vertex.point, connected_vertex_points)
                        self.set_normal_value(new_vertex._normal_idx, new_vertex_normal)

        return new_vertex
    
    def remove_vertex(self, prim_state: PrimState, vertex: Vertex, reconnect_geometry: bool = True) -> bool:
        lod_dlevel = vertex._lod_dlevel
        subobject_idx = vertex._subobject_idx
        vertex_idx = vertex._vertex_idx
        has_updated_trilists = False

        indexed_trilists = self.get_indexed_trilists_in_subobject(lod_dlevel, subobject_idx)
        for prim_state_idx in indexed_trilists:
            if prim_state_idx == prim_state.idx:
                for indexed_trilist in indexed_trilists[prim_state_idx]:
                    changed_indexed_trilist = copy.deepcopy(indexed_trilist)
                    changed_indexed_trilist.vertex_idxs = []
                    changed_indexed_trilist.normal_idxs = []
                    changed_indexed_trilist.flags = []

                    triangles = [tuple(indexed_trilist.vertex_idxs[i : i + 3]) for i in range(0, len(indexed_trilist.vertex_idxs), 3)]
                    for tri_idx, tri in enumerate(triangles):
                        if vertex_idx not in tri:
                            changed_indexed_trilist.vertex_idxs.extend(tri)
                            changed_indexed_trilist.normal_idxs.append(indexed_trilist.normal_idxs[tri_idx])
                            changed_indexed_trilist.flags.append(indexed_trilist.flags[tri_idx])
                    
                    if reconnect_geometry:
                        for tri_idx, tri in enumerate(triangles):
                            if vertex_idx in tri:
                                connected_vertices = set(tri)
                                connected_vertices.discard(vertex_idx)
                                connected_vertices = list(connected_vertices)

                                if len(connected_vertices) >= 2:
                                    for i in range(len(connected_vertices)):
                                        for j in range(i + 1, len(connected_vertices)):
                                            new_triangle = [connected_vertices[i], connected_vertices[j], vertex_idx]

                                            vertex1 = self.get_vertex_in_subobject_by_idx(lod_dlevel, subobject_idx, new_triangle[0])
                                            vertex2 = self.get_vertex_in_subobject_by_idx(lod_dlevel, subobject_idx, new_triangle[1])
                                            vertex3 = self.get_vertex_in_subobject_by_idx(lod_dlevel, subobject_idx, new_triangle[2])

                                            new_normal = self.calculate_surface_normal(vertex1.point, vertex2.point, vertex3.point)
                                            new_normal_idx = self.add_normal(new_normal)

                                            changed_indexed_trilist.vertex_idxs.extend(new_triangle)
                                            changed_indexed_trilist.normal_idxs.append(new_normal_idx)
                                            changed_indexed_trilist.flags.append("00000000")

                    # TODO Adjust subobject header / vertex sets as necessary
                    self.update_indexed_trilist(changed_indexed_trilist)
                    has_updated_trilists = True

        return has_updated_trilists


class Trackcenter:
    def __init__(self, centerpoints: np.ndarray):
        self.centerpoints = centerpoints

    def __repr__(self):
        return f"Trackcenter(centerpoints={self.centerpoints})"
    
    def __add__(self, other):
        if not isinstance(other, Trackcenter):
            raise TypeError(f"Cannot add Trackcenter with {type(other).__name__}")
        
        combined_centerpoints = np.vstack((self.centerpoints, other.centerpoints))
        return Trackcenter(combined_centerpoints)
    
    def __eq__(self, other):
        if isinstance(other, Trackcenter):
            return np.array_equal(self.centerpoints, other.centerpoints)
        return False


def find_directory_files(directory: str, match_files: List[str], ignore_files: List[str]) -> List[str]:
    files = []

    for file_name in os.listdir(directory):
        if any([fnmatch.fnmatch(file_name, x) for x in match_files]):
            if any([fnmatch.fnmatch(file_name, x) for x in ignore_files]):
                continue
            files.append(file_name)

    return files


def load_file(filename: str, directory: str, encoding: str = None) -> File:
    if filename.endswith(".s"):
        raise ValueError("Please use the method 'load_shape(filename: str, directory: str) when loading a shapefile.'")
    
    return File(filename, directory, encoding=encoding)


def load_shape(filename: str, directory: str, encoding: str = None) -> Shapefile:
    if not filename.endswith(".s"):
        raise ValueError("Please use the method 'load_file(filename: str, directory: str) when loading a file that is not a shapefile.'")
    
    return Shapefile(filename, directory, encoding=encoding)


def generate_empty_centerpoints() -> Trackcenter:
    centerpoints = np.empty((0, 3))

    return Trackcenter(centerpoints)


def generate_straight_centerpoints(length: float, num_points: int = 1000, start_angle: float = 0, start_point: Point = Point(0, 0, 0)) -> Trackcenter:
    angle_rad = np.radians(start_angle)
    
    z = np.linspace(start_point.z, start_point.z + length, num_points)
    x = np.full_like(z, start_point.x)
    y = np.full_like(z, start_point.y)

    x_rotated = start_point.x + x * np.cos(angle_rad) - z * np.sin(angle_rad)
    z_rotated = start_point.z + x * np.sin(angle_rad) + z * np.cos(angle_rad)

    centerpoints = np.vstack((x_rotated, y, z_rotated)).T

    return Trackcenter(centerpoints)


def generate_curve_centerpoints(curve_radius: float, curve_angle: float, num_points: int = 1000, start_angle: float = 0, start_point: Point = Point(0, 0, 0)) -> Trackcenter:
    theta = np.radians(np.linspace(start_angle, start_angle + abs(curve_angle), num_points))

    z = start_point.z + curve_radius * np.sin(theta)
    x = start_point.x + curve_radius * (1 - np.cos(theta))
    y = np.full_like(x, start_point.y)

    if curve_angle < 0:
        x = start_point.x - (curve_radius * (1 - np.cos(theta)))

    centerpoints = np.vstack((x, y, z)).T
    
    return Trackcenter(centerpoints)


def generate_centerpoints_from_tsection(shape_name: str, tsection_file_path: str = None) -> Trackcenter:
    if tsection_file_path is None:
        module_directory = pathlib.Path(__file__).parent
        tsection_file_path = f"{module_directory}/tsection.dat"
    elif not os.path.exists(tsection_file_path):
        raise ValueError(f"Unable to generate centerpoints: Specified file '{tsection_file_path}' in parameter 'tsection_file_path' does not exist.")

    tracksections = []
    trackshapes = []
    with open(tsection_file_path, "r", encoding=_detect_encoding(tsection_file_path)) as f:
        text = f.read()

        if re.search(r"TrackPath \(", text):
            raise ValueError(f"""Unable to generate centerpoints: The specified file '{tsection_file_path}' in parameter 'tsection_file_path' is a local 
                tsection.dat. Only global tsection.dat files are supported.""")

        lines = text.split('\n')
        # TODO Create and return centerpoints based on data from the standardised global tsection.dat build 60 or the supplied file.
        raise NotImplementedError()

    raise ValueError(f"""Unable to generate centerpoints: Unknown shape '{shape_name}'. Instead create 
        them manually using the methods 'generate_straight_centerpoints' and 'generate_curve_centerpoints'.""")


def find_closest_centerpoint(point_along_track: Point, trackcenter: Trackcenter, plane='xz') -> Point:
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

    return Point.from_numpy(trackcenter.centerpoints[closest_index])


def signed_distance_from_centerpoint(point_along_track: Point, trackcenter_point: Point, plane="xz") -> float:
    point = point_along_track.to_numpy()
    center = trackcenter_point.to_numpy()

    if plane == "x":
        point_proj = np.array([point[0], 0, 0])
        center_proj = np.array([center[0], 0, 0])
        reference_vector = np.array([0, 1, 0])
    elif plane == "y":
        point_proj = np.array([0, point[1], 0])
        center_proj = np.array([0, center[1], 0])
        reference_vector = np.array([1, 0, 0])
    elif plane == "xy":
        point_proj = np.array([point[0], point[1], 0])
        center_proj = np.array([center[0], center[1], 0])
        reference_vector = np.array([1, 0, 0])
    elif plane == "xz":
        point_proj = np.array([point[0], 0, point[2]])
        center_proj = np.array([center[0], 0, center[2]])
        reference_vector = np.array([0, 1, 0])
    elif plane == "z":
        point_proj = np.array([0, 0, point[2]])
        center_proj = np.array([0, 0, center[2]])
        reference_vector = np.array([1, 0, 0])
    else:
        raise ValueError("Invalid plane. Choose 'x', 'y', 'xy', 'xz', or 'z'.")

    vector_to_point = point_proj - center_proj
    cross = np.cross(reference_vector, vector_to_point)
    signed_distance = np.linalg.norm(vector_to_point[:2]) * np.sign(cross[-1])

    return signed_distance


def distance_along_curved_track(point_along_track: Point, trackcenter: Trackcenter, curve_angle: float, curve_radius: float) -> float:
    point = point_along_track.to_numpy()
    centerpoints = trackcenter.centerpoints

    point_xz = point[[0, 2]]
    centerpoints_xz = centerpoints[:, [0, 2]]

    tck, _ = splprep(centerpoints_xz.T, s=0)
    num_samples = 1000
    u_values = np.linspace(0, 1, num_samples)
    spline_points_xz = np.array(splev(u_values, tck)).T

    tree = KDTree(spline_points_xz)
    _, index = tree.query(point_xz)

    arc_length = abs(curve_angle) * curve_radius
    segment_lengths = np.linalg.norm(np.diff(spline_points_xz, axis=0), axis=1)
    cumulative_distance = np.cumsum(np.full_like(segment_lengths, arc_length))
    cumulative_distance = np.insert(cumulative_distance, 0, 0)

    meters_to_degrees = 1 / 111320
    cumulative_distance_degrees = cumulative_distance * meters_to_degrees

    return cumulative_distance_degrees[index]


def distance_along_straight_track(point_along_track: Point, trackcenter: Trackcenter) -> float:
    point = point_along_track.to_numpy()
    centerpoints = trackcenter.centerpoints

    point_xz = point[[0, 2]]
    centerpoints_xz = centerpoints[:, [0, 2]]

    tck, _ = splprep(centerpoints_xz.T, s=0)
    num_samples = 1000
    u_values = np.linspace(0, 1, num_samples)
    spline_points_xz = np.array(splev(u_values, tck)).T

    tree = KDTree(spline_points_xz)
    _, index = tree.query(point_xz)

    segment_lengths = np.linalg.norm(np.diff(spline_points_xz, axis=0), axis=1)
    cumulative_distance = np.cumsum(segment_lengths)
    cumulative_distance = np.insert(cumulative_distance, 0, 0)

    return cumulative_distance[index]


def get_curve_centerpoint_from_angle(curve_radius: float, curve_angle: float, start_angle: float = 0, start_point: Point = Point(0, 0, 0)) -> Point:
    theta = np.radians(abs(curve_angle))
    
    local_z = curve_radius * np.sin(theta)
    local_x = curve_radius * (1 - np.cos(theta))
    y = start_point.y

    if curve_angle < 0:
        local_x = -local_x

    angle_rad = np.radians(start_angle)
    x = start_point.x + (local_x * np.cos(angle_rad) - local_z * np.sin(angle_rad))
    z = start_point.z + (local_x * np.sin(angle_rad) + local_z * np.cos(angle_rad))

    return Point.from_numpy(np.array([x, y, z]))


def get_straight_centerpoint_from_length(length: float, start_angle: float = 0, start_point: Point = Point(0, 0, 0)) -> Point:
    theta = np.radians(start_angle)

    x = start_point.x + length * np.cos(theta)
    z = start_point.z + length * np.sin(theta)
    y = start_point.y

    return Point.from_numpy(np.array([x, y, z]))


def get_new_position_from_angle(curve_radius: float, curve_angle: float, original_point: Point, trackcenter: Trackcenter, start_angle: float = 0, start_point: Point = Point(0, 0, 0)) -> Point:
    closest_center = find_closest_centerpoint(original_point, trackcenter, plane='xz')
    offset = original_point.to_numpy() - closest_center.to_numpy()

    calculated_curve_point = get_curve_centerpoint_from_angle(curve_radius, curve_angle, start_angle)

    new_x = start_point.x + calculated_curve_point.x
    new_z = start_point.z + calculated_curve_point.z

    new_position = np.array([new_x, original_point.y, new_z]) + offset

    return Point.from_numpy(new_position)


def get_new_position_from_length(length: float, original_point: Point, trackcenter: Trackcenter, start_angle: float = 0, start_point: Point = Point(0, 0, 0)) -> Point:
    closest_center = find_closest_centerpoint(original_point, trackcenter, plane='xz')
    offset = original_point.to_numpy() - closest_center.to_numpy()

    calculated_straight_point = get_straight_centerpoint_from_length(length, start_angle)

    new_x = start_point.x + calculated_straight_point.x
    new_z = start_point.z + calculated_straight_point.z

    new_position = np.array([new_x, original_point.y, new_z]) + offset

    return Point.from_numpy(new_position)


def get_new_position_from_trackcenter(signed_distance: float, original_point: Point, trackcenter: Trackcenter) -> Point:
    centerpoints = trackcenter.centerpoints
    closest_center = find_closest_centerpoint(original_point, trackcenter, plane="xz")

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

    new_position = closest_center + signed_distance * lateral_vector

    return Point.from_numpy(new_position)
