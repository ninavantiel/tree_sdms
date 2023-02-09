from config_figures import *

if __name__ == '__main__':
    nmds_rectangles = ee.FeatureCollection(earthengine_folder + 'nmds_fc_geos')
    covariate_img = ee.Image('projects/crowtherlab/nina/treemap/composite_to_sample')
    nmds_pca_fc = covariate_img.select([
        'SG_Coarse_fragments_005cm','SG_Silt_Content_005cm','SG_Soil_pH_H2O_005cm', 'CHELSA_bio12_1981_2010_V2_1',
        'CHELSA_bio15_1981_2010_V2_1', 'CHELSA_bio1_1981_2010_V2_1', 'CHELSA_bio4_1981_2010_V2_1',
        'CHELSA_gsl_1981_2010_V2_1', 'CHELSA_npp_1981_2010_V2_1'
    ]).reduceRegions(nmds_rectangles, ee.Reducer.mean())

    export_table_to_drive(nmds_pca_fc, 'nmds_pca_data')
