import pandas as pd 
import numpy as np
import subprocess
import math
import sys
from heapq import nlargest
import ee

# uncomment following 3 lines and comment the next line to use service account
#service_account = 'crowther-gee@gem-eth-analysis.iam.gserviceaccount.com'
#credentials = ee.ServiceAccountCredentials(service_account, '/Users/ninavantiel/Desktop/gem-eth-analysis-6bdd65390597.json')
#ee.Initialize(credentials)
ee.Initialize()

# full path to earthengine package (find by typing "which earthengine" in the command line)
earthengine = '/usr/local/Caskroom/miniconda/base/bin/earthengine' 

# read species list
species_list = set(pd.read_csv('species_list_trees_full.csv', header=None)[0])

sampled_covariates_names = [
 'SG_Coarse_fragments_005cm', 'SG_Silt_Content_005cm', 'SG_Soil_pH_H2O_005cm', 'CHELSA_bio12_1981_2010_V2_1', 'CHELSA_bio15_1981_2010_V2_1', 
 'CHELSA_bio1_1981_2010_V2_1', 'CHELSA_bio4_1981_2010_V2_1', 'CHELSA_gsl_1981_2010_V2_1', 'CHELSA_npp_1981_2010_V2_1'
]
model_covariate_names = ['coarse_fragments', 'silt_content', 'soil_ph', 'bio12', 'bio15', 'bio1', 'bio4', 'gsl', 'npp']

thresholds = ee.List.sequence(0, 1, None, 100)

treemap_dir = 'projects/crowtherlab/nina/treemap' 

sampled_data_dir = treemap_dir + '/sampled_data'
obs_points_dir = treemap_dir + '/points' 
obs_range_dir = treemap_dir + '/ranges' 
test_class_dir = treemap_dir +  '/cv_classifications'
sdm_coll = treemap_dir + '/sdms_binary' 

native_regions_table = ee.FeatureCollection(treemap_dir + '/GlobalTreeSearch') 
region_geo_buffer = ee.FeatureCollection(treemap_dir + '/country_geometries_with_buffer') 
ecoregions = ee.FeatureCollection(treemap_dir + '/Ecoregions')
pseudoabsences = ee.FeatureCollection(treemap_dir + '/pseudoabsences_1m_sampled').map(
	lambda f: f.select(sampled_covariates_names + ['presence'], model_covariate_names + ['presence']))

covariate_imgs = ee.ImageCollection(treemap_dir + '/covariate_avg_imgs').filter(ee.Filter.inList('system:index', [
  'covariates_1981_2010',
  'covariates_2011_2040_ssp126',
  'covariates_2011_2040_ssp370',
  'covariates_2011_2040_ssp585',
  'covariates_2041_2070_ssp126',
  'covariates_2041_2070_ssp370',
  'covariates_2041_2070_ssp585',
  'covariates_2071_2100_ssp126',
  'covariates_2071_2100_ssp370',
  'covariates_2071_2100_ssp585'
]))

unbounded_geo = ee.Geometry.Polygon([-180, 88, 0, 88, 180, 88, 180, -88, 0, -88, -180, -88], None, False)

models = ee.List([
    ee.List([ee.Classifier.smileRandomForest(numberOfTrees = 500, bagFraction = 0.632, minLeafPopulation = 10).setOutputMode('PROBABILITY'), 'RF_simple']),
    ee.List([ee.Classifier.smileRandomForest(numberOfTrees = 500, bagFraction = 0.632, minLeafPopulation = 3).setOutputMode('PROBABILITY'), 'RF_interm']),
    ee.List([ee.Classifier.smileGradientTreeBoost(numberOfTrees = 500, shrinkage = 0.005, maxNodes = 20).setOutputMode('PROBABILITY'), 'GBM_simple']),
    ee.List([ee.Classifier.smileGradientTreeBoost(numberOfTrees = 1000, shrinkage = 0.005, maxNodes = 20).setOutputMode('PROBABILITY'), 'GBM_interm']),
])

def export_image(image, description, asset_id):
	export = ee.batch.Export.image.toAsset(
		image = image,
		description = description,
		assetId = asset_id,
		crs = 'EPSG:4326',
		crsTransform = '[0.008333333333333333,0,-180,0,-0.008333333333333333,90]',
		region = unbounded_geo,
		maxPixels = int(1e13))
	export.start()
	print('Export started for ' + asset_id)


def export_fc(fc, description, asset_id):
	export = ee.batch.Export.table.toAsset(
		collection = fc,
		description = description,
		assetId = asset_id)
	export.start()
	print('Export started for ' + asset_id)

def prep_training_data(obs_points, pa_pool, max_points = 20000):
	max_obs = max_points / 2

	nobs_points = obs_points.size().getInfo()
	npa_pool = pa_pool.size().getInfo()
	print(f"{nobs_points} observations, {npa_pool} pseudoabsences available")

	if nobs_points >= max_obs:  
		if npa_pool >= max_obs: 
			obs_points = obs_points.randomColumn().limit(max_obs, 'random')
			pa_points = pa_pool.randomColumn().limit(max_obs, 'random')

		else:
			pa_points = pa_pool			
			obs_points = obs_points.randomColumn().limit(npa_pool, 'random')

	elif nobs_points >= max_points / 11: 
		if npa_pool >= max_points - nobs_points:
			pa_points = pa_pool.randomColumn().limit(max_obs-nobs_points, 'random')
	
		else:
			pa_points = pa_pool
			obs_points = obs_points.randomColumn().limit(npa_pool, 'random')
			
	elif nobs_points >= 500: 
		if npa_pool >= nobs_points / 10: 
			pa_points = pa_pool.randomColumn().limit(nobs_points*10, 'random')
			
		else:
			pa_points = pa_pool
			obs_points = obs_points.randomColumn().limit(int(npa_pool/10), 'random')

	else:
		pa_points = pa_pool.randomColumn().limit(5000, 'random')

	nobs = obs_points.size().getInfo()
	npa = pa_points.size().getInfo()
	training_data = obs_points.merge(pa_points).randomColumn()
	print(f"{nobs} observations, {npa} pseudoabsences selected")

	return [nobs, npa, training_data]




