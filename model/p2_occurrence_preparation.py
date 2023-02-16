from config import *

# Species for which to prepare occurrences is passed as a command line argument
# Run script in command line with "python 2_occurrence_preparation.py [species_name]"
species = sys.argv[1]

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

# Function to format sampeld points: 
def format_points(sampled_points):
	# Remove occurences with None values or all 0 values
	sampled_points = sampled_points.filter(ee.Filter.Or(
		ee.Filter.neq('SG_Coarse_fragments_005cm','None'), ee.Filter.neq('SG_Silt_Content_005cm','None'), 
		ee.Filter.neq('SG_Soil_pH_H2O_005cm','None'), ee.Filter.neq('CHELSA_bio12_1981_2010_V2_1','None'), 
		ee.Filter.neq('CHELSA_bio15_1981_2010_V2_1','None'), ee.Filter.neq('CHELSA_bio1_1981_2010_V2_1','None'),
		ee.Filter.neq('CHELSA_bio4_1981_2010_V2_1','None'), ee.Filter.neq('CHELSA_gsl_1981_2010_V2_1','None'), 
		ee.Filter.neq('CHELSA_npp_1981_2010_V2_1','None'), ee.Filter.neq('Resolve_Ecoregion','None')
	)).filter(ee.Filter.Or(
		ee.Filter.neq('SG_Coarse_fragments_005cm',0), ee.Filter.neq('SG_Silt_Content_005cm',0), 
		ee.Filter.neq('SG_Soil_pH_H2O_005cm',0), ee.Filter.neq('CHELSA_bio12_1981_2010_V2_1',0), 
		ee.Filter.neq('CHELSA_bio15_1981_2010_V2_1',0), ee.Filter.neq('CHELSA_bio1_1981_2010_V2_1',0),
		ee.Filter.neq('CHELSA_bio4_1981_2010_V2_1',0), ee.Filter.neq('CHELSA_gsl_1981_2010_V2_1',0), 
		ee.Filter.neq('CHELSA_npp_1981_2010_V2_1',0), ee.Filter.neq('Resolve_Ecoregion',0)
	))

	# Create geometries if Pixel_Lat and Pixel_Long were not set as lat/lon 
	# Usually due to the presence of 'None' values in Pixe_Lat and Pixel_Long (eg. for points in waterbodies)
	prop_names = sampled_points.first().propertyNames().getInfo()
	if 'Pixel_Long' in prop_names and 'Pixel_Lat' in prop_names:
		sampled_points = sampled_points.map(lambda f: f.setGeometry(ee.Geometry.Point([
            ee.Algorithms.If(ee.Algorithms.ObjectType(f.get('Pixel_Long')).compareTo('String').eq(0), ee.Number.parse(f.getString('Pixel_Long')), f.getNumber('Pixel_Long')),
            ee.Algorithms.If(ee.Algorithms.ObjectType(f.get('Pixel_Lat')).compareTo('String').eq(0), ee.Number.parse(f.getString('Pixel_Lat')), f.getNumber('Pixel_Lat'))
        ])))
	
	# Format features to make sure all covariate and ecoregion values are numerical
	# Select only formatted covariate and ecoregion values and set presence = 1
	sampled_points = sampled_points.map(format_feature).map(
		lambda f: f.select(model_covariate_names + ['Resolve_Ecoregion']).set({'presence': 1}))
	return sampled_points

if __name__ == '__main__':
	# Get feature collection of occurences of species of interest with sampled covariate values
	sampled_points = ee.FeatureCollection(sampled_data_dir + '/' + species)
	print(f"{sampled_points.size().getInfo()} points")

	# Format sampling points
	sampled_points = format_points(sampled_points)
	n_points = sampled_points.size().getInfo()
	print(f"{n_points} points after formatting")

	# If less than min_n_points non-null occurences, species will not be modelled
	if n_points < min_n_points :
		sys.exit(f"Less than {min_n_points} points -> no modelling")

	# Aggregate observations to the pixel level, keeping only one presence per pixel
	sampled_points = sampled_points.distinct('.geo')		
	n_points = sampled_points.size().getInfo()
	print(f"{n_points} points after aggregation")

	# If less than min_n_points non-null occurences, species will not be modelled
	if n_points < min_n_points :
		sys.exit(f"Less than {min_n_points} points -> no modelling")

	# Export feature collection to earthengine asset
	export_fc(sampled_points, 'prepped_occurrences_' + species, prepped_occurrences_dir + '/' + species)
