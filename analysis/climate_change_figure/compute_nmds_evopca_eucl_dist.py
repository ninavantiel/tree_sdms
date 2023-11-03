import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from config_figures import *

def scale_col(colname, df): 
    return MinMaxScaler().fit_transform(df[[colname]])

def eucl_dist(varlist, df): 
    return np.array([(df[v + '_current'] - df[v + '_future']) ** 2 for v in varlist]).sum(axis=0) ** 0.5

if __name__ == '__main__':
    # --- NMDS ---
    nmds = pd.read_csv(ecoregion_nmds_file).rename(columns={'y':'ECO_ID'}).drop(columns=['x'])
    nmds['ECO_ID'] = nmds['ECO_ID'].astype(int)
    
    # scale the 3 ordinations axes (current and future together)
    nmds['MDS1_scaled'] = scale_col('MDS1', nmds)
    nmds['MDS2_scaled'] = scale_col('MDS2', nmds)
    nmds['MDS3_scaled'] = scale_col('MDS3', nmds)

    # merge dataframes such that current and future NMDS values are on the same row
    nmds_merged = pd.merge(
        nmds[nmds.current_or_future == 'current'].drop(columns='current_or_future'), 
        nmds[nmds.current_or_future == 'future'].drop(columns='current_or_future'),
        on = 'ECO_ID', suffixes=('_current', '_future')
    )

    # compute euclidean distances between current and future NMDS values (unscaled and scaled)
    nmds_merged['eucl_dist'] = eucl_dist(['MDS1', 'MDS2', 'MDS3'], nmds_merged)
    nmds_merged['eucl_dist_scaled'] = eucl_dist(['MDS1_scaled', 'MDS2_scaled', 'MDS3_scaled'], nmds_merged)

    nmds_merged.to_csv(ecoregion_nmds_eucl_dist_file, index=False)

    # --- evoPCA ---
    evopca = pd.read_csv(ecoregion_evopca_file)
    evopca['ECO_ID'] = evopca.apply(lambda x: x.site.split('_')[1], axis=1).astype(int)
    evopca['current_or_future'] = evopca.apply(lambda x: x.site.split('_')[2], axis=1)

    # scale the 3 ordinations axes (current and future together)
    evopca['Axis1_scaled'] = scale_col('Axis1', evopca)
    evopca['Axis2_scaled'] = scale_col('Axis2', evopca)
    evopca['Axis3_scaled'] = scale_col('Axis3', evopca)

    # merge dataframes such that current and future evoPCA values are on the same row
    evopca_merged = pd.merge(
        evopca[evopca.current_or_future == 'current'].drop(columns=['current_or_future','site']), 
        evopca[evopca.current_or_future == 'future'].drop(columns=['current_or_future','site']),
        on = 'ECO_ID', suffixes=('_current', '_future')
    )

    # compute euclidean distances between current and future evoPCA values (unscaled and scaled)
    evopca_merged['eucl_dist'] = eucl_dist(['Axis1', 'Axis2', 'Axis3'], evopca_merged)
    evopca_merged['eucl_dist_scaled'] = eucl_dist(['Axis1_scaled', 'Axis2_scaled', 'Axis3_scaled'], evopca_merged)

    evopca_merged.to_csv(ecoregion_evopca_eucl_dist_file, index=False)