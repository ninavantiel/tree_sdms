import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from config_figures import *

if __name__ == '__main__':
    evopca_img = ee.ImageCollection([
        nmds_evopca_fc.reduceToImage(['Axis1'], ee.Reducer.first()),
        nmds_evopca_fc.reduceToImage(['Axis2'], ee.Reducer.first()),
        nmds_evopca_fc.reduceToImage(['Axis3'], ee.Reducer.first())
    ]).toBands()
    export_image_to_drive(evopca_img, 'evopca_img')

    nmds_img = ee.ImageCollection([
        nmds_evopca_fc.reduceToImage(['MDS1'], ee.Reducer.first()),
        nmds_evopca_fc.reduceToImage(['MDS2'], ee.Reducer.first()),
        nmds_evopca_fc.reduceToImage(['MDS3'], ee.Reducer.first())
    ]).toBands()
    export_image_to_drive(nmds_img, 'nmds_img')
