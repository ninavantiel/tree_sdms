from config_figures import *

if __name__ == '__main__':
    median_area_1981_2010 = sdms.map(lambda sdm: mask_sdm(sdm.select('covariates_1981_2010')).multiply(
        sdms_area_lat_elev_fc.filter(ee.Filter.eq('species', sdm.get('system:index'))).first().getNumber('area_1981_2010').divide(1e12)
    ).toInt64()).median()
    export_image_to_drive(median_area_1981_2010, 'median_area_global_1981_2010')

    median_area_2071_2100_ssp585 = sdms.map(lambda sdm: mask_sdm(sdm.select('covariates_2071_2100_ssp585')).multiply(
        sdms_area_lat_elev_fc.filter(ee.Filter.eq('species', sdm.get('system:index'))).first().getNumber('area_2071_2100_ssp585').divide(1e12)
    ).toInt64()).median()
    export_image_to_drive(median_area_2071_2100_ssp585, 'median_area_global_2071_2100_ssp585')
    print('done')