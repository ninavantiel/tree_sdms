from time import sleep
import multiprocessing
import sys
import os
import pandas as pd
from functools import partial
from contextlib import contextmanager
import ee
ee.Initialize()

treemap_dir = 'projects/crowtherlab/nina/treemap'
sampled_data_dir = treemap_dir + '/sampled_data_test'

species_occurence_fc = treemap_dir + '/treemap_data_all_species'
composite_to_sample = treemap_dir + '/composite_to_sample'
