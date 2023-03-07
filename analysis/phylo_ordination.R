library(V.PhyloMaker) # https://onlinelibrary.wiley.com/doi/full/10.1111/ecog.04434
library(tidyr)
library(dplyr)
library(tidyverse)
library(ggtree)
library(adiv)

setwd("~/Documents/treemap/treemap/analysis")

species_df <- read.csv("species_list.csv", header=FALSE, col.names = 'species')
species_df$species <- gsub('_', ' ', species_df$species)
species_df$genus <- separate(species_df, species, c("genus", "."), " ")$genus
head(species_df)
dim(species_df)

gts <- read.csv('../../globalTreeSearch.csv') 
gts <- gts %>% rename(species=taxon) %>% select('species', 'family') %>% unique()
head(gts)

species_df <- merge(x=species_df, y=gts, by='species', all.x=TRUE)
head(species_df)
dim(species_df)

tree.a <- phylo.maker(sp.list=species_df) 
ggtree(tree.a$scenario.3) + geom_tiplab(as_ylab=TRUE, color='firebrick')

community_mat <- read.csv("../../species_data_merged_scale_92766.csv")
colnames(community_mat) <- gsub('_', ' ', colnames(community_mat))
colnames(community_mat) <- gsub('\\.', '-', colnames(community_mat))
dim(community_mat)

comm <- community_mat %>% select(-c('x','y'))
colnames(comm) <- gsub(' ', '_', colnames(comm))
rownames(comm) <- NULL
dim(comm)

start <- Sys.time()
print(start)
evopca <- evopcahellinger(tree.a$scenario.3, comm, scannf = FALSE, nf = 3)
end <- Sys.time()
print(end-start)

save(evopca, file = '../../evopca.RData')

load('../../evopca.RData')

df <- community_mat %>% select('x','y') %>% cbind(evopca$li)
head(df)
write.csv(df, '../../evopca_df.csv', row.names = FALSE)

print((evopca$eig / sum(evopca$eig))[1:5])

plot(df$x, 1-df$y, col=rgb(
  apply(df[,c('Axis3','Axis1','Axis2')], 2, function(x){return((x-min(x)) / (max(x)-min(x)))}), maxColorValue = 1
))

