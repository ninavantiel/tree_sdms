from config_figures import *

def compute_species_stats_ecoregion(ecoid):
    eco = ecoregions.filter(ee.Filter.eq('ECO_ID', ecoid)).first()
    eco_geo = ecoregions.filter(ee.Filter.eq('ECO_ID', ecoid)).geometry()
    eco_area = ee.Image.pixelArea().reduceRegion(reducer = ee.Reducer.sum(), geometry = eco_geo, scale = scale_to_use, maxPixels = 1e13).getNumber('area')

    species = sdm_bboxes.filterBounds(eco_geo).aggregate_array('species')
    sdms_eco = sdms.filter(ee.Filter.inList('system:index', species)).map(lambda sdm: sdm.select(['covariates_1981_2010', 'covariates_2071_2100_ssp585'])).map(
        lambda sdm: sdm.set(sdm.rename(['in_eco_present', 'in_eco_future']).reduceRegion(
            reducer = ee.Reducer.anyNonZero(), geometry = eco_geo, scale = scale_to_use, maxPixels = 1e13
        ))
    ).filter(ee.Filter.Or(ee.Filter.eq('in_eco_present', 1), ee.Filter.eq('in_eco_future', 1)))

    sdm_area_present = sdms_eco.filter(ee.Filter.eq('in_eco_present', 1)).map(
        lambda sdm: sdm.set(mask_sdm(sdm).select(['covariates_1981_2010'],['sdm_area_present']).reduceRegion(reducer = ee.Reducer.sum(), geometry = eco_geo, scale = scale_to_use, maxPixels = 1e13))
    ).aggregate_array('sdm_area_present').reduce(ee.Reducer.median())

    sdm_area_future = sdms_eco.filter(ee.Filter.eq('in_eco_future', 1)).map(
        lambda sdm: sdm.set(mask_sdm(sdm).select(['covariates_2071_2100_ssp585'],['sdm_area_future']).reduceRegion(reducer = ee.Reducer.sum(), geometry = eco_geo, scale = scale_to_use, maxPixels = 1e13))
    ).aggregate_array('sdm_area_future').reduce(ee.Reducer.median())
  
    return ee.Feature(None, eco.toDictionary(['BIOME_NAME','BIOME_NUM','ECO_ID','ECO_NAME','REALM']).combine({
        'ECO_AREA': eco_area,
        'n_present': sdms_eco.filter(ee.Filter.eq('in_eco_present', 1)).size(),
        'n_future': sdms_eco.filter(ee.Filter.eq('in_eco_future', 1)).size(),
        'n_lost': sdms_eco.filter(ee.Filter.And(ee.Filter.eq('in_eco_present', 1), ee.Filter.eq('in_eco_future', 0))).size(),
        'n_gained': sdms_eco.filter(ee.Filter.And(ee.Filter.eq('in_eco_present', 0), ee.Filter.eq('in_eco_future', 1))).size(),
        'species_median_area_present': sdm_area_present, 'species_median_area_future': sdm_area_future
    }))

if __name__ == '__main__':
    all_biomes = biome_dictionary.getInfo()
    print(all_biomes)
    forest_biomes = biome_dictionary.select(biome_dictionary.keys().filter(ee.Filter.stringContains('item', 'Forest'))).getInfo()
    print(forest_biomes)

    for biome, biome_num in forest_biomes.items():
        if biome_num in [6]:#[12, 3, 2, 1]:
            print(biome, biome_num)

            # get distinct ECO_ID values for the biome
            biome_ecoregions = ecoregions.filter(ee.Filter.eq('BIOME_NUM', biome_num))
            biome_ecoregion_ids = biome_ecoregions.aggregate_array('ECO_ID').distinct()
            print(biome_ecoregions.size().getInfo(), 'ecoregion features -> ', biome_ecoregion_ids.size().getInfo(), 'distinct ecoregion IDs')

            # map compute_species_stats_ecoregion function over distinct ECO_ID (not ecoregion features, as some ECO_IDs are spread over multiple features)
            biome_ecoregions_species_stats = ee.FeatureCollection(biome_ecoregion_ids.map(compute_species_stats_ecoregion))
            export_table_to_drive(biome_ecoregions_species_stats, 'ecoregions_species_stats_biome_' + str(biome_num))
    
    #ecoregions_species_numbers = ecoregions.map(get_ecoregion_numbers)
    #export_table_to_drive(ecoregions_species_numbers, 'ecoregions_species_numbers')

