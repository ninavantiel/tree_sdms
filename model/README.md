# Model
This file describes the scripts found in the `model` directory. They contain the code for the pipeline for mapping tree species distributions combining environmental niche modelling and geographic range polygons. 

`config.py` contains variables and functions that are shared across all scripts. These are imported in other python scripts with `from config import *`. Variable values are accessible in bash scripts with `python3 config.py "VAR_NAME"`, replacing `VAR_NAME` with the name of the variable of interest.

## Prepare pseudoabsences
Generate pseudoabsences for SDMs by creating 1e6 uniformly sampled points across the Earth and sampling the model covariate values at each location. The `run_sampling` function from `p1_sample_covariates.py` script is used. The script only needs to be run once, as the pseudoabsences for each species will be sampled from the ones generated here.

## 1) Sample covariates
Get model covariate values for species occurence locations. Output is uploaded to earthengine via a Google Could Storage Bucket.

Run bash script `run_1_sample_covariates.sh` to run python script `p1_sample_covariates.py` for each species in `species_list.csv`

## 2) Prepare occurrences
Format species occurrences with sampled covariate values, specifically aggregating points to the pixel level, removing all-null points, formatting covariate values and setting geometries if necessary.

Run bash script `run_2_occurrence_preparation.sh` to run python script `p2_occurrence_preparation.py` for each species in `species_list.csv` for which the covariate values have already been sampled and the occurrence preparation script has not yet been run.

## 3) Compute range of interest
Compute geographic range polygon based on reported native countries and location of occurrences combined with the geometries of the ecoregions in which they are located, with large buffers of 1000 km. 

Run bash script `run_3_construct_range.sh` to run python script `p3_construct_range.py` for each species in `species_list.csv` for which the occurrences have already been prepared and the range has not yet been computed.

## 4) Model cross-validation
Perform 3-fold cross-validation using the prepared occurrence data and geogrpahic range polygon. Saves the predictions for each fold in a FeatureCollection.

Run bash script `run_4_cross_validation.sh` to run python script `p4_cross_validation.py` for each species in `species_list.csv` for which the range have already been computed and the cross-validation have not yet been performed.

## 5) Final model and mapping
Compute cross-validation results and obtain optimal binarization threshold. Train final ensemble model on full dataset and make SDM predictions for several sets of model covariates. Predicted species distributions are exported as a multi-band Image.

Run bash script `run_5_sdm_mapping.sh` to run python script `p5_sdm_mapping.py` for each species in `species_list.csv` for which the cross-validation have already been completed and the final model predictions have not yet been computed.

