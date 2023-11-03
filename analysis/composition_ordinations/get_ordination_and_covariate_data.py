import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from config_figures import *

if __name__ == '__main__':
    nmds_evopca_covs_fc = covariate_img.select([
        'SG_Coarse_fragments_005cm','SG_Silt_Content_005cm','SG_Soil_pH_H2O_005cm', 'CHELSA_bio12_1981_2010_V2_1',
        'CHELSA_bio15_1981_2010_V2_1', 'CHELSA_bio1_1981_2010_V2_1', 'CHELSA_bio4_1981_2010_V2_1',
        'CHELSA_gsl_1981_2010_V2_1', 'CHELSA_npp_1981_2010_V2_1'
    ]).reduceRegions(nmds_evopca_fc, ee.Reducer.mean())
    
    export_table_to_drive(nmds_evopca_covs_fc, 'ordinations_covariates_1981_2010')
