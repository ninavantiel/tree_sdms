from config import *

# Species for which to run mapping is passed as a command line argument
# Run script in command line with "python 5_sdm_mapping.py [species_name]"
species = sys.argv[1]

# Compute AUC (area under the ROC curve) 
def compute_auc(validation_metrics):
	vm_fc = ee.FeatureCollection(validation_metrics)
	# Get true positive rates (tpr) and false positive rates (fpr) values 
	tpr = vm_fc.aggregate_array('tpr')
	fpr = vm_fc.aggregate_array('fpr')
	return ee.List.sequence(1, vm_fc.size().subtract(1)).map(
		lambda i: (fpr.getNumber(ee.Number(i).subtract(1)).subtract(fpr.getNumber(i))).multiply((
			tpr.getNumber(ee.Number(i).subtract(1)).add(tpr.getNumber(i))).divide(2))
	).reduce(ee.Reducer.sum())

# Function to compute validation metrics for one cross validation fold classification
def compute_validation_metrics(classification):
	class_fc = ee.FeatureCollection(classification)
	def get_confusion_matrix(presence, predicted, threshold):
		if predicted == 1: 
			return class_fc.filter(ee.Filter.And(ee.Filter.equals('presence', presence), ee.Filter.gte('classification_avg', threshold))).size()
		if predicted == 0: 
			return class_fc.filter(ee.Filter.And(ee.Filter.equals('presence', presence), ee.Filter.lt('classification_avg', threshold))).size()
	def get_validation_metrics(threshold):
		tp = get_confusion_matrix(1, 1, threshold)
		fp = get_confusion_matrix(0, 1, threshold)
		tn = get_confusion_matrix(0, 0, threshold)
		fn = get_confusion_matrix(1, 0, threshold)
		return ee.Feature(None, {
			'fold': class_fc.first().get('fold'), 'threshold': threshold, 'tss': (tp.divide(tp.add(fn))).add(tn.divide(fp.add(tn))).subtract(1), 
			'tpr': tp.divide(tp.add(fn)), 'fpr': fp.divide(fp.add(tn)), 'precision': tp.divide(tp.add(fp)), 'recall': tp.divide(tp.add(fn))
		})
	return ee.FeatureCollection(thresholds.map(get_validation_metrics))    

def compute_cv_results(species):
	# Get cross validation classifications
	cv_results = ee.List([ee.FeatureCollection(cross_validation_dir + '/' + species + '_fold_' + str(i)) for i in range(k)])
	
	# Compute validation metrics for each cross validation fold for different thresholds
	validation_metrics = cv_results.map(compute_validation_metrics)

	# Compute mean AUC across cross validation folds
	auc = validation_metrics.map(compute_auc).reduce(ee.Reducer.mean())
	
	# Determine threshold that maximizes the average tss across cross validation folds
	validation_metrics = ee.FeatureCollection(validation_metrics).flatten()
	mean_tss = ee.FeatureCollection(thresholds.map(lambda threshold: ee.Feature(None, {
    	'threshold': threshold, 'mean_tss': validation_metrics.filterMetadata('threshold','equals',threshold).aggregate_mean('tss')
	})))
	threshold = mean_tss.filterMetadata('mean_tss','equals',mean_tss.aggregate_max('mean_tss')).first().get('threshold')
	
	# Compute average validation metrics for optimal threshold over cross validation folds
	tss = validation_metrics.filterMetadata('threshold','equals',threshold).aggregate_mean('tss')
	recall = validation_metrics.filterMetadata('threshold','equals',threshold).aggregate_mean('recall')
	precision = validation_metrics.filterMetadata('threshold','equals',threshold).aggregate_mean('precision')

	return threshold, tss, auc, recall, precision

if __name__ == '__main__':
	threshold, tss, auc, recall, precision = compute_cv_results(species)
	training_data, n_occ, n_pa, covariates, species_range = prepare_training_data(species)

	# Train each model in the ensemble on the full training set
	trained_models = models.map(lambda model_name, model: ee.Classifier(model).train(training_data, 'presence', covariates))

	# Apply models to each multiband covariate image 	
	sdms = ee.ImageCollection(covariate_img_col).map(lambda cov_img: ee.ImageCollection.fromImages(trained_models.map(
		lambda model_name, model: cov_img.clip(species_range).classify(model)
	).values()).mean()).toBands().rename(ee.ImageCollection(covariate_img_col).aggregate_array('system:index'))

	# Binarize sdm outputs with threshold and set properties
	sdms = sdms.gte(ee.Image.constant(threshold)).set({
		'threshold': threshold, 'tss': tss, 'auc': auc, 'recall': recall, 'precision': precision, 'nobs': n_occ, 'npa': n_pa
	})

	export_image(sdms, 'sdm_' + species, sdm_img_col + '/' + species)
	