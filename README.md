# treemap

Project description...

## Installation
code run with Python 3.8.13, Google Earth Engine, gsutil, ...

## Prepare data
`config.py` contains variables and functions to share across all scripts, such as paths to earthengine files and directories. These are imported with `from config import *`.

- input data

## Run modelling pipeline for species of interest

### 1) Sample covariates
Get model covariate values for species occurence locations

- Run bash script `1_run_sample_covariates.sh` to run python script `1_sample_covariates.py` for each species in `species_list.csv`
 - Modify grid size and number of concurrent processors to use in `1_sample_covariates.py`
- Run bash script `1_upload_sampled_covariates.sh` to upload locally saved csv files to earthengine via GCSB
  - Adapt the path to your GCSB and to the earthengine directory for sampled data (should match `sampled_data_dir` in `config.py`)


### 2) Prepare occurrences
Format species occurrence with sampled covariate values, specifically aggregating points to the pixel level, removing all-null points and formatting covariate values

- Run bash script `2_run_occurrence_preparation.sh`to run python script `2_occurrence_preparation.py` for each species in `species_list.csv` for which the covariate values have already been sampled and the occurrence preparation script has not yet been run.

### 3) Compute range of interest

### 4) Model cross-validation

### 5) Final model and mapping
