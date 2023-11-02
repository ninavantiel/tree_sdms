import sys
sys.path.insert(0, '/Users/nina/Documents/treemap/treemap/analysis')
from config_figures import *

sdms = ee.ImageCollection('projects/crowtherlab/nina/treemap/sdms_binary')

if __name__ == '__main__':
	sdm_stats = sdms.map(lambda sdm: ee.Feature(None, sdm.toDictionary()))
	export_table_to_drive(sdm_stats, 'sdm_stats_validation')
