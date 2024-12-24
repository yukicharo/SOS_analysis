#2024/07/05
#Written by Yuki Mizuno (University of Tsukuba)
#This script is to cut satellite images based on model tif each region
#You need to make model tif each region before running this script.
#If you want model tif each region, please contact me via e-mail.

import numpy as np
import glob
import os
import re
from osgeo import gdal
import rasterio
from rasterio.windows import from_bounds
from multiprocessing import Pool

input_folder = 'path to directory which contains satellite images'
output_folders = {
    "Hokkaido": '/path to ouput/Hokkaido/',
    "NTohoku": '/path to output/NTohoku/',
    "STohoku": '/path to shp file/STohoku/',
    "KantoKoshin": '/path to outout/KantoKoshin/',
    "Hokuriku": '/path to output/Hokuriku',
    "Tokai": '/path to output/Tokai/',
    "Kinki": '/path to output/Kinki/',
    "ChugokuShikoku": '/path to output/ChugokuShikoku/',
    "Kyusyu": '/path to output/Kyusyu/',
}

# path to model tif file each region
model_tifs = {
    "Hokkaido": "/path to model tif of Hokkaido/file_name.tif",
    "NTohoku": "/path to model tif of Northern Tohoku/file_name.tif",
    "STohoku": "/path to model tif of Southern Tohoku/file_name.tif",
    "KantoKoshin": "/path to model tif of KantoKoshin/file_name.tif",
    "Hokuriku": "/path to model tif of Hokuriku/file_name.tif",
    "Tokai": "/path to model tif of Tokai/file_name.tif",
    "Kinki": "/path to model tif of Kinki/file_name.tif",
    "ChugokuShikoku": "/path to model tif of ChugokuShikoku/file_name.tif",
    "Kyusyu": "/path to model tif of Kyusyu/file_name.tif",
}

list_files = glob.glob(os.path.join(input_folder, '*.tif'))

# Satellite file must include date as "%Y%m%d" and band number like VN05 or VN08.
# File name should be ..._%Y%m%d_band.tif.
date_pattern = re.compile(r"file_name_(\d{8})_(VN05|VN08).tif")

def get_bounds(model_tif):
    with rasterio.open(model_tif) as src:
        bounds = src.bounds
    return bounds


def clip_by_bounds(in_file, out_file, bounds):
    with rasterio.open(in_file) as src:
        window = from_bounds(*bounds, src.transform)
        out_image = src.read(1, window=window)
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[0],
            "width": out_image.shape[1],
            "transform": src.window_transform(window)
        })
    with rasterio.open(out_file, "w", **out_meta) as dest:
        dest.write(out_image, 1)


def process_file(file):
    try:
        input_image_basename = os.path.basename(file)
        
        match = date_pattern.search(input_image_basename)
        if match:
            date_str = match.group(1)  
            band = match.group(2)  
            
            for region, model_tif in model_tifs.items():
                bounds = get_bounds(model_tif)
                output_folder = output_folders[region]
                
                output_image_path = os.path.join(output_folder, f"{region}_{date_str}_{band}.tif")
                
                if os.path.exists(output_image_path):
                    print(f"File already exists, skipping: {output_image_path}")
                    continue
                
                
                clip_by_bounds(file, output_image_path, bounds)
        else:
            print(f"Could not extract date and band from filename: {input_image_basename}")
    except Exception as e:
        print(f"Error processing file {file}: {e}")

if __name__ == '__main__':
    with Pool(processes=16) as pool:
        pool.map(process_file, list_files)
