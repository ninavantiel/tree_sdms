from config import *

# Species to sample is passed as a command line argument
# Run script in command line with "python 1_sampled_covariates.py [species_name]"
species = sys.argv[1]

# Get feature collection of occurences of species of interest with sampled covariate values
sampled_points = ee.FeatureCollection(sampled_data_dir + '/' + species)
print(f"{sampled_points.size().getInfo()} points")

# Remove occurences with None values or all 0 values
sampled_points = sampled_points.filter(ee.Filter.Or(
	ee.Filter.neq('SG_Coarse_fragments_005cm','None'), ee.Filter.neq('SG_Silt_Content_005cm','None'), 
	ee.Filter.neq('SG_Soil_pH_H2O_005cm','None'), ee.Filter.neq('CHELSA_bio12_1981_2010_V2_1','None'), 
	ee.Filter.neq('CHELSA_bio15_1981_2010_V2_1','None'), ee.Filter.neq('CHELSA_bio1_1981_2010_V2_1','None'),
	ee.Filter.neq('CHELSA_bio4_1981_2010_V2_1','None'), ee.Filter.neq('CHELSA_gsl_1981_2010_V2_1','None'), 
	ee.Filter.neq('CHELSA_npp_1981_2010_V2_1','None'), ee.Filter.neq('Pixel_Long','None'), 
	ee.Filter.neq('Pixel_Lat','None'), ee.Filter.neq('Resolve_Ecoregion','None')
)).filter(ee.Filter.Or(
	ee.Filter.neq('SG_Coarse_fragments_005cm',0), ee.Filter.neq('SG_Silt_Content_005cm',0), 
	ee.Filter.neq('SG_Soil_pH_H2O_005cm',0), ee.Filter.neq('CHELSA_bio12_1981_2010_V2_1',0), 
	ee.Filter.neq('CHELSA_bio15_1981_2010_V2_1',0), ee.Filter.neq('CHELSA_bio1_1981_2010_V2_1',0),
	ee.Filter.neq('CHELSA_bio4_1981_2010_V2_1',0), ee.Filter.neq('CHELSA_gsl_1981_2010_V2_1',0), 
	ee.Filter.neq('CHELSA_npp_1981_2010_V2_1',0), ee.Filter.neq('Resolve_Ecoregion',0)
))
nobs = sampled_points.size().getInfo()
print(f"{nobs} points after removing null points")

# If less than 20 non-null occurences, species will not be modelled
	if nobs < 20 :
		print('Less than 20 non-null points -> no modelling!')
		return

	# Get property names of first feature to test if geometries need to be created (ie. they were not created during the import)
	prop_names = sampled_points.first().propertyNames().getInfo()
	if 'Pixel_Long' in prop_names and 'Pixel_Lat' in prop_names:
		print('Setting geometry')
		sampled_points = sampled_points.map(lambda f: f.setGeometry(ee.Geometry.Point([
            ee.Algorithms.If(ee.Algorithms.ObjectType(f.get('Pixel_Long')).compareTo('String').eq(0), 
                             ee.Number.parse(f.getString('Pixel_Long')), f.getNumber('Pixel_Long')),
            ee.Algorithms.If(ee.Algorithms.ObjectType(f.get('Pixel_Lat')).compareTo('String').eq(0), 
                             ee.Number.parse(f.getString('Pixel_Lat')), f.getNumber('Pixel_Lat')),
        ])))
	
	# Format features to make sure all covariate+ecoregion values are numerical
	sampled_points = sampled_points.map(format_feature)

	# Select only formatted covariates+ecoregion and set presence = 1
	sampled_points = sampled_points.map(lambda f: f.select(model_covariate_names + ['Resolve_Ecoregion']).set({'presence': 1}))
	print(f"{sampled_points.size().getInfo()} observations before aggregation to pixel level")

	# Aggregate observations to the pixel level, keeping only one presence per pixel
	obs_points = sampled_points.distinct('.geo')		
	nobs = obs_points.size().getInfo()

	# If less than 20 observations after aggregation, species will not be modelled
	if nobs < 20:
		print(f"{nobs} observations after aggregation -> no modelling!")
		return

	print(f"{nobs} observations after aggregation")

	# Export feature collection to earthengine asset
	export_obs = ee.batch.Export.table.toAsset(
		collection = obs_points,
		description =  'obs_points_' + species,
		assetId = obs_points_dir + '/' + species
	)
	if export: 
		export_obs.start()
		print('=> Exporting observation points.')	
