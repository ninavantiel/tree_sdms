sampled_data_dir=`python3 config.py "sampled_data_dir"`
occ_dir=`python3 config.py "prepped_occurrences_dir"`
earthengine create folder $occ_dir

sampled_data_ls=`earthengine ls ${sampled_data_dir}`
echo `echo $sampled_data_ls | grep -o $sampled_data_dir | wc -l` species sampled 

occ_ls=`earthengine ls ${occ_dir}`
echo `echo ${occ_ls} | grep -o $occ_dir | wc -l` species occurrences prepared

{
	while IFS=, read -r x; do
		if [[ "$sampled_data_ls" == *"$x"* ]]; then
			if [[ ! "$occ_ls" == *"$x"* ]]; then
				echo "**" $x
				python3 p2_occurrence_preparation.py ${x}
			fi
		fi
	done
} < species_list.csv
