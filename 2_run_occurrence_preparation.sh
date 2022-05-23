sampled_data_dir="projects/crowtherlab/nina/treemap/sampled_data_test"
prepped_points_dir="projects/crowtherlab/nina/treemap/prepped_points_test"
#earthengine create folder $prepped_points_dir

sampled_data_ls=`earthengine ls ${sampled_data_dir}`
echo `echo $sampled_data_ls | grep -o $sampled_data_dir | wc -l` species sampled 

prepped_points_ls=`earthengine ls ${prepped_points_dir}`
echo `echo ${prepped_points_ls} | grep -o $prepped_points_dir | wc -l` species occurrences prepared

{
	while IFS=, read -r x; do
		if [[ "$sampled_data_ls" == *"$x"* ]]; then
			if [[ ! "$prepped_points_ls" == *"$x"* ]]; then
				echo $x
				python3 2_occurrence_preparation.py ${x}
			fi
		fi
	done
} < species_list.csv
