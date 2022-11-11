bucket=`python3 config.py "bucket_path"`

# generate pseudoabsences
#python3 prep_generate_pseudoabsences.py
echo gsutil cp `python3 config.py "merged_pseudoabsences_filepath"` ${bucket} 


