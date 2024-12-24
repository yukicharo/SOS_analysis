#2024/12/10
#Written by Yuki Mizuno (University of Tsukuba)
#This script is to calculate spatial mean (your AOI, each region, etc).

import numpy as np
import glob
import rasterio
import geopandas as gpd
import os
from rasterio.mask import mask

# You need to fill in the blanks like ".../.../*.tif". Your tif file must be i band image.
list_files = glob.glob('path to directory which contains your target tif files')

shp_path = 'path to directory which contains your shp file'
shape = gpd.read_file(os.path.join(shp_path, "your shp file name"), encoding="shift-jis")

shapes = [feature["geometry"] for feature in shape.__geo_interface__["features"]]

def calculate_spatial_mean_in_region(in_file, shapes):
    with rasterio.open(in_file) as src:
        out_image, out_transform = mask(src, shapes, crop=True)
        
        out_image = out_image[0]  
        data_no_nan = out_image[~np.isnan(out_image)]
        spatial_mean = np.mean(data_no_nan)
        
    return spatial_mean

mean_values = []
for file in list_files:
    mean_value = calculate_spatial_mean_in_region(file, shapes)
    mean_values.append(mean_value)

for file, mean in zip(list_files, mean_values):
    print(f"File: {os.path.basename(file)} - Spatial Mean in Region: {mean}")

import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
plt.bar(range(len(list_files)), mean_values, tick_label=[os.path.basename(f) for f in list_files])
plt.xlabel('TIFF Files')
plt.ylabel('Spatial Mean in Region')
plt.title('Spatial Mean in Region for Each TIFF File')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()
