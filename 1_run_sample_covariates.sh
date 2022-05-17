if [ ! -e "sampled_data" ]; then
	mkdir sampled_data
fi

if [ ! -e "merged_data" ]; then
        mkdir merged_data
fi

{
	while IFS=, read -r x
		do
		if [ ! -e "merged_data/${x}.csv" ]; then
			python3 1_sample_covariates.py ${x}
		else
			echo "*" ${x}: sampling already done
		fi
	done
} < species_list.csv
