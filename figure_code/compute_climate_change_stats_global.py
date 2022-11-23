from config_figures import *

# function to compute per ecoregion statistics of SDM changes when applied to present (1981-2010) and future (2071-2100 SSP 5.85) climate scenarios
def compute_eco_stats_ecoregion(ecoid):    
    # get eco_geo by merging geometries of all ecoregion features with ECO_ID = ecoid (for some ECO_IDs there are mutliple features to take into account) and get ecoregion area
    eco_geo = ecoregions.filter(ee.Filter.eq('ECO_ID', ecoid)).geometry()
    # eco_area = ee.Image.pixelArea().reduceRegion(reducer = ee.Reducer.sum(), geometry = eco_geo, scale = scale_to_use, maxPixels = 1e13).getNumber('area')
    
    # reduce species pool by selecting species whose SDM bounding box intersects with eco_geo
    species = sdm_bboxes.filterBounds(eco_geo).aggregate_array('species')
    # reduce species pool further by selecting those that have at least one non zero pixel in the ecoregion for present or future SDM projections
    sdms_eco = sdms.filter(ee.Filter.inList('system:index', species)).map(lambda sdm: sdm.select(['covariates_1981_2010', 'covariates_2071_2100_ssp585'])).map(
        lambda sdm: sdm.set(sdm.rename(['in_eco_present', 'in_eco_future']).reduceRegion(
            reducer = ee.Reducer.anyNonZero(), geometry = eco_geo, scale = scale_to_use, maxPixels = 1e13
        ))
    ).filter(ee.Filter.Or(ee.Filter.eq('in_eco_present', 1), ee.Filter.eq('in_eco_future', 1)))

    # get SDM latitude and elevation shift for each species in ecoregion for present and future climate projections 
    sdms_eco_present_and_future = sdms_eco.filter(ee.Filter.And(ee.Filter.eq('in_eco_present', 1), ee.Filter.eq('in_eco_future', 1)))
    sdms_eco_lat_elev = sdms_area_lat_elev_fc.filter(ee.Filter.inList('species', sdms_eco_present_and_future.aggregate_array('system:index'))).map(lambda f: f.set({
        'latitude_shift': f.getNumber('latitude_2071_2100_ssp585').subtract(f.getNumber('latitude_1981_2010')),
        'elevation_shift': f.getNumber('elevation_2071_2100_ssp585').subtract(f.getNumber('elevation_1981_2010')),
    })).map(lambda f: f.set({
        'abs_latitude_shift': f.getNumber('latitude_shift').abs(), 'pos_elevation_shift': ee.Algorithms.If(f.getNumber('elevation_shift').gte(0), f.get('elevation_shift'), 0)
    }))
    
    # return feature with properties for biome name and number, eocregion ID and name, realm, ecoregion area, 
    # number of species in ecoregion for present and future climate projections, number of species lost and gained between both climate projections,
    # median SDM area across species for present and future climate projections, and median relative change in SDM area 
    return ee.Feature(None, ecoregions.filter(ee.Filter.eq('ECO_ID', ecoid)).first().toDictionary(['BIOME_NAME','BIOME_NUM','ECO_ID','ECO_NAME','REALM']).combine({
        'n_present': sdms_eco.filter(ee.Filter.eq('in_eco_present', 1)).size(),
        'n_future': sdms_eco.filter(ee.Filter.eq('in_eco_future', 1)).size(),
        'n_lost': sdms_eco.filter(ee.Filter.And(ee.Filter.eq('in_eco_present', 1), ee.Filter.eq('in_eco_future', 0))).size(),
        'n_gained': sdms_eco.filter(ee.Filter.And(ee.Filter.eq('in_eco_present', 0), ee.Filter.eq('in_eco_future', 1))).size(),
        'latitude_shift': sdms_eco_lat_elev.aggregate_array('latitude_shift').reduce(ee.Reducer.median()),
        'abs_latitude_shift': sdms_eco_lat_elev.aggregate_array('abs_latitude_shift').reduce(ee.Reducer.median()),
        'elevation_shift': sdms_eco_lat_elev.aggregate_array('elevation_shift').reduce(ee.Reducer.median()),
        'pos_elevation_shift': sdms_eco_lat_elev.aggregate_array('pos_elevation_shift').reduce(ee.Reducer.median())
    }))

if __name__ == '__main__':
    all_biomes = biome_dictionary.getInfo()
    print(all_biomes)
    forest_biomes = biome_dictionary.select(biome_dictionary.keys().filter(ee.Filter.stringContains('item', 'Forest'))).getInfo()
    print(forest_biomes)

    for biome, biome_num in forest_biomes.items(): 
        if biome_num != 1: continue
        print('*', biome, biome_num)
        
        # get distinct ECO_ID values for the biome
        biome_ecoregions = ecoregions.filter(ee.Filter.eq('BIOME_NUM', biome_num))
        biome_ecoregion_ids = biome_ecoregions.aggregate_array('ECO_ID').distinct()
        n_ecoids = biome_ecoregion_ids.size().getInfo()
        print(biome_ecoregions.size().getInfo(), 'ecoregion features -> ', n_ecoids, 'distinct ecoregion IDs')

        # map compute_species_stats_ecoregion function over distinct ECO_ID (not ecoregion features, as some ECO_IDs are spread over multiple features)
        biome_ecoregions_stats = ee.FeatureCollection(biome_ecoregion_ids.map(compute_eco_stats_ecoregion))
        if n_ecoids <= 50:
            export_table_to_drive(biome_ecoregions_stats, 'ecoregions_stats_v2_biome_' + str(biome_num))
        else:
            nchunks = ceil(n_ecoids/50.0)
            chunksize = ceil(n_ecoids / nchunks)
            print(n_ecoids, nchunks, chunksize)
            for i, idx in enumerate(range(0, n_ecoids, chunksize)):
                print(idx, idx+chunksize)
                print(biome_ecoregion_ids.slice(idx, idx+chunksize).size().getInfo())
                print('ecoregions_stats_v2_biome_' + str(biome_num) + '_chunk_' + str(i) + '_outof_' + str(nchunks))
                biome_ecoregions_stats = ee.FeatureCollection(biome_ecoregion_ids.slice(idx, idx+chunksize).map(compute_eco_stats_ecoregion))
                export_table_to_drive(biome_ecoregions_stats, 'ecoregions_stats_v2_biome_' + str(biome_num) + '_chunk_' + str(i) + '_outof_' + str(nchunks))

