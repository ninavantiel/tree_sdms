from config import * 

# Function to compute considered range for a given species
def compute_range(species, export = True):
	print(f"... {species}")

	# Compute reported native range with country geometries + 1000km buffer
	native_regions = native_regions_table.filterMetadata('taxon', 'equals', species.replace('_', ' ')).aggregate_array('country') 
	if native_regions.length().getInfo() > 0: 
		print(native_regions.getInfo())
		native_range = region_geo_buffer.filter(ee.Filter.inList('country_na', native_regions)).union().geometry()

	# If there is no reported native range, no modelling
	else: 
		print('No native countries information -> no modelling')
		return 

	# Get prepped observation points and filter to native range
	obs_points = ee.FeatureCollection(obs_points_dir + '/' + species).filterBounds(native_range)
	nobs = obs_points.size().getInfo()
	print(f"{nobs} obsevations in native range")
	
	# If there are less than 4 observations in the native range, do not compute range
	if nobs < 4:
		print('Less than 4 observations -> no range')
		return
	
	# If there are more than 10k observation in the native range aggregate points 
	# Aggregation by removing one decimal point on the coordinates (int(x*10)/10) and taking distinct geometries
	if nobs > 10000:
		obs_points = obs_points.map(lambda f: f.setGeometry(ee.Geometry.Point([
			f.geometry().coordinates().getNumber(0).multiply(10).round().divide(10), 
			f.geometry().coordinates().getNumber(1).multiply(10).round().divide(10)
		]))).distinct('.geo')
		nobs = obs_points.size().getInfo()
		print(f"aggregated to {nobs} points")

		# If there are more than 15k observation in the native range aggregate points again
		# Aggregation by simplifying decimal point on the coordinates (int(x*5)/5) and taking distinct geometries
		if nobs > 15000:
			obs_points = obs_points.map(lambda f: f.setGeometry(ee.Geometry.Point([
				f.geometry().coordinates().getNumber(0).multiply(5).round().divide(5), f.geometry().coordinates().getNumber(1).multiply(5).round().divide(5)
			]))).distinct('.geo')
			#nobs = obs_points.size().getInfo()
			print('aggregated again')

	# Filter outliers (points with less than 4 neighbors in 1000 km range) 
	spatialFilter = ee.Filter.withinDistance(distance = 1e6, leftField = '.geo', rightField = '.geo', maxError = 1e5)
	obs_neighbors = ee.Join.saveAll(matchesKey = 'neighbors', measureKey = 'distance', ordering = 'distance').apply(
		primary = obs_points, secondary = obs_points, condition = spatialFilter)
	obs_points = obs_neighbors.map(
		lambda f: f.set('neighSize', ee.List(f.get('neighbors')).size())
	).filterMetadata('neighSize', 'greater_than', 3)
	
	if obs_points.size().getInfo() == 0:
		print('No points in native range with enough neighbours -> no range')
		return

	# Contruct observation-based range, using the geometries of ecoregions in which observations are found
	# Get list of ecoregions in which there are observations 
	# Removing 9999, which is a placeholder for points that have no value for ecoregion
	ecoregion_list = obs_points.aggregate_array('Resolve_Ecoregion').distinct().remove(9999)

	# Determine small/large ecoregions based on the max distance of the bounds of the ecoregions
	def prep_ecoregions(eco):
		eco_fc = ecoregions.filterMetadata('ECO_ID', 'equals', eco)
		eco_f = ee.Feature(eco_fc.first()).setGeometry(eco_fc.union())
		eco_bounds = ee.List(eco_f.geometry().bounds().coordinates().get(0))
		max_dist = ee.Geometry.Point(eco_bounds.get(0)).distance(ee.Geometry.Point(eco_bounds.get(2)))
		return eco_f.set({'max_dist': max_dist})
	ecoregion_fc = ee.FeatureCollection(ecoregion_list.map(prep_ecoregions))

	# Small ecoregions (max distance < 1000 km): consider ecoregion geometry + 1000km buffer
	small_ecoregions = ecoregion_fc.filter(ee.Filter.lte('max_dist', 1e6))
	small_ecoregions_range = small_ecoregions.map(lambda f: f.setGeometry(f.geometry().buffer(1e6, 1e5)))

	# Large ecoregions (max distance > 1000 km): consider 250km buffer around observations in ecoregion + 1000km buffer
	# The intent is to not consider the full ecoregion if points are not found throughout the whole ecoregion
	# This is only relevant for ecoregions that are larger than the 1000km buffer applied afterwards
	def buffer_points_ecoregion(eco):
		eco_id = eco.get('ECO_ID')
		pts = obs_points.filterMetadata('Resolve_Ecoregion', 'equals', eco_id)
		eco_geo = pts.geometry().buffer(2e5, 100).intersection(eco.geometry(), 100)
		eco_geo_buffer = eco_geo.buffer(1e6, 1e5)
		return ee.Feature(eco).setGeometry(eco_geo_buffer)
	large_ecoregions = ecoregion_fc.filter(ee.Filter.gt('max_dist', 1e6))
	large_ecoregions_range = large_ecoregions.map (buffer_points_ecoregion)

	# Observation-based range is the union of range constructed for each considered ecoregion
	obs_range = ee.FeatureCollection(small_ecoregions_range.merge(large_ecoregions_range)).union().geometry()

	# Final considered range is the intersection of the observation-base range and the reported native range
	final_range = obs_range.intersection(native_range, 100)
	'''
	if final_range.area().getInfo() == 0: 
		print('Empty range -> no export')
		return
	'''
	# Export range
	if export: 
		export_fc(ee.FeatureCollection([ee.Feature(final_range, {})]), 'obs_range_' + species, obs_range_dir + '/' + species)

# Get list of species for which we have prepped observations, ie. that are ready for the compute_range function
obs_done = subprocess.run([earthengine, 'ls', obs_points_dir], stdout=subprocess.PIPE).stdout.decode('utf-8')
obs_done_species = set([x.replace('\n','') for x in obs_done.split(
    '\nprojects/earthengine-legacy/assets/' + obs_points_dir + '/')[1:]
])

# Get list of species that have already gone through the compute_range function
range_done = subprocess.run([earthengine, 'ls', obs_range_dir], stdout=subprocess.PIPE).stdout.decode('utf-8')
range_done_species = set([x.replace('\n','') for x in range_done.split(
    '\nprojects/earthengine-legacy/assets/' + obs_range_dir + '/')[1:]
])

# Run compute_range for species for which observations have been prepped but for which the range has not been constructed
print(f"{len(range_done_species)} species with range done out of {len(obs_done_species)} species with prepped observations")
print(f"-> {len(species_list.intersection(obs_done_species).difference(range_done_species))} species to run")

for species in set(species_list).intersection(set(obs_done_species).difference(range_done_species)): 
	compute_range(species, True)



