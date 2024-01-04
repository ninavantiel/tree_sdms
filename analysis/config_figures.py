import os
import sys
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import seaborn as sns
from math import ceil
import random
import time
from time import sleep
from functools import partial
from contextlib import contextmanager
import multiprocessing
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import ee

try: ee.Initialize()
except: sys.exit('ERROR starting earthengine python API')

#google drive
google_drive_folder = 'treemap'

# earthengine assets
earthengine_folder = 'projects/crowtherlab/nina/treemap/'

covariate_img = ee.Image(earthengine_folder + 'composite_to_sample')
all_sdms = ee.ImageCollection('projects/crowtherlab/nina/treemap/sdms_binary')
sdms = all_sdms.filter(ee.Filter.gte('nobs',90))
scale_to_use = sdms.first().projection().nominalScale()
sdm_bboxes = ee.FeatureCollection('users/ninavantiel/treemap/sdms_bbox').filter(ee.Filter.inList('species', sdms.aggregate_array('system:index')))

sdm_sum_filename = 'sdm_sum_equal_area'
sdm_sum_folder = 'projects/crowtherlab/nina/treemap_figures/'
sdm_sum = ee.Image(sdm_sum_folder + sdm_sum_filename)

FAO_countries = ee.FeatureCollection("FAO/GAUL/2015/level0")
mhs_ic = ee.ImageCollection('users/johanvandenhoogen/2023_tree_sdms/mhs')

ecoregions = ee.FeatureCollection(earthengine_folder + 'Ecoregions')
biome_image = ecoregions.reduceToImage(['BIOME_NUM'], ee.Reducer.first())
biome_dictionary = ee.Dictionary.fromLists(ecoregions.distinct('BIOME_NUM').aggregate_array('BIOME_NAME'), ecoregions.distinct('BIOME_NUM').aggregate_array('BIOME_NUM'))

ordinations_folder = 'users/ninavantiel/treemap/ordinations/'
nmds = ee.FeatureCollection(ordinations_folder + 'nmds_equal_area')#'nmds_scale_mult_100')
evopca = ee.FeatureCollection(ordinations_folder + 'evopca_equal_area')#'evopca_scale_mult_100')
nmds_evopca_fc_filename = 'nmds_evopca_equal_area_fc'
nmds_evopca_fc = ee.FeatureCollection(ordinations_folder + nmds_evopca_fc_filename)
nmds_evopca_cluster_fc = ee.FeatureCollection(ordinations_folder + 'ordinations_equal_area_cluster') 

unbounded_geo = ee.Geometry.Polygon([-180, 88, 0, 88, 180, 88, 180, -88, 0, -88, -180, -88], None, False)

# equal area projection for community level analyses
wkt6933 = '   PROJCS["WGS 84 / NSIDC EASE-Grid 2.0 Global",       GEOGCS["WGS 84",           DATUM["WGS_1984",               SPHEROID["WGS 84",6378137,298.257223563]],           PRIMEM["Greenwich",0],           UNIT["degree",0.0174532925199433,               AUTHORITY["EPSG","9122"]],           AUTHORITY["EPSG","4326"]],       PROJECTION["Cylindrical_Equal_Area"],       PARAMETER["standard_parallel_1",30],       PARAMETER["central_meridian",0],       PARAMETER["False_easting",0],       PARAMETER["False_northing",0],       UNIT["metre",1],       AXIS["Easting",EAST],       AXIS["Northing",NORTH],       AUTHORITY["EPSG","6933"]]'
proj6933 = ee.Projection(wkt6933)

sdms_area_lat_elev_filename = 'sdms_area_lat_elev'
sdms_area_lat_elev_folder = 'users/ninavantiel/treemap/range_size/'
sdms_area_lat_elev_fc = ee.FeatureCollection(sdms_area_lat_elev_folder + sdms_area_lat_elev_filename)

forest10_image = ee.Image('projects/crowtherlab/nina/treemap_figures/hansen_year2000').gte(10) 
elevation = ee.Image('projects/crowtherlab/nina/treemap_figures/elevation_img') # https://www.earthenv.org/topography
splot_data = ee.FeatureCollection('users/ninavantiel/treemap/sPlot_comparison/sPlot_data')
splot_sample_folder = 'users/ninavantiel/treemap/sPlot_comparison/splot_sdm/'
sdm_biome_drive_filename = 'sdm_biomes'

# local directories and files
datadir = '/Users/nina/Documents/treemap/treemap/data/'
figuredir = '/Users/nina/Documents/treemap/treemap/figures/'

validation_stats_file = datadir + 'sdm_stats_validation.csv'
sdm_splot_file = datadir + 'sdm_splot_comparison.csv'
sdm_mhs_iou_file = datadir + 'SDM_MHS_IoU.csv'
nmds_evopca_covariates_file = datadir + 'nmds_evopca_covariates_equal_area.csv'
sdms_area_lat_elev_file = datadir + sdms_area_lat_elev_filename + '.csv'
sdm_biome_drive_file = datadir + sdm_biome_drive_filename + '.csv'

sample_ecoregion_dir = datadir + 'ecoregion_species_composition/'
sample_ecoregion_file = datadir + 'ecoregion_species_sampled.csv'
ecoregion_nmds_file = datadir + 'nmds_3d_ecoregions_current_future.csv'
ecoregion_nmds_eucl_dist_file = datadir + 'nmds_current_future_eucl_dist.csv'
ecoregion_evopca_file = datadir + 'evopca_ecoregions_current_future_df.csv'
ecoregion_evopca_eucl_dist_file = datadir + 'evoPCA_current_future_eucl_dist.csv'
climate_change_ecoregion_file = datadir + 'climate_change_ecoregion_df.csv'

#function masking SDM pixels equal to 0 and pixels that are less than 50% within the SDM range (clipped)
def mask_sdm(sdm): return sdm.mask(sdm.mask().gte(0.5)).selfMask()
def unmask_mask(img): return img.mask(img.mask().gte(0.5)).unmask(0, False)

#export functions
def export_table_to_drive(fc, filename):
	export = ee.batch.Export.table.toDrive(
		collection = fc,
		description = filename,
		folder = google_drive_folder
	)
	export.start()

def export_table_to_asset(fc, filename, folder=earthengine_folder):
	export = ee.batch.Export.table.toAsset(
		collection = fc,
		description = filename,
		assetId = folder + filename
	)
	export.start()

def export_image_to_asset(image, filename, folder=earthengine_folder):
	export = ee.batch.Export.image.toAsset(
		image = image,
		description = filename,
		assetId = earthengine_folder + filename,
		crs = 'EPSG:4326',
		crsTransform = '[0.008333333333333333,0,-180,0,-0.008333333333333333,90]',
		region = unbounded_geo,
		maxPixels = int(1e13))
	export.start()

def export_image_to_drive(image, filename):
	export = ee.batch.Export.image.toDrive(
		image = image,
		description = filename,
		folder = google_drive_folder,
		crs = 'EPSG:4326',
		crsTransform = '[0.008333333333333333,0,-180,0,-0.008333333333333333,90]',
		region = unbounded_geo,
		maxPixels = int(1e13))
	export.start()