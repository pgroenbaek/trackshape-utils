# Railhead vertices from center to outside:
#[Vector((-0.7175, 0.2, 0.0))]
#[Vector((-0.7175, 0.325, 0.0))]
#[Vector((-0.8675, 0.325, 0.0))]
#[Vector((-0.8675, 0.2, 0.0))]

# Railhead vertices for ATracks:
# [Vector((-0.6785, 0.192, 0.0))]
# [Vector((-0.6785, 0.215, 0.0))]
# [Vector((-0.7694, 0.2268, 0.0))]
# [Vector((-0.7175, 0.325, 0.0))]
# [Vector((-0.7895, 0.325, 0.0))]
# [Vector((-0.7374, 0.2268, 0.0))]
# [Vector((-0.8285, 0.215, 0.0))]
# [Vector((-0.8285, 0.192, 0.0))]

# Points needed for UVPoints:
# Top of rail base: [Vector((-0.7535000443458557, 0.23000000417232513, 0.0))]
# Bottom of rail: [Vector((-0.7619999647140503, 0.1899999976158142, 0.0))]
# Bottom of rail: [Vector((-0.7619999647140503, 0.1899999976158142, 0.0))]

import os
import trackshapeutils as tsu
from collections import defaultdict

if __name__ == "__main__":
    shape_load_path = "./examples/data"
    shape_processed_path = "./examples/data/processed/NREmbAtracksRails"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = [
        # For testing
        "NR_Emb_a1t10mStrt.s",
        "NR_Emb_a1t250r10d.s",
        "NR_Emb_a2t1000r1d.s",
        "NR_Emb_a3t1000r1d.s",
        "NR_Emb_a4t1000r1d.s",
        "NR_EmbBase_a1t10mStrt.s",
        "NR_Ramp_a1t10mStrt.s",
        "NR_RWall_a1t10mStrt_lft.s",
        "NR_WallEmb_a1t10mStrt_lft.s",

        # All of the shapes
        #"NR_Emb_*.s",
        #"NR_EmbBase_*.s",
        #"NR_Ramp_*.s",
        #"NR_RWall_*.s",
        #"NR_WallEmb_*.s",
    ]
    ignore_shapes = ["*Tun*", "*Pnt*", "*Frog*"]
    
    os.makedirs(shape_processed_path, exist_ok=True)

    shape_names = tsu.find_directory_files(shape_load_path, match_shapes, ignore_shapes)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx + 1} of {len(shape_names)}...")
        print(f"\tName: {sfile_name}")

        # Process .s file
        new_sfile_name = sfile_name.replace("_a", "_AT_a")
        tsection_sfile_name = sfile_name.replace("a2dt", "a2t")
        tsection_sfile_name = tsection_sfile_name.replace("_lft", "")
        tsection_sfile_name = tsection_sfile_name.replace("_rgt", "")
        tsection_sfile_name = tsection_sfile_name.replace("NR_EmbBase_", "")
        tsection_sfile_name = tsection_sfile_name.replace("NR_Ramp_", "")
        tsection_sfile_name = tsection_sfile_name.replace("NR_RWall_", "")
        tsection_sfile_name = tsection_sfile_name.replace("NR_WallEmb_", "")
        tsection_sfile_name = tsection_sfile_name.replace("NR_Emb_", "")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

        trackcenter = tsu.generate_centerpoints_from_tsection(shape_name=tsection_sfile_name, num_points_per_path=100)

        # First find the vertices to work on.
        # The naming right/left refers to which side of the track it is relative to the track center.
        # The naming close/far refers to distance from the start of the track.
        lod_dlevel = 400
        subobject_idx = 0
        prim_states = new_sfile.get_prim_states_by_name("rail_side")

        for prim_state in prim_states:
            print(f"\tPrim State Idx: {prim_state.idx}")
            vertices_in_prim_state = new_sfile.get_vertices_by_prim_state(lod_dlevel, prim_state)
            vertices_in_subobject = new_sfile.get_vertices_in_subobject(lod_dlevel, subobject_idx)
            indexed_trilists = new_sfile.get_indexed_trilists_in_subobject_by_prim_state(lod_dlevel, subobject_idx, prim_state)

            if len(indexed_trilists) == 0:
                print(f"\tNothing to process")
                continue

            railside_indexed_trilist = indexed_trilists[0]
            
            # Find railside and railtop vertices.
            print(f"\tFinding railside and railtop vertices")
            railtop_vertices_outer = []
            railtop_vertices_inner = []
            railside_vertices_top = defaultdict(list)
            railside_vertices_bottom = defaultdict(list)

            for vertex in vertices_in_prim_state:
                if vertex.point.y == 0.325 and vertex.normal == tsu.Normal(0.0, 1.0, 0.0): # Railtop vertices
                    closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, trackcenter, plane="xz")
                    distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")
                    
                    if 0.8175 <= distance_from_center <= 0.9175 or -0.9175 <= distance_from_center <= -0.8175: # Outer railtop.
                        if not any(v.point == vertex.point for v in railtop_vertices_outer):
                            railtop_vertices_outer.append(vertex)

                    elif 0.6675 <= distance_from_center <= 0.7675 or -0.7675 <= distance_from_center <= -0.6675: # Inner railtop.
                        if not any(v.point == vertex.point for v in railtop_vertices_inner):
                            railtop_vertices_inner.append(vertex)


            for vertex in vertices_in_prim_state:
                if vertex.point.y == 0.2: # Railside bottom vertices
                    connected_vertex_idxs = new_sfile.get_connected_vertex_idxs(railside_indexed_trilist, vertex)

                    for connected_vertex_idx in connected_vertex_idxs:
                        connected_vertex = vertices_in_subobject[connected_vertex_idx]

                        if connected_vertex.point.y == 0.325 and connected_vertex.point.z == vertex.point.z: # Connected railside top vertices directly over the bottom ones
                            closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, trackcenter, plane="xz")
                            distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")

                            if 0.8175 <= distance_from_center <= 0.9175: # Outer right railside.
                                if not any(v.point == connected_vertex.point for v in railside_vertices_top["right_outer"]):
                                    railside_vertices_top["right_outer"].append(connected_vertex)
                                if not any(v.point == vertex.point for v in railside_vertices_bottom["right_outer"]):
                                    railside_vertices_bottom["right_outer"].append(vertex)

                            elif 0.6675 <= distance_from_center <= 0.7675: # Inner right railside.
                                if not any(v.point == connected_vertex.point for v in railside_vertices_top["right_inner"]):
                                    railside_vertices_top["right_inner"].append(connected_vertex)
                                if not any(v.point == vertex.point for v in railside_vertices_bottom["right_inner"]):
                                    railside_vertices_bottom["right_inner"].append(vertex)

                            elif -0.7675 <= distance_from_center <= -0.6675: # Inner left railside.
                                if not any(v.point == connected_vertex.point for v in railside_vertices_top["left_inner"]):
                                    railside_vertices_top["left_inner"].append(connected_vertex)
                                if not any(v.point == vertex.point for v in railside_vertices_bottom["left_inner"]):
                                    railside_vertices_bottom["left_inner"].append(vertex)

                            elif -0.9175 <= distance_from_center <= -0.8175: # Outer left railside.
                                if not any(v.point == connected_vertex.point for v in railside_vertices_top["left_outer"]):
                                    railside_vertices_top["left_outer"].append(connected_vertex)
                                if not any(v.point == vertex.point for v in railside_vertices_bottom["left_outer"]):
                                    railside_vertices_bottom["left_outer"].append(vertex)
            
            print(f"\tSorting railside vertices")
            for side in railside_vertices_top:
                railside_vertices_top[side].sort(key=lambda v: tsu.distance_along_nearest_trackcenter(v.point, trackcenter))
            
            for side in railside_vertices_bottom:
                railside_vertices_bottom[side].sort(key=lambda v: tsu.distance_along_nearest_trackcenter(v.point, trackcenter))
            
            print(f"\tGrouping railside vertices")
            parallel_tracks = lambda v1, v2: tsu.distance_between(v1.point, v2.point, plane="xz") <= 3.0

            for side in railside_vertices_top:
                railside_vertices_top[side] = tsu.group_vertices_by(railside_vertices_top[side], parallel_tracks)
            
            for side in railside_vertices_bottom:
                railside_vertices_bottom[side] = tsu.group_vertices_by(railside_vertices_bottom[side], parallel_tracks)

            # Find the quads between the vertical edges of the rail sides.
            print(f"\tFinding railside quads")
            railside_quads = defaultdict(list)

            for side in railside_vertices_top:
                for group_idx, group in enumerate(railside_vertices_top[side]):
                    for i in range(len(railside_vertices_top[side][group_idx]) - 1):
                        if group_idx > len(railside_quads[side]) - 1:
                            railside_quads[side].append([])
                        
                        bottom_close = railside_vertices_bottom[side][group_idx][i]
                        bottom_far = railside_vertices_bottom[side][group_idx][i + 1]
                        top_close = railside_vertices_top[side][group_idx][i]
                        top_far = railside_vertices_top[side][group_idx][i + 1]

                        quad = (bottom_close, top_close, top_far, bottom_far)
                        railside_quads[side][group_idx].append(quad)


            # Creation of ATracks-like rail sides and rail tops.
            # New vertices are added, and at the end their values are changed according to the contents of 'update_vertex_data'.
            # New triangles are added according to the contents of 'new_triangles'. The order of vertices in each 'new_triangles' list item determines direction of the face.
            update_vertex_data = [] # Format: [(vertex, new_height, new_center_distance, new_u_value, new_v_value, new_normal_vecx, new_normal_vecy, new_normal_vecz), ...]
            new_triangles = [] # Format: [(vertex1, vertex2, vertex3), ...]
            prev_vertices = None

            # Outer railtops.
            for idx, vertex in enumerate(railtop_vertices_outer):
                print(f"\tProcessing outer railtop {idx + 1} of {len(railtop_vertices_outer)}", end='\r')
                closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, trackcenter, plane="xz")
                distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")
                distance_along_track = tsu.distance_along_nearest_trackcenter(vertex.point, trackcenter)
                rails_delta_texcoord = 2
                u_value = float(distance_along_track * rails_delta_texcoord)

                # Updated values for existing vertices.
                update_vertex_data.extend([
                    (vertex, vertex.point.y, distance_from_center, u_value, -0.77, vertex.normal.vec_x, vertex.normal.vec_y, vertex.normal.vec_z),
                ])

            print("")

            # Inner railtops.
            for idx, vertex in enumerate(railtop_vertices_inner):
                print(f"\tProcessing inner railtop {idx + 1} of {len(railtop_vertices_inner)}", end='\r')
                closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, trackcenter, plane="xz")
                distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")
                distance_along_track = tsu.distance_along_nearest_trackcenter(vertex.point, trackcenter)
                rails_delta_texcoord = 2
                u_value = float(distance_along_track * rails_delta_texcoord)

                # Updated values for existing vertices.
                update_vertex_data.extend([
                    (vertex, vertex.point.y, distance_from_center, u_value, -0.875, vertex.normal.vec_x, vertex.normal.vec_y, vertex.normal.vec_z),
                ])

            print("")
            
            # Outer right railside.
            total_items = sum(len(group) for group in railside_quads["right_outer"])
            processed_items = 0
            for group_idx in range(len(railside_vertices_top["right_outer"])):
                for idx, (bottom_close, top_close, top_far, bottom_far) in enumerate(railside_quads["right_outer"][group_idx]):
                    processed_items += 1
                    print(f"\tProcessing outer right railside {processed_items} of {total_items}", end='\r')
                    distance_along_track_close = tsu.distance_along_nearest_trackcenter(top_close.point, trackcenter)
                    distance_along_track_far = tsu.distance_along_nearest_trackcenter(top_far.point, trackcenter)
                    rails_delta_texcoord = 2
                    u_value_close = float(distance_along_track_close * rails_delta_texcoord)
                    u_value_far = float(distance_along_track_far * rails_delta_texcoord)

                    # Updated values for existing vertices.
                    update_vertex_data.extend([
                        (bottom_close, 0.2268, 0.7694, u_value_close, -0.9808, -0.981249, -0.192746, 0.0),
                        (top_close, 0.325, 0.7895, u_value_close, -0.951, -0.981249, -0.192746, 0.0),
                        (top_far, 0.325, 0.7895, u_value_far, -0.951, -0.981249, -0.192746, 0.0),
                        (bottom_far, 0.2268, 0.7694, u_value_far, -0.9808, -0.981249, -0.192746, 0.0)
                    ])

                    # Insert new vertices and triangles from top to bottom of the new ATracks-like railside.
                    if idx == 0: # First quad of a railside, so also insert new vertices for the close side of the quad.
                        railbase_inner = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top1 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top2 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_bottom = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)

                        # Updated values for newly created vertices.
                        update_vertex_data.extend([
                            (railbase_inner, 0.2268, 0.7694, u_value_close, -0.975, -0.219822, 0.97554, 0.0),
                            (railbase_outer_top1, 0.215, 0.8285, u_value_close, -0.951, -0.219822, 0.97554, 0.0),
                            (railbase_outer_top2, 0.215, 0.8285, u_value_close, -0.951, -1.0, 0.0, 0.0),
                            (railbase_outer_bottom, 0.192, 0.8285, u_value_close, -0.975, -1.0, 0.0, 0.0)
                        ])
                        prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                    
                    # Add new vertices for the far side of the quad.
                    railbase_inner = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top1 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top2 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_bottom = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)

                    # Updated values for the created vertices.
                    update_vertex_data.extend([
                        (railbase_inner, 0.2268, 0.7694, u_value_far, -0.975, -0.219822, 0.97554, 0.0),
                        (railbase_outer_top1, 0.215, 0.8285, u_value_far, -0.951, -0.219822, 0.97554, 0.0),
                        (railbase_outer_top2, 0.215, 0.8285, u_value_far, -0.951, -1.0, 0.0, 0.0),
                        (railbase_outer_bottom, 0.192, 0.8285, u_value_far, -0.975, -1.0, 0.0, 0.0)
                    ])

                    # Specify new triangles from the new vertices to the previous set of vertices added for the railside.
                    prev_railbase_inner, prev_railbase_outer_top1, prev_railbase_outer_top2, prev_railbase_outer_bottom = prev_vertices
                    new_triangles.extend([
                        (railbase_inner, prev_railbase_inner, railbase_outer_top1),
                        (railbase_outer_top1, prev_railbase_inner, prev_railbase_outer_top1),
                        (railbase_outer_top1, prev_railbase_outer_top1, railbase_outer_top2),
                        (railbase_outer_top2, prev_railbase_outer_top1, prev_railbase_outer_top2),
                        (railbase_outer_top2, prev_railbase_outer_top2, railbase_outer_bottom),
                        (railbase_outer_bottom, prev_railbase_outer_top2, prev_railbase_outer_bottom),
                    ])
                    prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
            
            print("")

            # Inner right railside.
            total_items = sum(len(group) for group in railside_quads["right_inner"])
            processed_items = 0
            for group_idx in range(len(railside_vertices_top["right_inner"])):
                for idx, (bottom_close, top_close, top_far, bottom_far) in enumerate(railside_quads["right_inner"][group_idx]):
                    processed_items += 1
                    print(f"\tProcessing inner right railside {processed_items} of {total_items}", end='\r')
                    distance_along_track_close = tsu.distance_along_nearest_trackcenter(top_close.point, trackcenter)
                    distance_along_track_far = tsu.distance_along_nearest_trackcenter(top_far.point, trackcenter)
                    rails_delta_texcoord = 2
                    u_value_close = float(distance_along_track_close * rails_delta_texcoord)
                    u_value_far = float(distance_along_track_far * rails_delta_texcoord)

                    # Updated values for existing vertices.
                    update_vertex_data.extend([
                        (bottom_close, 0.2268, 0.7374, u_value_close, -0.9808, 0.981249, -0.192746, 0.0),
                        (top_close, 0.325, 0.7175, u_value_close, -0.951, 0.981249, -0.192746, 0.0),
                        (top_far, 0.325, 0.7175, u_value_far, -0.951, 0.981249, -0.192746, 0.0),
                        (bottom_far, 0.2268, 0.7374, u_value_far, -0.9808, 0.981249, -0.192746, 0.0)
                    ])

                    # Insert new vertices and triangles from top to bottom of the new ATracks-like railside.
                    if idx == 0: # First quad of the railside, so also insert new vertices for the close side of the quad.
                        railbase_inner = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top1 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top2 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_bottom = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)

                        # Updated values for newly created vertices.
                        update_vertex_data.extend([
                            (railbase_inner, 0.2268, 0.7374, u_value_close, -0.975, 0.219822, 0.97554, 0.0),
                            (railbase_outer_top1, 0.215, 0.6785, u_value_close, -0.951, 0.219822, 0.97554, 0.0),
                            (railbase_outer_top2, 0.215, 0.6785, u_value_close, -0.951, 1.0, 0.0, 0.0),
                            (railbase_outer_bottom, 0.192, 0.6785, u_value_close, -0.975, 1.0, 0.0, 0.0)
                        ])
                        prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                    
                    # Add new vertices for the far side of the quad.
                    railbase_inner = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top1 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top2 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_bottom = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)

                    # Updated values for the created vertices.
                    update_vertex_data.extend([
                        (railbase_inner, 0.2268, 0.7374, u_value_far, -0.975, 0.219822, 0.97554, 0.0),
                        (railbase_outer_top1, 0.215, 0.6785, u_value_far, -0.951, 0.219822, 0.97554, 0.0),
                        (railbase_outer_top2, 0.215, 0.6785, u_value_far, -0.951, 1.0, 0.0, 0.0),
                        (railbase_outer_bottom, 0.192, 0.6785, u_value_far, -0.975, 1.0, 0.0, 0.0)
                    ])

                    # Specify new triangles from the new vertices to the previous set of vertices added for the railside.
                    prev_railbase_inner, prev_railbase_outer_top1, prev_railbase_outer_top2, prev_railbase_outer_bottom = prev_vertices
                    new_triangles.extend([
                        (railbase_inner, railbase_outer_top1, prev_railbase_inner),
                        (railbase_outer_top1, prev_railbase_outer_top1, prev_railbase_inner),
                        (railbase_outer_top1, railbase_outer_top2, prev_railbase_outer_top1),
                        (railbase_outer_top2, prev_railbase_outer_top1, prev_railbase_outer_top2),
                        (railbase_outer_top2, railbase_outer_bottom, prev_railbase_outer_top2),
                        (railbase_outer_bottom, prev_railbase_outer_bottom, prev_railbase_outer_top2),
                    ])
                    prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                
            print("")

            # Inner left railside.
            total_items = sum(len(group) for group in railside_quads["left_inner"])
            processed_items = 0
            for group_idx in range(len(railside_vertices_top["left_inner"])):
                for idx, (bottom_close, top_close, top_far, bottom_far) in enumerate(railside_quads["left_inner"][group_idx]):
                    processed_items += 1
                    print(f"\tProcessing inner left railside {processed_items} of {total_items}", end='\r')
                    distance_along_track_close = tsu.distance_along_nearest_trackcenter(top_close.point, trackcenter)
                    distance_along_track_far = tsu.distance_along_nearest_trackcenter(top_far.point, trackcenter)
                    rails_delta_texcoord = 2
                    u_value_close = float(distance_along_track_close * rails_delta_texcoord)
                    u_value_far = float(distance_along_track_far * rails_delta_texcoord)

                    # Updated values for existing vertices.
                    update_vertex_data.extend([
                        (bottom_close, 0.2268, -0.7374, u_value_close, -0.9808, -0.981249, -0.192746, 0.0),
                        (top_close, 0.325, -0.7175, u_value_close, -0.951, -0.981249, -0.192746, 0.0),
                        (top_far, 0.325, -0.7175, u_value_far, -0.951, -0.981249, -0.192746, 0.0),
                        (bottom_far, 0.2268, -0.7374, u_value_far, -0.9808, -0.981249, -0.192746, 0.0)
                    ])
                    
                    # Insert new vertices and triangles from top to bottom of the new ATracks-like railside.
                    if idx == 0: # First quad of the railside, so also insert new vertices for the close side of the quad.
                        railbase_inner = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top1 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top2 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_bottom = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)

                        # Updated values for newly created vertices.
                        update_vertex_data.extend([
                            (railbase_inner, 0.2268, -0.7374, u_value_close, -0.975, -0.219822, 0.97554, 0.0),
                            (railbase_outer_top1, 0.215, -0.6785, u_value_close, -0.951, -0.219822, 0.97554, 0.0),
                            (railbase_outer_top2, 0.215, -0.6785, u_value_close, -0.951, -1.0, 0.0, 0.0),
                            (railbase_outer_bottom, 0.192, -0.6785, u_value_close, -0.975, -1.0, 0.0, 0.0)
                        ])
                        prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                    
                    # Add new vertices for the far side of the quad.
                    railbase_inner = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top1 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top2 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_bottom = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)

                    # Updated values for the created vertices.
                    update_vertex_data.extend([
                        (railbase_inner, 0.2268, -0.7374, u_value_far, -0.975, -0.219822, 0.97554, 0.0),
                        (railbase_outer_top1, 0.215, -0.6785, u_value_far, -0.951, -0.219822, 0.97554, 0.0),
                        (railbase_outer_top2, 0.215, -0.6785, u_value_far, -0.951, -1.0, 0.0, 0.0),
                        (railbase_outer_bottom, 0.192, -0.6785, u_value_far, -0.975, -1.0, 0.0, 0.0)
                    ])

                    # Specify new triangles from the new vertices to the previous set of vertices added for the railside.
                    prev_railbase_inner, prev_railbase_outer_top1, prev_railbase_outer_top2, prev_railbase_outer_bottom = prev_vertices
                    new_triangles.extend([
                        (railbase_inner, prev_railbase_inner, railbase_outer_top1),
                        (railbase_outer_top1, prev_railbase_inner, prev_railbase_outer_top1),
                        (railbase_outer_top1, prev_railbase_outer_top1, railbase_outer_top2),
                        (railbase_outer_top2, prev_railbase_outer_top1, prev_railbase_outer_top2),
                        (railbase_outer_top2, prev_railbase_outer_top2, railbase_outer_bottom),
                        (railbase_outer_bottom, prev_railbase_outer_top2, prev_railbase_outer_bottom),
                    ])
                    prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
            
            print("")

            # Outer left railside.
            total_items = sum(len(group) for group in railside_quads["left_outer"])
            processed_items = 0
            for group_idx in range(len(railside_vertices_top["left_outer"])):
                for idx, (bottom_close, top_close, top_far, bottom_far) in enumerate(railside_quads["left_outer"][group_idx]):
                    processed_items += 1
                    print(f"\tProcessing outer left railside {processed_items} of {total_items}", end='\r')
                    distance_along_track_close = tsu.distance_along_nearest_trackcenter(top_close.point, trackcenter)
                    distance_along_track_far = tsu.distance_along_nearest_trackcenter(top_far.point, trackcenter)
                    rails_delta_texcoord = 2
                    u_value_close = float(distance_along_track_close * rails_delta_texcoord)
                    u_value_far = float(distance_along_track_far * rails_delta_texcoord)

                    # Updated values for existing vertices.
                    update_vertex_data.extend([
                        (bottom_close, 0.2268, -0.7694, u_value_close, -0.9808, 0.981249, -0.192746, 0.0),
                        (top_close, 0.325, -0.7895, u_value_close, -0.951, 0.981249, -0.192746, 0.0),
                        (top_far, 0.325, -0.7895, u_value_far, -0.951, 0.981249, -0.192746, 0.0),
                        (bottom_far, 0.2268, -0.7694, u_value_far, -0.9808, 0.981249, -0.192746, 0.0)
                    ])

                    # Insert new vertices and triangles from top to bottom of the new ATracks-like railside.
                    if idx == 0: # First quad of the railside, so also insert new vertices for the close side of the quad.
                        railbase_inner = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top1 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top2 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_bottom = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_close.point, bottom_close.uv_point, bottom_close.normal)

                        # Updated values for newly created vertices.
                        update_vertex_data.extend([
                            (railbase_inner, 0.2268, -0.7694, u_value_close, -0.975, 0.219822, 0.97554, 0.0),
                            (railbase_outer_top1, 0.215, -0.8285, u_value_close, -0.951, 0.219822, 0.97554, 0.0),
                            (railbase_outer_top2, 0.215, -0.8285, u_value_close, -0.951, 1.0, 0.0, 0.0),
                            (railbase_outer_bottom, 0.192, -0.8285, u_value_close, -0.975, 1.0, 0.0, 0.0)
                        ])
                        prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                    
                    # Add new vertices for the far side of the quad.
                    railbase_inner = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top1 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top2 = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_bottom = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, railside_indexed_trilist, bottom_far.point, bottom_far.uv_point, bottom_far.normal)

                    # Updated values for the created vertices.
                    update_vertex_data.extend([
                        (railbase_inner, 0.2268, -0.7694, u_value_far, -0.975, 0.219822, 0.97554, 0.0),
                        (railbase_outer_top1, 0.215, -0.8285, u_value_far, -0.951, 0.219822, 0.97554, 0.0),
                        (railbase_outer_top2, 0.215, -0.8285, u_value_far, -0.951, 1.0, 0.0, 0.0),
                        (railbase_outer_bottom, 0.192, -0.8285, u_value_far, -0.975, 1.0, 0.0, 0.0)
                    ])

                    # Specify new triangles from the new vertices to the previous set of vertices added for the railside.
                    prev_railbase_inner, prev_railbase_outer_top1, prev_railbase_outer_top2, prev_railbase_outer_bottom = prev_vertices
                    new_triangles.extend([
                        (railbase_inner, railbase_outer_top1, prev_railbase_inner),
                        (railbase_outer_top1, prev_railbase_outer_top1, prev_railbase_inner),
                        (railbase_outer_top1, railbase_outer_top2, prev_railbase_outer_top1),
                        (railbase_outer_top2, prev_railbase_outer_top1, prev_railbase_outer_top2),
                        (railbase_outer_top2, railbase_outer_bottom, prev_railbase_outer_top2),
                        (railbase_outer_bottom, prev_railbase_outer_bottom, prev_railbase_outer_top2),
                    ])
                    prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
            
            print("")

            # Update the values of existing and created vertices.
            for idx, (vertex, new_height, new_center_distance, new_u_value, new_v_value, new_normal_vecx, new_normal_vecy, new_normal_vecz) in enumerate(update_vertex_data):
                print(f"\tUpdating vertex {idx + 1} of {len(update_vertex_data)}", end='\r')
                new_position = tsu.get_new_position_from_trackcenter(new_center_distance, vertex.point, trackcenter)
                vertex.point.x = new_position.x
                vertex.point.y = new_height
                vertex.point.z = new_position.z
                vertex.uv_point.u = new_u_value
                vertex.uv_point.v = new_v_value
                vertex.normal.vec_x = new_normal_vecx
                vertex.normal.vec_y = new_normal_vecy
                vertex.normal.vec_z = new_normal_vecz
                new_sfile.update_vertex(vertex)
            
            print("")

            # Insert new triangles between the created vertices.
            for idx, (vertex1, vertex2, vertex3) in enumerate(new_triangles):
                print(f"\tInserting triangle {idx + 1} of {len(new_triangles)}", end='\r')
                new_sfile.insert_triangle_between(railside_indexed_trilist, vertex1, vertex2, vertex3)

            print("")

        new_sfile.save()
        new_sfile.compress(ffeditc_path)

        # Process .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()