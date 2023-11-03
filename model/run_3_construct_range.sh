occ_dir=`python3 config.py "prepped_occurrences_dir"`
range_dir=`python3 config.py "range_dir"`
earthengine create folder $range_dir

occ_ls=`earthengine ls ${occ_dir}`
echo `echo ${occ_ls} | grep -o $occ_dir | wc -l` species occurrences prepared

ranges_ls=`earthengine ls ${range_dir}`
echo `echo ${ranges_ls} | grep -o $range_dir | wc -l` species ranges done

{
	while IFS=, read -r x; do
		if [[ "$occ_ls" == *"$x"* ]]; then
			if [[ ! "$ranges_ls" == *"$x"* ]]; then
				echo "**" $x
				python3 p3_construct_range.py ${x}
			fi
		fi
	done
} < species_list.csv
