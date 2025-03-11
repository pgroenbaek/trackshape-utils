
import os
import fnmatch
import subprocess
import re
import copy
import codecs
import shutil
import numpy as np
from scipy.interpolate import splprep, splev
from scipy.spatial import KDTree
from typing import List, Dict, Tuple


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
        """Convert the Point object to a NumPy array."""
        return np.array([self.x, self.y, self.z])

    @classmethod
    def from_numpy(cls, array: np.ndarray):
        """Create a Point object from a NumPy array."""
        if array.shape != (3,):
            raise ValueError("Input array must have shape (3,).")
        return cls(array[0], array[1], array[2])

class UVPoint:
    def __init__(self, u: float, v: float):
        self.u = u
        self.v = v
    
    def __repr__(self):
        return f"UVPoint(x={self.u}, y={self.v})"


class Normal:
    def __init__(self, vec_x: float, vec_y: float, vec_z: float):
        self.vec_x = vec_x
        self.vec_y = vec_y
        self.vec_z = vec_z
    
    def __repr__(self):
        return f"Normal(vec_x={self.vec_x}, vec_y={self.vec_y}, vec_z={self.vec_z})"


class Vertex:
    def __init__(self, vertex_idx: int, point: Point, uv_point: UVPoint, point_idx: int, uv_point_idx: int, normal_idx: int, \
            lod_dlevel: int, prim_state: PrimState, subobject_idx: int):
        self.point = point
        self.uv_point = uv_point
        self.normal = normal
        self._vertex_idx = vertex_idx
        self._point_idx = point_idx
        self._uv_point_idx = uv_point_idx
        self._normal_idx = normal_idx
        self._lod_dlevel = lod_dlevel
        self._prim_state = prim_state
        self._subobject_idx = subobject_idx
    
    def __repr__(self):
        return f"""Vertex(vertex_idx={self._vertex_idx}, point={self.point}, point_idx={self._point_idx}, uv_point={self.uv_point}, 
            uv_point_idx={self._uv_point_idx}, normal={self.normal}, normal_idx={self._normal_idx},
            lod_dlevel={self._normal_idx}, prim_state={self._prim_state}, subobject_idx={self._subobject_idx})"""


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
            with open(self.filepath, 'w') as f:
                pass

    def _read(self) -> List[str]:
        with open(self.filepath, 'r', encoding=_detect_encoding(self.filepath)) as f:
            return f.read().split('\n')
    
    def _save(self, encoding: str = None) -> None:
        if encoding is None:
            encoding = self.encoding
        with open(self.filepath, 'w', encoding=encoding) as f:
            text = '\n'.join(self.lines)
            f.write(text)

    def copy(self, new_filename: str, new_directory: str = None) -> "File":
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

    def is_compressed(self) -> bool:
        with open(self.filepath, 'r', encoding=_detect_encoding(self.filepath)) as f:
            try:
                header = f.read(32)
                if header.startswith("SIMISA@@@@@@@@@@JINX0s1t______"):
                    return False
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
            self._lines = super()._read()

    @property
    def lines(self) -> List[str]:
        if self.is_compressed():
            raise AttributeError("Cannot access lines when the shapefile is compressed. Use the 'decompress(ffeditc_path: str)' method first.")
        return self._lines

    def get_lod_dlevels(self) -> List[int]:
        lod_dlevels = []

        for line in self.lines:
            if "dlevel_selection (" in line.lower():
                parts = line.split()
                lod_dlevels.append(int(parts[2]))

        return sorted(lod_dlevels)
    
    def get_prim_states(self) -> List[PrimState]:
        prim_states = []
        prim_state_idx = 0

        for line in self.lines:
            if "prim_state " in line.lower():
                parts = line.split()
                prim_states.append(PrimState(prim_state_idx, parts[1]))
                prim_state_idx += 1

        return prim_states
    
    def get_prim_state_by_name(self, prim_state_name: str) -> PrimState:
        prim_state_idx = 0

        for line in self.lines:
            if "prim_state " in line.lower():
                parts = line.split()
                if parts[1] == prim_state_name:
                    return PrimState(prim_state_idx, parts[1])
                prim_state_idx += 1

        return None

    def get_subobject_idxs_in_lod_dlevel(self, lod_dlevel: int) -> List[int]:
        subobject_idxs = []
        subobject_idx = 0
        current_dlevel = -1

        for line_idx in range(0, len(self.lines)):
            line = self.lines[line_idx]

            if "dlevel_selection (" in line.lower():
                parts = line.split()
                current_dlevel = int(parts[2])

            if "sub_object (" in line.lower() and current_dlevel == lod_dlevel:
                subobject_idxs.append(subobject_idx)
                subobject_idx += 1

        return subobject_idxs
    
    def get_vertices_in_subobject_idx(self, lod_dlevel: int, prim_state: PrimState, subobject_idx: int) -> List[Vertex]:
        vertices = []
        # TODO
        return vertices
    
    def get_connected_vertices(self, vertex: Vertex) -> List[Vertex]:
        connected_vertices = []
        # TODO
        return connected_vertices
    
    def update_vertex(self, vertex: Vertex) -> None:
        raise NotImplementedError()
        self._save()
    
    def insert_vertex_between(self, vertex1: Vertex, vertex2: Vertex) -> Vertex:
        raise NotImplementedError()
        self._save()
    
    def remove_vertex(self, vertex: Vertex, reconnect_geometry: bool = True) -> None:
        raise NotImplementedError()
        self._save()
    
    # def get_uv_point_idxs(self):
    #     uv_point_idxs = {}

    #     for line_idx in range(0, len(self.lines)):
    #         sfile_line = self.lines[line_idx]
    #         if 'vertex (' in sfile_line.lower():
    #             parts = "".join(self.lines[line_idx : line_idx + 2]).split(" ")
    #             uv_point_idxs[int(parts[3])] = int(parts[9])

    #     return uv_point_idxs

    # def get_uv_point_value(self, uv_point_idx):
    #     current_uv_point_idx = 0

    #     for line_idx in range(0, len(self.lines)):
    #         sfile_line = self.lines[line_idx]
    #         if 'uv_point (' in sfile_line.lower():
    #             if current_uv_point_idx == uv_point_idx:
    #                 parts = sfile_line.split(" ")
    #                 return float(parts[2]), float(parts[3]),
    #             current_uv_point_idx += 1

    #     return None

    # def set_uv_point_value(self, uv_point_idx, u_value, v_value):
    #     current_uv_point_idx = 0

    #     for line_idx in range(0, len(self.lines)):
    #         sfile_line = self.lines[line_idx]
    #         if 'uv_point (' in sfile_line.lower():
    #             if current_uv_point_idx == uv_point_idx:
    #                 parts = sfile_line.split(" ")
    #                 parts[2] = str(u_value)
    #                 parts[3] = str(v_value)
    #                 sfile_line = " ".join(parts)
    #                 self.lines[line_idx] = sfile_line
    #                 break
    #             current_uv_point_idx += 1

    # def get_point_idxs_by_prim_state_name(self):
    #     points_by_prim_state_name = {}
    #     current_prim_state_name = None
    #     processing_primitives = False
    #     collecting_vertex_idxs = False
    #     current_vertex_indices = []
    #     vertices_map = []

    #     prim_state_names = get_prim_state_names(self.lines)

    #     for sfile_line in self.lines:
    #         if 'sub_object (' in sfile_line.lower():
    #             vertices_map = []

    #         if 'vertex ' in sfile_line.lower():
    #             parts = sfile_line.split()
    #             if len(parts) > 3:
    #                 point_idx = int(parts[3])
    #                 vertices_map.append(point_idx)

    #         if 'prim_state_idx' in sfile_line.lower():
    #             parts = sfile_line.split(" ")
    #             current_prim_state_name = prim_state_names[int(parts[2])]
    #             if current_prim_state_name not in points_by_prim_state_name:
    #                 points_by_prim_state_name[current_prim_state_name] = []
            
    #         if 'indexed_trilist' in sfile_line.lower():
    #             processing_primitives = True
    #             current_vertex_indices = []

    #         if 'vertex_idxs' in sfile_line.lower() or collecting_vertex_idxs:
    #             parts = sfile_line.replace('vertex_idxs', '').replace('(', '').replace(')', '').split()
    #             if parts:
    #                 if not collecting_vertex_idxs:
    #                     parts = parts[1:]
    #                 current_vertex_indices.extend(map(int, parts))
    #             collecting_vertex_idxs = not sfile_line.endswith(')')

    #         if processing_primitives and ')' in sfile_line.lower() and current_vertex_indices:
    #             for vertex_idx in current_vertex_indices:
    #                 point_index = vertices_map[vertex_idx]
    #                 if point_index not in points_by_prim_state_name[current_prim_state_name]:
    #                     points_by_prim_state_name[current_prim_state_name].append(point_index)
    #             processing_primitives = False

    #     return points_by_prim_state_name

    # def get_prim_state_names(self):
    #     prim_state_names = []

    #     for sfile_line in self.lines:
    #         if "prim_state " in sfile_line.lower():
    #             parts = sfile_line.split()
    #             prim_state_names.append(parts[1])

    #     return prim_state_names

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


class Trackcenter:
    def __init__(self, centerpoints):
        self.centerpoints = centerpoints

    def __repr__(self):
        return f"Trackcenter(centerpoints={self.centerpoints})"
    
    def __add__(self, trackcenter2):
        return Trackcenter(np.vstack((self.centerpoints, trackcenter2.centerpoints)))


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
        raise AttributeError("You are trying to load a shapefile. Please use the method 'load_shape(filename: str, directory: str) instead.'")
    
    return File(filename, directory, encoding=encoding)


def load_shape(filename: str, directory: str, encoding: str = None) -> Shapefile:
    if not filename.endswith(".s"):
        raise AttributeError("You are trying to load a file that is not a shapefile. Please use the method 'load_file(filename: str, directory: str) instead.'")
    
    return Shapefile(filename, directory, encoding=encoding)


def generate_empty_centerpoints() -> Trackcenter:
    empty_centerpoints = np.empty((0, 3))
    return Trackcenter(empty_centerpoints)


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
    raise NotImplementedError()


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