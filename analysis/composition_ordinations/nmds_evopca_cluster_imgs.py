import sys
sys.path.insert(0, '/Users/nina/Documents/treemap/treemap/analysis')
from config_figures import *

if __name__ == '__main__':
    scale_mult_100 = scale_to_use.multiply(100)
    proj = sdms.first().reproject(crs = 'EPSG:4326', scale = scale_mult_100).projection()

    # add geometry to feature collection with rectangle constructed around (x,y) center points
    # add area of geoemtry as property
    fc_with_geo = nmds_evopca_cluster_fc.map(lambda f: f.setGeometry(ee.Geometry.Rectangle([
        f.getNumber('x').subtract(0.5), f.getNumber('y').subtract(0.5), f.getNumber('x').add(0.5), f.getNumber('y').add(0.5)
    ], proj)))

    nmds_cluster_img = fc_with_geo.reduceToImage(['nmds_cluster'], ee.Reducer.first()).toInt().add(ee.Image.constant(1)).toInt()
    export_image_to_drive(nmds_cluster_img, 'nmds_cluster_int_add1')

    evopca_cluster_img = fc_with_geo.reduceToImage(['evopca_cluster'], ee.Reducer.first()).toInt().add(ee.Image.constant(1).toInt()).toInt()
    export_image_to_drive(evopca_cluster_img, 'evopca_cluster_int_add1')
    