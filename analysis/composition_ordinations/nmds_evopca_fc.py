import sys
sys.path.insert(0, '/Users/nina/Documents/treemap/treemap/analysis')
from config_figures import *

if __name__ == '__main__':
    # join NMDS and evoPCA feature collections with filter that matches x and y properties
    eq_filter = ee.Filter.And(ee.Filter.equals(leftField = 'x', rightField = 'x'), ee.Filter.equals(leftField = 'y', rightField = 'y'))
    joined_fc = ee.Join.inner('nmds','evopca').apply(nmds, evopca, eq_filter).map(lambda f: ee.Feature(f.get('evopca')).copyProperties(ee.Feature(f.get('nmds'))))

    # get projection with 3,000 arc second scale
    scale_mult_100 = scale_to_use.multiply(100)
    print(scale_mult_100.getInfo())
    proj = sdms.first().reproject(crs = 'EPSG:4326', scale = scale_mult_100).projection()

    # add geometry to feature collection with rectangle constructed around (x,y) center points
    # add area of geoemtry as property
    fc_with_geo = joined_fc.map(lambda f: f.setGeometry(ee.Geometry.Rectangle([
        f.getNumber('x').subtract(0.5), f.getNumber('y').subtract(0.5), f.getNumber('x').add(0.5), f.getNumber('y').add(0.5)
    ], proj))).map(lambda f: f.set('area', f.geometry().area()))

    # export feature collection to asset
    export_table_to_asset(fc_with_geo, nmds_evopca_fc_filename, ordinations_folder)

