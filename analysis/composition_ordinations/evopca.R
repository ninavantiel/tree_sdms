library(V.PhyloMaker) # https://onlinelibrary.wiley.com/doi/full/10.1111/ecog.04434
library(tidyr)
library(dplyr)
library(tidyverse)
library(ggtree)
library(adiv)
library(tictoc)

setwd('/Users/nina/Documents/treemap/treemap/data/')
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
# ggtree(tree.a$scenario.3) + geom_tiplab(as_ylab=TRUE, color='firebrick')

# read and format community matrix where rows correspond to sites and columns to species
comm.matrix <- fread(comm.matrix.filename, sep=',')
#colnames(comm.matrix) <- gsub('_', ' ', colnames(comm.matrix))
colnames(comm.matrix) <- gsub('\\.', '-', colnames(comm.matrix))
comm.matrix <- comm.matrix %>% select(-c('x','y'))
#colnames(comm.matrix) <- gsub(' ', '_', colnames(comm.matrix))
#rownames(comm.matrix) <- NULL

tic()
evopca <- evopcahellinger(tree.a$scenario.3, comm.matrix, scannf = FALSE, nf = 3)
toc()

save(evopca, file = '../../evopca.RData')

load('../../evopca.RData')

df <- community_mat %>% select('x','y') %>% cbind(evopca$li)
head(df)
write.csv(df, '../../evopca_df.csv', row.names = FALSE)

print((evopca$eig / sum(evopca$eig))[1:5])

plot(df$x, 1-df$y, col=rgb(
  apply(df[,c('Axis3','Axis1','Axis2')], 2, function(x){return((x-min(x)) / (max(x)-min(x)))}), maxColorValue = 1
))

