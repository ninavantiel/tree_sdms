import sys
sys.path.insert(0, '/Users/nina/Documents/treemap/treemap/analysis')
from config_figures import *

import os
os.chdir('/Users/nina/Documents/treemap/treemap/data/')

if __name__ == '__main__':
    print(sys.path)
    nmds = pd.read_csv('nmds_3d_ecoregions_current_future.csv').rename(columns={'y':'ECO_ID'})
    nmds_current = nmds[nmds.current_or_future == 'current'][['ECO_ID','MDS1','MDS2','MDS3']].rename(columns={'MDS1':'current_MDS1','MDS2':'current_MDS2','MDS3':'current_MDS3'})
    nmds_future = nmds[nmds.current_or_future == 'future'][['ECO_ID','MDS1','MDS2','MDS3']].rename(columns={'MDS1':'future_MDS1','MDS2':'future_MDS2','MDS3':'future_MDS3'})
    nmds = pd.merge(nmds_current, nmds_future)
    nmds['ECO_ID'] = nmds['ECO_ID'].astype(int)

    evopca = pd.read_csv('evopca_ecoregions_current_future_df.csv')
    evopca['ECO_ID'] = evopca.apply(lambda x: x.site.split('_')[1], axis=1)
    evopca['current_or_future'] = evopca.apply(lambda x: x.site.split('_')[2], axis=1)
    evopca_current = evopca[evopca.current_or_future == 'current'][['ECO_ID','Axis1','Axis2','Axis3']].rename(columns={'Axis1':'current_evoPCA1','Axis2':'current_evoPCA2','Axis3':'current_evoPCA3'})
    evopca_future = evopca[evopca.current_or_future == 'future'][['ECO_ID','Axis1','Axis2','Axis3']].rename(columns={'Axis1':'future_evoPCA1','Axis2':'future_evoPCA2','Axis3':'future_evoPCA3'})
    evopca = pd.merge(evopca_current, evopca_future)
    evopca['ECO_ID'] = evopca['ECO_ID'].astype(int)
    
    df = pd.merge(nmds, evopca, on='ECO_ID')
    df['MDS_euclidean_distance'] = df.apply(lambda x: ((x['current_MDS1']-x['future_MDS1']) ** 2 + ((x['current_MDS2']-x['future_MDS2']) ** 2) + ((x['current_MDS3']-x['future_MDS3']) ** 2)) ** 0.5, axis=1)
    df['evoPCA_euclidean_distance'] = df.apply(lambda x: ((x['current_evoPCA1']-x['future_evoPCA1']) ** 2 + ((x['current_evoPCA2']-x['future_evoPCA2']) ** 2) + ((x['current_evoPCA3']-x['future_evoPCA3']) ** 2)) ** 0.5, axis=1)

    df.to_csv('nmds_evopca_eucl_dist_ecoregions_current_future.csv', index=False)