library(V.PhyloMaker) # https://onlinelibrary.wiley.com/doi/full/10.1111/ecog.04434
library(tidyr)
library(tidyverse)
library(adiv)
library(tictoc)
library(data.table)

setwd('/Users/nina/Documents/treemap/treemap/data/')
comm.matrix.filename <- 'ecoregion_species_sampled.csv'

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

# read and format community matrix where rows correspond to sites and columns to species
comm.matrix <- data.frame(fread(comm.matrix.filename, sep=','))
colnames(comm.matrix) <- gsub('\\.', '-', colnames(comm.matrix))
rownames(comm.matrix) <- comm.matrix$site
comm.matrix$site <- NULL
comm.matrix.sel <- comm.matrix[rowSums(comm.matrix) != 0, colSums(comm.matrix) != 0]

# make phylogenetic tree for species in dataframe 
tree.a <- phylo.maker(sp.list=species_df) 

tic()
evopca <- evopcahellinger(tree.a$scenario.3, comm.matrix.sel, scannf = FALSE, nf = 3)
toc()

save(evopca, file = 'evopca_ecoregions_current_future.RData')

# load('evopca_ecoregions_current_future.RData')

df <- comm.matrix.sel %>% rownames_to_column('site') %>% 
  select('site') %>% cbind(evopca$li)
head(df)
write.csv(df, 'evopca_ecoregions_current_future_df.csv', row.names = FALSE)

print((evopca$eig / sum(evopca$eig))[1:5])


