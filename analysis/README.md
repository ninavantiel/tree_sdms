# Analysis
This file describes the scripts found in the `analysis` directory. They contain the code for the downstream analyses and figures using the modelled species distributions. They are organized in subdirectories. The scripts in each subdirectory are listed below in the order that they are intented to be run with a brief explanation.

`config_figures.py` contains variables and functions that are shared across all scripts. These are imported in other python scripts with `from config_figures import *`. 

## Model evaluation
Scripts used to compute and/or evaluate model performance can be found in the directory `validation_figures`. 

- `get_sdm_validation_stats.py`: export validation metrics saved as properties in  earthengine image collection of SDMs to csv file.
- `splot_sdm_sample_values.py`: sample SDM values for every sPlot site
- `splot_sdm_confusion_matrices.py`: compute confusion matrix for each species between sPlot presence-absence data and predicted SDM.
- `mhs_validation.py`: compute intersection over union (IoU) of SDM distributions and maximum habitat suitability (MHS) maps from the Tree species distribution data and maps for Europe” report from the European Commission (https://data.europa.eu/doi/10.2760/489485).
- `sdms_sum.py`: compute sum of all binary SDMs with 1981-2010 climate variables. 
- `validation_figures.ipynb`: (i) plot cross-validation evalution metrics against number of occurrences. (ii) plot histogram of cross-validation evaluation metrics. (iii) plot histograms of sPlot validation metrics. (iv) plot IoU with MHS maps.

## Species composition analyses
Scripts used to investigate the composition of tree species across the globe can be found in the directory `composition_ordinations`. 

- `sample_species_composition.py`: sample the SDM images at 3,000-arc seconds to create a global community matrix.
- `nmds.R`: compute taxonomic composition ordination with non-metric multidimensional scaling (NMDS) using the sampled community matrix. Final output is a csv file containing the NMDS results.
- `evopca.R`: compute phylogenetic composition ordination with phylogenetic PCA (evoPCA). Final output is a csv file containing the evoPCA results.
- ***Output csv files from NMDS and evoPCA were both manually uploaded to earthengine as feature collections before the next steps were performed.***
- `nmds_evopca_fc.py`: join NMDS and evoPCA feature collections and add geometries corresponding to 3,000*3,000 arc seconds pixels around the saved coordinates. Final output is an earthengine feature collection containing both NMDS and evoPCA results and geometries.
- `nmds_evopca_img.py`: create multi-band images from NMDS-evoPCA feature collection with geometries. 
- `get_ordination_and_covariate_data.py`: sample the mean values of the covariates used for modelling within each 3,000-arc second pixel. Final output is a csv files containing ordination and covariate values. 
- `redundancy_analysis.R`: run redundancy and variation partitioning analysis for NMDS and evoPCA with clamatic and edaphic covariates. 
- `ordination_plots.ipynb`: (i) plot NMDS and evoPCA values in PCA of environmental covariate with RGB colors indicating the ordination values. (ii) plot NMDS and evoPCA values in 2-dimensions and histograms in 1- and 2-dimensions. (iii) perform clustering analysis on NMDS and evoCPA values with plots and best clustering results saved. 
- ***Best clustering results csv was manually uploaded to earthengine as a feature collection befor the next script was run.***
- `nmds_evopca_cluster_imgs.py`: create image of NMDS and evoPCA clustering results. 

## Species occupancy analyses
Scripts used the investigate species range sizes can be found in the directory `range_size_figure`. 

- `compute_sdm_area_latitude_elevation.py`: compute area covered, median latitude and median elevation of SDMs with climatic variables 1981-2010 (unconstrained and clipped to forests, ie. >=10% tree cover) and 2071-2100 SSP 5.85 (unconstrained). Results are saved in an earthengine feature collection and exported into a csv.
- `compute_median_sdm_area_image.py`: compute image of median species range size for SDMs clipped to >= 10% tree cover with climate variables of 1981-2010
- `compute_sdm_biome.py`: compute percentage of SDM area in each biome 
- `range_size_figure.py`: (i) plot SDM range size (unconstrained and >= 10% tree cover) distribution and mean range reduction per biome. (ii) plot SDM median latitude against SDM range size. 

## Effect of climate change
Scripts used the investigate the effects of climate change on tree species distributions estimated by our models can be found in the directory `climate_change_figure`. 

- `sample_ecoregion_species_composition.py`: sample for each ecoregion the presence of species according to SDMs with climate variables 1981-2010 and 2071-2100 SSP 5.85 to create an ecoregion-level community matrix with current and future climate.
- `nmds_current_future.R`: compute taxonomic composition ordination with non-metric multidimensional scaling (NMDS) using the sampled ecoregion-level current and future community matrix. Final output is a csv file containing the NMDS results.
- `evopca_current_future.R`: compute phylogenetic composition ordination with phylogenetic PCA (evoPCA) using the sampled ecoregion-level current and future community matrix. Final output is a csv file containing the evoPCA results.
- `compute_nmds_evopca_eucl_dist.py`: compute euclidean distance between current and future NMDS and evoPCA values.
- `climate_change_figure.ipynb`: (i) compute fraction of species gained and lost, and median absolute latitude shift and median elevation shift per ecoregion. (ii) plot average median absolute latitude shift, median elevation shift, fraction of gained and lost species, change in NMDS and evoPCA across ecoregions in each biome. 
