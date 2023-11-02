import sys
sys.path.insert(0, '/Users/nina/Documents/treemap/treemap/analysis')
from config_figures import *

if __name__ == '__main__':
	sdm_sum = sdms.map(
		lambda sdm: unmask_mask(sdm.select(['covariates_1981_2010']))
	).sum().toFloat()
	export_image_to_asset(sdm_sum, sdm_sum_filename, folder=sdm_sum_folder)

	sdm_sum_log = sdm_sum.log10()
	export_image_to_drive(sdm_sum_log, 'species_richness_log')
