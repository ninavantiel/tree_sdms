from config_figures import *

# function to compute per ecoregion statistics of SDM changes when applied to present (1981-2010) and future (2071-2100 SSP 5.85) climate scenarios
def compute_species_stats_ecoregion(ecoid):    
    # get eco_geo by merging geometries of all ecoregion features with ECO_ID = ecoid (for some ECO_IDs there are mutliple features to take into account) and get ecoregion area
    eco_geo = ecoregions.filter(ee.Filter.eq('ECO_ID', ecoid)).geometry()
    eco_area = ee.Image.pixelArea().reduceRegion(reducer = ee.Reducer.sum(), geometry = eco_geo, scale = scale_to_use, maxPixels = 1e13).getNumber('area')

    #eco = ecoregions.filter(ee.Filter.eq('ECO_ID', ecoid)).first()
    
    # reduce species pool by selecting species whose SDM bounding box intersects with eco_geo
    species = sdm_bboxes.filterBounds(eco_geo).aggregate_array('species')
    # reduce species pool further by selecting those that have at least one non zero pixel in the ecoregion for present or future SDM projections
    sdms_eco = sdms.filter(ee.Filter.inList('system:index', species)).map(lambda sdm: sdm.select(['covariates_1981_2010', 'covariates_2071_2100_ssp585'])).map(
        lambda sdm: sdm.set(sdm.rename(['in_eco_present', 'in_eco_future']).reduceRegion(
            reducer = ee.Reducer.anyNonZero(), geometry = eco_geo, scale = scale_to_use, maxPixels = 1e13
        ))
    ).filter(ee.Filter.Or(ee.Filter.eq('in_eco_present', 1), ee.Filter.eq('in_eco_future', 1)))

    # compute SDM area in ecoregion for each species for present and future climate projections and relative change between both [(area_future - area_present) / area_present]
    sdm_area = sdms_eco.map(lambda sdm: sdm.set(sdm.multiply(ee.Image.pixelArea()).rename(['area_present','area_future']).reduceRegion(
        reducer = ee.Reducer.sum(), geometry = eco_geo, scale = scale_to_use, maxPixels = 1e13
    ))).map(lambda sdm: sdm.set('area_change', (sdm.getNumber('area_future').subtract(sdm.getNumber('area_present'))).divide(sdm.getNumber('area_present'))))
    
    # compute median SDM area in ecoregion across species for present and future climate projections and median relative change in area
    median_area_present = sdm_area.filter(ee.Filter.eq('in_eco_present', 1)).aggregate_array('area_present').reduce(ee.Reducer.median())
    median_area_future = sdm_area.filter(ee.Filter.eq('in_eco_future', 1)).aggregate_array('area_future').reduce(ee.Reducer.median())
    median_area_change = sdm_area.filter(ee.Filter.eq('in_eco_present', 1)).aggregate_array('area_change').reduce(ee.Reducer.median())
  
    # return feature with properties for biome name and number, eocregion ID and name, realm, ecoregion area, 
    # number of species in ecoregion for present and future climate projections, number of species lost and gained between both climate projections,
    # median SDM area across species for present and future climate projections, and median relative change in SDM area 
    return ee.Feature(None, ecoregions.filter(ee.Filter.eq('ECO_ID', ecoid)).first().toDictionary(['BIOME_NAME','BIOME_NUM','ECO_ID','ECO_NAME','REALM']).combine({
        'ECO_AREA': eco_area,
        'n_present': sdms_eco.filter(ee.Filter.eq('in_eco_present', 1)).size(),
        'n_future': sdms_eco.filter(ee.Filter.eq('in_eco_future', 1)).size(),
        'n_lost': sdms_eco.filter(ee.Filter.And(ee.Filter.eq('in_eco_present', 1), ee.Filter.eq('in_eco_future', 0))).size(),
        'n_gained': sdms_eco.filter(ee.Filter.And(ee.Filter.eq('in_eco_present', 0), ee.Filter.eq('in_eco_future', 1))).size(),
        'median_area_present': median_area_present, 'median_area_future': median_area_future, 'median_area_change': median_area_change
    }))

if __name__ == '__main__':
    all_biomes = biome_dictionary.getInfo()
    print(all_biomes)
    forest_biomes = biome_dictionary.select(biome_dictionary.keys().filter(ee.Filter.stringContains('item', 'Forest'))).getInfo()
    print(forest_biomes)

    #print(forest_biomes.values())
    '''
    for biome, biome_num in all_biomes.items(): #forest_biomes.items():
        if biome_num not in forest_biomes.values():
            print(biome, biome_num)

            # get distinct ECO_ID values for the biome
            biome_ecoregions = ecoregions.filter(ee.Filter.eq('BIOME_NUM', biome_num))
            biome_ecoregion_ids = biome_ecoregions.aggregate_array('ECO_ID').distinct()
            print(biome_ecoregions.size().getInfo(), 'ecoregion features -> ', biome_ecoregion_ids.size().getInfo(), 'distinct ecoregion IDs')

            # map compute_species_stats_ecoregion function over distinct ECO_ID (not ecoregion features, as some ECO_IDs are spread over multiple features)
            biome_ecoregions_species_stats = ee.FeatureCollection(biome_ecoregion_ids.map(compute_species_stats_ecoregion))
            export_table_to_drive(biome_ecoregions_species_stats, 'ecoregions_species_stats_v2_biome_' + str(biome_num))
    '''

    n_chunks = 2
    for biome, biome_num in forest_biomes.items():
        if biome_num in [1, 12]:
            print(biome, biome_num)

            # get distinct ECO_ID values for the biome
            biome_ecoregions = ecoregions.filter(ee.Filter.eq('BIOME_NUM', biome_num))
            biome_ecoregion_ids = biome_ecoregions.aggregate_array('ECO_ID').distinct()
            print(biome_ecoregions.size().getInfo(), 'ecoregion features -> ', biome_ecoregion_ids.size().getInfo(), 'distinct ecoregion IDs')

            n_eco = biome_ecoregion_ids.size().getInfo()
            chunksize = int(n_eco / n_chunks) + 1
            for start_id in range(0, n_eco, chunksize):
                print(start_id, start_id+chunksize)
                print(biome_ecoregion_ids.slice(start_id, start_id+chunksize).size().getInfo())
            
                # map compute_species_stats_ecoregion function over distinct ECO_ID (not ecoregion features, as some ECO_IDs are spread over multiple features)
                biome_ecoregions_species_stats = ee.FeatureCollection(biome_ecoregion_ids.slice(start_id, start_id+chunksize).map(compute_species_stats_ecoregion))
                export_table_to_drive(biome_ecoregions_species_stats, 'ecoregions_species_stats_v2_biome_' + str(biome_num) + '_eco_' + str(start_id) + 'to' + str(start_id+chunksize))
