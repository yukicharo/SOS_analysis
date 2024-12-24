#2024/07/11
#Written by Yuki Mizuno and Hina Tachikawa (University of Tsukuba)
#This code plot GRVI timeseries from digital camera images each year

import cv2
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import re

#Files should include "%Y%m%d" or "%Y-%m-%d"
list_files = sorted(glob.glob("path to your dital camera directory"))

def calculate_grvi_safely(green, red):
    denominator = green + red
    grvi = np.divide((green - red), denominator)
    return grvi

fig, ax1 = plt.subplots(figsize=(12, 6))
grvi_values = []
dates = []
yearly_data = {}

for file in list_files:
    input_image_basename = os.path.basename(file)
    dataset = cv2.imread(file) 
    blue = dataset[:,:,0].astype("int16")
    green = dataset[:,:,1].astype("int16")
    red = dataset[:,:,2].astype("int16")
    grvi = calculate_grvi_safely(green, red)
    spatial_mean_grvi = np.mean(grvi)
    grvi_values.append(spatial_mean_grvi) 

    #date_match = re.search(r'\d{4}-\d{2}-\d{2}|\d{8}', input_image_basename)
    date_match = re.search(r'\d{8}|\d{4}-\d{2}-\d{2}', input_image_basename)
    if date_match:
        date_string = date_match.group()
        try:
            extracted_date = datetime.datetime.strptime(date_string, "%Y%m%d")
        except ValueError:
            extracted_date = datetime.datetime.strptime(date_string, "%Y-%m-%d")

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

# list of colors each year
custom_colors = ['#FFF100', '#F6AA00', '#4DC4FF', '#03AF7A', '#005AFF', '#FF4B00', '#000000']
#custom_colors = ['#FFF100', '#F6AA00', '#4DC4FF', '#03AF7A', '#005AFF', '#FF4B00']

# plot each year
for i, (year, data) in enumerate(yearly_data.items()):
    c = custom_colors[i % len(custom_colors)]
    df = pd.DataFrame({'Date':yearly_data[year]['days_of_year'], 'GRVI':yearly_data[year]['grvi_values']})
    df['Moving_Average'] = df['GRVI'].rolling(window=3).mean() 
    df['GRVI_3DayMA'] = df['GRVI'].rolling(window=3).mean()
    #ax1.scatter(df['Date'].to_numpy(), df['GRVI'].to_numpy(), color=c, label=str(year))
    ax1.plot(df['Date'].to_numpy(), df['GRVI_3DayMA'].to_numpy(), label=str(year), linewidth=2, color=c)

#for i in range(10, 370, 10):
    #plt.vlines(i, -0.6, 0.6, color='black', alpha=0.3)

# Add horizontal lines for GRVI=0
ax1.axhline(y=0, color='black', linewidth=0.8)

# Add vertical lines for months
month_days = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
for i, day_value in enumerate(month_days):
    ax1.axvline(x=day_value, color='black', linestyle='--', linewidth=0.8)

# Add month label
month_days = [16, 45, 74, 105, 135, 166, 196, 228, 259, 289, 319, 350]
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
for i, day_value in enumerate(month_days):
    ax1.text(day_value - 0.5, 0.28, month_names[i], ha='center', va='top', fontsize=20) #default=15

ax1.set_xlim(0, 365) 
ax1.set_ylim(-0.3,0.3) 
ax1.set_xlabel('DOY (Day of Year)', fontsize=20)
ax1.set_ylabel('GRVI', fontsize=20) #default=14
ax1.set_title(' your title of this figure', fontstyle='italic', fontsize=16)
plt.xticks(fontsize=16) 
plt.yticks(fontsize=16) 
plt.minorticks_on() 


#plt.legend(bbox_to_anchor=(0.5, -0.1), loc='lower center', ncol=7, borderaxespad=-5, fontsize=16, edgecolor='black') #default=10
#ax1.xaxis.grid(False)

fig.tight_layout()
plt.savefig("path to your output directory", dpi=300)
plt.show()
