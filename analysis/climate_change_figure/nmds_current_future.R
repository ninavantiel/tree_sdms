library(vegan)
library(ape)
library(tibble)
library(ggplot2)
library(data.table)
library(dplyr)
library(tidyr)
library(tictoc)

setwd('/Users/nina/Documents/treemap/treemap/data/')
comm.matrix.filename <- 'ecoregion_species_sampled.csv'
output.file.prefix <- 'nmds_3d_ecoregions_current_future'

# if distance matrix was not already computed, compute it
# otherwise, load it 
if (! file.exists(paste0(output.file.prefix, '_dist_mat.Rdata'))){
  # read community matrix where rows correspond to ecoregions and columns to species
  comm.matrix <- data.frame(fread(comm.matrix.filename, sep=','))
  rownames(comm.matrix) <- comm.matrix$site
  comm.matrix$site <- NULL
  
  # remove columns that contain only 0s
  comm.matrix.sel <- comm.matrix[rowSums(comm.matrix) != 0, colSums(comm.matrix) != 0]
  
  # compute distance matrix among sites and save
  tic()
  dist.mat <- vegdist(comm.matrix.sel, distance = 'sorensen')
  toc()
  save(dist.mat, file = paste0(output.file.prefix, '_dist_mat.Rdata'))
} else {
  load(paste0(output.file.prefix, '_dist_mat.Rdata'))
}

# compute 3d NMDS on distance matrix
tic()
nmds.output <- metaMDSiter(dist.mat, k=3)
toc()
print(nmds.output)

# format NMDS output to include coordinates (x, y) and save csv
nmds.points <- data.frame(nmds.output$points[,1:3]) %>% 
  rownames_to_column('site') %>% 
  separate(site, c('ecoregion','ecoid','current_or_future'), sep='_')
print(head(nmds.points))
fwrite(nmds.points, paste0(output.file.prefix, '.csv'))
