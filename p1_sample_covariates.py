from config import *

# Number of concurrent processors to use 
# Try 50 first. Decrease if getting lots of "Too many aggregation" errors (> 10/minute). Should be able to use at least 20. 
NPROC = 50

# Species to sample is passed as a command line argument
# Run script in command line with "python 1_sampled_covariates.py [species_name]"
args = sys.argv
species = args[1] if len(args) > 1 else None

# Composite multiband image to sample
composite = ee.Image(composite_to_sample)

terra_poly = composite.select(["Pixel_Lat"]).toInt().reduceToVectors(
  geometry = unbounded_geo,
  crs = composite.select("Abs_Lat").projection(),
  scale = composite.select("Abs_Lat").projection().nominalScale().getInfo(),
  geometryType = 'polygon',
  eightConnected = False,
  labelProperty = 'zone',
  maxPixels = 1e13
)

# Function to convert a FC to a pandas DataFrame
def FCDFconv(fc):
  features = fc.getInfo()['features']
  dictarray = []
  for f in features: 
    dict = f['properties']
    dictarray.append(dict)
  df = pd.DataFrame(dictarray)
  return df

# Generate grid covering region of interest with size*size rectangles
def generateGrid(region, size):
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
      return ee.Geometry.Rectangle([x1, y1, x1.add(dx), y1.add(dy)], None, False)
    return ee.List.sequence(0, bins.subtract(1)).map(f2)
  grid = ee.List.sequence(0, bins.subtract(1)).map(f1).flatten().flatten()
  return grid

# Extract composite image values for points in gridcell region
# Handles the too-many requests error by idling the worker with backof
def extract_grid(region, points, bands):
  success = False
  idle = 0

  result = []
  while not success:
    try:
      if int(points.filterBounds(ee.Feature(region).geometry()).size().getInfo()) < 12000:
        values = (composite.reduceRegions(
          collection = points.filterBounds(ee.Feature(region).geometry()), 
          reducer = ee.Reducer.first(), 
          scale = composite.projection().nominalScale().getInfo(),
          tileScale = 16
        ).toList(50000).getInfo())

        for item in values:
          values = item['properties']
          row = [str(values[key]) for key in bands]
          row = ",".join(row)
          result.append(row + "\n")

        # if len(result) > 0:
        #   print("Processed %d features" % len(result))
        
        return result

      else:
        pointsWithRandom = points.filterBounds(ee.Feature(region).geometry()).randomColumn()
        nPoints = pointsWithRandom.size().getInfo()
        # Number of subsets when trying to sample a FC that is too large
        nSubsets = round(int((nPoints/9000)), 0)+1
        # List of bins
        mapList = list(range(1, nSubsets+1))
        # List of breakpoints
        breakPoints = [x / nSubsets for x in [0]+mapList]
        print('FC too large: ', nPoints, ', splitting in ', nSubsets, ' subsets')
        result_sub = []
        # success = False
        for i in mapList:
          result_sub = []
          values = (composite.reduceRegions(
            collection = pointsWithRandom.filter(ee.Filter.And(ee.Filter.gte('random', breakPoints[i - 1]), ee.Filter.lte('random', breakPoints[i]))), 
            reducer = ee.Reducer.first(), 
            scale = composite.projection().nominalScale().getInfo(), 
            tileScale = 16
          ).toList(50000).getInfo())

          for item in values:
            values = item['properties']
            row = [str(values[key]) for key in bands]
            row = ",".join(row)
            result_sub.append(row + "\n")

          # print('Items added in subset ', i, ":", len(result_sub))
          result = result + result_sub
          print('Processed ', len(result), ' from', nPoints, 'after ', i, '/', nSubsets, 'subsets')

        return result

    except Exception as e:
      print(e)
      success = False
      idle = (1 if idle > 5 else idle + 1)
      print("idling for %d" % idle)
      sleep(idle)

# Call function to extract composite image values for points in gridcell region and write results locally
def extract_and_write_grid(n, grids, points, region, outdir, outfile, gridsize, bands):
  region = grids.get(n)
  results = extract_grid(region, points, bands)
  if len(results) > 0:
    print('Processed features: ', len(results))
  if len(results) > 0:
    outpath = outfile if gridsize == 1 else outdir + "sampled_%d.csv" % n
    #with open(outdir + "sampled_%d.csv" % n, "w") as f:
    with open(outpath, "w") as f:
      f.write(",".join(bands))
      f.write("\n")
      f.writelines(results)
      f.close()

