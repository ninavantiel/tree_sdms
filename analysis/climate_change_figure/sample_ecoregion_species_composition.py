import os
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

# function to compute per ecoregion statistics of SDM changes when applied to present (1981-2010) and future (2071-2100 SSP 5.85) climate scenarios
def compute_eco_stats_ecoregion(ecoid):   
    if os.path.isfile(outfile(ecoid)):
        return    

    # get eco_geo by merging geometries of all ecoregion features with ECO_ID = ecoid (for some ECO_IDs there are mutliple features to take into account) and get ecoregion area
    eco_geo = ecoregions.filter(ee.Filter.eq('ECO_ID', ecoid)).geometry()
    
    # reduce species pool by selecting species whose SDM bounding box intersects with eco_geo
    species = sdm_bboxes.filterBounds(eco_geo).aggregate_array('species')
    print(f"{ecoid}: {species.length().getInfo()} species")

    # compute whether species have at least one non zero pixel in the ecoregion for current and future climate SDMs
    sdms_eco = sdms.filter(ee.Filter.inList('system:index', species)).map(
        lambda sdm: sdm.set(sdm.select(['covariates_1981_2010','covariates_2071_2100_ssp585']).reduceRegion(
            reducer = ee.Reducer.anyNonZero(), geometry = eco_geo, scale = scale_to_use.multiply(10), maxPixels = 1e13
        ))
    ).map(lambda sdm: ee.Feature(None, {'species': sdm.get('system:index'), 'current': sdm.get('covariates_1981_2010'), 'future': sdm.get('covariates_2071_2100_ssp585')}))

    print(f"{ecoid}: SAMPLING VALUES")
    done = False
    idle = 0
    while not done:
        try:
            props = ['species','current','future']
            #values = sdms_eco.getInfo()['features']
            #results = [','.join([str(item['properties'][p]) for p in props]) + '\n' for item in values]
            #done = True
            #print(f"{ecoid}: sampling done in one go")

            #print(f"{ecoid}: sampling failed in one go, trying in chunks")
            size = sdms_eco.size().getInfo()
            print(f"{ecoid}: sampling {size} elements")
            #print(sdms_eco.first().getInfo())
            chunk_vals = sdms_eco.aggregate_array('system:index').getInfo()
            chunksize = 50
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

    if not os.path.exists(outdir): os.makedirs(outdir)
    outdir_list = os.listdir(outdir)
    print(len(outdir_list), 'ecoregions done')

    if len(outdir_list) < n_ecoids:

        # for ecoid in ecoregion_ids:
        #     #econame = forest_ecoregions.filter(ee.Filter.eq('ECO_ID', ecoid)).first().get('ECO_NAME').getInfo()
        #     print(ecoid, 'SAMPLING...')
        #     start = time.time()
        #     compute_eco_stats_ecoregion(ecoid, outfile(ecoid))
        #     end = time.time()
        #     print('TIME', end-start)
            
        NPROC = 20
        with poolcontext(NPROC) as pool:
            results = pool.map(partial(compute_eco_stats_ecoregion), ecoregion_ids)

    '''
    # if all gridcells have been sampled, merge output files
	if len(outdir_list) == n_ecoids:		
        df_list = []
		# loop through files in output directory 
		for i, filename in enumerate(outdir_list):
			# get number of lines in file
			n = sum(1 for l in open(outdir + filename))

			# if files has at least 1 line, read with pandas
			if n != 0:
				#skip_idx = random.sample(range(1, n), int(n*(1-merge_subset_frac)))
				df = pd.read_csv(outdir + filename)#, skiprows=skip_idx)

				# get list of species that were not sampled for gridcell and add columns full of 0s for those species
				missing_species = [s for s in species if s not in df.columns]
				df = df.join(pd.DataFrame(np.zeros((df.shape[0], len(missing_species))), columns = missing_species))
				if i%10==0: print(i, n, df.shape)
				
				# sort columns of dataframe so they are in order (lon, lat, species)
				df = df[['x', 'y'] + species]
				
				# append to dataframe list
				df_list.append(df)
		
		# concatenate all dataframes in list and save as csv
		df_merge = pd.concat(df_list)
		df_merge.to_csv(outfile, index = False)
    '''