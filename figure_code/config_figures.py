# import os
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt

import ee
try: ee.Initialize()
except: sys.exit('ERROR starting earthengine python API')

#google drive
google_drive_folder = 'treemap'
google_drive_path = '~/Google Drive/My Drive/' + google_drive_folder

#earthengine assets
earthengine_folder = 'users/ninavantiel/treemap/'

sdms = ee.ImageCollection('projects/crowtherlab/nina/treemap/sdms_binary').filter(ee.Filter.gte('nobs',90))
sdm_bboxes = ee.FeatureCollection(earthengine_folder + 'sdms_bbox') 
scale_to_use = sdms.first().projection().nominalScale()
forest_image = ee.Image('projects/crowtherlab/nina/treemap_figures/hansen_year2000').gte(10) # current forests = Hansen et al. tree cover in 2010 >= 10% 
ecoregions = ee.FeatureCollection('projects/crowtherlab/nina/treemap/Ecoregions')
biome_image = ecoregions.reduceToImage(['BIOME_NUM'], ee.Reducer.first())
biome_dictionary = ee.Dictionary.fromLists(ecoregions.distinct('BIOME_NUM').aggregate_array('BIOME_NAME'), ecoregions.distinct('BIOME_NUM').aggregate_array('BIOME_NUM'))
elevation = ee.Image('projects/crowtherlab/nina/treemap_figures/elevation_img') # https://www.earthenv.org/topography
unbounded_geo = ee.Geometry.Polygon([-180, 88, 0, 88, 180, 88, 180, -88, 0, -88, -180, -88], None, False)

#filenames
sdms_area_lat_elev_drive_filename = 'sdms_area_latitude_elevation'
sdms_area_lat_elev_asset_filename = 'sdms_area_latitude_elevation_fc'
sdms_area_lat_elev_fc = ee.FeatureCollection(earthengine_folder + sdms_area_lat_elev_asset_filename)

sdms_forest_area_lat_elev_drive_filename = 'sdms_forest_area_latitude_elevation'
sdms_forest_area_lat_elev_asset_filename = 'sdms_forest_area_latitude_elevation_fc'
sdms_forest_area_lat_elev_fc = ee.FeatureCollection(earthengine_folder + sdms_forest_area_lat_elev_asset_filename)

#function masking SDM pixels equal to 0 and pixels that are less than 50% within the SDM range (clipped)
def mask_sdm(sdm): return sdm.mask(sdm.mask().gte(0.5)).selfMask()

#export functions
def export_table_to_drive(fc, filename):
	export = ee.batch.Export.table.toDrive(
		collection = fc,
		description = filename,
		folder = google_drive_folder
	)
	export.start()

def export_table_to_asset(fc, filename):
	export = ee.batch.Export.table.toAsset(
		collection = fc,
		description = filename,
		assetId = earthengine_folder + filename

	)
	export.start()

def export_image_to_asset(image, filename):
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