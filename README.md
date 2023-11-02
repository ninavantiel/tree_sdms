This repository contains all the code used in the results presented in the manuscript "Regional uniqueness of tree species composition and response to forest loss and climate change". It is organized in two main parts:
1. `model` directory: modelling pipeline to estimate the spatial distribution of tree species at the global level at 30-arc second resolution using Google EarthEngine.
2. `analysis` directory: scripts for the downstream analyses and figures using the modelled distributions of 10,590 tree species.

The majority of scipts are in Python and interact with Earthengine through the Google Earthengine Python API. There are also some scripts solely in Python and some in R. 

README files in each of the subdirectories contain further details about the scripts.