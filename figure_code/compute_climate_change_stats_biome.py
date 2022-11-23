from config_figures import *

# function to compute per ecoregion statistics of SDM changes when applied to present (1981-2010) and future (2071-2100 SSP 5.85) climate scenarios
def compute_climate_change_stats_biome(biome_num):
    sdms_in_biome = sdms.map(
        lambda sdm: sdm.select(['covariates_1981_2010','covariates_2071_2100_ssp585']).multiply(biome_image.eq(ee.Image.constant(biome_num)).selfMask())
    ).map(lambda sdm: sdm.set(sdm.rename(['in_biome_present', 'in_biome_future']).reduceRegion(
        reducer = ee.Reducer.anyNonZero(), geometry = unbounded_geo, scale = scale_to_use, maxPixels = 1e13
    ))).filter(ee.Filter.Or(ee.Filter.eq('in_biome_present', 1), ee.Filter.eq('in_biome_future', 1))).limit(50)

    sdms_biome_present_and_future = sdms_in_biome.filter(ee.Filter.And(ee.Filter.eq('in_biome_present', 1), ee.Filter.eq('in_biome_future', 1)))
    sdms_biome_lat_elev = sdms_area_lat_elev_fc.filter(ee.Filter.inList('species', sdms_biome_present_and_future.aggregate_array('system:index'))).map(
        lambda f: f.set({
            'latitude_shift': f.getNumber('latitude_2071_2100_ssp585').subtract(f.getNumber('latitude_1981_2010')),
            'elevation_shift': f.getNumber('elevation_2071_2100_ssp585').subtract(f.getNumber('elevation_1981_2010'))
        })
    )
    
    # return feature with properties for biome name and number, eocregion ID and name, realm, ecoregion area, 
    # number of species in ecoregion for present and future climate projections, number of species lost and gained between both climate projections,
    # median SDM area across species for present and future climate projections, and median relative change in SDM area 
    return ee.Feature(None, ecoregions.filter(ee.Filter.eq('BIOME_NUM', biome_num)).first().toDictionary(['BIOME_NAME','BIOME_NUM']).combine({
        'n_present': sdms_in_biome.filter(ee.Filter.eq('in_biome_present', 1)).size(),
        'n_future': sdms_in_biome.filter(ee.Filter.eq('in_biome_future', 1)).size(),
        'n_lost': sdms_in_biome.filter(ee.Filter.And(ee.Filter.eq('in_biome_present', 1), ee.Filter.eq('in_biome_future', 0))).size(),
        'n_gained': sdms_in_biome.filter(ee.Filter.And(ee.Filter.eq('in_biome_present', 0), ee.Filter.eq('in_biome_future', 1))).size(),
        'latitude_shift': sdms_biome_lat_elev.aggregate_array('latitude_shift').reduce(ee.Reducer.median()),
        'elevation_shift': sdms_biome_lat_elev.aggregate_array('elevation_shift').reduce(ee.Reducer.median()),
    }))

if __name__ == '__main__':
    forest_biomes = biome_dictionary.select(biome_dictionary.keys().filter(ee.Filter.stringContains('item', 'Forest'))).values()
    print(forest_biomes.getInfo())
    biome_climate_change_stats = ee.FeatureCollection(forest_biomes.map(compute_climate_change_stats_biome))
    export_table_to_drive(biome_climate_change_stats, 'biome_climate_change_stats')
    '''
    all_biomes = biome_dictionary.getInfo()
    print(all_biomes)
    forest_biomes = biome_dictionary.select(biome_dictionary.keys().filter(ee.Filter.stringContains('item', 'Forest'))).getInfo()
    print(forest_biomes)

    for biome, biome_num in forest_biomes.items(): # all_biomes.items(): 
        print(biome, biome_num)
        
        # get distinct ECO_ID values for the biome
        biome_ecoregions = ecoregions.filter(ee.Filter.eq('BIOME_NUM', biome_num))
        biome_ecoregion_ids = biome_ecoregions.aggregate_array('ECO_ID').distinct()
        print(biome_ecoregions.size().getInfo(), 'ecoregion features -> ', biome_ecoregion_ids.size().getInfo(), 'distinct ecoregion IDs')

        # map compute_species_stats_ecoregion function over distinct ECO_ID (not ecoregion features, as some ECO_IDs are spread over multiple features)
        biome_ecoregions_stats = ee.FeatureCollection(biome_ecoregion_ids.map(compute_eco_stats_ecoregion))
        export_table_to_drive(biome_ecoregions_stats, 'ecoregions_stats_v2_biome_' + str(biome_num))
    '''