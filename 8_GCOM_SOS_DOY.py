#2024/07/05
#Written by Yuki Mizuno (University of Tsukuba)
#This script is to determine SOS from CCI value. SOS is defined as "CCI last exceed 0 from negative from Mar. to Jun.

import os
import glob
import numpy as np
from osgeo import gdal, osr
import datetime


def read_satellite_images(vn05_dir, vn08_dir, year):
    # Your file must include date in this format "%Y%m%d". This directry should include only Mar. to Jun. data.
    vn05_files = sorted(glob.glob(os.path.join(vn05_dir, f'your file name of green band (VN05)'))) #...{year}.tif
    vn08_files = sorted(glob.glob(os.path.join(vn08_dir, f'your file name of red band (VN08)'))) #...{year}.tif

    vn05_images = [gdal.Open(f).ReadAsArray() for f in vn05_files]
    vn08_images = [gdal.Open(f).ReadAsArray() for f in vn08_files]

    return vn05_images, vn08_images, vn05_files, vn08_files

def calculate_cci(vn05_images, vn08_images):
    cci_images = []
    for vn05, vn08 in zip(vn05_images, vn08_images):
        cci = (vn05 - vn08) / (vn05 + vn08)
        cci = np.where(np.isnan(cci), 0, cci)  
        cci_images.append(cci)
    return cci_images

def extract_doy(file_paths):
    doys = []
    for path in file_paths:
        date_str = os.path.basename(path).split('_')[3]
        date = datetime.datetime.strptime(date_str, "%Y%m%d")
        doy = date.timetuple().tm_yday
        doys.append(doy)
    return doys

def find_leaf_out_date(cci_images, doys):
    leaf_out_dates = np.zeros(cci_images[0].shape)
    for i in range(cci_images[0].shape[0]):
        for j in range(cci_images[0].shape[1]):
            pre_date = None
            post_date = None
            for k in range(len(cci_images)-1):
                if cci_images[k][i, j] < 0 and cci_images[k+1][i, j] >= 0:
                    pre_date = doys[k]
                    post_date = doys[k+1]
            if pre_date is not None and post_date is not None:
                median_date = (pre_date + post_date) / 2.0
                leaf_out_dates[i, j] = np.ceil(median_date)  
    return leaf_out_dates

def clear_memory(*args):
    for arg in args:
        del arg

def create_geotiff(out_path, array, ref_ds):
    driver = gdal.GetDriverByName('GTiff')
    rows, cols = array.shape
    out_raster = driver.Create(out_path, cols, rows, 1, gdal.GDT_Float32)
    out_raster.SetGeoTransform(ref_ds.GetGeoTransform())
    out_raster.SetProjection(ref_ds.GetProjection())
    out_raster.GetRasterBand(1).WriteArray(array)
    out_raster.FlushCache()
    out_raster = None

# Main workflow
years = range(2018, 2025)
vn05_dir = 'path to your directory contains green band files'
vn08_dir = 'path to your directory contains red band files'

leaf_out_dates_all_years = []

for year in years:
    vn05_images, vn08_images, vn05_files, vn08_files = read_satellite_images(vn05_dir, vn08_dir, year)
    cci_images = calculate_cci(vn05_images, vn08_images)
    doys = extract_doy(vn05_files)
    leaf_out_dates = find_leaf_out_date(cci_images, doys)
    leaf_out_dates_all_years.append(leaf_out_dates)
    clear_memory(vn05_images, vn08_images, cci_images)

# Ranking and output
leaf_out_dates_all_years = np.array(leaf_out_dates_all_years)
rankings = np.argsort(leaf_out_dates_all_years, axis=0)

for year, leaf_out_dates in zip(years, leaf_out_dates_all_years):
    ref_ds = gdal.Open(vn05_files[0]) 
    output_path = f'/path to directory of outouts/file_name_{year}.tif'
    create_geotiff(output_path, leaf_out_dates, ref_ds)
