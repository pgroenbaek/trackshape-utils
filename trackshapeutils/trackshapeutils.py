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


class Normal:
    def __init__(self, vec_x: float, vec_y: float, vec_z: float):
        self.vec_x = vec_x
        self.vec_y = vec_y
        self.vec_z = vec_z
    
    def __repr__(self):
        return f"Normal(vec_x={self.vec_x}, vec_y={self.vec_y}, vec_z={self.vec_z})"


class Vertex:
    def __init__(self, vertex_idx: int, point: Point, uv_point: UVPoint, normal: Normal, point_idx: int, uv_point_idx: int, normal_idx: int, \
            lod_dlevel: int, prim_state: PrimState, prim_state_idx: int, subobject_idx: int):
        self.point = point
        self.uv_point = uv_point
        self.normal = normal
        self._vertex_idx = vertex_idx
        self._point_idx = point_idx
        self._uv_point_idx = uv_point_idx
        self._normal_idx = normal_idx
        self._lod_dlevel = lod_dlevel
        self._prim_state = prim_state
        self._prim_state_idx = prim_state_idx
        self._subobject_idx = subobject_idx
    
    def __repr__(self):
        return f"""Vertex(vertex_idx={self._vertex_idx}, point={self.point}, point_idx={self._point_idx}, uv_point={self.uv_point}, 
            uv_point_idx={self._uv_point_idx}, normal={self.normal}, normal_idx={self._normal_idx},
            lod_dlevel={self._normal_idx}, prim_state={self._prim_state}, subobject_idx={self._subobject_idx})"""


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
    
    def _save(self, encoding: str = None) -> None:
        if encoding is not None:
            self.encoding = encoding
        with open(self.filepath, 'w', encoding=self.encoding) as f:
            text = '\n'.join(self.lines)
            f.write(text)

    def copy(self, new_filename: str = None, new_directory: str = None) -> "File":
        if new_filename is None and new_directory is None:
            raise AttributeError("Either supply a new filename, a new directory or both.")
        if new_filename == self.filename and new_directory == self.directory:
            raise AttributeError("Cannot copy the file to itself. Please specify either a new filename and/or a new directory.")

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
        self._save()
    
    def replace_ignorecase(self, search_exp: str, replace_str: str) -> None:
        pattern = re.compile(search_exp, re.IGNORECASE)
        text = '\n'.join(self.lines)
        text = pattern.sub(replace_str, text)
        self._lines = text.split('\n')
        self._save()
    
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
            self._lines = []

    def decompress(self, ffeditc_path) -> None:
        if self.is_compressed():
            subprocess.call([ffeditc_path, self.filepath, "/u", "/o:" + self.filepath])
            self.encoding = _detect_encoding(self.filepath)
            self._lines = super()._read()

    @property
    def lines(self) -> List[str]:
        if self.is_compressed():
            raise AttributeError("Cannot access lines when the shapefile is compressed. Please use the 'decompress(ffeditc_path: str)' method first.")
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
                    self._save()
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
                self._save()
                return True

        return False
    
    def add_point(self, point: Point) -> int:
        processing_points = False

        for line_idx, line in enumerate(self.lines):
            if 'points (' in line.lower():
                processing_points = True

            if processing_points and ')' in line.lower() and 'point (' not in line.lower():
                processing_points = False
                self.lines[line_idx : line_idx] = [f"\t\tpoint ( {point.x} {point.y} {point.z} )"]
                self._save()
                return len(self.get_points()) - 1

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
                    self._save()
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
                self._save()
                return True

        return False
    
    def add_uvpoint(self, uv_point: UVPoint) -> Optional[int]:
        processing_uv_points = False

        for line_idx, line in enumerate(self.lines):
            if 'uv_points (' in line.lower():
                processing_uv_points = True

            if processing_uv_points and ')' in line.lower() and 'uv_point (' not in line.lower():
                processing_uv_points = False
                self.lines[line_idx : line_idx] = [f"\t\tuv_point ( {uv_point.u} {uv_point.v} )"]
                self._save()
                return len(self.get_uvpoints()) - 1

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
                    self._save()
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
                self._save()
                return True

        return False
    
    def add_normal(self, normal: Normal) -> Optional[int]:
        processing_normals = False

        for line_idx, line in enumerate(self.lines):
            if 'normals (' in line.lower():
                processing_normals = True

            if processing_normals and ')' in line.lower() and len(line.lower()) < 6:
                processing_normals = False
                self.lines[line_idx : line_idx] = [f"\t\tvector ( {normal.vec_x} {normal.vec_y} {normal.vec_z} )"]
                self._save()
                return len(self.get_normals()) - 1

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

                    if processing_trilist and ')' in line.lower():
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
        raise NotImplementedError()

    def get_vertices_in_subobject(self, lod_dlevel: int, subobject_idx: int) -> List[Vertex]:
        vertices = {}
        current_dlevel = -1
        current_subobject_idx = -1
        current_vertex_idx = 0

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
                        parts = ' '.join(self.lines[line_idx : line_idx + 2]).split(' ')
                        vertices[current_vertex_idx] = Vertex(
                            vertex_idx=current_vertex_idx,
                            point=None, # Fill after vertices list has been processed.
                            uv_point=None, # Fill after vertices list has been processed.
                            normal=None, # Fill after vertices list has been processed.
                            point_idx=int(parts[3]),
                            uv_point_idx=int(parts[10]),
                            normal_idx=int(parts[4]),
                            lod_dlevel=current_dlevel,
                            prim_state=None, # Fill after vertices list has been processed.
                            prim_state_idx=-1, # Fill after vertices list has been processed.
                            subobject_idx=current_subobject_idx
                        )
                        current_vertex_idx += 1

        points = self.get_points()
        uvpoints = self.get_uvpoints()
        normals = self.get_normals()
        prim_states = self.get_prim_states()
        indexed_trilists = self.get_indexed_trilists_in_subobject(lod_dlevel, subobject_idx)

        vertices_in_subobject = []
        for vertex_idx, vertex in vertices.items():
            vertex.point = points[vertex._point_idx]
            vertex.uv_point = uvpoints[vertex._uv_point_idx]
            vertex.normal = normals[vertex._normal_idx]
            for prim_state_idx in indexed_trilists:
                for indexed_trilist in indexed_trilists[prim_state_idx]:
                    if vertex_idx in indexed_trilist.vertex_idxs:
                        vertex._prim_state_idx = prim_state_idx
                        vertex._prim_state = prim_states[prim_state_idx]
            vertices_in_subobject.append(vertex)

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
            for vertex in vertices:
                if vertex._prim_state_idx == prim_state.idx:
                    vertices_by_prim_state.append(vertex)

        return vertices_by_prim_state

    def get_connected_vertices(self, vertex: Vertex) -> List[Vertex]:
        find_vertex_idx = vertex._vertex_idx
        find_vertex_dlevel = vertex._lod_dlevel
        find_vertex_subobject_idx = vertex._subobject_idx
        find_vertex_prim_state_idx = vertex._prim_state_idx

        vertices = self.get_vertices_in_subobject(find_vertex_dlevel, find_vertex_subobject_idx)
        indexed_trilists = self.get_indexed_trilists_in_subobject(find_vertex_dlevel, find_vertex_subobject_idx)

        connected_vertices = []
        connected_vertex_idxs = []
        if find_vertex_prim_state_idx in indexed_trilists:
            indexed_trilists_for_prim_state = indexed_trilists[find_vertex_prim_state_idx]
            for indexed_trilist in indexed_trilists_for_prim_state:
                triangles = indexed_trilist.vertex_idxs
                for tri in [tuple(triangles[i : i + 3]) for i in range(0, len(triangles), 3)]:
                    if find_vertex_idx in tri:
                        for vertex_idx in tri:
                            if vertex_idx != find_vertex_idx:
                                connected_vertex_idxs.append(vertex_idx)
                                connected_vertex_idxs = list(set(connected_vertex_idxs))

            for vertex_idx in connected_vertex_idxs:
                connected_vertices.append(vertices)

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
                        self._save()
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
    
    def insert_vertex_between(self, vertex1: Vertex, vertex2: Vertex) -> Vertex:
        if vertex1._lod_dlevel != vertex2._lod_dlevel:
            raise AttributeError("Cannot insert a new vertex between vertices in two different LOD distance levels.")
        if vertex1._subobject_idx != vertex2._subobject_idx:
            raise AttributeError("Cannot insert a new vertex between vertices in two different subobjects.")
        if vertex1._prim_state_idx != vertex2._prim_state_idx:
            raise AttributeError("Cannot insert a new vertex between vertices in two different prim states.")

        # TODO Steps:
        # Remove old triangle from vertex_idxs in trilist
        # Remove normal for old triangle from normal_idxs in trilist
        # Remove flag for old triangle from flags in trilist
        # Insert new point
        # Insert new uv_point
        # Insert new normal in vertex
        # Insert new triangles in trilist vertex_idxs
        # Insert new normals for newly created triangles in trilist normal_idxs
        # Insert new flags for newly created triangles in trilist flags
        # Insert new vertex
        # Adjust subobject header / vertex sets as necessary
        raise NotImplementedError()
    
    def remove_vertex(self, vertex: Vertex, reconnect_geometry: bool = True) -> bool:
        raise NotImplementedError()
    
    # def insert_vertex_between(self, point1, point1_idx, point2, point2_idx, prim_state_name):
    #     last_point_count_line_idx = 0
    #     last_point_line_idx = 0
    #     num_point_idxs = 0
    #     last_uvpoint_count_line_idx = 0
    #     last_uvpoint_line_idx = 0
    #     num_uvpoint_idxs = 0
    #     last_normals_count_line_idx = 0
    #     last_normals_line_idx = 0
    #     num_normals_idxs = 0
    #     last_vertices_count_line_idx = 0
    #     last_vertices_line_idx = 0
    #     current_vertex_idx = 0
    #     current_prim_state_name = None
    #     last_indexed_trilist_line_idx = 0
    #     num_indexed_trilist_lines = 0
    #     processing_normals = False
    #     processing_trilist = False
    #     reading_triangles = False
    #     new_vertex_trilist = []
    #     reading_normals = False
    #     new_normals_trilist = []
    #     reading_flags = False
    #     new_flags_trilist = []
    #     updated_triangles = False
    #     triangles = []
    #     normals = []
    #     flags = []
    #     insert_lines = {}
    #     replace_lines = {}
    #     delete_lines = []
    #     vertex1_idx = 0
    #     vertex2_idx = 0
        
    #     new_point = (point1 + point2) / 2
    #     prim_state_names = get_prim_state_names(self.lines)

    #     # First figure out what lines to update (if anything)
    #     for line_idx in range(0, len(self.lines)):
    #         sfile_line = self.lines[line_idx]

    #         if 'points (' in sfile_line.lower():
    #             last_point_count_line_idx = line_idx
            
    #         if 'point (' in sfile_line.lower():
    #             last_point_line_idx = line_idx
    #             num_point_idxs += 1
            
    #         if 'uv_points (' in sfile_line.lower():
    #             last_uvpoint_count_line_idx = line_idx
            
    #         if 'uv_point (' in sfile_line.lower():
    #             last_uvpoint_line_idx = line_idx
    #             num_uvpoint_idxs += 1
            
    #         if 'normals (' in sfile_line.lower():
    #             last_normals_count_line_idx = line_idx
    #             processing_normals = True

    #         if 'vector (' in sfile_line.lower():
    #             last_normals_line_idx = line_idx
    #             num_normals_idxs += 1

    #         if processing_normals and ')' in sfile_line.lower() and len(sfile_line.lower()) < 6:
    #             processing_normals = False

    #         if 'sub_object (' in sfile_line.lower():
    #             current_vertex_idx = 0
            
    #         if 'vertices (' in sfile_line.lower():
    #             last_vertices_count_line_idx = line_idx

    #         if 'vertex ' in sfile_line.lower():
    #             parts = sfile_line.split(" ")
    #             if point1_idx == int(parts[3]):
    #                 vertex1_idx = current_vertex_idx
    #             elif point2_idx == int(parts[3]):
    #                 vertex2_idx = current_vertex_idx
    #             last_vertices_line_idx = line_idx
    #             current_vertex_idx += 1

    #         if 'prim_state_idx' in sfile_line.lower():
    #             parts = sfile_line.split(" ")
    #             current_prim_state_name = prim_state_names[int(parts[2])]
            
    #         if current_prim_state_name == prim_state_name:

    #             if processing_trilist:
    #                 num_indexed_trilist_lines += 1
                
    #             if 'indexed_trilist' in sfile_line.lower():
    #                 processing_trilist = True
    #                 last_indexed_trilist_line_idx = line_idx
    #                 triangles = []

    #             if 'vertex_idxs (' in sfile_line.lower() or reading_triangles:
    #                 parts = sfile_line.replace('vertex_idxs', '').replace('(', '').replace(')', '').split()
    #                 if parts:
    #                     if not reading_triangles:
    #                         parts = parts[1:]
    #                     triangles.extend(map(int, parts))
    #                 reading_triangles = not sfile_line.endswith(')')
    #                 if not reading_triangles:
    #                     new_vertex_index = current_vertex_idx + 1
    #                     for tri in [tuple(triangles[i : i + 3]) for i in range(0, len(triangles), 3)]:
    #                         if vertex1_idx in tri and vertex2_idx in tri:
    #                             # Replace the edge with two new triangles
    #                             v3 = [v for v in tri if v not in (vertex1_idx, vertex2_idx)][0]
    #                             new_vertex_trilist.append((vertex1_idx, new_vertex_index, v3))
    #                             new_vertex_trilist.append((new_vertex_index, vertex2_idx, v3))
    #                             updated_triangles = True
    #                         else:
    #                             new_vertex_trilist.append(tri)
                
    #             if 'normal_idxs (' in sfile_line.lower() or reading_normals:
    #                 parts = sfile_line.replace('normal_idxs', '').replace('(', '').replace(')', '').split()
    #                 if parts:
    #                     if not reading_normals:
    #                         parts = parts[1:]
    #                     normals.extend(map(int, parts))
    #                 reading_normals = not sfile_line.endswith(')')
    #                 if not reading_triangles:
    #                     new_vertex_index = current_vertex_idx + 1
    #                     for normal in normals:
    #                         new_normals_trilist.append(normal)
                
    #             if 'flags (' in sfile_line.lower() or reading_flags:
    #                 parts = sfile_line.replace('flags', '').replace('(', '').replace(')', '').split()
    #                 if parts:
    #                     if not reading_flags:
    #                         parts = parts[1:]
    #                     flags.extend(map(int, parts))
    #                 reading_flags = not sfile_line.endswith(')')
    #                 if not reading_triangles:
    #                     new_vertex_index = current_vertex_idx + 1
    #                     for flag in flags:
    #                         new_flags_trilist.append(flag)

    #             if processing_trilist and ')' in sfile_line.lower() and updated_triangles:
    #                 replace_lines[last_point_count_line_idx] = "\tpoints ( %d" % (num_point_idxs + 1)
    #                 insert_lines[last_point_line_idx + 1] = "\t\tpoint ( %f %f %f )" % (new_point[0], new_point[1], new_point[2])
    #                 replace_lines[last_uvpoint_count_line_idx] = "\tuv_points ( %d" % (num_uvpoint_idxs + 1)
    #                 insert_lines[last_uvpoint_line_idx + 1] = "\t\tuv_point ( %f %f )" % (0, 0)
    #                 replace_lines[last_normals_count_line_idx] = "\normals ( %d" % (num_normals_idxs + 1)
    #                 insert_lines[last_normal_line_idx + 1] = "\t\vector ( %f %f %f )" % (0, 0, 1)
    #                 insert_lines[last_vertices_line_idx + 3] = [
    #                     "\t\t\t\t\t\t\t\tvertex ( 00000000 %d %d ff969696 ff808080" % (last_point_line_idx + 1, last_normal_line_idx + 1),
    #                     "\t\t\t\t\t\t\t\t\tvertex_uvs ( 1 %d )" % (last_uvpoint_line_idx + 1),
    #                     "\t\t\t\t\t\t\t\t)",
    #                 ]

    #                 num_new_indexed_trilist_lines = 1

    #                 vertex_trilist_chunks = [tuple(new_vertex_trilist[i : i + 197]) for i in range(0, len(new_vertex_trilist), 197)]
    #                 for index, chunk in enumerate(vertex_trilist_chunks):
    #                     line = "\t\t\t\t\t\t\t\t\t"

    #                     if index == 0:
    #                         line += "vertex_idxs ( %d " % (len(new_vertex_trilist)) + " ".join(chunk)
    #                     elif index == len(vertex_trilist_chunks) - 1:
    #                         line += " ".join(chunk) + " )"
    #                     else:
    #                         line += " ".join(chunk)
                        
    #                     if num_new_indexed_trilist_lines > num_indexed_trilist_lines:
    #                         replace_lines[last_indexed_trilist_line_idx + num_new_indexed_trilist_lines] = line
    #                     else:
    #                         insert_lines[last_indexed_trilist_line_idx + num_new_indexed_trilist_lines] = line
    #                     num_new_indexed_trilist_lines += 1
                    
    #                 normals_trilist_chunks = [tuple(new_normals_trilist[i : i + 197]) for i in range(0, len(new_normals_trilist), 197)]
    #                 for index, chunk in enumerate(normals_trilist_chunks):
    #                     line = "\t\t\t\t\t\t\t\t\t"

    #                     if index == 0:
    #                         line += "normal_idxs ( %d " % (len(new_normals_trilist)) + " ".join(chunk)
    #                     elif index == len(normals_trilist_chunks) - 1:
    #                         line += " ".join(chunk) + " )"
    #                     else:
    #                         line += " ".join(chunk)
                        
    #                     if num_new_indexed_trilist_lines > num_indexed_trilist_lines:
    #                         replace_lines[last_indexed_trilist_line_idx + num_new_indexed_trilist_lines] = line
    #                     else:
    #                         insert_lines[last_indexed_trilist_line_idx + num_new_indexed_trilist_lines] = line
    #                     num_new_indexed_trilist_lines += 1
                    
                    
    #                 flags_trilist_chunks = [tuple(new_lags_trilist[i : i + 197]) for i in range(0, len(new_flags_trilist), 197)]
    #                 for index, chunk in enumerate(flags_trilist_chunks):
    #                     line = "\t\t\t\t\t\t\t\t\t"

    #                     if index == 0:
    #                         line += "normal_idxs ( %d " % (len(new_flags_trilist)) + " ".join(chunk)
    #                     elif index == len(flags_trilist_chunks) - 1:
    #                         line += " ".join(chunk) + " )"
    #                     else:
    #                         line += " ".join(chunk)
                        
    #                     if num_new_indexed_trilist_lines > num_indexed_trilist_lines:
    #                         replace_lines[last_indexed_trilist_line_idx + num_new_indexed_trilist_lines] = line
    #                     else:
    #                         insert_lines[last_indexed_trilist_line_idx + num_new_indexed_trilist_lines] = line
    #                     num_new_indexed_trilist_lines += 1
                    
    #                 # TODO what if there is fewer new lines than num_indexed_trilist_lines? (= delete the rest)

    #                 processing_primitives = False
    #                 updated_triangles = False
    #                 new_vertex_trilist = []
    #                 new_normals_trilist = []
    #                 new_flags_trilist = []
    #                 num_indexed_trilist_lines = 0

    #     # Update lines from the bottom and upwards
    #     print("delete_lines: " + str(delete_lines))
    #     print("replace_lines: " + str(replace_lines))
    #     print("insert_lines: " + str(insert_lines))

    #     # for line_idx in range(len(self.lines), 0):
    #     #     if line_idx in delete_lines:
    #     #         del self.lines[line_idx]
    #     #     if line_idx in replace_lines:
    #     #         self.lines[line_idx] = insert_lines[line_idx]
    #     #     if line_idx in insert_lines:
    #     #         self.lines[line_idx : line_idx] = insert_lines[line_idx]
        
    #     #return new_point_idx, new_uvpoint_idx, new_normals_idx

    # def remove_vertex(vertices, indexed_trilist, vertex_index):
    #     indexed_trilist = [tri for tri in indexed_trilist if vertex_index not in tri]
    #     return vertices, indexed_trilist


    # def remove_vertex_and_reconnect_geometry(vertices, indexed_trilist, vertex_index):
    #     affected_triangles = [tri for tri in indexed_trilist if vertex_index in tri]
    #     indexed_trilist = [tri for tri in indexed_trilist if vertex_index not in tri]
        
    #     connected_vertices = set()
    #     for tri in affected_triangles:
    #         connected_vertices.update(tri)
    #     connected_vertices.discard(vertex_index)
    #     connected_vertices = list(connected_vertices)
        
    #     if len(connected_vertices) >= 2:
    #         for i in range(len(connected_vertices)):
    #             for j in range(i + 1, len(connected_vertices)):
    #                 indexed_trilist.append((connected_vertices[i], connected_vertices[j]))
        
    #     return vertices, indexed_trilist


