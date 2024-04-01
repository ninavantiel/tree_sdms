import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from config_figures import *

if __name__ == '__main__':
    # join NMDS and evoPCA feature collections with filter that matches x and y properties
    eq_filter = ee.Filter.And(ee.Filter.equals(leftField = 'x', rightField = 'x'), ee.Filter.equals(leftField = 'y', rightField = 'y'))
    joined_fc = ee.Join.inner('nmds','evopca').apply(nmds, evopca, eq_filter).map(lambda f: ee.Feature(f.get('evopca')).copyProperties(ee.Feature(f.get('nmds'))))

    # equal area projection with 100 km scale
    proj = proj6933.atScale(1e5)

    # add geometry to feature collection with rectangle constructed around (x,y) center points
    # add area of geoemtry as property
    fc_with_geo = joined_fc.map(lambda f: f.setGeometry(ee.Geometry.Rectangle([
        f.getNumber('x').subtract(0.5), (f.getNumber('y').multiply(-1)).subtract(0.5), f.getNumber('x').add(0.5), (f.getNumber('y').multiply(-1)).add(0.5)
    ], proj, False).transform('EPSG:4326', 100))).map(lambda f: f.set('area', f.geometry().area(10)))

    # export feature collection to asset
    export_table_to_asset(fc_with_geo, nmds_evopca_fc_filename)

