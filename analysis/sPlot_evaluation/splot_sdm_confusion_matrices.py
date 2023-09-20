import sys
sys.path.insert(0, '/Users/nina/Documents/treemap/treemap/analysis')
from config_figures import * 

def compute_confusion_matrix(species):
    fc = ee.FeatureCollection('users/ninavantiel/treemap/sPlot_comparison/splot_sdm/' + species)
    tp = fc.filter(ee.Filter.And(ee.Filter.eq('sdm_presence', 1), ee.Filter.eq('splot_presence', 1))).size()#.getInfo()
    tn = fc.filter(ee.Filter.And(ee.Filter.eq('sdm_presence', 0), ee.Filter.eq('splot_presence', 0))).size()#.getInfo()
    fp = fc.filter(ee.Filter.And(ee.Filter.eq('sdm_presence', 1), ee.Filter.eq('splot_presence', 0))).size()#.getInfo()
    fn = fc.filter(ee.Filter.And(ee.Filter.eq('sdm_presence', 0), ee.Filter.eq('splot_presence', 1))).size()#.getInfo()
    #return pd.DataFrame([[tp, tn, fp, fn]], index=[s], columns=['tp','tn','fp','fn'])
    return ee.Feature(None, {'species': species, 'tp':tp, 'tn':tn, 'fp':fp, 'fn':fn})

if __name__ == '__main__':
    sdm_species = sdms.aggregate_array('system:index')
    splot_species = splot_data.distinct('Species').aggregate_array('Species').map(lambda x: ee.String(x).replace(' ','_'))

    species = sdm_species.filter(ee.Filter.inList('item', splot_species)).getInfo()
    print(len(species), 'species')

    conf_mats = ee.FeatureCollection([compute_confusion_matrix(s) for s in species])
    export_table_to_drive(conf_mats, 'sdm_splot_comparison')
    
