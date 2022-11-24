from config_figures import *

realms = ecoregions.aggregate_array('REALM').distinct()
realm_dict = ee.Dictionary.fromLists(realms, ee.List.sequence(1, realms.length()))
ecoregions = ecoregions.map(lambda eco: eco.set('REALM_ID', realm_dict.get(eco.get('REALM'))))
realm_image = ecoregions.reduceToImage(['REALM_ID'], ee.Reducer.first())

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

def get_sdm_realm_v2(sdm):
    sdm = sdm.select('covariates_1981_2010')
    sdm_realm_areas = realms.map(lambda r: sdm.multiply(realm_image).selfMask().eq(ee.Image.constant(realm_dict.get(r))).multiply(ee.Image.pixelArea()).reduceRegion(
        reducer = ee.Reducer.sum(), geometry = unbounded_geo, scale = scale_to_use, maxPixels = 1e13
    ).get('covariates_1981_2010'))
    sdm_realm_areas_dict = ee.Dictionary.fromLists(realms, sdm_realm_areas)
    sum = sdm_realm_areas_dict.values().reduce(ee.Reducer.sum())
    return ee.Feature(None, sdm_realm_areas_dict.map(lambda k,v: ee.Number(v).divide(sum).multiply(100).round())).set('species', sdm.get('system:index'))

if __name__ == '__main__':
    print(sdms.limit(2).map(get_sdm_realm_v2).getInfo())
    sdm_realms = sdms.map(get_sdm_realm_v2)
    export_table_to_drive(sdm_realms, sdm_realm_drive_filename + '_v2')
