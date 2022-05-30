sampled_data_dir=`python3 config.py "sampled_data_localdir"`
merged_data_dir=`python3 config.py "merged_data_localdir"`

if [ ! -e $sampled_data_dir ]; then
	mkdir $sampled_data_dir
fi
if [ ! -e "$merged_data_dir" ]; then
        mkdir $merged_data_dir
fi

sampled_data_ee_dir=`python3 config.py "sampled_data_dir"`
earthengine create folder $sampled_data_ee_dir
sampled_data_ls=`earthengine ls ${sampled_data_ee_dir}`
echo `echo $sampled_data_ls | grep -o $sampled_data_ee_dir | wc -l` sampled species uploaded to gee
echo `cat species_list.csv | wc -l` species in list

{
	while IFS=, read -r x
		do
		#if [ ! -e "${merged_data_dir}/${x}.csv" ]; then
		if [[ ! "$sampled_data_ls" == *"$x"* ]]; then
			python3 p1_sample_covariates.py ${x}
		else
			echo $x already done
		fi
	done
} < species_list.csv
