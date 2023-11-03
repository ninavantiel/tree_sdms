import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from config_figures import *

if __name__ == '__main__':
    median_area_img = sdms.map(
        lambda sdm: mask_sdm(
            sdm.select('covariates_1981_2010').multiply(forest10_image)
        ).multiply(sdms_area_lat_elev_fc.filter(ee.Filter.And(
            ee.Filter.eq('species', sdm.get('system:index')),
            ee.Filter.eq('climate','1981_2010'), 
            ee.Filter.eq('min_tree_cover',10) 
        )).first().getNumber('area_1981_2010')).toFloat()).median()

    export_image_to_drive(median_area_img, 'median_area_forest_1981_2010')
    export_image_to_drive(median_area_img.log10(), 'median_area_forest_1981_2010_log10')