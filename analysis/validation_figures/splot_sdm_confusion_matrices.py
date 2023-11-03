import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
from config_figures import *

def compute_confusion_matrix(species):
    fc = ee.FeatureCollection(splot_sample_folder + species)
    tp = fc.filter(ee.Filter.And(ee.Filter.eq('sdm_presence', 1), ee.Filter.eq('splot_presence', 1))).size()#.getInfo()
    tn = fc.filter(ee.Filter.And(ee.Filter.eq('sdm_presence', 0), ee.Filter.eq('splot_presence', 0))).size()#.getInfo()
    fp = fc.filter(ee.Filter.And(ee.Filter.eq('sdm_presence', 1), ee.Filter.eq('splot_presence', 0))).size()#.getInfo()
    fn = fc.filter(ee.Filter.And(ee.Filter.eq('sdm_presence', 0), ee.Filter.eq('splot_presence', 1))).size()#.getInfo()
    return ee.Feature(None, {'species': species, 'tp':tp, 'tn':tn, 'fp':fp, 'fn':fn})

if __name__ == '__main__':
    sdm_species = sdms.aggregate_array('system:index')
    splot_species = splot_data.distinct('Species').aggregate_array('Species').map(lambda x: ee.String(x).replace(' ','_'))

    species = sdm_species.filter(ee.Filter.inList('item', splot_species)).getInfo()
    print(len(species), 'species')

    conf_mats = ee.FeatureCollection([compute_confusion_matrix(s) for s in species])
    export_table_to_drive(conf_mats, 'sdm_splot_comparison')
    
