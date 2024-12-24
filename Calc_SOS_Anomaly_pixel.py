#2024/07/05
#Written by Yuki Mizuno
#This script is to calculate anomalies of SOS each year and pixel.

import os
import numpy as np
from osgeo import gdal

# データのディレクトリ
input_dir = 'path to directory contains your SOS files'
output_dir = 'path to directory for outputs'

# 年の範囲
years = range(2018, 2025)

# すべての年のデータを格納するリスト
ect_all_years = []

# 各年のデータを読み込む
for year in years:
    file_path = os.path.join(input_dir, f'your_file_name_{year}.tif')
    dataset = gdal.Open(file_path)
    if dataset is None:
        print(f'No file: {file_path}')
        continue
    ect_data = dataset.GetRasterBand(1).ReadAsArray().astype(np.float32)
    ect_all_years.append(ect_data)
    if year == 2018:
        ref_ds = dataset  

# 3D配列に変換
ect_all_years = np.array(ect_all_years)

# Calculate AVE from 2018 to 2022 as a baseline
def calculate_average(ect_all_years, start_year, end_year):
    start_index = start_year - years[0]
    end_index = end_year - years[0] + 1
    with np.errstate(invalid='ignore'):
        averages = np.nanmean(ect_all_years[start_index:end_index], axis=0)
    return averages


def calculate_anomalies(ect_all_years, averages):
    anomalies = np.empty_like(ect_all_years)
    for i in range(ect_all_years.shape[0]):
        with np.errstate(invalid='ignore'):
            anomalies[i] = ect_all_years[i] - averages
            anomalies[i] = np.where(np.isnan(ect_all_years[i]), np.nan, anomalies[i])
    return anomalies

# 平均の計算
averages = calculate_average(ect_all_years, 2018, 2022)

# 各年のアノマリーを計算
anomalies = calculate_anomalies(ect_all_years, averages)

# GeoTIFFファイルを作成する関数
def create_geotiff(out_path, array, ref_ds):
    driver = gdal.GetDriverByName('GTiff')
    rows, cols = array.shape
    out_raster = driver.Create(out_path, cols, rows, 1, gdal.GDT_Float32)
    out_raster.SetGeoTransform(ref_ds.GetGeoTransform())
    out_raster.SetProjection(ref_ds.GetProjection())
    band = out_raster.GetRasterBand(1)
    band.WriteArray(array)
    band.SetNoDataValue(np.nan)
    out_raster.FlushCache()
    out_raster = None

# アノマリーマップを出力ディレクトリに保存
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for i, year in enumerate(years):
    output_path = os.path.join(output_dir, f'your_output_name_{year}.tif')
    create_geotiff(output_path, anomalies[i], ref_ds)
    print(f'Successfully saved: {output_path}')
