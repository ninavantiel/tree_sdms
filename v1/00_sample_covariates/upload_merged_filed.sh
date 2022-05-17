gsutil -m cp merged_data/*.csv gs://nina_other_bucket/treemap_sampled_dec21/
for f in `gsutil ls gs://nina_other_bucket/treemap_sampled_dec21/`
do
	f1=${f##*/}
	f2=${f1%.*}
	echo $f2
	if [[ $f2 != "" ]]
	then
		echo upload to gee
		echo earthengine upload table --x_column Pixel_Long --y_column Pixel_Lat --asset_id projects/crowtherlab/nina/treemap/sampled_data/${f2} $f
	fi
done
