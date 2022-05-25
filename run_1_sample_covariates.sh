sampled_data_dir=`python3 config.py "sampled_data_localdir"`
merged_data_dir=`python3 config.py "merged_data_localdir"`

if [ ! -e $sampled_data_dir ]; then
	mkdir $sampled_data_dir
fi
if [ ! -e "$merged_data_dir" ]; then
        mkdir $merged_data_dir
fi

{
	while IFS=, read -r x
		do
		if [ ! -e "${merged_data_dir}/${x}.csv" ]; then
			python3 p1_sample_covariates.py ${x}
		fi
	done
} < species_list.csv
