library(V.PhyloMaker) # https://onlinelibrary.wiley.com/doi/full/10.1111/ecog.04434
library(tidyr)
library(dplyr)
library(tidyverse)
library(ggtree)
library(betapart)
library(PhyloMeasures)
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

community_mat <- read.csv("../../species_data_merged_scale_92766.csv")
colnames(community_mat) <- gsub('_', ' ', colnames(community_mat))
colnames(community_mat) <- gsub('\\.', '-', colnames(community_mat))
dim(community_mat)

species_df_sel <- species_df
species_df_sel <- merge(x=species_df_sel, y=gts, by='species', all.x=TRUE)
head(species_df_sel)
dim(species_df_sel)

#example <- read.csv("~/Downloads/ECOG-04434/Appendix_3-Example_species_list.csv")
#head(example)
tree.a <- phylo.maker(sp.list=species_df_sel) #, tree=GBOTB.extended, nodes=nodes.info.1, scenarios="S3")
ggtree(tree.a$scenario.3) + geom_tiplab(as_ylab=TRUE, color='firebrick')

tree <- as.phylo(tree.a$scenario.3)
tree$node.label <- NULL
# plot(tree)
is.rooted(tree)

dim(community_mat)
community_mat_sel <- community_mat %>% select('x', 'y', species_df_sel$species)
dim(community_mat_sel)
community_mat_sel <- community_mat_sel[rowSums(community_mat_sel %>% select(-c('x','y'))) > 0,]
dim(community_mat_sel)
# head(community_mat_sel)

community_mat_sel <- community_mat_sel[sample(nrow(community_mat_sel), 100), ]
dim(community_mat_sel)

comm <- community_mat_sel %>% select(-c('x','y'))
colnames(comm) <- gsub(' ', '_', colnames(comm))
rownames(comm) <- NULL
dim(comm)

###### phylosor from phylomeasures (deprecated R package but still usable) ######
# tmp <- comm[sample(nrow(comm), 100), ] #comm[1:5000,]
# tmp <- tmp[rowSums(tmp) > 0,colSums(tmp) > 0]
# dim(tmp)

start <- Sys.time()
phylosor <- phylosor.query(tree, comm)
end <- Sys.time()
print(end-start)
# 552x380 -> 1.7 seconds 
# 1000x6401 -> 42 seconds
# 5000x7182 -> 14 minutes
# 19535x10590 ->


phylodis <- 1 - phylosor
PCOA <- pcoa(phylodis)

normalise <- function(x) {
  x_norm <- (x - min(x)) / (max(x) - min(x))
  return(x_norm)
}
plot_df <- community_mat_sel %>% select('x','y') %>% cbind(as_tibble(apply(PCOA$vectors[,1:3], 2, normalise)))
head(plot_df)

plot(plot_df$x, 1-plot_df$y, col=rgb(plot_df[,c('Axis.1','Axis.2','Axis.3')]))

###### evo pca, ordination directly ######
# tmp <- comm[1:10000,]
# tmp <- tmp[rowSums(tmp) > 0,colSums(tmp) > 0]
# dim(tmp)

start <- Sys.time()
evopca <- evopcahellinger(tree, comm)
end <- Sys.time()
print(end-start)
# 552x380 -> 10 seconds
# 1000x4601 -> 51 seconds
# 5000x7182 -> 6 minutes
# 10000x10126 -> 
# 19535x10590 -> memory limit

plot_df <- community_mat_sel %>% select('x','y') %>% cbind(apply(evopca$l1, 2, normalise))
head(plot_df)
plot(plot_df$x, 1-plot_df$y, col=rgb(plot_df[,c('RS1','RS2','RS3')]))

# phylo beta pair, probably slowest option
# start <- Sys.time()
# phylobeta <- phylo.beta.pair(x=comm, tree=tree) #
# end <- Sys.time()
# print(end-start)
# PCOA <- pcoa(phylobeta$phylo.beta.sor)
# 
# barplot(PCOA$values$Relative_eig[1:10])
# 
# # Plot your results
# biplot.pcoa(PCOA)




