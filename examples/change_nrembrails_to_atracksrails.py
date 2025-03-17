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
        new_sfile_name = sfile_name.replace(".s", "_AT.s")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

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

        #trackcenter = tsu.generate_curve_centerpoints(curve_radius=250, curve_angle=-10, num_points=10000, start_angle=0, start_point=tsu.Point(0, 0, 0))
        trackcenter = tsu.generate_straight_centerpoints(length=10, num_points=1000, start_angle=0, start_point=tsu.Point(0, 0, 0))

        lod_dlevel = 400
        prim_state = new_sfile.get_prim_state_by_name("rail_side")
        vertices_in_prim_state = new_sfile.get_vertices_by_prim_state(lod_dlevel, prim_state)
        
        railhead_vertex_pairs = []

        # Find railhead vertex pairs to modify.
        for vertex in vertices_in_prim_state:
            if vertex.point.y == 0.2: # Railhead bottom vertices
                connected_vertices = new_sfile.get_connected_vertices(prim_state, vertex)

                for connected_vertex in connected_vertices:
                    if connected_vertex.point.y == 0.325 and connected_vertex.point.z == vertex.point.z: # Connected railhead top vertices directly over the bottom ones
                        closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, trackcenter, plane="xz")
                        distance_from_center = tsu.signed_distance_from_centerpoint(vertex.point, closest_centerpoint, plane="xz")

                        railside_bottom_vertex = vertex
                        railside_top_vertex = connected_vertex

                        railhead_vertex_pairs.append(tuple([distance_from_center, railside_bottom_vertex, railside_top_vertex]))

        # Modify each railside vertex pair, add extra vertices between them and also set positions of the extra vertices.
        for distance_from_center, railside_bottom_vertex, railside_top_vertex in railhead_vertex_pairs:

            # Modify positions of the two existing railside vertices to be the two endpoints of the new ATracks-like railside.
            if 0.8175 <= distance_from_center <= 0.9175: # Outside right rail.
                # Set bottom railside vertex to outermost railbase ATracks position.
                new_position = tsu.get_new_position_from_trackcenter(0.8285, railside_bottom_vertex.point, trackcenter)
                railside_bottom_vertex.point.x = new_position.x # Set recalculated x
                railside_bottom_vertex.point.y = 0.192 # Set height
                railside_bottom_vertex.point.z = new_position.z # Set recalculated z
                # TODO Modify UVPoint, recalc normal
                new_sfile.update_vertex(railside_bottom_vertex)

                # Set top railside vertex to outermost railtop ATracks position.
                new_position = tsu.get_new_position_from_trackcenter(0.7895, railside_top_vertex.point, trackcenter)
                railside_top_vertex.point.x = new_position.x # Set recalculated x
                railside_top_vertex.point.y = 0.325 # Set height
                railside_top_vertex.point.z = new_position.z # Set recalculated z
                # TODO Modify UVPoint, recalc normal
                new_sfile.update_vertex(railside_top_vertex)

            elif 0.6675 <= distance_from_center <= 0.7675: # Inside right rail.
                # Set bottom railside vertex to innermost railbase ATracks position.
                new_position = tsu.get_new_position_from_trackcenter(0.6785, railside_bottom_vertex.point, trackcenter)
                railside_bottom_vertex.point.x = new_position.x # Set recalculated x
                railside_bottom_vertex.point.y = 0.192 # Set height
                railside_bottom_vertex.point.z = new_position.z # Set recalculated z
                # TODO Modify UVPoint, recalc normal
                new_sfile.update_vertex(railside_bottom_vertex)

                # Set top railside vertex to innermost railtop ATracks position.
                new_position = tsu.get_new_position_from_trackcenter(0.7175, railside_top_vertex.point, trackcenter)
                railside_top_vertex.point.x = new_position.x # Set recalculated x
                railside_top_vertex.point.y = 0.325 # Set height
                railside_top_vertex.point.z = new_position.z # Set recalculated z
                # TODO Modify UVPoint, recalc normal
                new_sfile.update_vertex(railside_top_vertex)

            elif -0.7675 <= distance_from_center <= -0.6675: # Inside right rail.
                # Set bottom railside vertex to innermost railbase ATracks position.
                new_position = tsu.get_new_position_from_trackcenter(-0.6785, railside_bottom_vertex.point, trackcenter)
                railside_bottom_vertex.point.x = new_position.x # Set recalculated x
                railside_bottom_vertex.point.y = 0.192 # Set height
                railside_bottom_vertex.point.z = new_position.z # Set recalculated z
                # TODO Modify UVPoint, recalc normal
                new_sfile.update_vertex(railside_bottom_vertex)

                # Set top railside vertex to innermost railtop ATracks position.
                new_position = tsu.get_new_position_from_trackcenter(-0.7175, railside_top_vertex.point, trackcenter)
                railside_top_vertex.point.x = new_position.x # Set recalculated x
                railside_top_vertex.point.y = 0.325 # Set height
                railside_top_vertex.point.z = new_position.z # Set recalculated z
                # TODO Modify UVPoint, recalc normal
                new_sfile.update_vertex(railside_top_vertex)

            elif -0.9175 <= distance_from_center <= -0.8175: # Outside left rail.
                # Set bottom railside vertex to outermost railbase ATracks position.
                new_position = tsu.get_new_position_from_trackcenter(-0.8285, railside_bottom_vertex.point, trackcenter)
                railside_bottom_vertex.point.x = new_position.x # Set recalculated x
                railside_bottom_vertex.point.y = 0.192 # Set height
                railside_bottom_vertex.point.z = new_position.z # Set recalculated z
                # TODO Modify UVPoint, recalc normal
                new_sfile.update_vertex(railside_bottom_vertex)

                # Set top railside vertex to outermost railtop ATracks position.
                new_position = tsu.get_new_position_from_trackcenter(-0.7895, railside_top_vertex.point, trackcenter)
                railside_top_vertex.point.x = new_position.x # Set recalculated x
                railside_top_vertex.point.y = 0.325 # Set height
                railside_top_vertex.point.z = new_position.z # Set recalculated z
                # TODO Modify UVPoint, recalc normal
                new_sfile.update_vertex(railside_top_vertex)


            # Insert new vertices between the railside endpoints from bottom to top.
            # Two at each position to be able to set the UVPoints properly.
            railbase_top_outer_vertex1 = new_sfile.insert_vertex_between(prim_state, railside_bottom_vertex, railside_top_vertex)
            railbase_top_outer_vertex2 = new_sfile.insert_vertex_between(prim_state, railbase_top_outer_vertex1, railside_top_vertex)
            railbase_top_inner_vertex1 = new_sfile.insert_vertex_between(prim_state, railbase_top_outer_vertex2, railside_top_vertex)
            railbase_top_inner_vertex2 = new_sfile.insert_vertex_between(prim_state, railbase_top_inner_vertex1, railside_top_vertex)

            # Adjust positions of the inserted vertices.
            if 0.8175 <= distance_from_center <= 0.9175: # Outside right rail.
                # Set position of outer top railbase vertices.
                new_position = tsu.get_new_position_from_trackcenter(0.8285, railbase_top_outer_vertex1.point, trackcenter)
                railbase_top_outer_vertex1.point.x = new_position.x # Set recalculated x
                railbase_top_outer_vertex2.point.x = new_position.x # Set recalculated x
                railbase_top_outer_vertex1.point.y = 0.215 # Set height
                railbase_top_outer_vertex2.point.y = 0.215 # Set height
                railbase_top_outer_vertex1.point.z = new_position.z # Set recalculated z
                railbase_top_outer_vertex2.point.z = new_position.z # Set recalculated z
                #railbase_top_outer_vertex1.normal.x = 1
                #railbase_top_outer_vertex2.normal.x = 1
                # TODO Modify UVPoints, recalc normals
                new_sfile.update_vertex(railbase_top_outer_vertex1)
                new_sfile.update_vertex(railbase_top_outer_vertex2)

                # Set position of inner top railbase vertices.
                new_position = tsu.get_new_position_from_trackcenter(0.7694, railbase_top_inner_vertex1.point, trackcenter)
                railbase_top_inner_vertex1.point.x = new_position.x # Set recalculated x
                railbase_top_inner_vertex2.point.x = new_position.x # Set recalculated x
                railbase_top_inner_vertex1.point.y = 0.2268 # Set height
                railbase_top_inner_vertex2.point.y = 0.2268 # Set height
                railbase_top_inner_vertex1.point.z = new_position.z # Set recalculated z
                railbase_top_inner_vertex2.point.z = new_position.z # Set recalculated z
                #railbase_top_inner_vertex1.normal.x = 1
                #railbase_top_inner_vertex2.normal.x = 1
                # TODO Modify UVPoints, recalc normals
                new_sfile.update_vertex(railbase_top_inner_vertex1)
                new_sfile.update_vertex(railbase_top_inner_vertex2)

            elif 0.6675 <= distance_from_center <= 0.7675: # Inside right rail.
                # Set position of outer top railbase vertices.
                new_position = tsu.get_new_position_from_trackcenter(0.6785, railbase_top_outer_vertex1.point, trackcenter)
                railbase_top_outer_vertex1.point.x = new_position.x # Set recalculated x
                railbase_top_outer_vertex2.point.x = new_position.x # Set recalculated x
                railbase_top_outer_vertex1.point.y = 0.215 # Set height
                railbase_top_outer_vertex2.point.y = 0.215 # Set height
                railbase_top_outer_vertex1.point.z = new_position.z # Set recalculated z
                railbase_top_outer_vertex2.point.z = new_position.z # Set recalculated z
                #railbase_top_outer_vertex1.normal.x = 1
                #railbase_top_outer_vertex2.normal.x = 1
                # TODO Modify UVPoints, recalc normals
                new_sfile.update_vertex(railbase_top_outer_vertex1)
                new_sfile.update_vertex(railbase_top_outer_vertex2)

                # Set position of inner top railbase vertices.
                new_position = tsu.get_new_position_from_trackcenter(0.7374, railbase_top_inner_vertex1.point, trackcenter)
                railbase_top_inner_vertex1.point.x = new_position.x # Set recalculated x
                railbase_top_inner_vertex2.point.x = new_position.x # Set recalculated x
                railbase_top_inner_vertex1.point.y = 0.2268 # Set height
                railbase_top_inner_vertex2.point.y = 0.2268 # Set height
                railbase_top_inner_vertex1.point.z = new_position.z # Set recalculated z
                railbase_top_inner_vertex2.point.z = new_position.z # Set recalculated z
                #railbase_top_inner_vertex1.normal.x = 1
                #railbase_top_inner_vertex2.normal.x = 1
                # TODO Modify UVPoints, recalc normals
                new_sfile.update_vertex(railbase_top_inner_vertex1)
                new_sfile.update_vertex(railbase_top_inner_vertex2)

            elif -0.7675 <= distance_from_center <= -0.6675: # Inside right rail.
                # Set position of outer top railbase vertices.
                new_position = tsu.get_new_position_from_trackcenter(-0.6785, railbase_top_outer_vertex1.point, trackcenter)
                railbase_top_outer_vertex1.point.x = new_position.x # Set recalculated x
                railbase_top_outer_vertex2.point.x = new_position.x # Set recalculated x
                railbase_top_outer_vertex1.point.y = 0.215 # Set height
                railbase_top_outer_vertex2.point.y = 0.215 # Set height
                railbase_top_outer_vertex1.point.z = new_position.z # Set recalculated z
                railbase_top_outer_vertex2.point.z = new_position.z # Set recalculated z
                #railbase_top_outer_vertex1.normal.x = 1
                #railbase_top_outer_vertex2.normal.x = 1
                # TODO Modify UVPoints, recalc normals
                new_sfile.update_vertex(railbase_top_outer_vertex1)
                new_sfile.update_vertex(railbase_top_outer_vertex2)

                # Set position of inner top railbase vertices.
                new_position = tsu.get_new_position_from_trackcenter(-0.7374, railbase_top_inner_vertex1.point, trackcenter)
                railbase_top_inner_vertex1.point.x = new_position.x # Set recalculated x
                railbase_top_inner_vertex2.point.x = new_position.x # Set recalculated x
                railbase_top_inner_vertex1.point.y = 0.2268 # Set height
                railbase_top_inner_vertex2.point.y = 0.2268 # Set height
                railbase_top_inner_vertex1.point.z = new_position.z # Set recalculated z
                railbase_top_inner_vertex2.point.z = new_position.z # Set recalculated z
                #railbase_top_inner_vertex1.normal.x = 1
                #railbase_top_inner_vertex2.normal.x = 1
                # TODO Modify UVPoints, recalc normals
                new_sfile.update_vertex(railbase_top_inner_vertex1)
                new_sfile.update_vertex(railbase_top_inner_vertex2)

            elif -0.9175 <= distance_from_center <= -0.8175: # Outside left rail.
                # Set position of outer top railbase vertices.
                new_position = tsu.get_new_position_from_trackcenter(-0.8285, railbase_top_outer_vertex1.point, trackcenter)
                railbase_top_outer_vertex1.point.x = new_position.x # Set recalculated x
                railbase_top_outer_vertex2.point.x = new_position.x # Set recalculated x
                railbase_top_outer_vertex1.point.y = 0.215 # Set height
                railbase_top_outer_vertex2.point.y = 0.215 # Set height
                railbase_top_outer_vertex1.point.z = new_position.z # Set recalculated z
                railbase_top_outer_vertex2.point.z = new_position.z # Set recalculated z
                #railbase_top_outer_vertex1.normal.x = 1
                #railbase_top_outer_vertex2.normal.x = 1
                # TODO Modify UVPoints, recalc normals
                new_sfile.update_vertex(railbase_top_outer_vertex1)
                new_sfile.update_vertex(railbase_top_outer_vertex2)

                # Set position of inner top railbase vertices.
                new_position = tsu.get_new_position_from_trackcenter(-0.7694, railbase_top_inner_vertex1.point, trackcenter)
                railbase_top_inner_vertex1.point.x = new_position.x # Set recalculated x
                railbase_top_inner_vertex2.point.x = new_position.x # Set recalculated x
                railbase_top_inner_vertex1.point.y = 0.2268 # Set height
                railbase_top_inner_vertex2.point.y = 0.2268 # Set height
                railbase_top_inner_vertex1.point.z = new_position.z # Set recalculated z
                railbase_top_inner_vertex2.point.z = new_position.z # Set recalculated z
                #railbase_top_inner_vertex1.normal.x = 1
                #railbase_top_inner_vertex2.normal.x = 1
                # TODO Modify UVPoints, recalc normals
                new_sfile.update_vertex(railbase_top_inner_vertex1)
                new_sfile.update_vertex(railbase_top_inner_vertex2)

            #print(railbase_top_outer_vertex1)
            #print(railbase_top_outer_vertex2)
            #print(railbase_top_inner_vertex1)
            #print(railbase_top_inner_vertex2)
            #print("--")
        new_sfile.save()
        #new_sfile.compress(ffeditc_path)

        # Process .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()