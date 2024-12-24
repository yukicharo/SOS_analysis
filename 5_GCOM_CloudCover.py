#2024/06/20
#Written by Yuki Mizuno (University of Tsukuba)
#This script is to cover low quality pixels due to cloud, BRDF, etc. based on QA_flag.

from osgeo import gdal
import numpy as np
import glob
import os
import re
from multiprocessing import Pool, Manager

# Each file must include date as "%Y%m%d".
qa_directory = "path to directory contains QA_flag files"
vn03_directory = "path to directory contains satellite images"
output_directory = "path to directory for outputs"

date_pattern = re.compile(r"_(\d{8})_")

def save_array_as_tiff(output_file, array, reference_file):
    driver = gdal.GetDriverByName('GTiff')
    rows, cols = array.shape
    dataset = gdal.Open(reference_file)
    out_raster = driver.Create(output_file, cols, rows, 1, gdal.GDT_Float32)
    out_raster.SetGeoTransform(dataset.GetGeoTransform())
    out_raster.SetProjection(dataset.GetProjection())
    out_raster.GetRasterBand(1).WriteArray(array)
    out_raster.FlushCache()

def adjust_array_size(qa_array, vn03_array):
    qa_rows, qa_cols = qa_array.shape
    vn03_rows, vn03_cols = vn03_array.shape

    if qa_rows == vn03_rows and qa_cols == vn03_cols:
        return vn03_array

    adjusted_array = np.full((qa_rows, qa_cols), np.nan, dtype=float)

    min_rows = min(qa_rows, vn03_rows)
    min_cols = min(qa_cols, vn03_cols)
    adjusted_array[:min_rows, :min_cols] = vn03_array[:min_rows, :min_cols]

    return adjusted_array

def process_file(args):
    qa_file, error_dates = args
    try:
       
        match = date_pattern.search(qa_file)
        if not match:
            return
        date_str = match.group(1)

        output_mask_VN03 = os.path.join(output_directory, f"output_file_name_{date_str}_band.tif") #band should be VN05 or VN08

        if os.path.exists(output_mask_VN03):
            print(f"Output file already exists for {date_str}. Skipping.")
            return

        VN03_file = os.path.join(vn03_directory, f"file_name_{date_str}_band.tif") #band should be VN05 or VN08
        if not os.path.exists(VN03_file):
            print(f"VN03 file not found for {date_str}")
            error_dates.append(date_str)
            return

        QN = gdal.Open(qa_file).ReadAsArray().astype(float)
        VN03_array = gdal.Open(VN03_file).ReadAsArray().astype(float)

     
        VN03_array = adjust_array_size(QN, VN03_array)

       
        QN_trans = np.where(QN == 2, 1, np.nan)
        mask_VN03 = QN_trans * VN03_array

        
        save_array_as_tiff(output_mask_VN03, mask_VN03, VN03_file)

    except Exception as e:
        print(f"Error processing date {date_str}: {e}")
        error_dates.append(date_str)

if __name__ == '__main__':
    qa_files = glob.glob(os.path.join(qa_directory, "file_name_*_QA_flag.tif"))

    with Manager() as manager:
        error_dates = manager.list()

        with Pool(processes=4) as pool:
            pool.map(process_file, [(qa_file, error_dates) for qa_file in qa_files])

        if error_dates:
            print("\nErrors occurred on the following dates:")
            for date_str in error_dates:
                print(date_str)
