import ee
ee.Initialize()

import os
import sys
import random
import pandas as pd
import numpy as np
from time import sleep
from functools import partial
from contextlib import contextmanager
import multiprocessing

scaling_factor = 100 # original scale is 30 arc seconds, sampling scale will be 30*[scaling_factor] arc seconds
sdm_band = 'covariates_2071_2100_ssp585'

gridsize = 200
chunksize = 5000 

sdms = ee.ImageCollection('projects/crowtherlab/nina/treemap/sdms_binary').filter(ee.Filter.gte('nobs',90))
sdm_sum = ee.Image('projects/crowtherlab/nina/treemap_figures/sdm_sum')
sdm_bboxes = ee.FeatureCollection('projects/crowtherlab/nina/treemap_figures/sdms_bbox').filter(ee.Filter.inList('species', sdms.aggregate_array('system:index')))
scale_to_use = sdms.first().projection().nominalScale().multiply(scaling_factor)

def unmask_mask(img): return img.mask(img.mask().gte(0.5)).unmask(0, False)
sdms_to_sample = sdms.map(lambda sdm: unmask_mask(sdm.select(sdm_band)).reproject(crs = 'EPSG:4326', scale = scale_to_use))
pixel_image = ee.Image.pixelCoordinates(sdms_to_sample.first().projection())

unbounded_geo = ee.Geometry.Polygon([-180, 88, 0, 88, 180, 88, 180, -88, 0, -88, -180, -88], None, False)

os.chdir('/Users/nina/Documents/treemap/treemap/')
outdir = 'data/species_data_' + sdm_band + '_gridsize_' + str(gridsize) + '_scale_' + str(int(scale_to_use.getInfo())) + '/'
outfile = 'data/species_data_' + sdm_band + '_scale_' + str(int(scale_to_use.getInfo())) + '.csv'

def generateGrid(region, size):
	"""Generate a grid covering the region with size*size rectangles"""
	bins = ee.Number(size)
	coords = ee.List(region.coordinates().get(0))
	xs = coords.map(lambda l : ee.List(l).get(0))
	ys = coords.map(lambda l : ee.List(l).get(1))

	xmin = ee.Number(xs.reduce(ee.Reducer.min()))
	xmax = ee.Number(xs.reduce(ee.Reducer.max()))
	ymin = ee.Number(ys.reduce(ee.Reducer.min()))
	ymax = ee.Number(ys.reduce(ee.Reducer.max()))

	dx = xmax.subtract(xmin).divide(bins)
	dy = ymax.subtract(ymin).divide(bins)

	def f1(n):
		def f2(m):
			x1 = xmin.add(dx.multiply(n))
			y1 = ymin.add(dy.multiply(m))
			return ee.Feature(ee.Geometry.Rectangle([x1, y1, x1.add(dx), y1.add(dy)], None, False), {})
		return ee.List.sequence(0, bins.subtract(1)).map(f2)
	grid = ee.FeatureCollection(ee.List.sequence(0, bins.subtract(1)).map(f1).flatten().flatten())
	return grid

def write_results(results, filepath, props):
	if len(results) > 0:
		print(f"Writing {len(results)} rows in file {filepath}")
		with open(filepath, "w") as f:
			f.write(",".join(props))
			f.write("\n")
			f.writelines(results)
			f.close()
	else: 
		print(f"Writing empty file ({len(results)} rows) in {filepath}")
		with open(filepath, "w") as f:
			f.close()

