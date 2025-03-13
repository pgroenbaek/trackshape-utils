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

import pytest
import trackshapeutils as tsu

@pytest.fixture(scope="module")
def global_storage():
    data = {
        "shape": tsu.load_shape("DK10f_A1tPnt5dLft.s", "./tests/data"),
        "shape_copied": tsu.load_shape("DK10f_A1tPnt5dLft_copied.s", "./tests/data"),
        "shape_compressed": tsu.load_shape("DK10f_A1tPnt5dLft_compressed.s", "./tests/data")
    }
    data["shape_changed"] = data["shape"].copy(new_filename="DK10f_A1tPnt5dLft_changed.s")
    return data

def test_shape_is_compressed(global_storage):
    shape = global_storage["shape_compressed"]
    assert shape.is_compressed()

def test_shape_is_not_compressed(global_storage):
    shape = global_storage["shape"]
    assert not shape.is_compressed()

def test_shape_repl_uncompressed(global_storage):
    shape = global_storage["shape"]
    shape_string = str(shape)
    assert 'compressed=False' in shape_string
    assert 'lines' in shape_string

def test_shape_repl_compressed(global_storage):
    shape = global_storage["shape_compressed"]
    shape_string = str(shape)
    assert 'compressed=True' in shape_string

def test_copy_shape(global_storage):
    shape = global_storage["shape"]
    copied_shape = shape.copy(new_filename="DK10f_A1tPnt5dLft_copied.s")
    assert copied_shape.filename == "DK10f_A1tPnt5dLft_copied.s"

def test_lines_access(global_storage):
    shape = global_storage["shape"]
    try:
        lines = shape.lines
    except Exception as e:
        pytest.fail(f"An unexpected exception occurred: {e}")
    assert isinstance(lines, list) and len(lines) > 0

def test_lines_access_denied(global_storage):
    shape = global_storage["shape_compressed"]
    with pytest.raises(AttributeError) as exc_info:
        lines = shape.lines

def test_get_lod_dlevels(global_storage):
    shape = global_storage["shape"]
    lod_dlevels = shape.get_lod_dlevels()
    assert len(lod_dlevels) == 4
    assert lod_dlevels[0] == 200
    assert lod_dlevels[1] == 500
    assert lod_dlevels[2] == 800
    assert lod_dlevels[3] == 2000

def test_get_prim_states(global_storage):
    shape = global_storage["shape"]
    prim_states = shape.get_prim_states()
    assert len(prim_states) == 30

def test_get_prim_state_by_name(global_storage):
    shape = global_storage["shape"]
    prim_state = shape.get_prim_state_by_name("DB_Track2sw_top")
    assert prim_state.name == "DB_Track2sw_top"
    assert prim_state.idx == 6

def test_get_prim_state_by_idx(global_storage):
    shape = global_storage["shape"]
    prim_state = shape.get_prim_state_by_idx(6)
    assert prim_state.name == "DB_Track2sw_top"
    assert prim_state.idx == 6

def test_get_points(global_storage):
    shape = global_storage["shape"]
    points = shape.get_points()
    assert len(points) == 3962

def test_get_point_by_idx(global_storage):
    shape = global_storage["shape"]
    point = shape.get_point_by_idx(3)
    assert point.x == 1.7
    assert point.y == 0.14698
    assert point.z == 75.1042

def test_set_point_value(global_storage):
    shape = global_storage["shape_changed"]
    point_idx_to_update = 4
    new_x_value = 0.5
    new_y_value = 0.5
    new_z_value = 0.5
    point_to_update = tsu.Point(new_x_value, new_y_value, new_z_value)
    shape.set_point_value(point_idx_to_update, point_to_update)
    shape._read()
    updated_point = shape.get_point_by_idx(point_idx_to_update)
    assert updated_point.x == new_x_value
    assert updated_point.y == new_y_value
    assert updated_point.z == new_z_value

def test_set_point_count(global_storage):
    shape = global_storage["shape_changed"]
    updated_count = shape.set_point_count(0)
    assert updated_count

def test_add_point(global_storage):
    shape = global_storage["shape_changed"]
    new_point = tsu.Point(0, 0, 0)
    new_point_index = shape.add_point(new_point)
    shape._read()
    assert new_point_index is not None
    updated_point = shape.get_point_by_idx(new_point_index)
    assert updated_point.x == new_point.x
    assert updated_point.y == new_point.y
    assert updated_point.z == new_point.z

def test_get_uvpoints(global_storage):
    shape = global_storage["shape"]
    uvpoints = shape.get_uvpoints()
    assert len(uvpoints) == 1841

def test_get_uvpoint_by_idx(global_storage):
    shape = global_storage["shape"]
    uvpoint = shape.get_uvpoint_by_idx(3)
    assert uvpoint.u == 0.7158
    assert uvpoint.v == -14.0208

