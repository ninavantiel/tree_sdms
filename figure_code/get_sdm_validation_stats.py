import ee
ee.Initialize()

sdms = ee.ImageCollection('projects/crowtherlab/nina/treemap/sdms_binary')

if __name__ == '__main__':
	sdm_stats = sdms.map(lambda sdm: ee.Feature(None, sdm.toDictionary()))
	
	export = ee.batch.Export.table.toDrive(
		collection = sdm_stats,
		description = 'sdm_stats_validation',
		folder = 'treemap'
	)
	export.start()