import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "./examples/data"
    shape_processed_path = "./examples/data/processed/NREmbAtracksRails"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = ["NR_Emb_a1t250r10d.s"]
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

        trackcenter = tsu.generate_curve_centerpoints(curve_radius=250, curve_angle=-10, num_points=10000, start_angle=0, start_point=tsu.Point(0, 0, 0))

        lod_dlevel = 400
        prim_state = new_sfile.get_prim_state_by_name("rail_side")
        vertices_in_prim_state = new_sfile.get_vertices_by_prim_state(lod_dlevel, prim_state)
        
        for vertex in vertices_in_prim_state:
            closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, trackcenter, plane='xz')
            trackcenter_distance = tsu.signed_distance_from_centerpoint(vertex.point, closest_centerpoint, plane="xz")

            if vertex.point.y == 0.2: # Railhead bottom vertices
                connected_vertices = new_sfile.get_connected_vertices(prim_state, vertex)

                for connected_vertex in connected_vertices:
                    if connected_vertex.point.y == 0.325 and connected_vertex.point.z == vertex.point.z: # Connected railhead top vertices directly over the bottom ones
                        new_vertex1 = new_sfile.insert_vertex_between(prim_state, vertex, connected_vertex)
                        #new_vertex2 = new_sfile.insert_vertex_between(prim_state, vertex, connected_vertex)

                        # TODO: Generated track center for curves seem to veer off a bit at the far end.
                        # TODO: Insert and reposition vertices
                        trackcenter_distance_new_vertex = tsu.signed_distance_from_centerpoint(new_vertex.point, closest_centerpoint, plane="xz")
                        if 0.8175 <= trackcenter_distance <= 0.9175:
                            pass
                        elif 0.6675 <= trackcenter_distance <= 0.7675:
                            pass
                        elif -0.7675 <= trackcenter_distance <= -0.6675:
                            pass
                        elif -0.9175 <= trackcenter_distance <= -0.8175:
                            pass
                        print(trackcenter_distance_new_vertex)
            

        new_sfile.save()
        #new_sfile.compress(ffeditc_path)

        # Process .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()