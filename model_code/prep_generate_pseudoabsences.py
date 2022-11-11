from config import *
from p1_sample_covariates import * 

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
	outdir = sampled_pseudoabsences_localdir
	outfile = merged_pseudoabsences_filepath

	# If sampled dir exists, remove it and its content to start clean
	if os.path.exists(outdir): 
		outdir_ls = [outdir + f for f in os.listdir(outdir) if os.path.isfile(outdir + f)]
		[os.remove(f) for f in outdir_ls]
		os.rmdir(outdir)

	# Generate n_pseudoabsences random points
	random_points = ee.FeatureCollection.randomPoints(region = terra_poly_low_res, points = n_pseudoabsences).map(
		lambda p: p.set({'lon': p.geometry().coordinates().get(0), 'lat': p.geometry().coordinates().get(1)	}))
	n_points = random_points.size().getInfo()
	print(n_points)

	# If sampled data file exists, go directly to upload
	if os.path.exists(outfile): print("Sampling already done, skipping to upload")
	# If sampled data file does not exist, sample data
	else: run_sampling(random_points, n_points, outdir, outfile)

	# If final file has the correct number of rows, upload to earthengine
	upload_output(outfile, n_points, bucket_path + '/pseudoabsences_n' + str(n_points) + '.csv', treemap_dir + '/pseudoabsences_n' + str(n_points))
