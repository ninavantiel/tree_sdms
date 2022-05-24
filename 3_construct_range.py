from config import *

# Species for which to construct range is passed as a command line argument
# Run script in command line with "python 3_construct range.py [species_name]"
species = sys.argv[1]

# From an ecoregion id, constructs a feature with the ecoregion's geometry and the maximum width/height of its bbox 
def prep_ecoregions(eco_id):
	eco_fc = ee.FeatureCollection(ecoregions).filterMetadata('ECO_ID', 'equals', eco_id)
	eco_f = ee.Feature(eco_fc.first()).setGeometry(eco_fc.union())
	eco_bounds = ee.List(eco_f.geometry().bounds().coordinates().get(0))
	max_dist = ee.Geometry.Point(eco_bounds.get(0)).distance(ee.Geometry.Point(eco_bounds.get(2)))
	return eco_f.set({'max_dist': max_dist})

if __name__ == '__main__':
	# NATIVE RANGE
	# Get list of countries in reported native range
	native_countries = ee.FeatureCollection(native_countries_fc).filterMetadata('taxon', 'equals', species.replace('_', ' ')).aggregate_array('country')

	# If there is no data on native countries, species wil not be modelled
	if native_countries.length().getInfo() == 0:
		sys.exit(f"No native countries data -> no range")

	# Construct native countries range 
	native_range = ee.FeatureCollection(countries_geometries).filter(ee.Filter.inList('country_na', native_countries)).union().geometry()

	# OCCURRENCE RANGE
	# Get prepped occurences and filter to native countries range
	points = ee.FeatureCollection(prepped_occurrences_dir + '/' + species).filterBounds(native_range)
	n_points = points.size().getInfo()
	print(f"{n_points} occurrences in native range")
	
	# If there are less than 20 observations in the native range, no modelling -> do not compute range 
	if n_points < min_n_points :
		sys.exit(f"Less than {min_n_points} points -> no range")

	# If there are more than 10k occurrences in the native range, aggregate points 
	# Aggregation by removing one decimal point on the coordinates (int(x*10)/10) and taking distinct geometries
	if n_points > 10000:
		points = points.map(lambda f: f.setGeometry(ee.Geometry.Point([
			f.geometry().coordinates().getNumber(0).multiply(10).round().divide(10), 
			f.geometry().coordinates().getNumber(1).multiply(10).round().divide(10)
		]))).distinct('.geo')
		n_points = points.size().getInfo()
		print(f"aggregated to {n_points} occurrences")

		# If there are still more than 15k occurrences in the native range, aggregate further
		# Aggregation by simplifying coordinate decimal point (int(x*5)/5) and taking distinct geometries
		if n_points > 15000:
			points = points.map(lambda f: f.setGeometry(ee.Geometry.Point([
				f.geometry().coordinates().getNumber(0).multiply(5).round().divide(5), f.geometry().coordinates().getNumber(1).multiply(5).round().divide(5)
			]))).distinct('.geo')
			#n_points = points.size().getInfo() 
			#print(f"aggregated to {n_points} occurrences")

	# Remove outliers (occurrences with less than 4 neighbors in 1000 km range) 
	spatial_filter = ee.Filter.withinDistance(distance = 1e6, leftField = '.geo', rightField = '.geo', maxError = 1e5)
	neighbors = ee.Join.saveAll(matchesKey = 'neighbors', measureKey = 'distance', ordering = 'distance').apply(
		primary = points, secondary = points, condition = spatial_filter)
	points = neighbors.map(lambda f: f.set('n_neighbors', ee.List(f.get('neighbors')).size())).filterMetadata('n_neighbors', 'greater_than', 3)
	
	if points.size().getInfo() == 0:
		sys.exit('No points in native range with enough neighbours -> no range')

	# Contruct occurrence range, using the geometries of ecoregions in which occurrences are found

	# Get list of ecoregions in which there are observations (9999 is a placeholder for points with no ecoregion value)
	eco_id_list = points.aggregate_array('Resolve_Ecoregion').distinct().remove(9999)

	# Construct ecoregion fc with maximum height/width of ecoregion bbox to determine small vs. large ecoregions
	ecoregion_fc = ee.FeatureCollection(eco_id_list.map(prep_ecoregions))

	# Small ecoregions (max distance < 1000 km): consider ecoregion geometry + 1000km buffer
	small_ecoregions_range = ecoregion_fc.filter(ee.Filter.lte('max_dist', 1e6)).map(
		lambda f: f.setGeometry(f.geometry().buffer(1e6, 1e5)))

	# Large ecoregions (max distance > 1000 km): consider 250km buffer around occurrences in ecoregion + 1000km buffer
	# Considering the position of occurrences within the ecoregion is only relevant for ecoregions larger than the buffer 
	large_ecoregions_range = ecoregion_fc.filter(ee.Filter.gt('max_dist', 1e6)).map(lambda eco: ee.Feature(eco).setGeometry(
		points.filterMetadata('Resolve_Ecoregion', 'equals', eco.get('ECO_ID')).geometry().buffer(2e5, 100).intersection(eco.geometry(), 100).buffer(1e6, 1e5)
	))

	# Occurrence range is the union of the ecoreigon ranges
	obs_range = ee.FeatureCollection(small_ecoregions_range.merge(large_ecoregions_range)).union().geometry()

	# FINAL RANGE
	# Final range is the intersection of the occurrence range and the native countries range
	final_range = obs_range.intersection(native_range, 100)

	# Export range
	export_fc(ee.FeatureCollection([ee.Feature(final_range, {})]), 'range_' + species, range_dir + '/' + species)
