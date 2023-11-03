import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
from config_figures import *

if __name__ == '__main__':
	sdm_stats = all_sdms.map(lambda sdm: ee.Feature(None, sdm.toDictionary()))
	export_table_to_drive(sdm_stats, 'sdm_stats_validation')
