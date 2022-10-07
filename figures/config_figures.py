import ee

try: ee.Initialize()
except: sys.exit('ERROR starting earthengine python API')

google_drive_folder = 'ETHZ/treemap'

sdms = ee.ImageCollection('projects/crowtherlab/nina/treemap/sdms_binary').filter(ee.Filter.gte('nobs',90))
scale_to_use = sdms.first().projection().nominalScale()

## Potential forest: Bastin et al. potential tree cover >= 10%
potential_forest = ee.Image('projects/crowtherlab/nina/treemap_figures/bastin_potential_tree_cover').gte(10) 
## Current forests: Hansen et al. tree cover in 2010 >= 10% (intersected with potential forests)
current_forest = ee.Image('projects/crowtherlab/nina/treemap_figures/hansen_year2000').gte(10).And(potential_forest)

ecoregions = ee.FeatureCollection('projects/crowtherlab/nina/treemap/Ecoregions')
biome_image = ecoregions.reduceToImage(['BIOME_NUM'], ee.Reducer.first())
biome_dictionary = ee.Dictionary.fromLists(
	ecoregions.distinct('BIOME_NUM').aggregate_array('BIOME_NAME'), 
	ecoregions.distinct('BIOME_NUM').aggregate_array('BIOME_NUM')
).remove(['N/A'])

unbounded_geo = ee.Geometry.Polygon([-180, 88, 0, 88, 180, 88, 180, -88, 0, -88, -180, -88], None, False)

## Function masking SDM pixels equal to 0 and pixels that are less than 50% within the SDM range (clipped)
def mask_sdm(sdm): return sdm.mask(sdm.mask().gte(0.5)).selfMask()