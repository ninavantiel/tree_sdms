from config_figures import *

def get_ecoregion_numbers(eco):
    species = sdm_bboxes.filterBounds(eco.geometry()).aggregate_array('species')
    
    sdms_eco = sdms.filter(ee.Filter.inList('system:index', species)).map(lambda sdm: sdm.select(['covariates_1981_2010', 'covariates_2071_2100_ssp585'])).map(
        lambda sdm: sdm.set(sdm.rename(['in_eco_present', 'in_eco_future']).reduceRegion(
            reducer = ee.Reducer.anyNonZero(), geometry = eco.geometry(), scale = scale_to_use, maxPixels = 1e13
        ))
    ).filter(ee.Filter.Or(ee.Filter.eq('in_eco_present', 1), ee.Filter.eq('in_eco_future', 1)))
  
    return ee.Feature(None, eco.toDictionary(['BIOME_NAME','BIOME_NUM','ECO_ID','ECO_NAME','REALM']).combine({
        'n_present': sdms_eco.filter(ee.Filter.eq('in_eco_present', 1)).size(),
        'n_future': sdms_eco.filter(ee.Filter.eq('in_eco_future', 1)).size(),
        'n_lost': sdms_eco.filter(ee.Filter.And(ee.Filter.eq('in_eco_present', 1), ee.Filter.eq('in_eco_future', 0))).size(),
        'n_gained': sdms_eco.filter(ee.Filter.And(ee.Filter.eq('in_eco_present', 0), ee.Filter.eq('in_eco_future', 1))).size()
    }))

if __name__ == '__main__':
    print(biome_dictionary.getInfo())
    forest_biomes = biome_dictionary.select(biome_dictionary.keys().filter(ee.Filter.stringContains('item', 'Forest'))).getInfo()
    print(forest_biomes)

    for biome, biome_num in forest_biomes.items():
        if biome_num == 6:
            print(biome, biome_num)
            biome_ecoregions = ecoregions.filter(ee.Filter.eq('BIOME_NAME', biome))
            print(biome_ecoregions.size().getInfo(), 'ecoregions')
            biome_ecoregions_species_numbers = biome_ecoregions.map(get_ecoregion_numbers)
            export_table_to_drive(biome_ecoregions_species_numbers, 'ecoregions_species_numbers_biome_' + str(biome_num))
    
    #ecoregions_species_numbers = ecoregions.map(get_ecoregion_numbers)
    #export_table_to_drive(ecoregions_species_numbers, 'ecoregions_species_numbers')
