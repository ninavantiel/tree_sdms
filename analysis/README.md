# Analysis
This file describes the scripts found in the `analysis` directory. They contain the code for the downstream analyses and figures using the modelled species distributions.

`config_figures.py` contains variables and functions that are shared across all scripts. These are imported in other python scripts with `from config_figures import *`. 

## Species composition analyses
Scripts used to investigate the composition of tree species across the globe can be found in the directory `composition_ordinations`. Below, the scripts are listed in the order that they are intented to be used with a brief explanation.

- `sample_species_composition.py`: sample the distributions at 3,000-arc seconds to create a global community matrix (uses the `sdm_sum` earthengine image which is created with a script in the `supp_figures`). 
- `nmds.R`: compute taxonomic composition ordination with non-metric multidimensional scaling (NMDS) using the sampled community matrix. Final output is a csv file containing the NMDS results.
- `evopca.R`: compute phylogenetic composition ordination with phylogenetic PCA (evoPCA). Final output is a csv file containing the evoPCA results.
- **Output csv files from NMDS and evoPCA were both manually uploaded to earthengine as feature collections before the next steps were performed.**
- `nmds_evopca_fc.py`: join NMDS and evoPCA feature collections and add geometries corresponding to 3,000*3,000 arc-seconds pixels around the saved coordinates. Final output is an earthengine feature collection containing both NMDS and evoPCA results and geometries.
- `nmds_evopca_img.py`: create multi-band images from NMDS-evoPCA feature collection with geometries. 
- `get_ordination_and_covariate_data.py`: samples the mean values of the covariates used for modelling within each 3,000-arc second pixel. Final output is a csv files containing ordination and covariate values. 
- `redundancy_analysis.R`: runs redundancy and variation partitioning analysis for NMDS and evoPCA with clamatic and edaphic covariates. 
- `ordination_plots.ipynb`: (i) plots NMDS and evoPCA values in PCA of environmental covariate with RGB colors indicating the ordination values. (ii) plots NMDS and evoPCA values in 2-dimensions and histograms in 1- and 2-dimensions. (iii) performs clustering analysis on NMDS and evoCPA values with plots and best clustering results saved. 
- **Best clustering results csv was manually uploaded to earthengine as a feature collection befor the next script was run.**
- `nmds_evopca_cluster_imgs.py`: create image of NMDS and evoPCA clustering results. 
