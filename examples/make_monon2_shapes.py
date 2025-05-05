import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "E:/NR_Bahntrasse_2.1_AT/NR_Bahntrasse_2.1"
    shape_processed_path = "E:/NR_Bahntrasse_2.1_AT/MONON2"
    monon2_path = "D:/Games/Open Rails/Content/MONON2/ROUTES/MONON-2/Tracks-ND"
    monon2_folders = ["NR_Emb_track", "NR_Emb_track_Rock", "NR_EmbBase_track"]
    bt21at_folders = ["NR_Emb_AT", "NR_Emb_AT", "NR_EmbBase_AT"]
    ffeditc_path = "./ffeditc_unicode.exe"
    match_files = ["*.s"]
    ignore_files = ["*.sd"]
    

    for monon2_folder in monon2_folders:
        os.makedirs(f"{shape_processed_path}/{monon2_folder}", exist_ok=True)
        
        shape_names = tsu.find_directory_files(f"{monon2_path}/{monon2_folder}", match_files, ignore_files)

        for idx, sfile_name in enumerate(shape_names):
            print(f"Shape {idx + 1} of {len(shape_names)}...")
            
            # Process .s file
            bt21at_sfile_name = sfile_name.replace("_a", "_AT_a")

            sfile = tsu.load_shape(bt21at_sfile_name, f"{shape_load_path}/{bt21at_folders[monon2_folders.index(monon2_folder)]}")
            new_sfile = sfile.copy(new_filename=sfile_name, new_directory=f"{shape_processed_path}/{monon2_folder}")
            new_sfile.decompress(ffeditc_path)

            if "_Rock" in monon2_folder:
                new_sfile.replace_ignorecase("NR_Emb_green.ace", "Bridge_Berm_Track_Rock.ace")
                new_sfile.replace_ignorecase("NR_EmbBase.ace", "NR_EmbBase_Rock.ace")

            new_sfile.save()
            new_sfile.compress(ffeditc_path)

            # Process .sd file
            bt21at_sdfile_name = bt21at_sfile_name.replace(".s", ".sd")
            sdfile_name = sfile_name.replace(".s", ".sd")

            sdfile = tsu.load_file(bt21at_sdfile_name, f"{shape_load_path}/{bt21at_folders[monon2_folders.index(monon2_folder)]}")
            new_sdfile = sdfile.copy(new_filename=sdfile_name, new_directory=f"{shape_processed_path}/{monon2_folder}")
            new_sdfile.save()