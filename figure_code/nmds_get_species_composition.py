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

gridsize = 200
chunksize = 5000 
scaling_factor = 100
merge_subset_frac = 1#0.1#1 # cannot be 0, maximum 1

sdms = ee.ImageCollection('projects/crowtherlab/nina/treemap/sdms_binary').filter(ee.Filter.gte('nobs',90))
sdm_sum = ee.Image('projects/crowtherlab/nina/treemap_figures/sdm_sum')
sdm_bboxes = ee.FeatureCollection('projects/crowtherlab/nina/treemap_figures/sdms_bbox').filter(ee.Filter.inList('species', sdms.aggregate_array('system:index')))
scale_to_use = sdms.first().projection().nominalScale().multiply(scaling_factor)
def unmask_mask(img): return img.mask(img.mask().gte(0.5)).unmask(0, False)
sdms_current = sdms.map(lambda sdm: unmask_mask(sdm.select('covariates_1981_2010')).reproject(crs = 'EPSG:4326', scale = scale_to_use))
pixel_image = ee.Image.pixelCoordinates(sdms_current.first().projection())

unbounded_geo = ee.Geometry.Polygon([-180, 88, 0, 88, 180, 88, 180, -88, 0, -88, -180, -88], None, False)

outdir = '../treemap_figures_data/sampled_species_composition/gridsize_' + str(gridsize) + '_scale_' + str(int(scale_to_use.getInfo())) + '/'
outfile = '../treemap_figures_data/sampled_species_composition/species_data_scale_' + str(int(scale_to_use.getInfo())) + (
	('_subset_' + str(int(merge_subset_frac*100)) + 'percent.csv') if merge_subset_frac != 1 else '.csv')

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

def get_sampled_values(sampled, props):
	values = sampled.getInfo()['features']
	return [','.join([str(item['properties'][p]) for p in props]) + '\n' for item in values]

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
	gridcell = grid.get(n)
	grid_filepath = outdir + 'grid_' + str(n) + '.csv' 
	#str(ee.Feature(gridcell).get('x').getInfo()) + '_' + str(ee.Feature(gridcell).get('y').getInfo()) + '.csv' 
	#grid_filepath = outdir + 'grid_' + str(n) + '_' + str(int(ee.Feature(gridcell).get('x').getInfo())) + '_latlon_' + str(int(ee.Feature(gridcell).get('y').getInfo())) + '.csv' 
	#print(f"Gridcell {n} output file path: {grid_filepath.split(outdir)[1]} ({grid_filepath})") 
	if os.path.exists(grid_filepath): 
		#print(f"{n}: already sampled (.)")
		return

	gridcell_species = sdm_bboxes.filterBounds(ee.Feature(gridcell).geometry()).aggregate_array('species')
	n_gridcell_species = gridcell_species.size().getInfo()
	#print(f"{n}: sampling {n_gridcell_species} species...")
	props = gridcell_species.getInfo() + ['x', 'y']

	gridcell_sdms = sdms_current.filter(ee.Filter.inList('system:index', gridcell_species))
	image_to_sample = gridcell_sdms.toBands().mask(gridcell_sdms.sum()).addBands(pixel_image)
	sampled = image_to_sample.sample(ee.Feature(gridcell).geometry()).map(
		lambda f: f.select(f.propertyNames(), f.propertyNames().map(
			lambda x: ee.String(x).replace('_covariates_1981_2010','')
		))
	)

	done = False
	idle = 0
	while not done:
		if os.path.exists(grid_filepath): 
			print(f"{n}: already sampled (..)")
			return
		
		try:
			n_sampled = sampled.size().getInfo()
			print(f"{n}: {n_gridcell_species} species to sample at {n_sampled} points...")
			if n_sampled == 0: 
				#print(f"{n}: empty gridcell")
				write_results([], grid_filepath, props)
				return
			if os.path.exists(grid_filepath): 
				print(f"{n}: already sampled (...)")
				return

			chunk_vals = sampled.aggregate_array('system:index').getInfo()
			results = []
			for i in range(int(n_sampled/chunksize) + 1):
				chunk_results = get_sampled_values(sampled.filter(ee.Filter.inList('system:index', chunk_vals[i*chunksize:(i+1)*chunksize])), props)
				results = results + chunk_results
				print(f"{n}: {len(chunk_results)} elements processed for chunk {i+1}/{int(n_sampled/chunksize)+1} -> {len(results)}/{n_sampled} elements processed")
			write_results(results, grid_filepath, props)

		except Exception as e:
			print(e)
			return
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
	print('Scale:', scale_to_use.getInfo())

	print('Outdir:', outdir)
	if not os.path.exists(outdir): os.makedirs(outdir)
	outdir_list = os.listdir(outdir)
	
	print('Outfile:', outfile)
	if os.path.exists(outfile): sys.exit('Sampled species data file already exists.')
	grid = sdm_sum.reduceRegions(
		collection = generateGrid(unbounded_geo, gridsize), reducer = ee.Reducer.anyNonZero(), scale = scale_to_use
	).filter(ee.Filter.eq('any', 1)).map(
		lambda f: f.set(ee.Dictionary.fromLists(['x','y'], ee.List(f.geometry().coordinates().get(0)).get(0)))
	)
	n_gridcells = grid.size().getInfo()
	print(f"Grid size: {n_gridcells}")
	print(f"Gridcells done: {len(outdir_list)}")
	
	if len(outdir_list) < n_gridcells:
		grid_list = grid.toList(n_gridcells)
		NPROC = 50
		with poolcontext(NPROC) as pool:
			results = pool.map(partial(sample_species_data, grid=grid_list, outdir=outdir), range(0, n_gridcells))
		
		outdir_list = os.listdir(outdir)
		print(f"Gridcells done: {len(outdir_list)} / {n_gridcells}")

	# If all gridcells have been sampled, merge output files
	if len(outdir_list) == n_gridcells:
		species = sdms.aggregate_array('system:index').getInfo()
		df_list = []

		for i, filename in enumerate(outdir_list):
			n = sum(1 for l in open(outdir + filename))
			if n != 0:
				skip_idx = random.sample(range(1, n), int(n*(1-merge_subset_frac)))
				df = pd.read_csv(outdir + filename, skiprows=skip_idx)
				missing_species = [s for s in species if s not in df.columns]
				df = df.join(pd.DataFrame(np.zeros((df.shape[0], len(missing_species))), columns = missing_species))
				if i%10==0: print(i, n, df.shape)
				df = df[['x', 'y'] + species]
				df_list.append(df)
		df_merge = pd.concat(df_list)
		df_merge.to_csv(outfile, index = False)
