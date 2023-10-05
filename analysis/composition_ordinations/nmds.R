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
comm.matrix.filename <- 'species_data_covariates_1981_2010_scale_92766.csv'
output.file.prefix <- 'nmds_3d_1981_2010_scale_92766'

npar = 6

# if distance matrix was not already computed, compute it
# otherwise, load it 
if (! file.exists(paste0(output.file.prefix, '_dist_mat.Rdata'))){
  # read community matrix where rows correspond to sites and columns to species
  comm.matrix <- fread(comm.matrix.filename, sep=',')
  comm.matrix <- data.frame(comm.matrix) 
  
  # set coordinates (x, y) as row names
  rownames(comm.matrix) <- paste(comm.matrix$x, comm.matrix$y, sep='_')
  comm.matrix$x <- NULL
  comm.matrix$y <- NULL
  print('Community matrix shape')
  print(dim(comm.matrix))
  
  # remove columns (species) that contain only 0s
  comm.matrix.sel <- comm.matrix %>% select_if(colSums(.) != 0)
  print('Community matrix shape after removing species that do not occur')
  print(dim(comm.matrix.sel))
  
  tmp <- comm.matrix.sel[,1:1000]
  tmp <- tmp[rowSums(tmp) != 0, colSums(tmp) !=0]
  comm.matrix.sel <- tmp
  
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
nmds.output <- metaMDSiter(dist.mat, k=3, parallel = npar)
toc()
print(nmds.output)

# format NMDS output to include coordinates (x, y) and save csv
nmds.points <- data.frame(nmds.output$points[,1:3]) %>% 
  rownames_to_column('x_y') %>% 
  separate(x_y, c('x','y'), sep='_')
print(head(nmds.points))
fwrite(nmds.points, paste0(output.file.prefix, '.csv'))

#g1 <- ggplot(nmds.points, aes(x=MDS1, y=MDS2)) + geom_point()
#g2 <- ggplot(nmds.points, aes(x=MDS1, y=MDS3)) + geom_point()
#g3 <- ggplot(nmds.points, aes(x=MDS2, y=MDS3)) + geom_point()
#g <- grid.arrange(g1, g2, g3, ncol=3)
#ggsave(g, file=paste0(output.file.prefix, '.png'), width = 10, height = 4)
