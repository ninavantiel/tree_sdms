from config_figures import *

def get_sdm_realm(sdm):
    sdm = sdm.select('covariates_1981_2010')

    sdm_in_ecoregions = sdm.reduceRegions(ecoregions, ee.Reducer.anyNonZero(), scale_to_use).filter(ee.Filter.eq('any',1))
    realms = sdm_in_ecoregions.aggregate_array('REALM').distinct()

    sdm_area = sdms_area_lat_elev_fc.filter(ee.Filter.eq('species', sdm.get('system:index'))).first().getNumber('area_1981_2010')
    sdm_area_in_ecoregions = sdm.multiply(ee.Image.pixelArea()).reduceRegions(sdm_in_ecoregions, ee.Reducer.sum(), scale_to_use)

    realm_area = ee.Dictionary.fromLists(realms, ee.Algorithms.If(realms.length().eq(1), [1], realms.map(
        lambda realm: sdm_area_in_ecoregions.filter(ee.Filter.eq('REALM', realm)).aggregate_sum('sum').divide(sdm_area)
    )))

    return ee.Feature(None, {'species': sdm.get('system:index')}).set(realm_area)
    
if __name__ == '__main__':
    print(sdms.limit(5).map(get_sdm_realm).getInfo())
    sdm_realms = sdms.map(get_sdm_realm)
    export_table_to_drive(sdm_realms, 'sdm_realms ')
