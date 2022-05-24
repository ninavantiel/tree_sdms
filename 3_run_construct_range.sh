prepped_occurrences_dir=`python3 config.py "prepped_occurrences_dir"`
range_dir=`python3 config.py "range_dir"`
#earthengine create folder $range_dir

prepped_occurrences_ls=`earthengine ls ${prepped_occurrences_dir}`
echo `echo ${prepped_occurrences_ls} | grep -o $prepped_occurrences_dir | wc -l` species occurrences prepared

ranges_ls=`earthengine ls ${range_dir}`
echo `echo ${ranges_ls} | grep -o $range_dir | wc -l` species ranges done

{
	while IFS=, read -r x; do
		if [[ "$prepped_occurrences_ls" == *"$x"* ]]; then
			if [[ ! "$ranges_ls" == *"$x"* ]]; then
				echo $x
				python3 3_construct_range.py ${x}
			fi
		fi
	done
} < species_list.csv
