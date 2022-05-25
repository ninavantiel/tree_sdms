from config import *
from p1_sample_covariates import * 

grid_width = 2 # 30

terra_poly_low_res = composite.select(["Pixel_Lat"]).toInt().reduceToVectors(
  geometry = unbounded_geo,
  crs = composite.select("Abs_Lat").projection(),
  scale = composite.select("Abs_Lat").projection().nominalScale().getInfo()*10,
  geometryType = 'polygon',
  eightConnected = False,
  labelProperty = 'zone',
  maxPixels = 1e13
)

if __name__ == '__main__':
	print('...')
	# Generate n_pseudoabsences random points
	random_points = ee.FeatureCollection.randomPoints(region = terra_poly_low_res, points = n_pseudoabsences)
	print('......')
	n_points = random_points.size().getInfo()
	print(n_points)
	'''
	random_points = random_points.map(lambda p: p.set({
    	'lon': p.geometry().coordinates().get(0), 'lat': p.geometry().coordinates().get(1)
	}))
	'''

	# Sample covariate values for random points
	grids = generateGrid(unbounded_geo, grid_width)
	size = grids.size().getInfo()
	print(f"Grid size: {size}")

	origCols = list(FCDFconv(random_points.limit(1)).columns)
	bands = composite.bandNames().getInfo()+origCols
	
	with poolcontext(NPROC) as pool:
	    pool.map(partial(extract_and_write_grid, grids=grids, points=random_points, region=terra_poly, 
	    	outdir=sampled_pseudoabsences_localdir, outfile=merged_pseudoabsences_filepath, gridsize=size, bands=bands), range(0, size))
	
	merge_sampled_data(sampled_pseudoabsences_localdir, merged_pseudoabsences_filepath)
	check_output(sampled_pseudoabsences_localdir, merged_pseudoabsences_filepath, n_points, size)
