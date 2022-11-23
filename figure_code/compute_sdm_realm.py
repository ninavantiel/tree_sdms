from config_figures import *

realms = ecoregions.aggregate_array('REALM').distinct()


def get_sdm_realm(sdm):
    sdm = sdm.select('covariates_1981_2010')
    sdm_area = sdms_area_lat_elev_fc.filter(ee.Filter.eq('species', sdm.get('system:index'))).first().getNumber('area_1981_2010')

    sdm_in_ecoregions = sdm.reduceRegions(ecoregions, ee.Reducer.anyNonZero(), scale_to_use).filter(ee.Filter.eq('any',1))
    sdm_area_in_ecoregions = sdm.multiply(ee.Image.pixelArea()).reduceRegions(sdm_in_ecoregions, ee.Reducer.sum(), scale_to_use)

    realms_sdm = sdm_in_ecoregions.aggregate_array('REALM').distinct()
    realm_area_sdm = ee.Dictionary.fromLists(realms_sdm, ee.Algorithms.If(realms_sdm.length().eq(1), [100], realms_sdm.map(
        lambda r: sdm_area_in_ecoregions.filter(ee.Filter.eq('REALM', r)).aggregate_sum('sum').divide(sdm_area).multiply(100).int()
    )))

    realms_no_sdm = realms.filter(ee.Filter.inList('item', realms_sdm).Not())
    realm_area_no_sdm = ee.Dictionary.fromLists(realms_no_sdm, ee.List.repeat(0, realms_no_sdm.length()))  

    return ee.Feature(None, {'species': sdm.get('system:index')}).set(realm_area_sdm.combine(realm_area_no_sdm))
    
if __name__ == '__main__':
    # print(sdms.limit(20).map(get_sdm_realm).getInfo())
    sdm_realms = sdms.map(get_sdm_realm)
    export_table_to_drive(sdm_realms, sdm_realm_drive_filename)
