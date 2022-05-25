bucket=`python3 config.py "bucket_path"`
merged_data_dir=`python3 config.py "merged_data_localdir"`
echo `ls ${merged_data_dir} | wc -l` species sampled 
gsutil -m cp -r ${merged_data_dir} ${bucket}

sampled_data_dir=`python3 config.py "sampled_data_dir"` 
earthengine create folder $sampled_data_dir
sampled_data_ls=`earthengine ls ${sampled_data_dir}`
echo `echo $sampled_data_ls | grep -o $sampled_data_dir | wc -l` sampled species uploaded to gee

for f in `gsutil ls ${bucket}/merged_data/`; do
	f1=${f##*/}
	f2=${f1%.*}
	if [[ $f2 != "" ]]; then
		if [[ ! "$sampled_data_ls" == *"$f2"* ]]; then
			earthengine upload table --x_column Pixel_Long --y_column Pixel_Lat --asset_id ${sampled_data_dir}/${f2} $f
		fi
	fi
done
