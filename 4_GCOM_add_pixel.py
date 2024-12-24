#2024/06/20
#Written by Yuki Mizuno
#In some cases, satellite data shape (size) is diffrence from each other after marging.
#So, in this script, you can reshape tif files based on model file.
#You can download model tile from same page.

from osgeo import gdal, ogr, osr
import os
import glob

# model tif file
reference_file = "/path/to/your/directory/JPN_merge_20240531_QA_flag.tif"

input_directory = "path to directory which contains satellite data"
output_directory = "path to directory for outputs"

os.makedirs(output_directory, exist_ok=True)

def get_extent_latlon(reference_file):
    dataset = gdal.Open(reference_file)
    geotransform = dataset.GetGeoTransform()
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize

    extent = [
        (geotransform[0], geotransform[3]),  #  (xmin, ymax)
        (geotransform[0] + cols * geotransform[1], geotransform[3]),  #  (xmax, ymax)
        (geotransform[0], geotransform[3] + rows * geotransform[5]),  # (xmin, ymin)
        (geotransform[0] + cols * geotransform[1], geotransform[3] + rows * geotransform[5])  #  (xmax, ymin)
    ]

    source_proj = osr.SpatialReference()
    source_proj.ImportFromWkt(dataset.GetProjection())

    target_proj = osr.SpatialReference()
    target_proj.ImportFromEPSG(4326)
    transform = osr.CoordinateTransformation(source_proj, target_proj)

    latlon_extent = [transform.TransformPoint(x, y)[:2] for x, y in extent]
    return latlon_extent

latlon_extent = get_extent_latlon(reference_file)
xmin, ymin = min(pt[0] for pt in latlon_extent), min(pt[1] for pt in latlon_extent)
xmax, ymax = max(pt[0] for pt in latlon_extent), max(pt[1] for pt in latlon_extent)
print(f"Clipping extent: xmin={xmin}, ymin={ymin}, xmax={xmax}, ymax={ymax}")


def clip_to_reference(input_file, output_file, reference_file):
    try:
      
        gdal.Warp(
            output_file,
            input_file,
            outputBounds=(xmin, ymin, xmax, ymax), 
            dstSRS="EPSG:4326" 
        )
        print(f"Clipped: {input_file} -> {output_file}")
    except Exception as e:
        print(f"Error clipping {input_file}: {e}")


tif_files = glob.glob(os.path.join(input_directory, "*.tif"))


for tif_file in tif_files:
    file_name = os.path.basename(tif_file)
    output_file = os.path.join(output_directory, file_name)
    clip_to_reference(tif_file, output_file, reference_file)

print("All files have been clipped.")
