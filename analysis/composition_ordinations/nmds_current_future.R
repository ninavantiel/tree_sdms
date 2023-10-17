library(vegan)
library(ape)
library(tibble)
library(ggplot2)
library(data.table)
library(dplyr)
library(tidyr)
library(gridExtra)
library(parallel)
library(tictoc)

setwd('/Users/nina/Documents/treemap/treemap/data/')
comm.matrix.current.filename <- 'species_data_covariates_1981_2010_scale_92766.csv'
comm.matrix.future.filename <- 'species_data_covariates_2071_2100_ssp585_scale_92766.csv'
output.file.prefix <- 'nmds_3d_1981_2010_AND_2071_2100_ssp585'

# if distance matrix was not already computed, compute it
# otherwise, load it 
if (! file.exists(paste0(output.file.prefix, '_dist_mat.Rdata'))){
  # read community matrix where rows correspond to sites and columns to species
  # for current and future climate variables
  comm.matrix.current <- data.frame(fread(comm.matrix.current.filename, sep=','))
  comm.matrix.future <- data.frame(fread(comm.matrix.future.filename, sep=','))
  
  # set coordinates (x, y) + current/future as row names
  rownames(comm.matrix.current) <- paste(comm.matrix.current$x, comm.matrix.current$y, 'current', sep='_')
  comm.matrix.current$x <- NULL
  comm.matrix.current$y <- NULL
  rownames(comm.matrix.future) <- paste(comm.matrix.future$x, comm.matrix.future$y, 'future', sep='_')
  comm.matrix.future$x <- NULL
  comm.matrix.future$y <- NULL
  
  # concatenate both dataframes together and remove columns that contain only 0s
  full.comm.mat <- rbind(comm.matrix.current, comm.matrix.future)
  comm.matrix.sel <- full.comm.mat %>% select_if(colSums(.) != 0)
  
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
  rownames_to_column('x_y') %>% 
  separate(x_y, c('x','y','current_or_future'), sep='_')
print(head(nmds.points))
fwrite(nmds.points, paste0(output.file.prefix, '.csv'))