class Trackcenter:
    def __init__(self, centerpoints):
        self.centerpoints = centerpoints

    def __repr__(self):
        return f"Trackcenter(centerpoints={self.centerpoints})"
    
    def __add__(self, trackcenter2):
        combined_centerpoints = np.vstack((self.centerpoints, trackcenter2.centerpoints))
        return Trackcenter(combined_centerpoints)


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
        raise AttributeError("Please use the method 'load_shape(filename: str, directory: str) when loading a shapefile.'")
    
    return File(filename, directory, encoding=encoding)


def load_shape(filename: str, directory: str, encoding: str = None) -> Shapefile:
    if not filename.endswith(".s"):
        raise AttributeError("Please use the method 'load_file(filename: str, directory: str) when loading a file that is not a shapefile.'")
    
    return Shapefile(filename, directory, encoding=encoding)


def generate_empty_centerpoints() -> Trackcenter:
    centerpoints = np.empty((0, 3))

    return Trackcenter(centerpoints)


def generate_straight_centerpoints(length: float, num_points: int = 1000, start_point: Point = Point(0, 0, 0)) -> Trackcenter:
    z = np.linspace(start_point.z, start_point.z + length, num_points)
    x = np.full_like(z, start_point.x)
    y = np.full_like(z, start_point.y)

    centerpoints = np.vstack((x, y, z)).T

    return Trackcenter(centerpoints)


