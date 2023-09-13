library(vegan)
library(tidyverse)

setwd("~/Documents/treemap/treemap/analysis")

evopca_df <- as_tibble(read.csv('../../evopca_df.csv'))

nmds_covs_df <- as_tibble(read.csv('~/Google Drive/My Drive/treemap/nmds_pca_data.csv')) %>% 
  select(-.geo, -system.index) %>% 
  rename(MAT = CHELSA_bio1_1981_2010_V2_1, T_season = CHELSA_bio4_1981_2010_V2_1, 
         annual_P = CHELSA_bio12_1981_2010_V2_1, P_season = CHELSA_bio15_1981_2010_V2_1,
         GSL = CHELSA_gsl_1981_2010_V2_1, NPP = CHELSA_npp_1981_2010_V2_1,
         coarse_frag = SG_Coarse_fragments_005cm, silt = SG_Silt_Content_005cm,
         soil_pH = SG_Soil_pH_H2O_005cm)
nmds_covs_df

df <- inner_join(evopca_df, nmds_covs_df) 
df
plot(df$x, df$y)
plot(df_sample$x, df_sample$y)

community_mat <- read.csv("../../species_data_merged_scale_92766.csv")
# community_mat[1:5,1:5]

df_com <- inner_join(df, community_mat)
df_com_sample <- sample_n(df_com, 1000)
df_com_sample

cov_names <- c("annual_P", "P_season", "MAT", "T_season", "GSL", "NPP", "coarse_frag",  
               "silt", "soil_pH")
evopca_names <- c("Axis1", "Axis2", "Axis3")
nmds_names <- c("MDS1", "MDS2", "MDS3")

covs <- df %>% select(all_of(cov_names))
covs <- decostand(covs, method = "standardize") # mean = 0, standard deviation = 1

evopca <- df %>% select(all_of(evopca_names))
evopca <- decostand(evopca, method = "standardize") # mean = 0, standard deviation = 1

nmds <- df %>% select(all_of(nmds_names))
nmds <- decostand(nmds, method = "standardize") # mean = 0, standard deviation = 1

com <- df_com_sample %>% select(-one_of('x', 'y', cov_names, evopca_names, nmds_names))
covs_sample <- df_com_sample %>% select(all_of(cov_names))

com.capscale <- capscale(com ~ ., data=covs_sample, distance = "bray")
com.capscale
RsquareAdj(com.capscale) # explained variance

evopca.rda.all <- rda(formula = evopca ~ ., data=covs)
round(100*(summary(evopca.rda.all)$cont$importance[2, 1:2]), 2)
RsquareAdj(evopca.rda.all) # explained variance
sqrt(vif.cca(evopca.rda.all))

TP_covs = covs %>% select(MAT, T_season, annual_P, P_season)
other_covs = covs %>% select(GSL, NPP, coarse_frag, silt, soil_pH)
covs_part <- varpart(evopca, TP_covs, other_covs)
covs_part

evopca.rda <- rda(formula = evopca ~ MAT + T_season + P_season + annual_P, data=covs)
summary(evopca.rda)

## extract % explained by the first 2 axes
perc <- round(100*(summary(evopca.rda)$cont$importance[2, 1:2]), 2)

## extract scores - these are coordinates in the RDA space
sc_si <- scores(evopca.rda, display="sites", choices=c(1,2), scaling=1)
sc_sp <- scores(evopca.rda, display="species", choices=c(1,2), scaling=1)
sc_bp <- scores(evopca.rda, display="bp", choices=c(1, 2), scaling=1)

evopca_rda_sites <- cbind(df %>% select(x, y, Axis1, Axis2, Axis3), data.frame(sc_si))
write_csv(evopca_rda_sites, '../../rda_evopca_sites.csv')
write_csv(data.frame(sc_sp), '../../rda_evopca_species.csv')
write_csv(data.frame(sc_bp), '../../rda_evopca_env.csv')


RsquareAdj(evopca.rda) # explained variance
plot(evopca.rda) # triplot
sqrt(vif.cca(evopca.rda))
anova.cca(evopca.rda, by = "axis") # axis significance
anova.cca(evopca.rda, by = "term") # term significance
anova.cca(evopca.rda)

evopca.rda.T <- rda(formula = evopca ~ MAT + T_season, data=covs)
RsquareAdj(evopca.rda.T) # explained variance
anova.cca(evopca.rda, by = "axis") # axis significance

TP_covs = covs %>% select(MAT, T_season, annual_P, P_season)
other_covs = covs %>% select(GSL, NPP, coarse_frag, silt, soil_pH)
covs_part <- varpart(evopca, TP_covs, other_covs)
covs_part

nmds.rda.all <- rda(formula = nmds ~ ., data=covs)
RsquareAdj(nmds.rda.all) # explained variance

nmds.rda <- rda(formula = nmds ~ MAT + T_season + P_season + annual_P, data=covs)
plot(nmds.rda) # triplot

## extract scores - these are coordinates in the RDA space
sc_si <- scores(nmds.rda, display="sites", choices=c(1,2), scaling=1)
sc_sp <- scores(nmds.rda, display="species", choices=c(1,2), scaling=1)
sc_bp <- scores(nmds.rda, display="bp", choices=c(1, 2), scaling=1)

nmds_rda_sites <- cbind(df %>% select(x, y, MDS1, MDS2, MDS3), data.frame(sc_si))
write_csv(nmds_rda_sites, '../../rda_nmds_sites.csv')
write_csv(data.frame(sc_sp), '../../rda_nmds_species.csv')
write_csv(data.frame(sc_bp), '../../rda_nmds_env.csv')


nmds.rda
plot(nmds.rda) # triplot

RsquareAdj(nmds.rda) # explained variance
anova.cca(nmds.rda, by = "term") # term significance
anova.cca(nmds.rda) # term significance

covs_part <- varpart(nmds, T_covs, P_covs)
covs_part

evopca.rda_selcovs <- rda(formula = evopca ~ MAT + T_season + P_season, data=covs)
RsquareAdj(evopca.rda_selcovs) # explained variance
plot(evopca.rda_selcovs) # triplot
sqrt(vif.cca(evopca.rda_selcovs))
anova.cca(evopca.rda_selcovs, by = "term") # term significance

evopca.rda1 <- rda(formula = evopca ~ P_season + T_season + annual_P + MAT + Condition(GSL + NPP + coarse_frag + silt + soil_pH), data=covs)
evopca.rda1
RsquareAdj(evopca.rda1) # explained variance
plot(evopca.rda1) # triplot


"annual_P", "P_season", "MAT", "T_season", "GSL", "NPP", "coarse_frag",  
"silt", "soil_pH")

evopca.rda
coef(evopca.rda)
# summary(evopca.rda)
plot(evopca.rda) # triplot
RsquareAdj(evopca.rda) # explained variance

# permutation tests
anova.cca(evopca.rda, permutations = 999) # global significance, p = 0.001 -> RDA model is significant
anova.cca(evopca.rda, by = "axis") # axis significance
anova.cca(evopca.rda, by = "term") # term significance

sqrt(vif.cca(evopca.rda))


ordiplot(evopca.rda, scaling = 2, type = "text")

nmds.rda <- rda(formula = nmds ~ ., data=covs)
nmds.rda
coef(nmds.rda)
plot(nmds.rda) # triplot
RsquareAdj(nmds.rda) # explained variance
