import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
from config_figures import *

def splot_sdm_comparison(species):
    sdm = sdms.filter(ee.Filter.eq('system:index', species)).first().select('covariates_1981_2010')
    sdm_bbox = sdm_bboxes.filter(ee.Filter.eq('species', species)).first().geometry()
    
    species_splot = splot_data.filterBounds(sdm_bbox).distinct('.geo').map(lambda f: f.set('splot_presence', 0))
    presences = splot_data.filter(ee.Filter.eq('Species', ee.String(species).replace('_',' ')))
    species_splot_pa = species_splot.filter(ee.Filter.bounds(presences)).map(lambda f: f.set('splot_presence', 1)).merge(species_splot.filter(ee.Filter.bounds(presences).Not()))
    species_sdm_splot_pa = sdm.reduceRegions(collection = species_splot_pa, reducer = ee.Reducer.first(), scale = scale_to_use).filter(ee.Filter.notNull(['first'])).map(
        lambda f: f.select(['first', 'splot_presence'],['sdm_presence', 'splot_presence'])
    )
    export_table_to_asset(species_sdm_splot_pa, species, splot_sample_folder)

if __name__ == '__main__':
    sdm_species = sdms.aggregate_array('system:index')
    splot_species = splot_data.distinct('Species').aggregate_array('Species').map(lambda x: ee.String(x).replace(' ','_'))

    species = sdm_species.filter(ee.Filter.inList('item', splot_species)).getInfo()
    print(len(species), 'species')

    for s in species:
        splot_sdm_comparison(s)