def generate_curve_centerpoints(curve_radius: float, curve_angle: float, num_points: int = 1000, start_point: Point = Point(0, 0, 0)) -> Trackcenter:
    theta = np.radians(np.linspace(0, abs(curve_angle), num_points))

    z = start_point.z + curve_radius * np.sin(theta)
    x = start_point.x + curve_radius * (1 - np.cos(theta))
    y = np.full_like(x, start_point.y)

    if curve_angle < 0:
        x = start_point.x - (curve_radius * (1 - np.cos(theta)))

    centerpoints = np.vstack((x, y, z)).T
    
    return Trackcenter(centerpoints)


def autodetect_centerpoints(shape_name: str) -> Trackcenter:
    module_directory = pathlib.Path(__file__).parent
    tsection_file_path = f"{module_directory}/tsection.dat"

    tracksections = []
    trackshapes = []
    with open(tsection_file_path, "r", encoding="utf-16-le") as f:
        lines = f.read().split('\n')
        # TODO Create and return centerpoints based on data from the standardised global tsection.dat
        raise NotImplementedError()

    raise AttributeError(f"""Unable to autodetect centerpoints: Unknown shape '{shape_name}'. Instead create 
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


def get_curve_point_from_angle(radius: float, curve_angle: float) -> Point:
    theta = np.radians(abs(angle_degrees))

    z = radius * np.sin(theta)
    x = radius * (1 - np.cos(theta))
    y = 0

    if curve_angle < 0:
        x = -x
    
    return Point.from_numpy(np.array([x, y, z]))
    

def get_new_position_from_angle(curve_radius: float, curve_angle: float, original_point: Point, trackcenter: Trackcenter) -> Point:
    closest_center = find_closest_centerpoint(original_point, trackcenter, plane='xz')
    offset = original_point.to_numpy() - closest_center.to_numpy()
    
    start_point = trackcenter.centerpoints[0]
    
    calculated_curve_point = get_curve_point_from_angle(curve_radius, curve_angle)
    new_x = start_point[0] + calculated_curve_point[0]
    new_z = start_point[2] + calculated_curve_point[2]
    
    new_position = np.array([new_x, original_point[1], new_z]) + offset

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
