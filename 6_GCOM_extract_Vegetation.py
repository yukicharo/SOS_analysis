#2024/06/25
#Written by Yuki Mizuno (university of Tsukuba)
#This script is to exclude non-vegetation area using vegetation map of 250 m resolution.
#Before you run this, you should reshape vegetation map to model tif (No.4 script) and convert original value to 1 or 0 (1: Vegetation area, 0: Area you want to exclude).

from osgeo import gdal
import numpy as np
import os
import glob

reference_file = "/path/to/your/vegetation_map/file_name.tif"

input_directory = "path to directory contains satellite data"
output_directory = "path to directory for outputs"

os.makedirs(output_directory, exist_ok=True)

ref_dataset = gdal.Open(reference_file)
ref_array = ref_dataset.GetRasterBand(1).ReadAsArray().astype(float)
ref_shape = ref_array.shape


mismatched_files = []

def process_file(input_file, reference_array, reference_shape):
    try:
        
        dataset = gdal.Open(input_file)
        band = dataset.GetRasterBand(1)
        array = band.ReadAsArray().astype(float)

     
        if array.shape != reference_shape:
            mismatched_files.append(input_file)
            return

        # Masking: Extract only vegetation map=1 pixel.
        masked_array = np.where(reference_array == 1, array, np.nan)

        output_file = os.path.join(output_directory, os.path.basename(input_file))

        driver = gdal.GetDriverByName('GTiff')
        out_dataset = driver.Create(
            output_file,
            dataset.RasterXSize,
            dataset.RasterYSize,
            1,
            gdal.GDT_Float32
        )
        out_dataset.SetGeoTransform(dataset.GetGeoTransform())
        out_dataset.SetProjection(dataset.GetProjection())
        out_band = out_dataset.GetRasterBand(1)
        out_band.WriteArray(masked_array)

        out_band.FlushCache()
        del out_dataset

        print(f"Processed: {input_file} -> {output_file}")
    except Exception as e:
        print(f"Error processing {input_file}: {e}")

tif_files = glob.glob(os.path.join(input_directory, "*.tif"))

for tif_file in tif_files:
    process_file(tif_file, ref_array, ref_shape)

if mismatched_files:
    print("\nFiles with mismatched shapes:")
    for file in mismatched_files:
        print(file)
else:
    print("\nAll files match the reference shape.")