def test_set_uvpoint_value(global_storage):
    shape = global_storage["shape_changed"]
    uv_point_idx_to_update = 4
    new_u_value = 0.5
    new_v_value = 0.5
    uv_point_to_update = tsu.UVPoint(new_u_value, new_v_value)
    shape.set_uvpoint_value(uv_point_idx_to_update, uv_point_to_update)
    shape._read()
    updated_uv_point = shape.get_uvpoint_by_idx(uv_point_idx_to_update)
    assert updated_uv_point.u == new_u_value
    assert updated_uv_point.v == new_v_value

def test_set_uvpoint_count(global_storage):
    shape = global_storage["shape_changed"]
    updated_count = shape.set_uvpoint_count(0)
    assert updated_count

def test_add_uvpoint(global_storage):
    shape = global_storage["shape_changed"]
    new_uvpoint = tsu.UVPoint(0, 0)
    new_uvpoint_index = shape.add_uvpoint(new_uvpoint)
    shape._read()
    assert new_uvpoint_index is not None
    added_uvpoint = shape.get_uvpoint_by_idx(new_uvpoint_index)
    assert added_uvpoint.u == new_uvpoint.u
    assert added_uvpoint.v == new_uvpoint.v

def test_get_normals(global_storage):
    shape = global_storage["shape"]
    normals = shape.get_normals()
    assert len(normals) == 2725

def test_get_normal_by_idx(global_storage):
    shape = global_storage["shape"]
    normal = shape.get_normal_by_idx(3)
    assert normal.vec_x == 0
    assert normal.vec_y == 0.994208
    assert normal.vec_z == 0

def test_set_normal_value(global_storage):
    shape = global_storage["shape_changed"]
    normal_idx_to_update = 4
    new_vec_x_value = 0.5
    new_vec_y_value = 0.5
    new_vec_z_value = 0.5
    normal_to_update = tsu.Normal(new_vec_x_value, new_vec_y_value, new_vec_z_value)
    shape.set_normal_value(normal_idx_to_update, normal_to_update)
    shape._read()
    updated_normal = shape.get_normal_by_idx(normal_idx_to_update)
    assert updated_normal.vec_x == new_vec_x_value
    assert updated_normal.vec_y == new_vec_y_value
    assert updated_normal.vec_z == new_vec_z_value

def test_set_normal_count(global_storage):
    shape = global_storage["shape_changed"]
    updated_count = shape.set_normal_count(0)
    assert updated_count

def test_add_normal(global_storage):
    shape = global_storage["shape_changed"]
    new_normal = tsu.Normal(0, 0, 0)
    new_normal_index = shape.add_normal(new_normal)
    shape._read()
    assert new_normal_index is not None
    added_normal = shape.get_normal_by_idx(new_normal_index)
    assert added_normal.vec_x == new_normal.vec_x
    assert added_normal.vec_y == new_normal.vec_y
    assert added_normal.vec_z == new_normal.vec_z

def test_get_subobject_idxs_in_lod_dlevel(global_storage):
    shape = global_storage["shape"]
    lod_dlevel = 200
    subject_idxs = shape.get_subobject_idxs_in_lod_dlevel(lod_dlevel)
    assert len(subject_idxs) == 5

def test_get_indexed_trilists_in_subobject(global_storage):
    shape = global_storage["shape"]
    lod_dlevel = 200
    subobject_idx = 0
    indexed_trilists = shape.get_indexed_trilists_in_subobject(lod_dlevel, subobject_idx)
    assert len(indexed_trilists) == 21
    assert len(indexed_trilists[0]) == 2

def test_get_vertices_in_subobject(global_storage):
    shape = global_storage["shape"]
    lod_dlevel = 200
    subobject_idx = 0
    vertices = shape.get_vertices_in_subobject(lod_dlevel, subobject_idx)
    assert len(vertices) == 7427

def test_get_vertices_by_prim_state(global_storage):
    shape = global_storage["shape"]
    lod_dlevel = 200
    prim_state = shape.get_prim_state_by_idx(0)
    vertices = shape.get_vertices_by_prim_state(lod_dlevel, prim_state)
    assert len(vertices) == 3227

def test_get_connected_vertices(global_storage):
    shape = global_storage["shape"]
    lod_dlevel = 200
    prim_state = shape.get_prim_state_by_idx(0)
    vertices = shape.get_vertices_by_prim_state(lod_dlevel, prim_state)
    connected_vertices = shape.get_connected_vertices(vertices[100])
    assert len(connected_vertices) == 2

def test_set_vertices_count(global_storage):
    shape = global_storage["shape_changed"]
    lod_dlevel = 200
    subobject_idx = 0
    updated_count = shape.set_vertices_count(lod_dlevel, subobject_idx, 133337)
    assert updated_count