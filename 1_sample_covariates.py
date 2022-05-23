from config import *

# Species to sample is passed as a command line argument
# Run script in command line with "python 1_sampled_covariates.py [species_name]"
species = sys.argv[1]

outdir = "sampled_data/" + species + "/"
outfile = "merged_data/" + species + ".csv"

# Get feature collection of occurences of species of interest 
points = ee.FeatureCollection(species_occurence_fc).filter(ee.Filter.eq('species', species))
n_points = points.size().getInfo()

# Number of gridcells to use (gridsize = GRID_WIDTH*GRID_WIDTH) 
GRID_WIDTH = 1 if n_points < 1000 else (10 if n_points < 10000 else 30)

# Number of concurrent processors to use 
# Try 50 first. Decrease if getting lots of "Too many aggregation" errors (> 10/minute). Should be able to use at least 20. 
NPROC = 50

# Composite multiband image to sample
compositeToUse = ee.Image(composite_to_sample)

# Function to convert a FC to a pandas DataFrame
def FCDFconv(fc):
  features = fc.getInfo()['features']
  dictarray = []
  for f in features: 
    dict = f['properties']
    dictarray.append(dict)
  df = pd.DataFrame(dictarray)
  return df

# Get column names of FC to sample
origCols = list(FCDFconv(points.limit(1)).columns)

# Bands to sample. Default: all bands in image plus variables present in FC to sample
BANDS = compositeToUse.bandNames().getInfo()+origCols

# Extract composite image values for points in gridcell region
# Handles the too-many requests error by idling the worker with backof
def extract_grid(region, points):
  success = False
  idle = 0

  result = []
  while not success:
    try:
      if int(points.filterBounds(ee.Feature(region).geometry()).size().getInfo()) < 12000:
        values = (compositeToUse.reduceRegions(
          collection = points.filterBounds(ee.Feature(region).geometry()), 
          reducer = ee.Reducer.first(), 
          scale = compositeToUse.projection().nominalScale().getInfo(),
          tileScale = 16
        ).toList(50000).getInfo())

        for item in values:
          values = item['properties']
          row = [str(values[key]) for key in BANDS]
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
          values = (compositeToUse.reduceRegions(
            collection = pointsWithRandom.filter(ee.Filter.And(ee.Filter.gte('random', breakPoints[i - 1]), ee.Filter.lte('random', breakPoints[i]))), 
            reducer = ee.Reducer.first(), 
            scale = compositeToUse.projection().nominalScale().getInfo(), 
            tileScale = 16
          ).toList(50000).getInfo())

          for item in values:
            values = item['properties']
            row = [str(values[key]) for key in BANDS]
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
def extract_and_write_grid(n, grids, points, region):
  region = grids.get(n)
  results = extract_grid(region, points)
  if len(results) > 0:
    print('Processed features: ', len(results))
  if len(results) > 0:
    with open(outdir + "sampled_%d.csv" % n, "w") as f:
      f.write(",".join(BANDS))
      f.write("\n")
      f.writelines(results)
      f.close()

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

# Generator for multiprocessing
@contextmanager
def poolcontext(*args, **kwargs):
    pool = multiprocessing.Pool(*args, **kwargs)
    yield pool
    pool.terminate()

if __name__ == '__main__':
  if points.size().getInfo() < min_n_points:
    sys.exit(f"* {species}: {n_points} points -> no sampling")
  print(f"*** {species}: {n_points} points to sample")
  if not os.path.exists(outdir): os.makedirs(outdir)
  else: sys.exit("ERROR -> sampled_data dir exists but merged_data file does not exist")

  unboundedGeo = ee.Geometry.Polygon([[[-180, 88], [180, 88], [180, -88], [-180, -88]]], None, False)
  terra_poly = compositeToUse.select(["Pixel_Lat"]).toInt().reduceToVectors(
    geometry= unboundedGeo,
    crs= compositeToUse.select("Abs_Lat").projection(),
    scale= compositeToUse.select("Abs_Lat").projection().nominalScale().getInfo(),
    geometryType= 'polygon',
    eightConnected= False,
    labelProperty= 'zone',
    maxPixels= 1e13
  )

  grids = generateGrid(unboundedGeo, GRID_WIDTH)
  size = grids.size().getInfo()
  print("Grid size: %d " % size)

  with poolcontext(NPROC) as pool:
    #results = 
    pool.map(partial(extract_and_write_grid, grids=grids, points=points, region=terra_poly), range(0, size))

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

  with open(outfile) as f: n_lines = sum(1 for line in f)
  if n_lines == n_points + 1: 
    print("Sampling successfull, removing files")
    [os.remove(f) for f in sampled_data]
    os.rmdir(outdir)
  else:
    print(f"ERROR -> {n_lines} lines for {n_points} sampled points in {outfile}")






