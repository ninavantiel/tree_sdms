library(V.PhyloMaker) 
library(tidyr)
library(tidyverse)
library(adiv)
library(tictoc)
library(data.table)

# set working directory 
setwd('path/to/your/data/dir/') # ** CHANGE THIS TO PATH TO YOUR DATA DIRECTORY **

# name of community matrix file
comm.matrix.filename <- 'species_data_covariates_1981_2010_scale_92766.csv'

# create dataframe of species with species name and genus
species_df <- read.csv("species_list.csv", header=FALSE, col.names = 'species')
species_df$species <- gsub('_', ' ', species_df$species)
species_df$genus <- separate(species_df, species, c("genus", "."), " ")$genus
head(species_df)
dim(species_df)

# get family from globalTreeSearch and add to dataframe
gts <- read.csv('globalTreeSearch.csv') 
gts <- gts %>% rename(species=taxon) %>% select('species', 'family') %>% unique()
species_df <- merge(x=species_df, y=gts, by='species', all.x=TRUE)
head(species_df)
dim(species_df)

# make phylogenetic tree for species in dataframe 
tree.a <- phylo.maker(sp.list=species_df) 

# read and format community matrix where rows correspond to sites and columns to species
comm.matrix.df <- fread(comm.matrix.filename, sep=',')
colnames(comm.matrix.df) <- gsub('\\.', '-', colnames(comm.matrix.df))
comm.matrix <- comm.matrix.df %>% select(-c('x','y'))

# perform phylogenetic PCA and save output
tic()
evopca <- evopcahellinger(tree.a$scenario.3, comm.matrix, scannf = FALSE, nf = 3)
toc()
save(evopca, file = 'evopca.RData')

# format output into dataframe and save it
df <- comm.matrix.df %>% select('x','y') %>% cbind(evopca$li)
head(df)
write.csv(df, 'evopca_df.csv', row.names = FALSE)

# compute and print variance explained by the 5 first principal components
print((evopca$eig / sum(evopca$eig))[1:5])