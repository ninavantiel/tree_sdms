try:
	from time import sleep
	import multiprocessing
	import sys
	import os
	import random
	import math
	from heapq import nlargest
	import subprocess
	import pandas as pd
	from functools import partial
	from contextlib import contextmanager
	import ee
except ImportError: sys.exit('Not all packages are installed. \n Packages: time, multiprocessing, sys, os, random, math, heapq, subprocess, pandas, functools, contextlib, ee')

try: ee.Initialize()
except: sys.exit('ERROR starting earthengine python API')

earthengine = subprocess.run(['which', 'earthengine'], stdout=subprocess.PIPE).stdout.decode('utf-8').replace('\n','')

# google cloud storage bucket path for sampled data
bucket_path = 'gs://nina_other_bucket'

# local directory paths
sampled_data_localdir = 'data/sampled_data'
merged_data_localdir = 'data/merged_data'
sampled_pseudoabsences_localdir = 'data/sampled_pseudoabsences/'
merged_pseudoabsences_filepath = 'data/pseudoabsences.csv'

# directory and file paths in google earthengine
treemap_dir = 'projects/crowtherlab/nina/treemap'

sampled_data_dir = treemap_dir + '/sampled_data_test'
prepped_occurrences_dir = treemap_dir + '/prepped_points_test' 
range_dir = treemap_dir + '/ranges_test' 
cross_validation_dir = treemap_dir + '/cross_validation_test'
sdm_img_col = treemap_dir + '/sdms_test'

species_occurence_fc = treemap_dir + '/treemap_data_all_species'
composite_to_sample = treemap_dir + '/composite_to_sample'
native_countries_fc = treemap_dir + '/GlobalTreeSearch'
countries_geometries = treemap_dir + '/country_geometries_with_buffer'
ecoregions = treemap_dir + '/Ecoregions'
pseudoabsence_fc = treemap_dir + '/pseudoabsences'
covariate_img_col = treemap_dir + '/covariate_avg_imgs'

model_covariate_names = ['coarse_fragments', 'silt_content', 'soil_ph', 'bio12', 'bio15', 'bio1', 'bio4', 'gsl', 'npp']
models = ee.Dictionary({
	'RF_simple': ee.Classifier.smileRandomForest(numberOfTrees = 500, bagFraction = 0.632, minLeafPopulation = 10).setOutputMode('PROBABILITY'),
	'RF_interm': ee.Classifier.smileRandomForest(numberOfTrees = 500, bagFraction = 0.632, minLeafPopulation = 3).setOutputMode('PROBABILITY'), 
	'GBM_simple': ee.Classifier.smileGradientTreeBoost(numberOfTrees = 500, shrinkage = 0.005, maxNodes = 20).setOutputMode('PROBABILITY'), 
	'GBM_interm': ee.Classifier.smileGradientTreeBoost(numberOfTrees = 1000, shrinkage = 0.005, maxNodes = 20).setOutputMode('PROBABILITY')
})
unbounded_geo = ee.Geometry.Polygon([[[-180, 88], [180, 88], [180, -88], [-180, -88]]], None, False)

min_n_points = 20 # Minimum number of points to run scripts
n_pseudoabsences = 1e6 # Number of psuedoabsences to generate in 0_generate_pseudoabsences.py
k = 3 # Number of folds for k-fold cross validation 
thresholds = ee.List.sequence(0, 1, None, 100) # thresholds to test for optimal threshold testing

def export_fc(fc, description, asset_id):
	export = ee.batch.Export.table.toAsset(
		collection = fc,
		description = description,
		assetId = asset_id)
	export.start()
	print('Export started for ' + asset_id)

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

def prepare_training_data(species, max_n = 20000):
	# Get range and occurrences filtered to range
	species_range = ee.FeatureCollection(range_dir + '/' + species).geometry()
	occurrences = ee.FeatureCollection(prepped_occurrences_dir + '/' + species).filterBounds(species_range).map(
		lambda f: f.select(model_covariate_names + ['presence']))
	n_points = occurrences.size().getInfo()

	# If less than min_n_points occurences, species will not be modelled
	if n_points < min_n_points :
		print(f"Less than {min_n_points} occurrences -> no modelling")
		return 'EXIT', None, None
	
	# Get pseudoabsences points in range
	pseudoabsences = ee.FeatureCollection(pseudoabsence_fc).filterBounds(species_range)

	# Prepare training data for modelling: subsample observations and/or pseudoabsences depending on number of points available
	# A random number property is added to each feature for selection of folds for k-fold cross validation
	max_occ = max_n / 2
	n_occ = occurrences.size().getInfo()
	n_pa = pseudoabsences.size().getInfo()
	print(f"{n_occ} occurrences, {n_pa} pseudoabsences available")

	if n_occ >= max_occ:  
		if n_pa >= max_occ: n_occ_sample, n_pa_sample = max_occ, max_occ
		else: n_occ_sample, n_pa_sample = n_pa, n_pa
	elif n_occ >= max_n / 11: 
		if n_pa >= max_n - n_occ: n_occ_sample, n_pa_sample = n_occ, max_n - n_occ
		else: n_occ_sample, n_pa_sample = n_pa, n_pa
	elif n_occ >= 500: 
		if n_pa >= n_occ / 10: n_occ_sample, n_pa_sample = n_occ, n_occ * 10
		else: n_occ_sample, n_pa_sample = n_pa / 10, n_pa
	else: n_occ_sample, n_pa_sample = n_occ, 5000

	occurrences = occurrences.randomColumn().limit(n_occ_sample, 'random')
	pseudoabsences = pseudoabsences.randomColumn().limit(n_pa_sample, 'random')

	n_occ = occurrences.size().getInfo()
	n_pa = pseudoabsences.size().getInfo()
	training_data = occurrences.merge(pseudoabsences).randomColumn()
	print(f"{n_occ} observations, {n_pa} pseudoabsences selected")

	# If there are less than 90 observations, select subset of covariates based on variable importance in simple random forest model
	if n_occ < 90:
		n_cov = math.floor(n_occ/10)
		var_imp = ee.Classifier(models.get('RF_simple')).train(training_data, 'presence', model_covariate_names).explain().get('importance').getInfo()
		covariates = nlargest(n_cov, var_imp, key = var_imp.get)
		print(f"Less than 90 observations, {n_cov} covariates selected: {covariates}")
	# If there are at least 90 observations, keep all covariates
	else: covariates = model_covariate_names

	return training_data, n_occ, n_pa, covariates, species_range

if __name__ == '__main__':
	if len(sys.argv) > 1:
		var_name = sys.argv[1]
		print(globals()[var_name])

