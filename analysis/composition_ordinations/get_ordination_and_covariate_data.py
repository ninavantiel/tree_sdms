import sys
sys.path.insert(0, '/Users/nina/Documents/treemap/treemap/analysis')
from config_figures import *

if __name__ == '__main__':
    nmds_evopca_fc = ee.FeatureCollection('users/ninavantiel/treemap/ordinations/nmds_evopca_fc')
    covariate_img = ee.Image('users/ninavantiel/treemap/treemap_composite_image')
    nmds_evopca_covs_fc = covariate_img.select([
        'SG_Coarse_fragments_005cm','SG_Silt_Content_005cm','SG_Soil_pH_H2O_005cm', 'CHELSA_bio12_1981_2010_V2_1',
        'CHELSA_bio15_1981_2010_V2_1', 'CHELSA_bio1_1981_2010_V2_1', 'CHELSA_bio4_1981_2010_V2_1',
        'CHELSA_gsl_1981_2010_V2_1', 'CHELSA_npp_1981_2010_V2_1'
    ]).reduceRegions(nmds_evopca_fc, ee.Reducer.mean())

    export_table_to_drive(nmds_evopca_covs_fc, 'ordinations_sampled_covariates_1981_2010')
