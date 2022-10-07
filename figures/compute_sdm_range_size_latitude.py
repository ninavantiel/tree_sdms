from config_figures import *

## Function returning an image collection with SDMs modelled with current/future climate covariates and clipped to current/potential forests
def make_sdms_to_reduce(sdm):
	sdm_current_forest = ee.Image(sdm).multiply(current_forest)
	sdm_potential_forest = ee.Image(sdm).multiply(potential_forest)

	return ee.ImageCollection([
		ee.Image(mask_sdm(sdm_current_forest.select(['covariates_1981_2010']))).set('sdm', 'current_forest_1981_2010'), 
		ee.Image(mask_sdm(sdm_current_forest.select(['covariates_2071_2100_ssp585']))).set('sdm', 'current_forest_2071_2100_ssp585'), 
		ee.Image(mask_sdm(sdm_potential_forest.select(['covariates_1981_2010']))).set('sdm', 'potential_forest_1981_2010'), 
		ee.Image(mask_sdm(sdm_potential_forest.select(['covariates_2071_2100_ssp585']))).set('sdm', 'potential_forest_2071_2100_ssp585')
	])

## Function computing SDM range size and median latitude 
def sdm_range_size_lat(sdm):
	area = sdm.multiply(ee.Image.pixelArea()).rename('area').reduceRegion(
		reducer = ee.Reducer.sum(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
	)
	median_lat = sdm.multiply(ee.Image.pixelLonLat().select('latitude')).rename('median_lat').reduceRegion(
		reducer = ee.Reducer.median(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
	)
	return ee.Feature(None, area.combine(median_lat)).set('sdm', sdm.get('sdm'))

## Get SDM range size and median latitude for SDMs modelled with current/future climate covariates and clipped to current/potential forests
def get_sdm_range_size_lat(sdm):
	sdms_to_reduce = make_sdms_to_reduce(sdm)

	## Get SDM range size and median latitude for each image in sdms_to_reduce
	## Set median_lat to -9999 for SDM that are empty
	sdm_range_size_lat_fc = sdms_to_reduce.map(sdm_range_size_lat).map(
		lambda f: f.set('median_lat', ee.Algorithms.If(f.propertyNames().contains('median_lat'), f.get('median_lat'), -9999))
	)

	range_sizes = ee.Dictionary.fromLists(
		sdm_range_size_lat_fc.aggregate_array('sdm').map(lambda n: ee.String(n).cat('_area')), sdm_range_size_lat_fc.aggregate_array('area')
	)
	median_lats = ee.Dictionary.fromLists(
		sdm_range_size_lat_fc.aggregate_array('sdm').map(lambda n: ee.String(n).cat('_median_lat')), sdm_range_size_lat_fc.aggregate_array('median_lat')
	)
	return ee.Feature(None, range_sizes.combine(median_lats).set('species', sdm.get('system:index')))

## Get SDM range size in each biome for SDMs modelled with current/future climate covariates and clipped to current/potential forests
def get_sdm_biome_range_size(sdm):
 	sdms_to_reduce = make_sdms_to_reduce(sdm).map(
 		lambda img: img.multiply(biome_image).set({'sdm': img.get('sdm'), 'species': sdm.get('system:index')})
 	)

 	sdm_biome_areas = sdms_to_reduce.map(lambda img: ee.Feature(None, biome_dictionary.map(
 		lambda name, num: img.eq(ee.Image.constant(num)).multiply(ee.Image.pixelArea()).rename('area').reduceRegion(
 			reducer = ee.Reducer.sum(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
 		).getNumber('area')
 	)).set({'species': img.get('species'), 'sdm': img.get('sdm')}))
 	return sdm_biome_areas

if __name__ == '__main__':
	print(sdms.size().getInfo(), 'sdms in analysis')
	
	sdms_area_lat = sdms.map(get_sdm_range_size_lat)
	export = ee.batch.Export.table.toDrive(
		collection = sdms_area_lat,
		description = 'sdms_range_size_latitude',
		folder = google_drive_folder
	)
	export.start()

	sdms_biome_area = sdms.map(get_sdm_biome_range_size).flatten()
	export = ee.batch.Export.table.toDrive(
		collection = sdms_biome_area,
		description = 'sdms_biome_range_size',
		folder = google_drive_folder
	)
	export.start()

	