def sample_species_data(n, grid, outdir):
	# get gridcell 
	gridcell = grid.get(n)

	# path to output file for sampled data from gridcell
	# if file already exists, return
	grid_filepath = outdir + 'grid_' + str(n) + '.csv' 
	if os.path.exists(grid_filepath): 
		return

	# get list of species that may be in gricell based on SDM bounding boxes
	gridcell_species = sdm_bboxes.filterBounds(ee.Feature(gridcell).geometry()).aggregate_array('species')
	n_gridcell_species = gridcell_species.size().getInfo()
	props = gridcell_species.getInfo() + ['x', 'y']

	# filter SDMs to get species that are in gridcell and convert from ImageCollection to multi-band Image
	gridcell_sdms = sdms_to_sample.filter(ee.Filter.inList('system:index', gridcell_species))
	image_to_sample = gridcell_sdms.toBands().mask(gridcell_sdms.sum()).addBands(pixel_image)

	# sample multi-band Image within geometry and rename bands 
	sampled = image_to_sample.sample(ee.Feature(gridcell).geometry()).map(
		lambda f: f.select(f.propertyNames(), f.propertyNames().map(
			lambda x: ee.String(x).replace(ee.String('_').cat(sdm_band),'')
		))
	)

	# get sampled data locally and save in output file
	done = False
	idle = 0
	while not done:
		# if output file exists, sampling was already done, return 
		if os.path.exists(grid_filepath): 
			print(f"{n}: already sampled")
			return
		
		try:
			# get number of sampled species and sites (pixels) in gridcell
			n_sampled = sampled.size().getInfo()
			print(f"{n}: {n_gridcell_species} species to sample at {n_sampled} points...")

			# if 0 sites were sampled, empty gridcell, return
			if n_sampled == 0: 
				#print(f"{n}: empty gridcell")
				write_results([], grid_filepath, props)
				return

			# if output file exists, sampling was already done, return 
			if os.path.exists(grid_filepath): 
				print(f"{n}: already sampled (...)")
				return

			# get list of indices for sampled sites
			# sites will be processed in "chunsize" sized batches
			# for every chunk get values for sites and append to results
			chunk_vals = sampled.aggregate_array('system:index').getInfo()
			results = []
			for i in range(int(n_sampled/chunksize) + 1):
				values = sampled.filter(ee.Filter.inList('system:index', chunk_vals[i*chunksize:(i+1)*chunksize])).getInfo()['features']
				chunk_results = [','.join([str(item['properties'][p]) for p in props]) + '\n' for item in values]
				results = results + chunk_results
				print(f"{n}: {len(chunk_results)} elements processed for chunk {i+1}/{int(n_sampled/chunksize)+1} -> {len(results)}/{n_sampled} elements processed")
			
			# write results into csv with "write_results" function
			write_results(results, grid_filepath, props)

		except Exception as e:
			#print(e)
			#return
			done = False
			idle = (1 if idle > 5 else idle + 1)
			print("idling for %d" % idle)
			sleep(idle)

@contextmanager
def poolcontext(*args, **kwargs):
    """This just makes the multiprocessing easier with a generator."""
    pool = multiprocessing.Pool(*args, **kwargs)
    yield pool
    pool.terminate()

if __name__ == '__main__':
	# print scale at which SDM data will be sampled (30 arc-seconds * scaling_factor)
	print('Scale:', scale_to_use.getInfo())

	# print path to output directory for sampled data, create directory if it does not exist
	print('Ouput directory:', outdir)
	if not os.path.exists(outdir): os.makedirs(outdir)
	outdir_list = os.listdir(outdir)
	
	# print path to output file for merged sampled data
	# if file exists, do not continue script
	print('Output file:', outfile)
	if os.path.exists(outfile): sys.exit('Sampled species data file already exists.')

	# create grid and filter out gridcells in which there is no SDM data (in the oceans)
	grid = sdm_sum.reduceRegions(
		collection = generateGrid(unbounded_geo, gridsize), reducer = ee.Reducer.anyNonZero(), scale = scale_to_use
	).filter(ee.Filter.eq('any', 1)).map(
		lambda f: f.set(ee.Dictionary.fromLists(['x','y'], ee.List(f.geometry().coordinates().get(0)).get(0)))
	)

	# print number of gridcells remaining in grid and number of gridcells already sampled
	n_gridcells = grid.size().getInfo()
	print(f"Grid size: {n_gridcells}")
	print(f"Gridcells done: {len(outdir_list)}")
	
	# if not all gridcells have been sampled, sample them
	if len(outdir_list) < n_gridcells:
		# convert grid from FeatureCollection to List
		grid_list = grid.toList(n_gridcells)

		# set up multi-processing context with number of processes NPROC
		NPROC = 50
		with poolcontext(NPROC) as pool:
			# apply sampling function "sample_species_data" to each gridcell in the grid List with specified output directory
			# if gricell is not empty, writes results for each gridcell in a file in output directory
			results = pool.map(partial(sample_species_data, grid=grid_list, outdir=outdir), range(0, n_gridcells))
		
		outdir_list = os.listdir(outdir)
		print(f"Gridcells done: {len(outdir_list)} / {n_gridcells}")

	# if all gridcells have been sampled, merge output files
	if len(outdir_list) == n_gridcells:
		# get list of all species names
		species = sdms.aggregate_array('system:index').getInfo()
		
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