# Generator for multiprocessing
@contextmanager
def poolcontext(*args, **kwargs):
    pool = multiprocessing.Pool(*args, **kwargs)
    yield pool
    pool.terminate()

# Merge sampled data files into one and remove non-merged dats
def merge_sampled_data(outdir, outfile):
  sampled_data = [outdir + f for f in os.listdir(outdir) if os.path.isfile(outdir + f)]
  print(f"{len(sampled_data)} files to merge")

  fout = open(outfile,"a")
  # first file:
  for line in open(sampled_data[0]): fout.write(line)
  # now the rest:    
  for num in range(1,len(sampled_data)):
    try:
      f = open(sampled_data[num])
      f.__next__()
      for line in f: fout.write(line)
      f.close()
    except IOError:
      pass
  fout.close()

  [os.remove(f) for f in sampled_data]
  os.rmdir(outdir)

def run_sampling(points, n_points, outdir, outfile):
  # Number of gridcells to use (gridsize = GRID_WIDTH*GRID_WIDTH) 
  grid_width = 1 if n_points < 1000 else (10 if n_points < 10000 else 30)

  # Get column names of FC to sample
  origCols = list(FCDFconv(points.limit(1)).columns)

  # Bands to sample: all bands in image plus variables present in FC to sample
  bands = composite.bandNames().getInfo()+origCols

  # Generate grid for sampling
  grids = generateGrid(unbounded_geo, grid_width)
  size = grids.size().getInfo()
  print(f"Grid size: {size}")

  # If multiple files will be generated, create a directory
  if size != 1: os.makedirs(outdir)

  # Run sampling on each gridcell with multiprocessing
  with poolcontext(NPROC) as pool:
    pool.map(partial(extract_and_write_grid, grids=grids, points=points, region=terra_poly, outdir=outdir, outfile=outfile, gridsize=size, bands=bands), range(0, size))

  # If grid was not of size 1, merge sampled data files
  if size != 1: merge_sampled_data(outdir, outfile)

# Check that final output file contains enough rows 
def upload_output(outfile, n_points, gcsb_path, asset_id):
  with open(outfile) as f: n_lines = sum(1 for line in f)
  print(f"{n_lines} in output for {n_points} in fc")
  if n_lines < n_points + 1:  
    print(f"ERROR -> {n_lines} lines for {n_points} sampled points in {outfile}")
    os.remove(outfile)
  else:
    print("Sampling successfull!")
    subprocess.run(['gsutil', 'cp', outfile, gcsb_path])
    subprocess.run([earthengine, 'upload', 'table', '--x_column', 'Pixel_Long', '--y_column', 'Pixel_Lat', '--asset_id', asset_id, gcsb_path])
  
if __name__ == '__main__':
  outdir = sampled_data_localdir + "/" + species + "/"
  outfile = merged_data_localdir + "/" + species + ".csv"

  # If sampled data dir exists, remove it and its content to start clean
  if os.path.exists(outdir): 
      outdir_ls = [outdir + f for f in os.listdir(outdir) if os.path.isfile(outdir + f)]
      [os.remove(f) for f in outdir_ls]
      os.rmdir(outdir)

  # Get feature collection of occurences of species of interest 
  points = ee.FeatureCollection(species_occurence_fc).filter(ee.Filter.eq('species', species))
    
  # If there are less than min_n_points, exit script
  n_points = points.size().getInfo()
  if n_points < min_n_points:
    sys.exit(f"* {species}: {n_points} points -> no sampling")
  print(f"*** {species}: {n_points} points to sample")

  # If sampled data file exists, go directly to upload
  if os.path.exists(outfile): print("Sampling already done, skipping to upload")
  # If sampled data file does not exist, sample data
  else: run_sampling(points, n_points, outdir, outfile)

  # If final file has the correct number of rows, upload to earthengine
  upload_output(outfile, n_points, bucket_path + '/merged_data/' + species + '.csv', sampled_data_dir + '/' + species)


  

  

  






