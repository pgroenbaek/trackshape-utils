import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "./examples/data/"
    shape_processed_path = "./examples/data/"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_files = ["*.s"]
    ignore_files = ["*.sd"]
    
    os.makedirs(shape_processed_path, exist_ok=True)

    shape_names = tsu.find_directory_files(shape_load_path, match_files, ignore_files)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx + 1} of {len(shape_names)}...")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        sfile.compress(ffeditc_path)