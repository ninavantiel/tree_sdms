if [ ! -e "merging_scripts" ]; then
	mkdir merging_scripts
fi

if [ ! -e "merged_data" ]; then
	mkdir merged_data
fi

{
	while IFS=, read -r x
		do
		echo $x
		if [ `ls sampled_data/${x} | wc -l` -eq 0 ]; then
			echo not sampled
		elif [ -e merged_data/${x}.csv ]; then
			echo already merged
		else
			echo merging...
			sed "s/TOFILL/$x/g" merge_files_TOFILL.py >> merging_scripts/merge_${x}.py
			python3 merging_scripts/merge_${x}.py
		fi
	done
} < species_to_resample.csv #species_list.csv

