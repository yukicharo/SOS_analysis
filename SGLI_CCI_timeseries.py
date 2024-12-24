#2024/07/10
#Written by Yuki Mizuno (University of Tsukuba)
#This script is to make timeseries of CCI from GCOM-C/SGLI data.
#Satellite data file name should include date as "%Y-%m-%d" or "%Y%m%d".

import numpy as np
import matplotlib.pyplot as plt
import glob
from osgeo import gdal
import datetime
import os
import re
import pandas as pd

green_band_dir = "path to your directory includes Green band (VN05)"
red_band_dir = "path to your directory includes Green band (VN08)"

green_files = sorted(glob.glob(os.path.join(green_band_dir, "*.tif")))
red_files = sorted(glob.glob(os.path.join(red_band_dir, "*.tif")))

def calculate_grvi_safely(green, red):
    denominator = green + red
    grvi = np.divide((green - red), denominator)
    return grvi

# area of interest
"""
# TOE
minX = 141.5560886
minY = 42.7061530
maxX = 141.5584245
maxY = 42.7084501
"""
# TKY
minX = 137.4228674
minY = 36.14374420
maxX = 137.42500402
maxY = 36.1458942
"""
# FHK
minX = 138.7624922876942435
minY = 35.4437351792199067
maxX = 138.7687515005773946
maxY = 35.4500083280096163
"""

grvi_values = []
dates = []
yearly_data = {}
output_folder = "path to your directory to save clipped satellite images"

fig, ax1 = plt.subplots(figsize=(12, 6))

for green_file, red_file in zip(green_files, red_files):
    input_image_basename = os.path.basename(green_file)
    output_image_path_green = os.path.join(output_folder, "clipped_green_" + input_image_basename)
    output_image_path_red = os.path.join(output_folder, "clipped_red_" + input_image_basename)

    green_dataset = gdal.Open(green_file, gdal.GA_ReadOnly)
    red_dataset = gdal.Open(red_file, gdal.GA_ReadOnly)

    gdal.Translate(output_image_path_green, green_dataset, projWin=[minX, maxY, maxX, minY])
    gdal.Translate(output_image_path_red, red_dataset, projWin=[minX, maxY, maxX, minY])

    cut_green_dataset = gdal.Open(output_image_path_green)
    cut_red_dataset = gdal.Open(output_image_path_red)

    green_array = cut_green_dataset.ReadAsArray().astype(float)
    red_array = cut_red_dataset.ReadAsArray().astype(float)

    grvi = calculate_grvi_safely(green_array, red_array)
    spatial_mean_grvi = np.mean(grvi)
    grvi_values.append(spatial_mean_grvi) 

    date_match = re.search(r'\d{4}-\d{2}-\d{2}|\d{8}', input_image_basename)
    if date_match:
        date_string = date_match.group()
        try:
            extracted_date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        except ValueError:
            extracted_date = datetime.datetime.strptime(date_string, "%Y%m%d")

        if extracted_date:
            year = extracted_date.year
            day_of_year = extracted_date.timetuple().tm_yday

            if year not in yearly_data:
                yearly_data[year] = {'days_of_year': [], 'grvi_values': []}

            yearly_data[year]['days_of_year'].append(day_of_year)
            yearly_data[year]['grvi_values'].append(spatial_mean_grvi)

            for year, data in yearly_data.items():
                sorted_indices = np.argsort(data['days_of_year'])
                sorted_days_of_year = np.array(data['days_of_year'])[sorted_indices]
                sorted_grvi_values = np.array(data['grvi_values'])[sorted_indices]

                yearly_data[year]['days_of_year'] = sorted_days_of_year.tolist()
                yearly_data[year]['grvi_values'] = sorted_grvi_values.tolist()


def interpolate_missing_dates(df, year):
    full_date_range = pd.DataFrame({'DOY': np.arange(1, 366)})
    df = full_date_range.merge(df, how='left', left_on='DOY', right_on='DOY')
    df['GRVI'].interpolate(method='linear', inplace=True)
    return df

# カスタムカラーリスト
custom_colors = ['#FFF100', '#F6AA00', '#4DC4FF', '#03AF7A', '#005AFF', '#FF4B00','#000000']

"""
# 年ごとにプロットを行う
for i, (year, data) in enumerate(yearly_data.items()):
    df = pd.DataFrame({'DOY': yearly_data[year]['days_of_year'], 'GRVI': yearly_data[year]['grvi_values']})
    df = interpolate_missing_dates(df, year)  
    c = custom_colors[i % len(custom_colors)]
    ax1.plot(df['DOY'].to_numpy(), df['GRVI'].to_numpy(), marker=".", label=str(year), linewidth=1, color=c)
"""

ax1.axhline(y=0, color='black', linewidth=0.8)

month_days = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
for i, day_value in enumerate(month_days):
    ax1.axvline(x=day_value, color='black', linestyle='--', linewidth=0.8)

month_days = [16, 45, 74, 105, 135, 166, 196, 228, 259, 289, 319, 350]
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
for i, day_value in enumerate(month_days):
    ax1.text(day_value - 0.5, 0.55, month_names[i], ha='center', va='top', fontsize=20)

ax1.set_xlim(0, 365)  
ax1.set_ylim(-0.6, 0.6)  
ax1.set_xlabel('DOY (Day of Year)', fontsize=20)
ax1.set_ylabel('CCI', fontsize=20)
ax1.set_title('your title of this figure', fontstyle='italic', fontsize=16)
plt.xticks(fontsize=16)  
plt.yticks(fontsize=16)  
plt.minorticks_on() 

# Identify the DOY for June 5, 2024
cutoff_date = datetime.datetime(2024, 6, 30)
cutoff_doy = cutoff_date.timetuple().tm_yday 

for i, (year, data) in enumerate(yearly_data.items()):
    df = pd.DataFrame({'DOY': yearly_data[year]['days_of_year'], 'GRVI': yearly_data[year]['grvi_values']})
    df = interpolate_missing_dates(df, year)  
    
    if year == 2024:
        df.loc[df['DOY'] > cutoff_doy, 'GRVI'] = np.nan

    c = custom_colors[i % len(custom_colors)]
    ax1.plot(df['DOY'].to_numpy(), df['GRVI'].to_numpy(), label=str(year), linewidth=2, color=c) #marker="o"


#plt.legend(bbox_to_anchor=(0.5, -0.1), loc='lower center', ncol=7, borderaxespad=-5, fontsize=10, edgecolor='black')
#ax1.xaxis.grid(False)

fig.tight_layout()
plt.savefig("path to your outout directory", dpi=300)
plt.show()
