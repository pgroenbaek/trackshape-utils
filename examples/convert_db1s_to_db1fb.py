import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    shape_converted_path = "./Converted_from_DB1s_to_DB1fb"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = ["DB1s_*.s"]
    ignore_shapes = ["*Tun*", "*Pnt*", "*Frog*"]
    
    os.path.makedirs(shape_converted_path)

    trackshape_names = tsu.find_directory_files(shape_load_path, match_shapes, ignore_shapes)

    for idx, original_shape_name in enumerate(trackshape_names):
        print(f"Shape {idx} of {len(trackshape_names)}...")
        
        # Convert .s file
        new_shape_name = original_shape_name.replace("DB1s_", "DB1fb_")
        original_shape_path = f"{shape_load_path}/{original_shape_name}"
        new_shape_path = f"{shape_converted_path}/{new_shape_name}"

        original_sfile = tsu.load_shape(original_shape_name, original_shape_path)
        new_sfile = original_sfile.copy(new_filename=new_shape_name, new_directory=new_shape_path)

        new_sfile.decompress(ffeditc_path)

        new_sfile.replace_ignorecase("DB_TrackSfs1.ace", "DB_Track1.ace")
        new_sfile.replace_ignorecase("DB_TrackSfs1s.ace", "DB_Track1s.ace")
        new_sfile.replace_ignorecase("DB_TrackSfs1w.ace", "DB_Track1w.ace")
        new_sfile.replace_ignorecase("DB_TrackSfs1sw.ace", "DB_Track1sw.ace")

        lod_dlevel = 200
        subobject_idxs = new_sfile.get_subobject_idxs_in_lod_dlevel(lod_dlevel)
        for subobject_idx in subobject_idxs:
            vertices_in_subobject = new_sfile.get_vertices_in_subobject(lod_dlevel, subobject_idx)
            for vertex in vertices_in_subobject:
                if vertex.point.y == 0.133:
                    vertex.point.y = 0.0833
                    new_sfile.update_vertex(vertex)
                elif vertex.point.y == 0.145:
                    vertex.point.y = 0.0945
                    new_sfile.update_vertex(vertex)

        new_sfile.save()
        new_sfile.compress(ffeditc_path)

        #  Convert .sd file
        original_sdfile_name = original_shape_name.replace(".s", ".sd")
        new_sdfile_name = new_shape_name.replace(".s", ".sd")
        original_sdfile_path = f"{shape_load_path}/{original_sdfile_name}"
        new_sdfile_path = f"{shape_converted_path}/{new_sdfile_name}"

        original_sdfile = tsu.load_file(original_sdfile_name, original_sdfile_path)
        new_sdfile = original_sdfile.copy(new_filename=new_sdfile_name, new_directory=new_sdfile_path)
        new_sdfile.replace_ignorecase(original_shape_name, new_shape_name)
        new_sdfile.save()