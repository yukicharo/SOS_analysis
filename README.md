# SOS_analysis

#My environment

#OS: Ubuntu22.04 LTS

#For pre-processing of satellite data, you need to run scripts as following:

#1. Download SGLI data from GPortal

$ for y in `seq 18 24`; do for m in `seq -w 1 12`; do for d in `seq -w 1 31`; do for t in 0427 0428 0528 0529; do wget -c --user=username --password=anonymous ftp://ftp.gportal.jaxa.jp/standard/GCOM-C/GCOM-C.SGLI/L2.LAND.RSRF/3/20${y}/${m}/${d}/GC1SG1_20${y}${m}??D01D_T${t}_L2SG_RSRFQ_300*.h5; done; done; done; done

#2. Reproject, Convert from h5 to tif

#Before do this, you have to move "SGLI_geo_map_linux.exe" to same directory

#You need to change "/Image_data/dataset" 

#You can show included datase.>h5dump -n filename.h5

$ for m in `seq -w 1 31`; do for t in T0427 T0428 T0528 T0529; do ./SGLI_geo_map_linux.exe GC1SG1_2023${m}${d}_${t}.h5 -d /Image_data/dataset -r NN; done; done

#3. Merge each tiles to 1 image

$ for y in `seq 18 23`; do for m in `seq -w 1 12`; do for d in `seq -w 1 31`; do gdal_merge.py GC*20${y}${m}${d}*_Rs_VN05.tif -o merge_20${y}${m}${d}_VN05.tif -n 65535 -a_nodata 65535; done; done; done

#After this, you can run 4_GCOM_add_pixel.py, 5_GCOM_Cloud_Cover.py, 6_GCOM_extract_vegetation.py, 7_GCOM_region_cut.py and 8_GCOM_SOS_DOY.py.

#If you want to calculate anomalies, you can run script to calculate its anomalies.

#If you want to calculate spatial mean, you can run script to calculate its spatial mean value.


#For making timeseries of DC_GRVI, you can run "DC_GRVI_timeseries.py".

#For making timeseries of CCI derived from GCOM-C/SGLI, you can run "SGLI_CCI_timeseries.py".
