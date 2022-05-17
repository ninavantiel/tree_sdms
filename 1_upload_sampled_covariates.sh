bucket=`python config_dict.py bucket`
gsutil cp -r merged_data ${bucket}

ee_folder=`python config_dict.py sampled_data_dir`
earthengine create folder $ee_folder

for f in `gsutil ls ${bucket}/merged_data/`; do
	f1=${f##*/}
	f2=${f1%.*}
	echo $f2
	if [[ $f2 != "" ]]; then
		earthengine upload table --x_column Pixel_Long --y_column Pixel_Lat --asset_id ${ee_folder}/${f2} $f
	fi
done
