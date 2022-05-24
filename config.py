from time import sleep
import multiprocessing
import sys
import os
import pandas as pd
from functools import partial
from contextlib import contextmanager
import ee
ee.Initialize()

# Minimum number of points to run scripts
# Used in 1_sampled_covariates, 2_occurrence_preparation
min_n_points = 20

treemap_dir = 'projects/crowtherlab/nina/treemap'
sampled_data_dir = treemap_dir + '/sampled_data_test'
prepped_occurrences_dir = treemap_dir + '/prepped_points_test' 
range_dir = treemap_dir + '/ranges_test' 

species_occurence_fc = treemap_dir + '/treemap_data_all_species'
composite_to_sample = treemap_dir + '/composite_to_sample'
native_countries_fc = treemap_dir + '/GlobalTreeSearch'
countries_geometries = treemap_dir + '/country_geometries_with_buffer'
ecoregions = treemap_dir + '/Ecoregions'

#pseudoabsences = ee.FeatureCollection(treemap_dir + '/pseudoabsences_1m_sampled').map(
#	lambda f: f.select(sampled_covariates_names + ['presence'], model_covariate_names + ['presence']))

model_covariate_names = ['coarse_fragments', 'silt_content', 'soil_ph', 'bio12', 'bio15', 'bio1', 'bio4', 'gsl', 'npp']

def export_fc(fc, description, asset_id):
	export = ee.batch.Export.table.toAsset(
		collection = fc,
		description = description,
		assetId = asset_id)
	export.start()
	print('Export started for ' + asset_id)

if __name__ == '__main__':
	var_name = sys.argv[1]
	print(globals()[var_name])

