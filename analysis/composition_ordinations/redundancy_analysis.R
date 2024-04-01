library(vegan)
library(tidyverse)
library(data.table)

# set working directory 
setwd('path/to/your/data/dir/') # ** CHANGE THIS TO PATH TO YOUR DATA DIRECTORY **

# read dataframe with ordination and covariate values
df <- as_tibble(read.csv('nmds_evopca_covariates_equal_area.csv')) %>% 
  select(-.geo, -system.index) %>% 
  rename(MAT = CHELSA_bio1_1981_2010_V2_1, T_season = CHELSA_bio4_1981_2010_V2_1, 
         annual_P = CHELSA_bio12_1981_2010_V2_1, P_season = CHELSA_bio15_1981_2010_V2_1,
         GSL = CHELSA_gsl_1981_2010_V2_1, NPP = CHELSA_npp_1981_2010_V2_1,
         coarse_frag = SG_Coarse_fragments_005cm, silt = SG_Silt_Content_005cm,
         soil_pH = SG_Soil_pH_H2O_005cm)

# read dataframe of community matrix
community_mat <- data.frame(fread("species_data_covariates_1981_2010_equal_area_scale_100000.csv", sep=','))

# join both dataframes
df_com <- inner_join(df, community_mat)

cov_names <- c("annual_P", "P_season", "MAT", "T_season", "GSL", "NPP", "coarse_frag",  
               "silt", "soil_pH")
evopca_names <- c("Axis1", "Axis2", "Axis3")
nmds_names <- c("MDS1", "MDS2", "MDS3")

# create dataframe of all covariates, and climate and soil variables separately
covs <- df %>% select(all_of(cov_names))
covs <- decostand(covs, method = "standardize") # mean = 0, standard deviation = 1
clim_covs <- covs %>% select('annual_P', 'P_season', 'MAT', 'T_season', 'GSL', 'NPP')
soil_covs <- covs %>% select('coarse_frag', 'silt', 'soil_pH')

# create dataframe of scaled evoPCA values
evopca <- df %>% select(all_of(evopca_names))
evopca <- decostand(evopca, method = "standardize") # mean = 0, standard deviation = 1

# create dataframe of scaled NMDS values
nmds <- df %>% select(all_of(nmds_names))
nmds <- decostand(nmds, method = "standardize") # mean = 0, standard deviation = 1

# create community matrix dataframe
com <- df_com %>% select(-one_of('x', 'y', 'area', cov_names, evopca_names, nmds_names))

########## redundancy analysis for evoPCA ############

evopca.rda.all <- rda(formula = evopca ~ ., data=covs)
RsquareAdj(evopca.rda.all) # explained variance $adj.r.squared [1] 0.5764499
anova.cca(evopca.rda.all, step = 1000) # statistically significant (p=0.001)

evopca.rda.clim <- rda(formula = evopca ~ ., data=clim_covs)
RsquareAdj(evopca.rda.clim) # explained variance $adj.r.squared [1] 0.51663
anova.cca(evopca.rda.clim, step = 1000) # statistically significant (p=0.001)

evopca.rda.soil <- rda(formula = evopca ~ ., data=soil_covs)
RsquareAdj(evopca.rda.soil) # explained variance $adj.r.squared [1] 0.4832123
anova.cca(evopca.rda.soil, step = 1000) # statistically significant (p=0.001)

evopca.var.part <- varpart(evopca, clim_covs, soil_covs)
evopca.var.part$part
plot(evopca.var.part, Xnames = c("Climate", "Soil"), # name the partitions
     bg = c("seagreen3", "mediumpurple"), alpha = 80, # colour the circles
     digits = 2, # only show 2 digits
     cex = 1)


######## redundancy analysis for NMDS ###############

nmds.rda.all <- rda(formula = nmds ~ ., data=covs)
RsquareAdj(nmds.rda.all) # explained variance $adj.r.squared [1] 0.1185482
anova.cca(nmds.rda.all, step = 1000) # statistically significant (p=0.001)

nmds.rda.clim <- rda(formula = nmds ~ ., data=clim_covs)
RsquareAdj(nmds.rda.clim) # explained variance $adj.r.squared [1] 0.1084375
anova.cca(nmds.rda.clim, step = 1000) # statistically significant (p=0.001)

nmds.rda.soil <- rda(formula = nmds ~ ., data=soil_covs)
RsquareAdj(nmds.rda.soil) # explained variance $adj.r.squared [1] 0.07232076
anova.cca(nmds.rda.soil, step = 1000) # statistically significant (p=0.001)

nmds.var.part <- varpart(nmds, clim_covs, soil_covs)
nmds.var.part$part
plot(nmds.var.part, Xnames = c("Climate", "Soil"), # name the partitions
     bg = c("seagreen3", "mediumpurple"), alpha = 80, # colour the circles
     digits = 2, # only show 2 digits
     cex = 1)
