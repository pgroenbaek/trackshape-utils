import re
import os
import pyffeditc
import shapeio
import trackshapeutils as tsu
from shapeedit import ShapeEditor

if __name__ == "__main__":
    ffeditc_path = "./ffeditc_unicode.exe"
    load_path = "./examples/data/"
    processed_path = "./examples/data/processed/V4hs1t_RKL"
    match_files = ["DB1z_a1t*.s"]
    ignore_files = ["*Tun*", "*Pnt*", "*Frog*"]
    
    os.makedirs(processed_path, exist_ok=True)

    shape_names = shapeio.find_directory_files(load_path, match_files, ignore_files)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx} of {len(shape_names)}...")

        # Process .s file
        new_sfile_name = sfile_name.replace("DB1z_", "V4hs1t_RKL_")
        new_sfile_name = new_sfile_name.replace("A1t", "")
        new_sfile_name = new_sfile_name.replace("a1t", "")

        tsection_sfile_name = sfile_name.replace("a2dt", "a2t")
        tsection_sfile_name = tsection_sfile_name.replace("DB1z_", "")
        trackcenters = tsu.trackcenters_from_global_tsection(shape_name=tsection_sfile_name, num_points_per_meter=12)

        shape_path = f"{load_path}/{sfile_name}"
        new_shape_path = f"{processed_path}/{new_sfile_name}"

        shapeio.copy(shape_path, new_shape_path)

        pyffeditc.decompress(ffeditc_path, new_shape_path)
        trackshape = shapeio.load(new_shape_path)

        for idx, image in enumerate(trackshape.images):
            image = re.sub(r"DB_Rails1.ace", "V4_Rails1.ace", image, flags=re.IGNORECASE)
            image = re.sub(r"DB_Rails1w.ace", "V4_Rails1.ace", image, flags=re.IGNORECASE)
            image = re.sub(r"DB_Track1.ace", "V4_RKLb.ace", image, flags=re.IGNORECASE)
            image = re.sub(r"DB_Track1s.ace", "V4_RKLs.ace", image, flags=re.IGNORECASE)
            image = re.sub(r"DB_Track1w.ace", "V4_RKLb.ace", image, flags=re.IGNORECASE)
            image = re.sub(r"DB_Track1sw.ace", "V4_RKLs.ace", image, flags=re.IGNORECASE)
            image = re.sub(r"DB_TrackSfs1.ace", "V4_RKLb.ace", image, flags=re.IGNORECASE)
            image = re.sub(r"DB_TrackSfs1s.ace", "V4_RKLs.ace", image, flags=re.IGNORECASE)
            image = re.sub(r"DB_TrackSfs1w.ace", "V4_RKLb.ace", image, flags=re.IGNORECASE)
            image = re.sub(r"DB_TrackSfs1sw.ace", "V4_RKLs.ace", image, flags=re.IGNORECASE)
            trackshape.images[idx] = image

        # RKL side
        # [Vector((-1.4025001525878906, 0.0, -0.12800000607967377))]
        # [Vector((-1.4125001430511475, 0.0, -0.019999999552965164))]
        # [Vector((-2.43250036239624, 0.0, 0.009999999776482582))]

        # normal track side
        # [Vector((-1.2999999523162842, 0.0, -0.13499999046325684))]
        # [Vector((-1.7000000476837158, 0.0, -0.13589999079704285))]
        # [Vector((-2.5999999046325684, 0.0, 0.019999999552965164))]

        trackshape_editor = ShapeEditor(trackshape)

        for lod_control in trackshape_editor.lod_controls():
            for lod_dlevel in lod_control.distance_levels():
                for sub_object in lod_dlevel.sub_objects():
                    # mb_sleeperbase
                    for primitive in sub_object.primitives(prim_state_name="mb_sleeperbase"):
                        for vertex in primitive.vertices():
                            vertex.point.y = 0.120 # Not needed, so set height below slab track surface

                    # mb_trackbed
                    for primitive in sub_object.primitives(prim_state_name="mb_trackbed"):
                        for vertex in primitive.vertices():
                            closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, trackcenter, plane="xz")
                            distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")

                            # Innermost mb_trackbed points
                            if distance_from_center < -1.65 and distance_from_center > -1.75:
                                new_position = tsu.get_new_position_from_trackcenter(-1.4125, vertex.point, trackcenter)
                                vertex.point.x = new_position.x # Set recalculated x
                                vertex.point.y = 0.02 # Set height
                                vertex.point.z = new_position.z # Set recalculated z
                            if distance_from_center > 1.65 and distance_from_center < 1.75:
                                new_position = tsu.get_new_position_from_trackcenter(1.4125, vertex.point, trackcenter)
                                vertex.point.x = new_position.x # Set recalculated x
                                vertex.point.y = 0.02 # Set height
                                vertex.point.z = new_position.z # Set recalculated z
                            
                            # Outermost mb_trackbed points
                            if distance_from_center < -2.55 and distance_from_center > -2.65:
                                new_position = tsu.get_new_position_from_trackcenter(-2.4325, vertex.point, trackcenter)
                                vertex.point.x = new_position.x # Set recalculated x
                                vertex.point.y = 0.01 # Set height
                                vertex.point.z = new_position.z # Set recalculated z
                            if distance_from_center > 2.55 and distance_from_center < 2.65:
                                new_position = tsu.get_new_position_from_trackcenter(2.4325, vertex.point, trackcenter)
                                vertex.point.x = new_position.x # Set recalculated x
                                vertex.point.y = 0.01 # Set height
                                vertex.point.z = new_position.z # Set recalculated z
                    
                    # mt_trackbed
                    for primitive in sub_object.primitives(prim_state_name="mt_trackbed"):
                        for vertex in primitive.vertices():
                            closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, trackcenter, plane="xz")
                            distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")

                            # Second to last outermost mt_trackbed points
                            if distance_from_center < -1.25 and distance_from_center > -1.35:
                                new_position = tsu.get_new_position_from_trackcenter(-1.4025, vertex.point, trackcenter)
                                vertex.point.x = new_position.x # Set recalculated x
                                vertex.point.y = 0.128 # Set height
                                vertex.point.z = new_position.z # Set recalculated z
                                if vertex.uv_point.u == 0.6357:
                                    vertex.uv_point.u = 0.6582
                                elif vertex.uv_point.u == 0.0918:
                                    vertex.uv_point.u = 0.0693
                            if distance_from_center > 1.25 and distance_from_center < 1.35:
                                new_position = tsu.get_new_position_from_trackcenter(1.4025, vertex.point, trackcenter)
                                vertex.point.x = new_position.x # Set recalculated x
                                vertex.point.y = 0.128 # Set height
                                vertex.point.z = new_position.z # Set recalculated z
                                if vertex.uv_point.u == 0.1143:
                                    vertex.uv_point.u = 0.0918
                                elif vertex.uv_point.u == 0.6582:
                                    vertex.uv_point.u = 0.6807
                            
                            # Outermost mt_trackbed points
                            if distance_from_center < -1.65 and distance_from_center > -1.75:
                                new_position = tsu.get_new_position_from_trackcenter(-1.4125, vertex.point, trackcenter)
                                vertex.point.x = new_position.x # Set recalculated x
                                vertex.point.y = 0.02 # Set height
                                vertex.point.z = new_position.z # Set recalculated z
                                if vertex.uv_point.u == 0.7158:
                                    vertex.uv_point.u = 0.6758
                                elif vertex.uv_point.u == 0.0742:
                                    vertex.uv_point.u = 0.0342
                            if distance_from_center > 1.65 and distance_from_center < 1.75:
                                new_position = tsu.get_new_position_from_trackcenter(1.4125, vertex.point, trackcenter)
                                vertex.point.x = new_position.x # Set recalculated x
                                vertex.point.y = 0.02 # Set height
                                vertex.point.z = new_position.z # Set recalculated z
                                if vertex.uv_point.u == 0.0342:
                                    vertex.uv_point.u = 0.0742
                                elif vertex.uv_point.u == 0.6758:
                                    vertex.uv_point.u = 0.7158
                
        shapeio.dump(trackshape, new_shape_path)
        pyffeditc.compress(ffeditc_path, new_shape_path)

        # Process .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile_path = f"{load_path}/{sdfile_name}"
        new_sdfile_path = f"{processed_path}/{new_sdfile_name}"

        shapeio.copy(sdfile_path, new_sdfile_path)
        shapeio.replace_ignorecase(new_sdfile_path, sfile_name, new_sfile_name)
