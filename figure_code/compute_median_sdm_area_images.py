from config_figures import *

if __name__ == '__main__':
    median_area_1981_2010 = sdms.map(lambda sdm: mask_sdm(sdm.select('covariates_1981_2010')).multiply(
        sdms_area_lat_elev_fc.filter(ee.Filter.eq('species', sdm.get('system:index'))).first().getNumber('area_1981_2010')
    ).toFloat()).median()
    # export_image_to_drive(median_area_1981_2010, 'median_area_global_1981_2010')
    # export_image_to_drive(median_area_1981_2010.log10(), 'median_area_global_1981_2010_log10')

    median_area_forest_1981_2010 = sdms.map(lambda sdm: mask_sdm(sdm.select('covariates_1981_2010')).mask(forest_image).multiply(
        sdms_forest_area_lat_elev_fc.filter(ee.Filter.eq('species', sdm.get('system:index'))).first().getNumber('area_1981_2010')
    ).toFloat()).median()
    export_image_to_drive(median_area_forest_1981_2010, 'median_area_forest_1981_2010')
    export_image_to_drive(median_area_forest_1981_2010.log10(), 'median_area_forest_1981_2010_log10')