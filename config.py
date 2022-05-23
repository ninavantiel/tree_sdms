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
prepped_points_dir = treemap_dir + '/prepped_points_test' 

species_occurence_fc = treemap_dir + '/treemap_data_all_species'
composite_to_sample = treemap_dir + '/composite_to_sample'

model_covariate_names = ['coarse_fragments', 'silt_content', 'soil_ph', 'bio12', 'bio15', 'bio1', 'bio4', 'gsl', 'npp']



