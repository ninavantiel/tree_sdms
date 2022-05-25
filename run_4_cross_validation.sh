range_dir=`python3 config.py "range_dir"`
cv_dir=`python3 config.py "cross_validation_dir"`
earthengine create folder $cv_dir

ranges_ls=`earthengine ls ${range_dir}`
echo `echo ${ranges_ls} | grep -o $range_dir | wc -l` species ranges done

cv_ls=`earthengine ls ${cv_dir}`
n_cv_ls=`echo ${cv_ls} | grep -o $cv_dir | wc -l`
echo `expr $n_cv_ls / 3` species cross validation done

{
	while IFS=, read -r x; do
		if [[ "$ranges_ls" == *"$x"* ]]; then
			n_x=`echo $cv_ls | grep -o $x | wc -l`
			echo $x $n_x
			if [[ ! $n_x -eq 3 ]]; then
				python3 p4_cross_validation.py ${x}
			fi
		fi
	done
} < species_list.csv
