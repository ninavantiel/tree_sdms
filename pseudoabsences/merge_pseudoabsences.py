from os import listdir
from os.path import isfile, join
import pandas as pd

fout=open("20201103_merged_pseudoabsences.csv","a")

sampled_data = [f for f in listdir("pa_1m_data") if isfile(join("pa_1m_data" , f))]

# first file:
for line in open("pa_1m_data/" + sampled_data[0]):
    fout.write(line)
# now the rest:    
for num in range(1,len(sampled_data)):
	try:
		f = open("pa_1m_data/" + sampled_data[num])
		f.__next__()
		for line in f:
			fout.write(line)
		f.close()
	except IOError:
	    pass

fout.close()

