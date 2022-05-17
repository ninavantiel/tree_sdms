import sys

treemap_dir = 'projects/crowtherlab/nina/treemap' 

dictionary = {
	"bucket": "gs://nina_other_bucket",

	"treemap_dir": treemap_dir,
	"sampled_data_dir": treemap_dir + "/sampled_data_test",

	"species_occurence_fc": treemap_dir + "/treemap_data_all_species",
	"composite_to_sample": treemap_dir + "/composite_to_sample"

#"obs_points_dir":  treemap_dir + "/points",
#"obs_range_dir": treemap_dir + '/ranges' 
#test_class_dir = treemap_dir +  '/cv_classifications'
#sdm_coll = treemap_dir + '/sdms_binary' 
}

def config_dict_get(key):
	if key in dictionary.keys(): return dictionary[key]
	else: print('Key not found in config dictionary')

if __name__ == '__main__':
	key = sys.argv[1]
	print(dictionary[key])
