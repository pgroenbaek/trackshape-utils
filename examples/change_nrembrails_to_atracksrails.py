import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "./examples/data"
    shape_processed_path = "./examples/data/processed/NREmbAtracksRails"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = ["NR_Emb_a1t250r10d.s"]
    ignore_shapes = ["*Tun*", "*Pnt*", "*Frog*"]
    
    os.makedirs(shape_processed_path, exist_ok=True)

    trackshape_names = tsu.find_directory_files(shape_load_path, match_shapes, ignore_shapes)

    for idx, original_shape_name in enumerate(trackshape_names):
        print(f"Shape {idx} of {len(trackshape_names)}...")

        trackcenter = tsu.generate_curve_centerpoints(curve_radius=250, curve_angle=-10, num_points=10000, start_angle=0, start_point=tsu.Point(0, 0, 0))
        
        # Convert .s file
        new_shape_name = original_shape_name.replace(".s", "_AT.s")

        original_sfile = tsu.load_shape(original_shape_name, shape_load_path)

        new_sfile = original_sfile.copy(new_filename=new_shape_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

        # Railhead vertices from center to outside:
        #[Vector((-0.7175000309944153, 0.20000000298023224, 0.0))]
        #[Vector((-0.7175000309944153, 0.32500001788139343, 0.0))]
        #[Vector((-0.8675000667572021, 0.32500001788139343, 0.0))]
        #[Vector((-0.8675000667572021, 0.20000000298023224, 0.0))]

        lod_dlevel = 400
        prim_state = new_sfile.get_prim_state_by_name("rail_side")
        vertices_in_prim_state = new_sfile.get_vertices_by_prim_state(lod_dlevel, prim_state)

        for vertex in vertices_in_prim_state:
            closest_centerpoint = tsu.find_closest_centerpoint(point_along_track=vertex.point, trackcenter=trackcenter, plane='xz')
            trackcenter_distance = tsu.signed_distance_from_centerpoint(point_along_track=vertex.point, trackcenter_point=closest_centerpoint, plane="xz")

            if vertex.point.y == 0.2: # Railhead bottom vertices
                connected_vertices = new_sfile.get_connected_vertices(prim_state, vertex)
                #print([v for v in connected_vertices if v.point.y == 0.325 and v.point.z == vertex.point.z])

                for connected_vertex in connected_vertices:
                    if connected_vertex.point.y == 0.325 and connected_vertex.point.z == vertex.point.z: # Connected railhead top vertices directly over the bottom ones
                        new_vertex = new_sfile.insert_vertex_between(prim_state, vertex, connected_vertex)
                        print(new_vertex)
            #new_sfile.remove_vertex(vertex, reconnect_geometry=False)

        new_sfile.save()
        #new_sfile.compress(ffeditc_path)

        #  Convert .sd file
        original_sdfile_name = original_shape_name.replace(".s", ".sd")
        new_sdfile_name = new_shape_name.replace(".s", ".sd")

        original_sdfile = tsu.load_file(original_sdfile_name, shape_load_path)
        new_sdfile = original_sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(original_shape_name, new_shape_name)
        new_sdfile.save()