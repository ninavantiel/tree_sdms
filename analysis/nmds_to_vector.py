from config_figures import *

if __name__ == '__main__':
    nmds_fc = ee.FeatureCollection('projects/crowtherlab/nina/treemap_figures/species_composition_nmds/nmds_3d_par4_scale_92766')
    scale_to_use = sdms.first().projection().nominalScale().multiply(100)
    proj = sdms.first().reproject(crs = 'EPSG:4326', scale = scale_to_use).projection()

    nmds_rectangles = nmds_fc.map(lambda f: f.setGeometry(ee.Geometry.Rectangle([
        f.getNumber('x').subtract(0.5), f.getNumber('y').subtract(0.5), f.getNumber('x').add(0.5), f.getNumber('y').add(0.5)
    ], proj)))
    export_table_to_asset(nmds_rectangles, 'nmds_fc_geos')

    '''
    points = points.limit(100)

    sdms_current = sdms.map(lambda sdm: unmask_mask(sdm.select('covariates_1981_2010')))
    image_to_sample = sdms_current.toBands().addBands(ee.Image.pixelCoordinates(sdms_current.first().projection()))
    sampled = image_to_sample.reduceRegions(points, ee.Reducer.first()).map(
        lambda f: f.select(f.propertyNames(), f.propertyNames().map(lambda x: ee.String(x).replace('_covariates_1981_2010','')))
    )

    export_table_to_drive(sampled, 'nmds_data_100_points')
    '''