cv_dir=`python3 config.py "cross_validation_dir"`
sdm_dir=`python3 config.py "sdm_img_col"`
earthengine create collection $sdm_dir

cv_ls=`earthengine ls ${cv_dir}`
n_cv_ls=`echo ${cv_ls} | grep -o $cv_dir | wc -l`
echo `expr $n_cv_ls / 3` species cross validation done

sdm_ls=`earthengine ls ${sdm_dir}`
echo `echo ${sdm_ls} | grep -o $sdm_dir | wc -l` species sdm mapping done

{
	while IFS=, read -r x; do
		n_x=`echo $cv_ls | grep -o $x | wc -l`
		if [[ $n_x -eq 3 ]]; then
			if [[ ! "$sdm_ls" == *"$x"* ]]; then
				echo "**" $x
				python3 p5_sdm_mapping.py ${x}
			fi
		fi
	done
} < species_list.csv
