from config import *

# Species for which to run cross validation is passed as a command line argument
# Run script in command line with "python 4_cross_validation.py [species_name]"
species = sys.argv[1]

# Function to train the ensemble model on k-1 folds and classify test points of fold i
# Folds are assigned randomly, with the random number column of the training data feature collection
def k_fold_cv(i, k, training_data, covariates):
	# Get test set: select points with random number x such that: i/k < x < (i+1)/k
	# k=3 --> i=0: 0 < x < 1/3, i=1: 1/3 < x < 2/3, i=2: 2/3 < x < 3/3
	test_set = training_data.filterMetadata('random', 'greater_than', ee.Number(i).divide(k)).filterMetadata('random', 'less_than', (ee.Number(i).add(1)).divide(k))

	# Get train set: select points with random number x such that: x > (i+1)/k or x < i/k
	# k=3 --> i=0: x > 1/3 or x < 0, i=1: x > 2/3 or x < 1/3, i=2: x > 1 or x < 2/3
	train_set = training_data.filterMetadata('random', 'greater_than', (ee.Number(i).add(1)).divide(k)).merge(training_data.filterMetadata('random', 'less_than', ee.Number(i).divide(k)))

	# Train models in ensemble. Models are defined in the config file.
	trained_models = models.map(lambda model_name, model: ee.Classifier(model).train(train_set, 'presence', covariates))

	# Compute average classification across all models for test set
	classification = test_set.map(lambda f: f.set({'fold': i, 'classification_avg': trained_models.map(
		lambda model_name, model: ee.FeatureCollection([f]).classify(model).first().get('classification')
	).values().reduce(ee.Reducer.mean())}))
	return classification

if __name__ == '__main__':
	# Get range and occurrences filtered to range
	species_range = ee.FeatureCollection(range_dir + '/' + species).geometry()
	points = ee.FeatureCollection(prepped_occurrences_dir + '/' + species).filterBounds(species_range).map(lambda f: f.select(model_covariate_names + ['presence']))
	n_points = points.size().getInfo()

	# If less than min_n_points occurences, species will not be modelled
	if n_points < min_n_points :
		sys.exit(f"Less than {min_n_points} occurrences -> no modelling")
	
	# Get pseudoabsences points in range
	pa_pool = ee.FeatureCollection(pseudoabsences).filterBounds(species_range)

	# Prepare training data for modelling: subsample observations and/or pseudoabsences depending on number of points available
	# A random number property is added to each feature for selection of folds for k-fold cross validation
	[n_occ, n_pa, training_data] = generate_training_data(points, pa_pool)

	# If there are less than 90 observations, select subset of covariates based on variable importance in simple random forest model
	if n_occ < 90:
		n_cov = math.floor(n_occ/10)
		var_imp = ee.Classifier(models.get('RF_simple')).train(training_data, 'presence', model_covariate_names).explain().get('importance').getInfo()
		covariates = nlargest(n_cov, var_imp, key = var_imp.get)
		print(f"Less than 90 observations, {n_cov} covariates selected: {covariates}")
	# If there are at least 90 observations, keep all covariates
	else: covariates = model_covariate_names
	print(covariates)

	# For each fold in the cross validation, train model and test on leave-out fold
	# Export test classification for each fold separately
	for i in range(k):
		cv_i = k_fold_cv(i, k, training_data, covariates)
		export_fc(cv_i, species + '_cv_fold_' + str(i), cross_validation_dir + '/' + species + '_fold_' + str(i))