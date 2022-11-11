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
	training_data, n_occ, n_pa, covariates, species_range = prepare_training_data(species)
	if training_data == 'EXIT':
		sys.exit()

	# For each fold in the cross validation, train model and test on leave-out fold
	# Export test classification for each fold separately
	for i in range(k):
		cv_i = k_fold_cv(i, k, training_data, covariates)
		export_fc(cv_i, species + '_cv_fold_' + str(i), cross_validation_dir + '/' + species + '_fold_' + str(i))


