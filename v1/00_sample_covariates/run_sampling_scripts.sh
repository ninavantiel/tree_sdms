if [ ! -e "sampling_scripts" ]; then
	mkdir sampling_scripts
fi
if [ ! -e "sampled_data" ]; then
	mkdir sampled_data
fi

{
	while IFS=, read -r x
		do
		echo $x

		if [ ! -e "sampled_data/${x}" ]; then
			mkdir sampled_data/${x}
		fi

		if [ `ls sampled_data/${x} | wc -l` -eq 0 ]; then
			echo sampling...
			sed "s/TOFILL/$x/g" sample_species_TOFILL.py >> sampling_scripts/sample_${x}.py
			python3 sampling_scripts/sample_${x}.py
		else
			echo sampling already done
		fi
	done
} < species_to_resample.csv #species_list.csv



