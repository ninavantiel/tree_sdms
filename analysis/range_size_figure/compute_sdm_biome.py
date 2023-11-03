import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from config_figures import *

biomes = ecoregions.aggregate_array('BIOME_NAME').distinct()

def get_sdm_biome(sdm):
    sdm = sdm.select('covariates_1981_2010')
    sdm_area = sdms_area_lat_elev_fc.filter(ee.Filter.And(
        ee.Filter.eq('species', sdm.get('system:index')), 
        ee.Filter.eq('climate', '1981_2010'),
        ee.Filter.eq('min_tree_cover', 0)
    )).first().getNumber('area')

    sdm_in_ecoregions = sdm.reduceRegions(ecoregions, ee.Reducer.anyNonZero(), scale_to_use).filter(ee.Filter.eq('any',1))
    sdm_area_in_ecoregions = sdm.multiply(ee.Image.pixelArea()).reduceRegions(sdm_in_ecoregions, ee.Reducer.sum(), scale_to_use)

    biomes_sdm = sdm_in_ecoregions.aggregate_array('BIOME_NAME').distinct()
    biome_area_sdm = ee.Dictionary.fromLists(biomes_sdm, ee.Algorithms.If(biomes_sdm.length().eq(1), [100], biomes_sdm.map(
        lambda b: sdm_area_in_ecoregions.filter(ee.Filter.eq('BIOME_NAME', b)).aggregate_sum('sum').divide(sdm_area).multiply(100).int()
    )))

    biomes_no_sdm = biomes.filter(ee.Filter.inList('item', biomes_sdm).Not())
    biome_area_no_sdm = ee.Dictionary.fromLists(biomes_no_sdm, ee.List.repeat(0, biomes_no_sdm.length()))  

    return ee.Feature(None, {'species': sdm.get('system:index')}).set(biome_area_sdm.combine(biome_area_no_sdm))

if __name__ == '__main__':
    sdm_biomes = sdms.map(get_sdm_biome)
    export_table_to_drive(sdm_biomes, sdm_biome_drive_filename)