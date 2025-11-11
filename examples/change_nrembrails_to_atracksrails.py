import os
import pyffeditc
import shapeio
import trackshapeutils as tsu
from shapeio.shape import Point, UVPoint, Vector
from shapeedit import ShapeEditor
from shapeedit.utils import grouping
from collections import defaultdict

if __name__ == "__main__":
    ffeditc_path = "./ffeditc_unicode.exe"
    load_path = "./examples/data/"
    processed_path = "./examples/data/processed/NREmbAtracksRails"
    match_files = [
        # For testing
        #"NR_Emb_a1t10mStrt.s",
        #"NR_Emb_a1t250r10d.s",
        #"NR_Emb_a2t1000r1d.s",
        #"NR_Emb_a3t1000r1d.s",
        #"NR_Emb_a4t1000r1d.s",
        #"NR_EmbBase_a1t10mStrt.s",
        #"NR_Ramp_a1t10mStrt.s",
        #"NR_RWall_a1t10mStrt_lft.s",
        #"NR_WallEmb_a1t10mStrt_lft.s",
        #"NR_Emb_a1t2000r20d.s",

        # All of the shapes
        "NR_Emb_*.s",
        "NR_EmbBase_*.s",
        "NR_Ramp_*.s",
        "NR_RWall_*.s",
        "NR_WallEmb_*.s",
    ]
    ignore_files = ["*.sd"]
    
    os.makedirs(processed_path, exist_ok=True)

    shape_names = shapeio.find_directory_files(load_path, match_files, ignore_files)

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

        shape_path = f"{load_path}/{sfile_name}"
        new_shape_path = f"{processed_path}/{new_sfile_name}"

        shapeio.copy(shape_path, new_shape_path)

        pyffeditc.decompress(ffeditc_path, new_shape_path)
        trackshape = shapeio.load(new_shape_path)

        trackshape_editor = ShapeEditor(trackshape)
        sub_object = trackshape_editor.lod_control(0).distance_level(400).sub_object(0)

        trackcenters = tsu.trackcenters_from_global_tsection(shape_name=tsection_sfile_name, num_points_per_meter=12)

        for primitive in sub_object.primitives(prim_state_name="rail_side"):
            print(f"\tPrim State Idx: {primitive.index}")
            vertices_in_primitive = primitive.vertices()
            vertices_in_subobject = sub_object.vertices()
            
            # First find the vertices to work on.
            # The naming right/left refers to which side of the track it is relative to the track center.
            # The naming close/far refers to distance from the start of the track.
            print(f"\tFinding railside and railtop vertices")
            railtop_vertices_outer = []
            railtop_vertices_inner = []
            railside_vertices_top = defaultdict(list)
            railside_vertices_bottom = defaultdict(list)

            for vertex in vertices_in_primitive:
                is_horizontal = (vertex.normal.x, vertex.normal.y, vertex.normal.z) == (0.0, 1.0, 0.0)
                if vertex.point.y == 0.325 and is_horizontal: # Railtop vertices
                    closest_trackcenter = tsu.find_closest_trackcenter(vertex.point, trackcenters, plane="xz")
                    closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, closest_trackcenter, plane="xz")
                    distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")
                    
                    if 0.7975 <= distance_from_center <= 0.9375 or -0.9375 <= distance_from_center <= -0.7975: # Outer railtop.
                        if not any(v.point == vertex.point for v in railtop_vertices_outer):
                            railtop_vertices_outer.append(vertex)

                    elif 0.6475 <= distance_from_center <= 0.7875 or -0.7875 <= distance_from_center <= -0.6475: # Inner railtop.
                        if not any(v.point == vertex.point for v in railtop_vertices_inner):
                            railtop_vertices_inner.append(vertex)
                    else:
                        with open('warnings.txt', 'a') as f:
                            f.write(f'Railtops: {sfile_name} (distance_from_center = {distance_from_center})\n')

            for vertex in vertices_in_primitive:
                if vertex.point.y == 0.2: # Railside bottom vertices
                    connected_vertices = primitive.connected_vertices(vertex)

                    for connected_vertex in connected_vertices:
                        if connected_vertex.point.y == 0.325 and connected_vertex.point.z == vertex.point.z: # Connected railside top vertices directly over the bottom ones
                            closest_trackcenter = tsu.find_closest_trackcenter(vertex.point, trackcenters, plane="xz")
                            closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, closest_trackcenter, plane="xz")
                            distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")

                            if 0.7975 <= distance_from_center <= 0.9375: # Outer right railside.
                                if not any(v.point == connected_vertex.point for v in railside_vertices_top["right_outer"]):
                                    railside_vertices_top["right_outer"].append(connected_vertex)
                                if not any(v.point == vertex.point for v in railside_vertices_bottom["right_outer"]):
                                    railside_vertices_bottom["right_outer"].append(vertex)

                            elif 0.6475 <= distance_from_center <= 0.7875: # Inner right railside.
                                if not any(v.point == connected_vertex.point for v in railside_vertices_top["right_inner"]):
                                    railside_vertices_top["right_inner"].append(connected_vertex)
                                if not any(v.point == vertex.point for v in railside_vertices_bottom["right_inner"]):
                                    railside_vertices_bottom["right_inner"].append(vertex)

                            elif -0.7875 <= distance_from_center <= -0.6475: # Inner left railside.
                                if not any(v.point == connected_vertex.point for v in railside_vertices_top["left_inner"]):
                                    railside_vertices_top["left_inner"].append(connected_vertex)
                                if not any(v.point == vertex.point for v in railside_vertices_bottom["left_inner"]):
                                    railside_vertices_bottom["left_inner"].append(vertex)

                            elif -0.9375 <= distance_from_center <= -0.7975: # Outer left railside.
                                if not any(v.point == connected_vertex.point for v in railside_vertices_top["left_outer"]):
                                    railside_vertices_top["left_outer"].append(connected_vertex)
                                if not any(v.point == vertex.point for v in railside_vertices_bottom["left_outer"]):
                                    railside_vertices_bottom["left_outer"].append(vertex)
                            else:
                                with open('warnings.txt', 'a') as f:
                                    f.write(f'Railsides: {sfile_name} (distance_from_center = {distance_from_center})\n')
            
            trackcenters = tsu.trackcenters_from_global_tsection(shape_name=tsection_sfile_name, num_points_per_meter=2)
            
            print(f"\tSorting railside vertices")
            distances = {}

            for side in railside_vertices_top:
                for v_top, v_bottom in zip(railside_vertices_top[side], railside_vertices_bottom[side]):
                    closest_trackcenter = tsu.find_closest_trackcenter(v_top.point, trackcenters, plane="xz")
                    distance = tsu.distance_along_trackcenter(v_top.point, closest_trackcenter, max_neighbor_dist=0.6)
                    distances[v_top.index] = distance
                    distances[v_bottom.index] = distance

            for side in railside_vertices_top:
                railside_vertices_top[side].sort(key=lambda v: distances[v.index])

            for side in railside_vertices_bottom:
                railside_vertices_bottom[side].sort(key=lambda v: distances[v.index])
            
            print(f"\tGrouping railside vertices")
            trackcenter_idxs = {}

            for side in railside_vertices_top:
                for v_top, v_bottom in zip(railside_vertices_top[side], railside_vertices_bottom[side]):
                    closest_trackcenter = tsu.find_closest_trackcenter(v_top.point, trackcenters, plane="xz")
                    trackcenter_idx = trackcenters.index(closest_trackcenter)
                    trackcenter_idxs[v_top.index] = trackcenter_idx
                    trackcenter_idxs[v_bottom.index] = trackcenter_idx

            parallel_tracks = lambda v1, v2: trackcenter_idxs[v1.index] == trackcenter_idxs[v2.index]

            for side in railside_vertices_top:
                railside_vertices_top[side] = grouping.group_items_by(railside_vertices_top[side], parallel_tracks)
            
            for side in railside_vertices_bottom:
                railside_vertices_bottom[side] = grouping.group_items_by(railside_vertices_bottom[side], parallel_tracks)

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

            trackcenters = tsu.trackcenters_from_global_tsection(shape_name=tsection_sfile_name, num_points_per_meter=7)

            # Creation of ATracks-like rail sides and rail tops.
            # New vertices are added, and at the end their values are changed according to the contents of 'update_vertex_data'.
            # New triangles are added according to the contents of 'new_triangles'. The order of vertices in each 'new_triangles' list item determines direction of the face.
            update_vertex_data = [] # Format: [(vertex, new_height, new_center_distance, new_u_value, new_v_value, new_normal_x, new_normal_y, new_normal_z), ...]
            new_triangles = [] # Format: [(vertex1, vertex2, vertex3), ...]
            prev_vertices = None

            # Outer railtops.
            for idx, vertex in enumerate(railtop_vertices_outer):
                print(f"\tProcessing outer railtop {idx + 1} of {len(railtop_vertices_outer)}", end='\r')
                closest_trackcenter = tsu.find_closest_trackcenter(vertex.point, trackcenters, plane="xz")
                closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, closest_trackcenter, plane="xz")
                distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")
                distance_along_track = tsu.distance_along_trackcenter(vertex.point, closest_trackcenter)
                rails_delta_texcoord = 2
                u_value = float(distance_along_track * rails_delta_texcoord)

                # Updated values for existing vertices.
                update_vertex_data.extend([
                    (vertex, vertex.point.y, distance_from_center, u_value, -0.77, vertex.normal.x, vertex.normal.y, vertex.normal.z)
                ])

            print("")

            # Inner railtops.
            for idx, vertex in enumerate(railtop_vertices_inner):
                print(f"\tProcessing inner railtop {idx + 1} of {len(railtop_vertices_inner)}", end='\r')
                closest_trackcenter = tsu.find_closest_trackcenter(vertex.point, trackcenters, plane="xz")
                closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, closest_trackcenter, plane="xz")
                distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")
                distance_along_track = tsu.distance_along_trackcenter(vertex.point, closest_trackcenter)
                rails_delta_texcoord = 2
                u_value = float(distance_along_track * rails_delta_texcoord)

                # Updated values for existing vertices.
                update_vertex_data.extend([
                    (vertex, vertex.point.y, distance_from_center, u_value, -0.875, vertex.normal.x, vertex.normal.y, vertex.normal.z)
                ])

            print("")
            
            # Outer right railside.
            total_items = sum(len(group) for group in railside_quads["right_outer"])
            processed_items = 0
            for group_idx in range(len(railside_quads["right_outer"])):
                for idx, (bottom_close, top_close, top_far, bottom_far) in enumerate(railside_quads["right_outer"][group_idx]):
                    processed_items += 1
                    print(f"\tProcessing outer right railside {processed_items} of {total_items}", end='\r')
                    closest_trackcenter = tsu.find_closest_trackcenter(top_close.point, trackcenters, plane="xz")
                    distance_along_track_close = tsu.distance_along_trackcenter(top_close.point, closest_trackcenter)
                    distance_along_track_far = tsu.distance_along_trackcenter(top_far.point, closest_trackcenter)
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
                        railbase_inner = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top1 = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top2 = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_bottom = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)

                        # Updated values for newly created vertices.
                        update_vertex_data.extend([
                            (railbase_inner, 0.2268, 0.7694, u_value_close, -0.975, -0.219822, 0.97554, 0.0),
                            (railbase_outer_top1, 0.215, 0.8285, u_value_close, -0.951, -0.219822, 0.97554, 0.0),
                            (railbase_outer_top2, 0.215, 0.8285, u_value_close, -0.951, -1.0, 0.0, 0.0),
                            (railbase_outer_bottom, 0.192, 0.8285, u_value_close, -0.975, -1.0, 0.0, 0.0)
                        ])
                        prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                    
                    # Add new vertices for the far side of the quad.
                    railbase_inner = primitive.add_vertex( bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top1 = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top2 = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_bottom = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)

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
            for group_idx in range(len(railside_quads["right_inner"])):
                for idx, (bottom_close, top_close, top_far, bottom_far) in enumerate(railside_quads["right_inner"][group_idx]):
                    processed_items += 1
                    print(f"\tProcessing inner right railside {processed_items} of {total_items}", end='\r')
                    closest_trackcenter = tsu.find_closest_trackcenter(top_close.point, trackcenters, plane="xz")
                    distance_along_track_close = tsu.distance_along_trackcenter(top_close.point, closest_trackcenter)
                    distance_along_track_far = tsu.distance_along_trackcenter(top_far.point, closest_trackcenter)
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
                        railbase_inner = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top1 = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top2 = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_bottom = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)

                        # Updated values for newly created vertices.
                        update_vertex_data.extend([
                            (railbase_inner, 0.2268, 0.7374, u_value_close, -0.975, 0.219822, 0.97554, 0.0),
                            (railbase_outer_top1, 0.215, 0.6785, u_value_close, -0.951, 0.219822, 0.97554, 0.0),
                            (railbase_outer_top2, 0.215, 0.6785, u_value_close, -0.951, 1.0, 0.0, 0.0),
                            (railbase_outer_bottom, 0.192, 0.6785, u_value_close, -0.975, 1.0, 0.0, 0.0)
                        ])
                        prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                    
                    # Add new vertices for the far side of the quad.
                    railbase_inner = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top1 = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top2 = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_bottom = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)

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
            for group_idx in range(len(railside_quads["left_inner"])):
                for idx, (bottom_close, top_close, top_far, bottom_far) in enumerate(railside_quads["left_inner"][group_idx]):
                    processed_items += 1
                    print(f"\tProcessing inner left railside {processed_items} of {total_items}", end='\r')
                    closest_trackcenter = tsu.find_closest_trackcenter(top_close.point, trackcenters, plane="xz")
                    distance_along_track_close = tsu.distance_along_trackcenter(top_close.point, closest_trackcenter)
                    distance_along_track_far = tsu.distance_along_trackcenter(top_far.point, closest_trackcenter)
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
                        railbase_inner = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top1 = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top2 = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_bottom = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)

                        # Updated values for newly created vertices.
                        update_vertex_data.extend([
                            (railbase_inner, 0.2268, -0.7374, u_value_close, -0.975, -0.219822, 0.97554, 0.0),
                            (railbase_outer_top1, 0.215, -0.6785, u_value_close, -0.951, -0.219822, 0.97554, 0.0),
                            (railbase_outer_top2, 0.215, -0.6785, u_value_close, -0.951, -1.0, 0.0, 0.0),
                            (railbase_outer_bottom, 0.192, -0.6785, u_value_close, -0.975, -1.0, 0.0, 0.0)
                        ])
                        prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                    
                    # Add new vertices for the far side of the quad.
                    railbase_inner = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top1 = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top2 = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_bottom = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)

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
            for group_idx in range(len(railside_quads["left_outer"])):
                for idx, (bottom_close, top_close, top_far, bottom_far) in enumerate(railside_quads["left_outer"][group_idx]):
                    processed_items += 1
                    print(f"\tProcessing outer left railside {processed_items} of {total_items}", end='\r')
                    closest_trackcenter = tsu.find_closest_trackcenter(top_close.point, trackcenters, plane="xz")
                    distance_along_track_close = tsu.distance_along_trackcenter(top_close.point, closest_trackcenter)
                    distance_along_track_far = tsu.distance_along_trackcenter(top_far.point, closest_trackcenter)
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
                        railbase_inner = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top1 = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_top2 = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)
                        railbase_outer_bottom = primitive.add_vertex(bottom_close.point, bottom_close.uv_point, bottom_close.normal)

                        # Updated values for newly created vertices.
                        update_vertex_data.extend([
                            (railbase_inner, 0.2268, -0.7694, u_value_close, -0.975, 0.219822, 0.97554, 0.0),
                            (railbase_outer_top1, 0.215, -0.8285, u_value_close, -0.951, 0.219822, 0.97554, 0.0),
                            (railbase_outer_top2, 0.215, -0.8285, u_value_close, -0.951, 1.0, 0.0, 0.0),
                            (railbase_outer_bottom, 0.192, -0.8285, u_value_close, -0.975, 1.0, 0.0, 0.0)
                        ])
                        prev_vertices = (railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                    
                    # Add new vertices for the far side of the quad.
                    railbase_inner = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top1 = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_top2 = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)
                    railbase_outer_bottom = primitive.add_vertex(bottom_far.point, bottom_far.uv_point, bottom_far.normal)

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
            for idx, (vertex, new_height, new_center_distance, new_u_value, new_v_value, new_normal_x, new_normal_y, new_normal_z) in enumerate(update_vertex_data):
                print(f"\tUpdating vertex {idx + 1} of {len(update_vertex_data)}", end='\r')
                closest_trackcenter = tsu.find_closest_trackcenter(vertex.point, trackcenters, plane="xz")
                new_position = tsu.get_new_position_from_trackcenter(new_center_distance, vertex.point, closest_trackcenter)
                vertex.point.x = new_position.x
                vertex.point.y = new_height
                vertex.point.z = new_position.z
                vertex.uv_point.u = new_u_value
                vertex.uv_point.v = new_v_value
                vertex.normal.x = new_normal_x
                vertex.normal.y = new_normal_y
                vertex.normal.z = new_normal_z
            
            print("")

            # Insert new triangles between the created vertices.
            for idx, (vertex1, vertex2, vertex3) in enumerate(new_triangles):
                print(f"\tInserting triangle {idx + 1} of {len(new_triangles)}", end='\r')
                primitive.insert_triangle(vertex1, vertex2, vertex3)

            print("")

        shapeio.dump(trackshape, new_shape_path)
        pyffeditc.compress(ffeditc_path, new_shape_path)

        # Process .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile_path = f"{load_path}/{sdfile_name}"
        new_sdfile_path = f"{processed_path}/{new_sdfile_name}"

        shapeio.copy(sdfile_path, new_sdfile_path)
        shapeio.replace_ignorecase(new_sdfile_path, sfile_name, new_sfile_name)
