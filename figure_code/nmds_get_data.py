from config_figures import *



if __name__ == '__main__':
    outdir = nmds_sampled_data_dir + "/" 
#   outfile = merged_data_localdir + "/" + species + ".csv"

    # Get feature collection of occurences of species of interest 
    points = ee.FeatureCollection('projects/crowtherlab/nina/treemap/pseudoabsences').randomColumn().sort('random')
    points = points.limit(1000)
    
    run_sampling(points, n_points, outdir, outfile)

    # If final file has the correct number of rows, upload to earthengine
    # upload_output(outfile, n_points, bucket_path + '/merged_data/' + species + '.csv', sampled_data_dir + '/' + species)
