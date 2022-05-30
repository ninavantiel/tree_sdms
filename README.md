# treemap

Project description...

## Installation
code run with Python 3.8.13, Google Earth Engine, gsutil, ...

## Prepare data
`config.py` contains variables and functions to share across all scripts. These are imported in other python scripts with `from config import *`. Variable values are accessible in bash scripts with `python3 config.py "VAR_NAME"`, replacing `VAR_NAME` with the name of the variable of interest.

- input data
 - treemap_data_all_species
 - pseudoabsences
 - gts and country geometries


## Run modelling pipeline for species of interest

### 1) Sample covariates
Get model covariate values for species occurence locations.

Run bash script `run_1_sample_covariates.sh` to run python script `p1_sample_covariates.py` for each species in `species_list.csv`

### 2) Prepare occurrences
Format species occurrences with sampled covariate values, specifically aggregating points to the pixel level, removing all-null points, formatting covariate values and setting geometries if necessary.

Run bash script `run_2_occurrence_preparation.sh`to run python script `p2_occurrence_preparation.py` for each species in `species_list.csv` for which the covariate values have already been sampled and the occurrence preparation script has not yet been run.

### 3) Compute range of interest

### 4) Model cross-validation

### 5) Final model and mapping
