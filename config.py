from time import sleep
import multiprocessing
import sys
import os
import random
import math
from heapq import nlargest
import pandas as pd
from functools import partial
from contextlib import contextmanager
import ee

try: ee.Initialize()
except: sys.exit('ERROR starting earthengine python API')

# Minimum number of points to run scripts
min_n_points = 20

# Number of psuedoabsences to generate in 0_generate_pseudoabsences.py
n_pseudoabsences = 100#1e6

# number of folds for k-fold cross validation 
k = 3

# google cloud storage bucket path for sampled data
bucket_path = 'gs://nina_other_bucket'

# local directory paths
sampled_data_localdir = '../sampled_data'
merged_data_localdir = '../merged_data'
sampled_pseudoabsences_localdir = '../sampled_pseudoabsences_test/'
merged_pseudoabsences_filepath = '../pseudoabsences_test.csv'

# directory and file paths in google earthengine
treemap_dir = 'projects/crowtherlab/nina/treemap'
sampled_data_dir = treemap_dir + '/sampled_data_test'
prepped_occurrences_dir = treemap_dir + '/prepped_points_test' 
range_dir = treemap_dir + '/ranges_test' 
cross_validation_dir = treemap_dir + '/cross_validation_test'

species_occurence_fc = treemap_dir + '/treemap_data_all_species'
composite_to_sample = treemap_dir + '/composite_to_sample'
native_countries_fc = treemap_dir + '/GlobalTreeSearch'
countries_geometries = treemap_dir + '/country_geometries_with_buffer'
ecoregions = treemap_dir + '/Ecoregions'
pseudoabsences = treemap_dir + '/pseudoabsences'

model_covariate_names = ['coarse_fragments', 'silt_content', 'soil_ph', 'bio12', 'bio15', 'bio1', 'bio4', 'gsl', 'npp']
models = ee.Dictionary({
	'RF_simple': ee.Classifier.smileRandomForest(numberOfTrees = 500, bagFraction = 0.632, minLeafPopulation = 10).setOutputMode('PROBABILITY'),
	'RF_interm': ee.Classifier.smileRandomForest(numberOfTrees = 500, bagFraction = 0.632, minLeafPopulation = 3).setOutputMode('PROBABILITY'), 
	'GBM_simple': ee.Classifier.smileGradientTreeBoost(numberOfTrees = 500, shrinkage = 0.005, maxNodes = 20).setOutputMode('PROBABILITY'), 
	'GBM_interm': ee.Classifier.smileGradientTreeBoost(numberOfTrees = 1000, shrinkage = 0.005, maxNodes = 20).setOutputMode('PROBABILITY')
})
unbounded_geo = ee.Geometry.Polygon([[[-180, 88], [180, 88], [180, -88], [-180, -88]]], None, False)

def export_fc(fc, description, asset_id):
	export = ee.batch.Export.table.toAsset(
		collection = fc,
		description = description,
		assetId = asset_id)
	export.start()
	print('Export started for ' + asset_id)

def generate_training_data(occurrences, pseudoabsences, max_n = 20000):
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
	return [n_occ, n_pa, training_data]

if __name__ == '__main__':
	var_name = sys.argv[1]
	print(globals()[var_name])

