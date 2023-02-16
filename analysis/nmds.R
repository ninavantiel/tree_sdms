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

setwd('/Users/ninavantiel/Documents/treemap/treemap_figures_data/')

dopar = TRUE
npar = 4

comm.matrix.filename <- 'sampled_species_composition/species_data_scale_92766.csv'
output.file.prefix <- 'nmds/nmds_3d_scale_92766_par'

comm.matrix <- fread(comm.matrix.filename, sep=',')
comm.matrix <- data.frame(comm.matrix) 
rownames(comm.matrix) <- paste(comm.matrix$x, comm.matrix$y, sep='_')
comm.matrix$x <- NULL
comm.matrix$y <- NULL
print('Community matrix shape')
print(dim(comm.matrix))

comm.matrix.sel = comm.matrix %>% select_if(colSums(.) != 0)
print('Community matrix shape after removing species that do not occur')
print(dim(comm.matrix.sel))

# NMDS
tic()
dist.mat <- vegdist(comm.matrix.sel, distance = 'sorensen')
toc()

tic()
if(dopar) {
  nmds.output <- metaMDSiter(dist.mat, k=3, parallel = npar)
} else {
  nmds.output <- metaMDS(dist.mat, k=3)
}
toc()
print(nmds.output)
nmds.points <- data.frame(nmds.output$points[,1:3]) %>% 
  rownames_to_column('x_y') %>% 
  separate(x_y, c('x','y'), sep='_')
print(head(nmds.points))
fwrite(nmds.points, paste0(output.file.prefix, '.csv'))

g1 <- ggplot(nmds.points, aes(x=MDS1, y=MDS2)) + geom_point()
g2 <- ggplot(nmds.points, aes(x=MDS1, y=MDS3)) + geom_point()
g3 <- ggplot(nmds.points, aes(x=MDS2, y=MDS3)) + geom_point()
g <- grid.arrange(g1, g2, g3, ncol=3)
ggsave(g, file=paste0(output.file.prefix, '.png'), width = 10, height = 4)
