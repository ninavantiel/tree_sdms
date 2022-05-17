from os import listdir
from os.path import isfile, join
import pandas as pd

speciesOfInterest = 'TOFILL'
print(speciesOfInterest)

dirOfInterest = "sampled_data/" + speciesOfInterest + "/"

fout=open("merged_data/" + speciesOfInterest + ".csv","a")

sampled_data = [f for f in listdir(dirOfInterest) if isfile(join(dirOfInterest, f))]
print(len(sampled_data))

# first file:
for line in open(dirOfInterest + sampled_data[0]):
    fout.write(line)
# now the rest:    
for num in range(1,len(sampled_data)):
	print(num)
	try:
		f = open(dirOfInterest + sampled_data[num])
		f.__next__()
		for line in f:
			fout.write(line)
		f.close()
	except IOError:
	    pass

fout.close()