# packages
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

# Initialize Google Earth Engine (GEE)
try: ee.Initialize()
except: sys.exit('ERROR starting earthengine python API')
earthengine = subprocess.run(['which', 'earthengine'], stdout=subprocess.PIPE).stdout.decode('utf-8').replace('\n','')

# Path to Google Cloud Storage Bucket to upload sampled data to
bucket_path = 'gs://path/to/GCS/bucket' # ** CHANGE THIS TO YOUR GCS BUCKET NAME **

# Paths to local directories for 
# - sampled data
# - file with merged sampled data for each species 
# - sampled pseudoabsences 
# ** CHANGE TO YOUR LOCAL DIRECTORIES **
sampled_data_localdir = 'data/sampled_data' 
merged_data_localdir = 'data/merged_data'
sampled_pseudoabsences_localdir = 'data/sampled_pseudoabsences/'
# Path to local file for merged sampled pseudoabsences
merged_pseudoabsences_filepath = 'data/pseudoabsences.csv'

# GEE paths to folders and assets
# Main folder 
treemap_dir = 'path/to/your/gee/folder' # ** CHANGE THIS TO THE PATH TO YOUR GEE FOLDER **
# Folder for FeatureCollections of sampled data for each species
sampled_data_dir = treemap_dir + '/sampled_data'
# Folder for FeatureCollections of prepared occurrence data for each species
prepped_occurrences_dir = treemap_dir + '/prepped_points' 
# Folder for FeatureCollections of geographic range polygons for each species
range_dir = treemap_dir + '/ranges' 
# Folder for FeatureCollections of predictions for model cross-validation for each species
cross_validation_dir = treemap_dir + '/cross_validation'
# ImageCollection for final SDM output images
sdm_img_col = treemap_dir + '/sdms'
# FeatureCollection containing raw occurrence data for all species
species_occurence_fc = treemap_dir + '/treemap_data_all_species'
# Multi-band Image containing model covariates and auxiliary variables:
# absolute latitude, pixel latitude and longitude, biome and ecoregion
composite_to_sample = treemap_dir + '/composite_to_sample'
# FeatureCollection containing native countries for each species
native_countries_fc = treemap_dir + '/GlobalTreeSearch'
# FeatureCollection containing geometries of countries with 1000km buffer
countries_geometries = treemap_dir + '/country_geometries_with_buffer'
# FeatureCollection containing ecoregions and biomes
ecoregions = treemap_dir + '/Ecoregions'
# FeatureCollection containing pseudoabsences with sampled model covariates
pseudoabsence_fc = treemap_dir + '/pseudoabsences'
# ImageCollection containing Images with sets of model covariates for SDM predictions
covariate_img_col = treemap_dir + '/covariate_avg_imgs'

# List of model covariate names
model_covariate_names = ['coarse_fragments', 'silt_content', 'soil_ph', 'bio12', 'bio15', 'bio1', 'bio4', 'gsl', 'npp']
# Minimum number of points to run scripts
min_n_points = 20 
# Number of psuedoabsences to generate in 0_generate_pseudoabsences.py
n_pseudoabsences = 1e6 
# Number of folds for k-fold cross validation 
k = 3

# GEE Dictionary of models (GEE Classifiers) to use in ensemble model
models = ee.Dictionary({
	'RF_simple': ee.Classifier.smileRandomForest(numberOfTrees = 500, bagFraction = 0.632, minLeafPopulation = 10).setOutputMode('PROBABILITY'),
	'RF_interm': ee.Classifier.smileRandomForest(numberOfTrees = 500, bagFraction = 0.632, minLeafPopulation = 3).setOutputMode('PROBABILITY'), 
	'GBM_simple': ee.Classifier.smileGradientTreeBoost(numberOfTrees = 500, shrinkage = 0.005, maxNodes = 20).setOutputMode('PROBABILITY'), 
	'GBM_interm': ee.Classifier.smileGradientTreeBoost(numberOfTrees = 1000, shrinkage = 0.005, maxNodes = 20).setOutputMode('PROBABILITY')
})
# GEE Geometry of considered region (we used a global, unbounded geometry)
unbounded_geo = ee.Geometry.Polygon([[[-180, 88], [180, 88], [180, -88], [-180, -88]]], None, False)
# GEE List of thresholds to test for optimal binarization threshold 
thresholds = ee.List.sequence(0, 1, None, 100) 
 
 # Function to export FeatureCollection to asset
def export_fc(fc, description, asset_id):
	export = ee.batch.Export.table.toAsset(
		collection = fc,
		description = description,
		assetId = asset_id)
	export.start()
	print('Export started for ' + asset_id)

# Function to export Image to asset
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

# Function to prepare training data for modelling (used in p4_cross_validation.py and p5_sdm_mapping.py)
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

