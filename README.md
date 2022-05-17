# treemap

Project description...

## Installation
code run with Python 3.8.13, Google Earth Engine, gsutil, ...

## Prepare data
`config_dict.py` contains variables to share across all scripts, such as paths to earthengine files and directories. These variables can be accessed from a python script with `from config_dict import *; config_dict_get("VARIABLE_NAME")` or from a bash script with `python config_dict.py VARIABLE NAME`
- input data

## Run modelling pipeline for species of interest

### Sample covariates
Get model covariate values for species occurence locations

- Run bash script `1_run_sample_covariates.sh` to run python script `1_sample_covariates.py` for each species in `species_list.csv`
- Run bash script `1_upload_sampled_covariates.sh` to upload locally saved csv files to earthengine

Modify minimum number of points per species to run sampling script, grid size and number of concurrent processors to use in `1_sample_covariates.py`

2) Prepare occurences

3) Compute range of interest

4) Model cross-validation

5) Final model and mapping
