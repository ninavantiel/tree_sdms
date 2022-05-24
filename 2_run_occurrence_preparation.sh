sampled_data_dir=`python3 config.py "sampled_data_dir"`
prepped_occurrences_dir=`python3 config.py "prepped_occurrences_dir"`
#earthengine create folder $prepped_points_dir

sampled_data_ls=`earthengine ls ${sampled_data_dir}`
echo `echo $sampled_data_ls | grep -o $sampled_data_dir | wc -l` species sampled 

prepped_occurrences_ls=`earthengine ls ${prepped_occurrences_dir}`
echo `echo ${prepped_occurrences_ls} | grep -o $prepped_occurrences_dir | wc -l` species occurrences prepared

{
	while IFS=, read -r x; do
		if [[ "$sampled_data_ls" == *"$x"* ]]; then
			if [[ ! "$prepped_occurrences_ls" == *"$x"* ]]; then
				echo $x
				python3 2_occurrence_preparation.py ${x}
			fi
		fi
	done
} < species_list.csv
