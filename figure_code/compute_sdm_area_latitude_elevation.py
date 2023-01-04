from config_figures import *

def get_sdm_area(sdm):
    species = sdm.get('system:index')
    sdm = sdm.select('covariates_1981_2010')
    sdm_ic = ee.ImageCollection([
        mask_sdm(sdm).set('min_tree_cover', 0),
        mask_sdm(sdm.multiply(forest10_image)).set('min_tree_cover', 10),
        mask_sdm(sdm.multiply(forest20_image)).set('min_tree_cover', 20)
    ])

    sdm_ic = sdm_ic.map(lambda img: img.set('area', img.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer = ee.Reducer.sum(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
	).get('covariates_1981_2010')))

    sdm_area = ee.Dictionary.fromLists(sdm_ic.aggregate_array('min_tree_cover').map(lambda x: ee.String('area_min_tree_cover_').cat(ee.Number(x).format())), sdm_ic.aggregate_array('area'))
    return ee.Feature(None, sdm_area).set('species', species)

def get_sdm_latitude_elevation(sdm):
    species = sdm.get('system:index')
    sdm_ic = ee.ImageCollection([
        mask_sdm(sdm.select(['covariates_1981_2010'],['sdm']).set('sdm', 'covariates_1981_2010')),
        mask_sdm(sdm.select(['covariates_2071_2100_ssp585'],['sdm']).set('sdm', 'covariates_2071_2100_ssp585'))
    ])

    sdm_ic = sdm_ic.map(lambda img: img.set({
        'latitude': img.multiply(ee.Image.pixelLonLat().select('latitude')).reduceRegion(
            reducer = ee.Reducer.median(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
        ).get('sdm'),
        'elevation': img.multiply(elevation).reduceRegion(
            reducer = ee.Reducer.median(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
        ).get('sdm')
    }))
    # .map(lambda img: img.set({
        # 'latitude': ee.Algorithms.If(img.getNumber('area').eq(0), -999, img.getNumber('latitude')),
        # 'elevation': ee.Algorithms.If(img.getNumber('area').eq(0), -999, img.getNumber('elevation')),
    # }))

    sdm_latitude = ee.Dictionary.fromLists(sdm_ic.aggregate_array('sdm').map(lambda x: ee.String(x).replace('covariates', 'latitude')), sdm_ic.aggregate_array('latitude'))
    sdm_elevation = ee.Dictionary.fromLists(sdm_ic.aggregate_array('sdm').map(lambda x: ee.String(x).replace('covariates', 'elevation')), sdm_ic.aggregate_array('elevation'))
    return ee.Feature(None, sdm_latitude.combine (sdm_elevation)).set('species', species)

def get_sdm_area_latitude_elevation(sdm):
    species = sdm.get('system:index')
    sdm_ic = ee.ImageCollection([
        mask_sdm(sdm.select(['covariates_1981_2010'],['sdm']).set('sdm', 'covariates_1981_2010')),
        mask_sdm(sdm.select(['covariates_2071_2100_ssp585'],['sdm']).set('sdm', 'covariates_2071_2100_ssp585'))
    ])
    sdm_ic = sdm_ic.map(lambda img: img.set(
        'area', img.multiply(ee.Image.pixelArea()).reduceRegion(
		    reducer = ee.Reducer.sum(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
	    ).get('sdm'),
        'latitude', img.multiply(ee.Image.pixelLonLat().select('latitude')).reduceRegion(
            reducer = ee.Reducer.median(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
        ).get('sdm'),
        'elevation', img.multiply(elevation).reduceRegion(
            reducer = ee.Reducer.median(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
        ).get('sdm')
    )).map(lambda img: img.set({
        'latitude': ee.Algorithms.If(img.getNumber('area').eq(0), -999, img.getNumber('latitude')),
        'elevation': ee.Algorithms.If(img.getNumber('area').eq(0), -999, img.getNumber('elevation')),
    }))

    sdm_area = ee.Dictionary.fromLists(sdm_ic.aggregate_array('sdm').map(lambda x: ee.String(x).replace('covariates', 'area')), sdm_ic.aggregate_array('area'))
    sdm_latitude = ee.Dictionary.fromLists(sdm_ic.aggregate_array('sdm').map(lambda x: ee.String(x).replace('covariates', 'latitude')), sdm_ic.aggregate_array('latitude'))
    sdm_elevation = ee.Dictionary.fromLists(sdm_ic.aggregate_array('sdm').map(lambda x: ee.String(x).replace('covariates', 'elevation')), sdm_ic.aggregate_array('elevation'))
    return ee.Feature(None, sdm_area.combine(sdm_latitude).combine (sdm_elevation)).set('species', species)

if __name__ == '__main__':
    print(sdms.size().getInfo(), 'sdms in analysis')
    '''
    sdms_forest10_area_lat_elev = sdms.map(lambda sdm: sdm.multiply(forest10_image)).map(get_sdm_area_latitude_elevation)
    export_table_to_drive(sdms_forest10_area_lat_elev, sdms_forest10_area_lat_elev_drive_filename)
    sdms_forest10_area_lat_elev_fc = sdms_forest10_area_lat_elev.map(lambda f: ee.Feature(f).setGeometry(ee.Geometry.Point([0,0])))
    export_table_to_asset(sdms_forest10_area_lat_elev_fc, sdms_forest10_area_lat_elev_asset_filename)
    '''

    print(get_sdm_area(sdms.first()).getInfo())
    sdm_area = ee.FeatureCollection(sdms.map(get_sdm_area))
    export_table_to_drive(sdm_area, sdm_area_drive_filename)
    export_table_to_asset(sdm_area.map(lambda f: f.setGeometry(ee.Geometry.Point([0,0]))), sdm_area_asset_filename)

    print(get_sdm_latitude_elevation(sdms.first()).getInfo())
    sdms_lat_elev = ee.FeatureCollection(sdms.map(get_sdm_latitude_elevation))
    export_table_to_drive(sdms_lat_elev, sdms_lat_elev_drive_filename) 
    export_table_to_asset(sdms_lat_elev.map(lambda f: f.setGeometry(ee.Geometry.Point([0,0]))), sdms_lat_elev_asset_filename)

    sdms_area_lat_elev = sdms.map(get_sdm_area_latitude_elevation)
    export_table_to_drive(sdms_area_lat_elev, sdms_area_lat_elev_drive_filename) 
    sdms_area_lat_elev_fc = sdms_area_lat_elev.map(lambda f: ee.Feature(f).setGeometry(ee.Geometry.Point([0,0])))
    export_table_to_asset(sdms_area_lat_elev_fc, sdms_area_lat_elev_asset_filename)