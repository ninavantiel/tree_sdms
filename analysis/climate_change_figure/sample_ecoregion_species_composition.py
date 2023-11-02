from contextlib import contextmanager
import multiprocessing
from functools import partial
import time
import sys
sys.path.insert(0, '/Users/nina/Documents/treemap/treemap/analysis')
from config_figures import *

os.chdir('/Users/nina/Documents/treemap/treemap/')
outdir = 'data/ecoregion_species_composition/'

def outfile(ecoid):
    return outdir + 'ecoregion_' + str(ecoid) + '.csv'

def get_ecoregion_species(ecoid):
    """Compute which species are present in ecoregion"""
    if os.path.isfile(outfile(ecoid)):
        return    

    # get eco_geo by merging geometries of all ecoregion features with ECO_ID = ecoid
    eco_geo = ecoregions.filter(ee.Filter.eq('ECO_ID', ecoid)).geometry()
    
    # reduce species pool by selecting species whose SDM bounding box intersects with eco_geo
    species = sdm_bboxes.filterBounds(eco_geo).aggregate_array('species')
    print(f"{ecoid}: {species.length().getInfo()} species")

    # compute whether species have at least one non zero pixel in the ecoregion for current and future climate SDMs
    sdms_eco = sdms.filter(ee.Filter.inList('system:index', species)).map(
        lambda sdm: sdm.set(sdm.select(['covariates_1981_2010','covariates_2071_2100_ssp585']).reduceRegion(
            reducer = ee.Reducer.anyNonZero(), geometry = eco_geo, scale = scale_to_use, maxPixels = 1e13
        ))
    ).map(lambda sdm: ee.Feature(None, {'species': sdm.get('system:index'), 'current': sdm.get('covariates_1981_2010'), 'future': sdm.get('covariates_2071_2100_ssp585')}))

	# get sampled data locally and save in output file
    done = False
    idle = 0
    while not done:
        try:           
            # get number of sampled species in gridcell
            size = sdms_eco.size().getInfo()
            print(f"{ecoid}: sampling {size} elements")

            # get list of indices for sampled species
			# species will be processed in "chunsize" sized batches
			# for every chunk get values for species and append to results
            chunk_vals = sdms_eco.aggregate_array('system:index').getInfo()
            chunksize = 100
            props = ['species','current','future']
            results = []
            for i in range(int(size/chunksize) + 1):
                values = sdms_eco.filter(ee.Filter.inList('system:index', chunk_vals[i*chunksize:(i+1)*chunksize])).getInfo()['features']
                chunk_results = [','.join([str(item['properties'][p]) for p in props]) + '\n' for item in values]
                results = results + chunk_results
                print(f"{ecoid}: {len(chunk_results)} elements processed for chunk {i+1}/{int(size/chunksize)+1} -> {len(results)}/{size} elements processed")

            if len(results) == size: done = True

        except Exception as e:
            done = False
            idle = (1 if idle > 5 else idle + 1)
            print(ecoid, " idling for %d" % idle)
            time.sleep(idle)      
    
    # write results into csv file
    print(f"{ecoid}: WRITING FILE")
    with open(outfile(ecoid), "w") as f:
        f.write(",".join(props))
        f.write("\n")
        f.writelines(results)
        f.close()
        
    return   

@contextmanager
def poolcontext(*args, **kwargs):
    """This just makes the multiprocessing easier with a generator."""
    pool = multiprocessing.Pool(*args, **kwargs)
    yield pool
    pool.terminate()

if __name__ == '__main__':
    forest_ecoregions = ecoregions.filter(ee.Filter.stringContains('BIOME_NAME', 'Forest'))
    ecoregion_ids = forest_ecoregions.aggregate_array('ECO_ID').distinct().getInfo()
    n_ecoids = len(ecoregion_ids)
    print(n_ecoids, 'ecoregions')

	# create directory if it does not exist
    if not os.path.exists(outdir): os.makedirs(outdir)
    # print number of ecoregions already sampled
    outdir_list = os.listdir(outdir)
    print(len(outdir_list), 'ecoregions done')

	# if not all ecoregions have been sampled, sample them
    if len(outdir_list) < n_ecoids:
        NPROC = 10
        with poolcontext(NPROC) as pool:
            results = pool.map(partial(get_ecoregion_species), ecoregion_ids)

    # if all ecoregions have been sampled, merge output files
    if len(outdir_list) == n_ecoids:	
        df_list = []
        species_list = sdms.aggregate_array('system:index').getInfo()

        for i, filename in enumerate(outdir_list):
            n = sum(1 for l in open(outdir + filename))
            
            # if files has at least 1 line, read with pandas
            if n != 0: 
                df = pd.read_csv(outdir + filename)
                missing_species = [s for s in species_list if s not in df.species.to_list()]
                df = pd.concat([df, pd.DataFrame({
                    'species': missing_species, 'current': np.zeros(len(missing_species)), 'future': np.zeros(len(missing_species))
                })]).set_index('species').T
                df.index = [filename.replace('.csv','_') + x for x in df.index]
                
                # sort columns to be in the oder of the species list
                df = df[species_list]
                assert df.shape == (2, 10590)
                df_list.append(df)

        df_merge = pd.concat(df_list)
        print(df_merge.shape)
        df_merge.to_csv('data/ecoregion_species_sampled.csv', index = True, index_label='site')
