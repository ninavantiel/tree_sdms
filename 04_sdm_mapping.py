from config import * 


# Function to compute validation metrics for a classified cross-validation test set
def compute_tss_auc(test_class):

	# Function to compute the TSS (true skill statistic), TPR (true positive rate), FPR (false positive rate),
	# precision and recall for a given threshold
	def compute_tss_tpr_fpr(threshold):
		tp = ee.FeatureCollection(test_class).filter(ee.Filter.And(
	    	ee.Filter.equals('presence', 1), ee.Filter.gte('classification_avg', threshold)
		)).size()
		fp = ee.FeatureCollection(test_class).filter(ee.Filter.And(
			ee.Filter.equals('presence', 0), ee.Filter.gte('classification_avg', threshold)
		)).size()
		fn = ee.FeatureCollection(test_class).filter(ee.Filter.And(
			ee.Filter.equals('presence', 1), ee.Filter.lt('classification_avg', threshold)
		)).size()
		tn = ee.FeatureCollection(test_class).filter(ee.Filter.And(
			ee.Filter.equals('presence', 0), ee.Filter.lt('classification_avg', threshold)
		)).size()
		return ee.Feature(None, {
			'threshold': threshold, 'tss': (tp.divide(tp.add(fn))).add(tn.divide(fp.add(tn))).subtract(1), 
			'tpr': tp.divide(tp.add(fn)), 'fpr': fp.divide(fp.add(tn)),
			'precision': tp.divide(tp.add(fp)), 'recall': tp.divide(tp.add(fn))
		})

	# Compute validation metrics for a each vaue in a list of thresholds (defined in config.py)
	tss_tpr_fpr = ee.FeatureCollection(thresholds.map(compute_tss_tpr_fpr))    

	# Get TOR and FPR values for AUC computation
	tpr = tss_tpr_fpr.aggregate_array('tpr')
	fpr = tss_tpr_fpr.aggregate_array('fpr')

	# Compute the AUC (area under the ROC curve) across thresholds
	auc = ee.List.sequence(1, tss_tpr_fpr.size().subtract(1)).map(
		lambda i: (fpr.getNumber(ee.Number(i).subtract(1)).subtract(fpr.getNumber(i))).multiply(
			(tpr.getNumber(ee.Number(i).subtract(1)).add(tpr.getNumber(i))).divide(2)
		)).reduce(ee.Reducer.sum())

	return ee.List([tss_tpr_fpr, auc])

# Function to compute cross validation results (optimal threshold, validation metrics), to train final model and predict SDM in the considered range
def compute_sdm(species, export = True):
	print(f"... {species}")

	# Get observation range 
	obs_range = ee.FeatureCollection(obs_range_dir + '/' + species).geometry()

	# Get observation points, filter to observation range
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
		print(f"Less than 90 observations. {ncov} 'covariates selected: {covariates}")
	# If there are at least 90 observations, keep all covariates
	else:
		covariates = model_covariate_names

    # Get cross validation test classification results
	cv_classifications_list = ee.List([ee.FeatureCollection(test_class_dir + '/' + species + '_fold_' + str(i)) for i in range(3)])
	# For each cross validation fold, compute AUC and validation metrics for different thresholds
	tss_auc = cv_classifications_list.map(compute_tss_auc)

	# Determine optimal threshold, maximizing the average TSS across cross validation folds
	tss_fc = ee.FeatureCollection(tss_auc.map(lambda l: ee.List(l).get(0))).flatten()
	mean_tss = ee.FeatureCollection(thresholds.map(lambda t: ee.Feature(None, {
    	'threshold': t, 'mean_tss': tss_fc.filterMetadata('threshold','equals',t).aggregate_mean('tss')
	})))
	threshold = mean_tss.filterMetadata('mean_tss','equals',mean_tss.aggregate_max('mean_tss')).first().get('threshold')

	# Compute average validation metrics for optimal threshold over cross validation folds
	tss = mean_tss.filterMetadata('mean_tss','equals',mean_tss.aggregate_max('mean_tss')).first().get('mean_tss')
	f1 = tss_fc.filterMetadata('threshold','equals',threshold).map(lambda f: f.set(
    	'f1', ee.Number(2).multiply((f.getNumber('precision').multiply(f.getNumber('recall'))).divide(f.getNumber('precision').add(f.getNumber('recall'))))
	)).aggregate_mean('f1')
	recall = tss_fc.filterMetadata('threshold','equals',threshold).aggregate_mean('recall')
	precision = tss_fc.filterMetadata('threshold','equals',threshold).aggregate_mean('precision')
	# Compute average AUC over cross validation folds
	auc = tss_auc.map(lambda l: ee.List(l).get(1)).reduce(ee.Reducer.mean())

	# Train each model in the ensemble on the full training set
	trained_models = models.map(lambda model: ee.List([
		ee.Classifier(ee.List(model).get(0)).train(training_data, 'presence', covariates), ee.List(model).get(1)
	]))

	# Apply models to each multiband covariate image 
	names = ee.ImageCollection(covariate_imgs).aggregate_array('system:index')
	sdms = ee.ImageCollection(covariate_imgs).map(
    	lambda cov_img: ee.ImageCollection.fromImages(trained_models.map(
        	lambda model: cov_img.clip(obs_range).classify(ee.List(model).get(0))
    	)).mean()
	).toBands().rename(names)

	# Binarize sdm outputs with threshold and set properties
	sdms = sdms.gte(ee.Image.constant(threshold)).set({
		'threshold': threshold, 'tss': tss, 'auc': auc, 'f1': f1, 'recall': recall, 'precision': precision, 'nobs': nobs, 'npa': npa, 'prevalence': nobs/(nobs+npa)
	})
	
	# Export binary sdm results
	if export: export_image(sdms, species + '_sdms', sdm_coll + '/' + species)

# Get list of species for which we have computed the results of the 3-fold cross-validation
cv_done = subprocess.run([earthengine, 'ls', test_class_dir], stdout=subprocess.PIPE).stdout.decode('utf-8')
cv_done_species_list = list([x.replace('\n','').split('_fold_')[0] for x in cv_done.split(
    '\nprojects/earthengine-legacy/assets/' + test_class_dir +'/')[1:]
])
cv_done_species = set(cv_done_species_list)

# Get list of species that have already gone through the compute_sdm function
sdm_done = subprocess.run([earthengine, 'ls', sdm_coll], stdout=subprocess.PIPE).stdout.decode('utf-8')
sdm_done_species_list = list([x.replace('\n','').split('_fold_')[0] for x in sdm_done.split(
    '\nprojects/earthengine-legacy/assets/' + sdm_coll +'/')[1:]
])
sdm_done_species = set(sdm_done_species_list)

# Run compute_sdm for species for which cross validation is done but for which the SDM has not been computed
print(f"{len(sdm_done_species)} species SDM mapping done out of {len(cv_done_species)} species with cross-validation")
print(f"-> {len(species_list.intersection(cv_done_species).difference(sdm_done_species))} species to run")

for species in set(species_list).intersection(cv_done_species).difference(sdm_done_species): 
	compute_sdm(species, True)
	


