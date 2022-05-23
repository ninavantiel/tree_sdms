from config import * 

# Function to format sampled points: fixes format issues in the covariates values (mix of strings and numerical values)
# Assigns Resolve_Ecoregion = 9999 to points where Resolve_Ecoregion was 'None'
def format_feature(f):
    return f.set({
        'coarse_fragments': ee.Algorithms.If(
            ee.Algorithms.ObjectType(f.get('SG_Coarse_fragments_005cm')).compareTo('String').eq(0), 
            ee.Number.parse(f.getString('SG_Coarse_fragments_005cm')), f.getNumber('SG_Coarse_fragments_005cm')
        ),
        'silt_content': ee.Algorithms.If(
            ee.Algorithms.ObjectType(f.get('SG_Silt_Content_005cm')).compareTo('String').eq(0), 
            ee.Number.parse(f.getString('SG_Silt_Content_005cm')), f.getNumber('SG_Silt_Content_005cm')
        ),
        'soil_ph': ee.Algorithms.If(
            ee.Algorithms.ObjectType(f.get('SG_Soil_pH_H2O_005cm')).compareTo('String').eq(0), 
            ee.Number.parse(f.getString('SG_Soil_pH_H2O_005cm')), f.getNumber('SG_Soil_pH_H2O_005cm')
        ),
        'bio12': ee.Algorithms.If(
            ee.Algorithms.ObjectType(f.get('CHELSA_bio12_1981_2010_V2_1')).compareTo('String').eq(0), 
            ee.Number.parse(f.getString('CHELSA_bio12_1981_2010_V2_1')), f.getNumber('CHELSA_bio12_1981_2010_V2_1')
        ),
        'bio15': ee.Algorithms.If(
            ee.Algorithms.ObjectType(f.get('CHELSA_bio15_1981_2010_V2_1')).compareTo('String').eq(0), 
            ee.Number.parse(f.getString('CHELSA_bio15_1981_2010_V2_1')), f.getNumber('CHELSA_bio15_1981_2010_V2_1')
        ),
        'bio1': ee.Algorithms.If(
            ee.Algorithms.ObjectType(f.get('CHELSA_bio1_1981_2010_V2_1')).compareTo('String').eq(0), 
            ee.Number.parse(f.getString('CHELSA_bio1_1981_2010_V2_1')), f.getNumber('CHELSA_bio1_1981_2010_V2_1')
        ),
        'bio4': ee.Algorithms.If(
            ee.Algorithms.ObjectType(f.get('CHELSA_bio4_1981_2010_V2_1')).compareTo('String').eq(0), 
            ee.Number.parse(f.getString('CHELSA_bio4_1981_2010_V2_1')), f.getNumber('CHELSA_bio4_1981_2010_V2_1')
        ),
        'gsl': ee.Algorithms.If(
            ee.Algorithms.ObjectType(f.get('CHELSA_gsl_1981_2010_V2_1')).compareTo('String').eq(0), 
            ee.Number.parse(f.getString('CHELSA_gsl_1981_2010_V2_1')), f.getNumber('CHELSA_gsl_1981_2010_V2_1')
        ),
        'npp': ee.Algorithms.If(
            ee.Algorithms.ObjectType(f.get('CHELSA_npp_1981_2010_V2_1')).compareTo('String').eq(0), 
            ee.Number.parse(f.getString('CHELSA_npp_1981_2010_V2_1')), f.getNumber('CHELSA_npp_1981_2010_V2_1')
        ),
        'Resolve_Ecoregion': ee.Algorithms.If(
    		ee.Algorithms.ObjectType(f.get('Resolve_Ecoregion')).compareTo('String').eq(0),
    		ee.Algorithms.If(
    			f.getString('Resolve_Ecoregion').compareTo('None').eq(0), 9999, ee.Number.parse(f.getString('Resolve_Ecoregion'))
    		), f.getNumber('Resolve_Ecoregion')
		)
    })

# Function to prepare observation points for modelling 
def prep_observations(species, export = True):
	print(f"... {species}")

	# Filter out points that have NAs or 0s for all covariate values
	sampled_points = ee.FeatureCollection(sampled_data_dir + '/' + species).filter(ee.Filter.Or(
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

	print(f"{old_nobs} observations previously")
	print(f"{nobs} observations")

	# If less than 20 non-null observations, species will not be modelled
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

# Get list of species for which the covariate values are sampled, ie. species that are ready for the prep_observations function
sampled = subprocess.run([earthengine, 'ls', sampled_data_dir], stdout=subprocess.PIPE).stdout.decode('utf-8')
sampled_species = set([x.replace('\n','') for x in sampled.split(
    '\nprojects/earthengine-legacy/assets/' + sampled_data_dir + '/')[1:]
])

# Get list of species that have already gone through the prep_observations function
obs_done = subprocess.run([earthengine, 'ls', obs_points_dir], stdout=subprocess.PIPE).stdout.decode('utf-8')
obs_done_species = set([x.replace('\n','') for x in obs_done.split(
    '\nprojects/earthengine-legacy/assets/' + obs_points_dir + '/')[1:]
])

# Run prep_observations for species for which covariates have been sampled but whose observations have not yet been prepped
print(f"{len(obs_done_species)} species with observation prep done out of {len(sampled_species)} sampled species out of {len(set(species_list))} total species")
print(f"{len(species_list.intersection(sampled_species).difference(obs_done_species))} species to run")

for species in set(species_list).intersection(set(sampled_species).difference(obs_done_species)): 
	prep_observations(species, True)


