from config import * 

# Function to compute train the ensemble model and classify test points for the i-th fold of a k-fold cross validation
def cv_classification(i, k, training_data, covariates):
	# Get test set: select points with random number x such that: i/k < x < (i+1)/k
	# eg. i=0: 0 < x < 1/3, i=1: 1/3 < x < 2/3, i=2: 2/3 < x < 3/3
	test_set = training_data.filterMetadata('random', 'greater_than', ee.Number(i).divide(k)).filterMetadata(
		'random', 'less_than', (ee.Number(i).add(1)).divide(k))

	# Get train set: select points with random number x such that: x > (i+1)/k or x < i/k
	# eg. i=0: x > 1/3 or x < 0, i=1: x > 2/3 or x < 1/3, i=2: x > 1 or x < 2/3
	train_set = training_data.filterMetadata('random', 'greater_than', (ee.Number(i).add(1)).divide(k)).merge(
		training_data.filterMetadata('random', 'less_than', ee.Number(i).divide(k)))

	# Train all models, for each model compute at list: [trained_model, model_name]
	# Used models are defined in the config.py file
	trained_models = models.map(lambda model: ee.List([
		ee.Classifier(ee.List(model).get(0)).train(train_set, 'presence', covariates), ee.List(model).get(1)
	]))

	# Compute average classification across all models for test set
	avg_classification = test_set.map(lambda f: f.set({
		'classification_avg': trained_models.map(
			lambda model: ee.FeatureCollection([f]).classify(ee.List(model).get(0)).first().get('classification')
		).reduce(ee.Reducer.mean()), 'fold': i
	}))
	return avg_classification

# Function to prepare training data for model and perform a k-fold cross validation (randomly assigned folds)
# The classifications of each fold of the cross validation are exported in separate feature collections in earthengine
def cv_3fold(species, k = 3, export = True):
	print(f"... {species}")

	# Get observation range 
	obs_range = ee.FeatureCollection(obs_range_dir + '/' + species).geometry()

	# Get observation points and filter to observation range
	obs_points = ee.FeatureCollection(obs_points_dir + '/' + species).filterBounds(obs_range).map(
		lambda f: f.select(model_covariate_names + ['presence'])
	)

	# Get pseudoabsences points in observation range
	pa_pool = pseudoabsences.filterBounds(obs_range)

	# Prepare training data for modelling: subsample observations and/or pseudoabsences depending on number of points available
	# A random number property is added to each feature for selection of folds for k-fold cross validation
	[nobs, npa, training_data] = prep_training_data(obs_points, pa_pool)

	# If there are less than 20 observations, no modeling
	if nobs < 20:
		print('Less than 20 observations -> no modeling')
		return
	# If there are less than 90 observations, select subset of covariates
	elif nobs < 90:
		ncov = math.floor(nobs/10)
		varimp = ee.Classifier(ee.List(models.get(0)).get(0)).train(
			training_data, 'presence', model_covariate_names).explain().get('importance').getInfo()
		covariates = nlargest(ncov, varimp, key = varimp.get)
		print(f"Less than 90 observations, {ncov} covariates selected: {covariates}")
	# If there are at least 90 observations, keep all covariates
	else:
		covariates = model_covariate_names
	
	# For each fold in the cross validation, train model and test on leave-out fold
	# Export test classification for each fold separately
	for i in range(k):
		cv_classification_i = cv_classification(i, k, training_data, covariates)
		if export:
			export_fc(cv_classification_i, 'cv_classification_' + species + '_fold_' + str(i), test_class_dir + '/' + species + '_fold_' + str(i))


# Get list of species for which we have compute the range, ie. that are ready for the cv_3fold function
range_done = subprocess.run([earthengine, 'ls', obs_range_dir], stdout=subprocess.PIPE).stdout.decode('utf-8')
range_done_species = set([x.replace('\n','') for x in range_done.split(
    '\nprojects/earthengine-legacy/assets/' + obs_range_dir + '/')[1:]
])

# Get list of species that have already gone through the compute_range function
cv_done = subprocess.run([earthengine, 'ls', test_class_dir], stdout=subprocess.PIPE).stdout.decode('utf-8')
cv_done_species_list = list([x.replace('\n','').split('_fold_')[0] for x in cv_done.split(
    '\nprojects/earthengine-legacy/assets/' + test_class_dir +'/')[1:]
])
cv_done_species = set(cv_done_species_list)

three_done = [s for s in cv_done_species if cv_done_species_list.count(s) == 3]
if len(cv_done_species) != len(three_done):
	print('Some species have not run successfully for all 3 cross validation folds:')
	print([s for s in cv_done_species if s not in three_done])
	sys.exit()

# Run compute_range for species for which observations have been prepped but for which the range has not been constructed
print(f"{len(cv_done_species)} species with cross validation done out of {len(range_done_species)} species with range")
print(f"-> {len(species_list.intersection(range_done_species).difference(cv_done_species))} species to run")

for species in set(species_list).intersection(set(range_done_species).difference(cv_done_species)): 
	cv_3fold(species, 3, True)
	
