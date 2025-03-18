import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "./examples/data"
    shape_processed_path = "./examples/data/processed/NREmbAtracksRails"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = [
        "NR_Emb_a1t10mStrt.s",
        #"NR_Emb_a1t250r10d.s"
        ]
    ignore_shapes = ["*Tun*", "*Pnt*", "*Frog*"]
    
    os.makedirs(shape_processed_path, exist_ok=True)

    shape_names = tsu.find_directory_files(shape_load_path, match_shapes, ignore_shapes)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx} of {len(shape_names)}...")

        # Process .s file
        new_sfile_name = sfile_name.replace("NR_Emb", "NR_Emb_AT")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

        #trackcenter = tsu.generate_curve_centerpoints(curve_radius=250, curve_angle=-10, num_points=10000, start_angle=0, start_point=tsu.Point(0, 0, 0))
        trackcenter = tsu.generate_straight_centerpoints(length=10, num_points=1000, start_angle=0, start_point=tsu.Point(0, 0, 0))

        lod_dlevel = 400
        prim_state = new_sfile.get_prim_state_by_name("rail_side")
        vertices_in_prim_state = new_sfile.get_vertices_by_prim_state(lod_dlevel, prim_state)
        indexed_trilists = new_sfile.get_indexed_trilists_in_subobject(lod_dlevel, 0)
        railside_indexed_trilist = indexed_trilists[prim_state.idx][0]
        
        # Identify vertical edges of the rail sides.
        railside_bottom_vertices = []
        railside_top_vertices = []

        for vertex in vertices_in_prim_state:
            if vertex.point.y == 0.2:  # Railside bottom vertices
                connected_vertices = new_sfile.get_connected_vertices(prim_state, vertex)

                for connected_vertex in connected_vertices:
                    if connected_vertex.point.y == 0.325 and connected_vertex.point.z == vertex.point.z:  # Connected railside top vertices directly over the bottom ones
                        railside_bottom_vertices.append(vertex)
                        railside_top_vertices.append(connected_vertex)

        if railside_bottom_vertices:
            railside_bottom_vertices.sort(key=lambda v: v.point.x)
            railside_top_vertices.sort(key=lambda v: v.point.x)

        # Find rectangles between the vertical edges of the rail sides.
        railside_rectangles = []

        for i in range(len(railside_bottom_vertices) - 1):
            bottom_left = railside_bottom_vertices[i]
            bottom_right = railside_bottom_vertices[i + 1]
            top_left = railside_top_vertices[i]
            top_right = railside_top_vertices[i + 1]

            tolerance = 0.05
            if abs(bottom_left.point.x - bottom_right.point.x) < tolerance:
                if abs(bottom_left.point.z - bottom_right.point.z) > tolerance:
                    rectangle = (bottom_left, top_left, top_right, bottom_right)
                    railside_rectangles.append(rectangle)
        
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
        for r in railside_rectangles:
            print(r)

        # Modify the existing railside vertices to be the top rectangle of the new ATracks-like railside.
        last_vertices_right_outer = None
        last_vertices_right_inner = None
        last_vertices_left_inner = None
        last_vertices_left_outer = None

        for bottom_left, top_left, top_right, bottom_right in railside_rectangles:
            # left = vertices closer to track start
            # right = vertices further away from track start

            first_rectangle = bottom_left.point.z == 0
            closest_centerpoint = tsu.find_closest_centerpoint(top_left.point, trackcenter, plane="xz")
            distance_from_center = tsu.signed_distance_between(top_left.point, closest_centerpoint, plane="xz")
            distance_along_track_left = tsu.distance_along_straight_track(top_left.point, trackcenter)
            distance_along_track_right = tsu.distance_along_straight_track(top_right.point, trackcenter)
            rails_delta_texcoord = 2
            u_value_left = float(distance_along_track_left * rails_delta_texcoord)
            u_value_right = float(distance_along_track_right * rails_delta_texcoord)

            update_vertex_data = [] # Format: [(vertex, new_height, new_center_distance, new_u_value, new_v_value, new_normal_vecx, new_normal_vecy, new_normal_vecz), ...]
            new_triangles = [] # Format: [(vertex1, vertex2, vertex3), ...]

            # Different values depending on which railside it is.
            if 0.8175 <= distance_from_center <= 0.9175: # Outside right rail.
                update_vertex_data.extend([
                    (bottom_left, 0.2268, 0.7694, u_value_left, -0.9808, -0.981249, -0.192746, 0.0),
                    (top_left, 0.325, 0.7895, u_value_left, -0.951, -0.981249, -0.192746, 0.0),
                    (top_right, 0.325, 0.7895, u_value_right, -0.951, -0.981249, -0.192746, 0.0),
                    (bottom_right, 0.2268, 0.7694, u_value_right, -0.9808, -0.981249, -0.192746, 0.0)
                ])
            elif 0.6675 <= distance_from_center <= 0.7675: # Inside right rail.
                update_vertex_data.extend([
                    (bottom_left, 0.2268, 0.7374, u_value_left, -0.9808, 0.981249, -0.192746, 0.0),
                    (top_left, 0.325, 0.7175, u_value_left, -0.951, 0.981249, -0.192746, 0.0),
                    (top_right, 0.325, 0.7175, u_value_right, -0.951, 0.981249, -0.192746, 0.0),
                    (bottom_right, 0.2268, 0.7374, u_value_right, -0.9808, 0.981249, -0.192746, 0.0)
                ])
            elif -0.7675 <= distance_from_center <= -0.6675: # Inside left rail.
                update_vertex_data.extend([
                    (bottom_left, 0.2268, -0.7374, u_value_left, -0.9808, -0.981249, -0.192746, 0.0),
                    (top_left, 0.325, -0.7175, u_value_left, -0.951, -0.981249, -0.192746, 0.0),
                    (top_right, 0.325, -0.7175, u_value_right, -0.951, -0.981249, -0.192746, 0.0),
                    (bottom_right, 0.2268, -0.7374, u_value_right, -0.9808, -0.981249, -0.192746, 0.0)
                ])
            elif -0.9175 <= distance_from_center <= -0.8175: # Outside left rail.
                update_vertex_data.extend([
                    (bottom_left, 0.2268, -0.7694, u_value_left, -0.9808, 0.981249, -0.192746, 0.0),
                    (top_left, 0.325, -0.7895, u_value_left, -0.951, 0.981249, -0.192746, 0.0),
                    (top_right, 0.325, -0.7895, u_value_right, -0.951, 0.981249, -0.192746, 0.0),
                    (bottom_right, 0.2268, -0.7694, u_value_right, -0.9808, 0.981249, -0.192746, 0.0)
                ])

            # Insert new vertices and triangles from top to bottom of the new ATracks-like railside.
            if first_rectangle: # First rectangle of a railside, so also insert new vertices for the left side of the rectangle.
                railbase_inner = new_sfile.add_vertex_to_subobject(lod_dlevel, 0, bottom_left.point, bottom_left.uv_point, bottom_left.normal)
                railbase_outer_top1 = new_sfile.add_vertex_to_subobject(lod_dlevel, 0, bottom_left.point, bottom_left.uv_point, bottom_left.normal)
                railbase_outer_top2 = new_sfile.add_vertex_to_subobject(lod_dlevel, 0, bottom_left.point, bottom_left.uv_point, bottom_left.normal)
                railbase_outer_bottom = new_sfile.add_vertex_to_subobject(lod_dlevel, 0, bottom_left.point, bottom_left.uv_point, bottom_left.normal)

                # Different values depending on which railside it is.
                if 0.8175 <= distance_from_center <= 0.9175: # Outside right rail.
                    update_vertex_data.extend([
                        (railbase_inner, 0.2268, 0.7694, u_value_left, -0.975, -0.219822, 0.97554, 0.0),
                        (railbase_outer_top1, 0.215, 0.8285, u_value_left, -0.951, -0.219822, 0.97554, 0.0),
                        (railbase_outer_top2, 0.215, 0.8285, u_value_left, -0.951, -1.0, 0.0, 0.0),
                        (railbase_outer_bottom, 0.192, 0.8285, u_value_left, -0.975, -1.0, 0.0, 0.0)
                    ])
                    last_vertices_right_outer = (bottom_left, railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                elif 0.6675 <= distance_from_center <= 0.7675: # Inside right rail.
                    update_vertex_data.extend([
                        (railbase_inner, 0.2268, 0.7374, u_value_left, -0.975, 0.219822, 0.97554, 0.0),
                        (railbase_outer_top1, 0.215, 0.6785, u_value_left, -0.951, 0.219822, 0.97554, 0.0),
                        (railbase_outer_top2, 0.215, 0.6785, u_value_left, -0.951, 1.0, 0.0, 0.0),
                        (railbase_outer_bottom, 0.192, 0.6785, u_value_left, -0.975, 1.0, 0.0, 0.0)
                    ])
                    last_vertices_right_inner = (bottom_left, railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                elif -0.7675 <= distance_from_center <= -0.6675: # Inside left rail.
                    update_vertex_data.extend([
                        (railbase_inner, 0.2268, -0.7374, u_value_left, -0.975, -0.219822, 0.97554, 0.0),
                        (railbase_outer_top1, 0.215, -0.6785, u_value_left, -0.951, -0.219822, 0.97554, 0.0),
                        (railbase_outer_top2, 0.215, -0.6785, u_value_left, -0.951, -1.0, 0.0, 0.0),
                        (railbase_outer_bottom, 0.192, -0.6785, u_value_left, -0.975, -1.0, 0.0, 0.0)
                    ])
                    last_vertices_left_inner = (bottom_left, railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
                elif -0.9175 <= distance_from_center <= -0.8175: # Outside left rail.
                    update_vertex_data.extend([
                        (railbase_inner, 0.2268, -0.7694, u_value_left, -0.975, 0.219822, 0.97554, 0.0),
                        (railbase_outer_top1, 0.215, -0.8285, u_value_left, -0.951, 0.219822, 0.97554, 0.0),
                        (railbase_outer_top2, 0.215, -0.8285, u_value_left, -0.951, 1.0, 0.0, 0.0),
                        (railbase_outer_bottom, 0.192, -0.8285, u_value_left, -0.975, 1.0, 0.0, 0.0)
                    ])
                    last_vertices_left_outer = (bottom_left, railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
            
            # Right side of the rectangle.
            railbase_inner = new_sfile.add_vertex_to_subobject(lod_dlevel, 0, bottom_right.point, bottom_right.uv_point, bottom_right.normal)
            railbase_outer_top1 = new_sfile.add_vertex_to_subobject(lod_dlevel, 0, bottom_right.point, bottom_right.uv_point, bottom_right.normal)
            railbase_outer_top2 = new_sfile.add_vertex_to_subobject(lod_dlevel, 0, bottom_right.point, bottom_right.uv_point, bottom_right.normal)
            railbase_outer_bottom = new_sfile.add_vertex_to_subobject(lod_dlevel, 0, bottom_right.point, bottom_right.uv_point, bottom_right.normal)

            # Different values and triangle ordering depending on which railside it is.
            # Also specify new triangles from the new vertices to the latest set of vertices added for the railside.
            if 0.8175 <= distance_from_center <= 0.9175: # Outside right rail.
                update_vertex_data.extend([
                    (railbase_inner, 0.2268, 0.7694, u_value_right, -0.975, -0.219822, 0.97554, 0.0),
                    (railbase_outer_top1, 0.215, 0.8285, u_value_right, -0.951, -0.219822, 0.97554, 0.0),
                    (railbase_outer_top2, 0.215, 0.8285, u_value_right, -0.951, -1.0, 0.0, 0.0),
                    (railbase_outer_bottom, 0.192, 0.8285, u_value_right, -0.975, -1.0, 0.0, 0.0)
                ])
                last_bottom_right, last_railbase_inner, last_railbase_outer_top1, last_railbase_outer_top2, last_railbase_outer_bottom = last_vertices_right_outer
                new_triangles.extend([
                    (bottom_right, last_bottom_right, railbase_inner),
                    (railbase_inner, last_bottom_right, last_railbase_inner),
                    (railbase_inner, last_railbase_inner, railbase_outer_top1),
                    (railbase_outer_top1, last_railbase_inner, last_railbase_outer_top1),
                    (railbase_outer_top1, last_railbase_outer_top1, railbase_outer_top2),
                    (railbase_outer_top2, last_railbase_outer_top1, last_railbase_outer_top2),
                    (railbase_outer_top2, last_railbase_outer_top2, railbase_outer_bottom),
                    (railbase_outer_bottom, last_railbase_outer_top2, last_railbase_outer_bottom),
                ])
                last_vertices_right_outer = (bottom_right, railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
            elif 0.6675 <= distance_from_center <= 0.7675: # Inside right rail.
                update_vertex_data.extend([
                    (railbase_inner, 0.2268, 0.7374, u_value_right, -0.975, 0.219822, 0.97554, 0.0),
                    (railbase_outer_top1, 0.215, 0.6785, u_value_right, -0.951, 0.219822, 0.97554, 0.0),
                    (railbase_outer_top2, 0.215, 0.6785, u_value_right, -0.951, 1.0, 0.0, 0.0),
                    (railbase_outer_bottom, 0.192, 0.6785, u_value_right, -0.975, 1.0, 0.0, 0.0)
                ])
                last_bottom_right, last_railbase_inner, last_railbase_outer_top1, last_railbase_outer_top2, last_railbase_outer_bottom = last_vertices_right_inner
                new_triangles.extend([
                    (bottom_right, railbase_inner, last_bottom_right),
                    (railbase_inner, last_railbase_inner, last_bottom_right),
                    (railbase_inner, railbase_outer_top1, last_railbase_inner),
                    (railbase_outer_top1, last_railbase_outer_top1, last_railbase_inner),
                    (railbase_outer_top1, railbase_outer_top2, last_railbase_outer_top1),
                    (railbase_outer_top2, last_railbase_outer_top1, last_railbase_outer_top2),
                    (railbase_outer_top2, railbase_outer_bottom, last_railbase_outer_top2),
                    (railbase_outer_bottom, last_railbase_outer_bottom, last_railbase_outer_top2),
                ])
                last_vertices_right_inner = (bottom_right, railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
            elif -0.7675 <= distance_from_center <= -0.6675: # Inside left rail.
                update_vertex_data.extend([
                    (railbase_inner, 0.2268, -0.7374, u_value_right, -0.975, -0.219822, 0.97554, 0.0),
                    (railbase_outer_top1, 0.215, -0.6785, u_value_right, -0.951, -0.219822, 0.97554, 0.0),
                    (railbase_outer_top2, 0.215, -0.6785, u_value_right, -0.951, -1.0, 0.0, 0.0),
                    (railbase_outer_bottom, 0.192, -0.6785, u_value_right, -0.975, -1.0, 0.0, 0.0)
                ])
                last_bottom_right, last_railbase_inner, last_railbase_outer_top1, last_railbase_outer_top2, last_railbase_outer_bottom = last_vertices_left_inner
                new_triangles.extend([
                    (bottom_right, last_bottom_right, railbase_inner),
                    (railbase_inner, last_bottom_right, last_railbase_inner),
                    (railbase_inner, last_railbase_inner, railbase_outer_top1),
                    (railbase_outer_top1, last_railbase_inner, last_railbase_outer_top1),
                    (railbase_outer_top1, last_railbase_outer_top1, railbase_outer_top2),
                    (railbase_outer_top2, last_railbase_outer_top1, last_railbase_outer_top2),
                    (railbase_outer_top2, last_railbase_outer_top2, railbase_outer_bottom),
                    (railbase_outer_bottom, last_railbase_outer_top2, last_railbase_outer_bottom),
                ])
                last_vertices_left_inner = (bottom_right, railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
            elif -0.9175 <= distance_from_center <= -0.8175: # Outside left rail.
                update_vertex_data.extend([
                    (railbase_inner, 0.2268, -0.7694, u_value_right, -0.975, 0.219822, 0.97554, 0.0),
                    (railbase_outer_top1, 0.215, -0.8285, u_value_right, -0.951, 0.219822, 0.97554, 0.0),
                    (railbase_outer_top2, 0.215, -0.8285, u_value_right, -0.951, 1.0, 0.0, 0.0),
                    (railbase_outer_bottom, 0.192, -0.8285, u_value_right, -0.975, 1.0, 0.0, 0.0)
                ])
                last_bottom_right, last_railbase_inner, last_railbase_outer_top1, last_railbase_outer_top2, last_railbase_outer_bottom = last_vertices_left_outer
                new_triangles.extend([
                    (bottom_right, railbase_inner, last_bottom_right),
                    (railbase_inner, last_railbase_inner, last_bottom_right),
                    (railbase_inner, railbase_outer_top1, last_railbase_inner),
                    (railbase_outer_top1, last_railbase_outer_top1, last_railbase_inner),
                    (railbase_outer_top1, railbase_outer_top2, last_railbase_outer_top1),
                    (railbase_outer_top2, last_railbase_outer_top1, last_railbase_outer_top2),
                    (railbase_outer_top2, railbase_outer_bottom, last_railbase_outer_top2),
                    (railbase_outer_bottom, last_railbase_outer_bottom, last_railbase_outer_top2),
                ])
                last_vertices_left_outer = (bottom_right, railbase_inner, railbase_outer_top1, railbase_outer_top2, railbase_outer_bottom)
            
            # Update the created vertices.
            for vertex, new_height, new_center_distance, new_u_value, new_v_value, new_normal_vecx, new_normal_vecy, new_normal_vecz in update_vertex_data:
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
            
            # Insert new triangles between the created vertices.
            for vertex1, vertex2, vertex3 in new_triangles:
                new_sfile.insert_triangle_between(railside_indexed_trilist, vertex1, vertex2, vertex3)

        new_sfile.save()
        #new_sfile.compress(ffeditc_path)

        # Process .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()