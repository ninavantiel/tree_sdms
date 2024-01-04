import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from config_figures import *

if __name__ == '__main__':
    proj = proj6933.atScale(1e5)

    # add geometry to feature collection with rectangle constructed around (x,y) center points
    # add area of geoemtry as property
    fc_with_geo = nmds_evopca_cluster_fc.map(lambda f: f.setGeometry(ee.Geometry.Rectangle([
        f.getNumber('x').subtract(0.5), (f.getNumber('y').multiply(-1)).subtract(0.5), 
        f.getNumber('x').add(0.5), (f.getNumber('y').multiply(-1)).add(0.5)
    ], proj, False).transform('EPSG:4326', 100)))

    nmds_cluster_img = fc_with_geo.reduceToImage(['nmds_cluster'], ee.Reducer.first()).toInt().add(ee.Image.constant(1)).toInt()
    export_image_to_drive(nmds_cluster_img, 'nmds_equal_area_cluster')

    evopca_cluster_img = fc_with_geo.reduceToImage(['evopca_cluster'], ee.Reducer.first()).toInt().add(ee.Image.constant(1).toInt()).toInt()
    export_image_to_drive(evopca_cluster_img, 'evopca_equal_area_cluster')
    