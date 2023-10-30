from config_figures import *

def get_sdm_area_latitude_min_tree_cover(sdm):
    species = sdm.get('system:index')
    sdm = sdm.select('covariates_1981_2010')
    sdm_ic = ee.ImageCollection([
        mask_sdm(sdm).set('min_tree_cover', 0),
        mask_sdm(sdm.multiply(forest10_image)).set('min_tree_cover', 10)
    ])

    sdm_ic = sdm_ic.map(lambda img: img.set({
        'area': img.multiply(ee.Image.pixelArea()).reduceRegion(
            reducer = ee.Reducer.sum(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
	    ).get('covariates_1981_2010'),
        'latitude': img.multiply(ee.Image.pixelLonLat().select('latitude')).reduceRegion(
            reducer = ee.Reducer.median(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
        ).get('covariates_1981_2010')
    })).map(lambda img: img.set('latitude', ee.Algorithms.If(img.getNumber('area').eq(0), -999, img.getNumber('latitude'))))

    sdm_area = ee.Dictionary.fromLists(
        sdm_ic.aggregate_array('min_tree_cover').map(lambda x: ee.String('area_min_tree_cover_').cat(ee.Number(x).format())), 
        sdm_ic.aggregate_array('area')
    )
    sdm_latitude = ee.Dictionary.fromLists(
        sdm_ic.aggregate_array('min_tree_cover').map(lambda x: ee.String('latitude_min_tree_cover_').cat(ee.Number(x).format())), 
        sdm_ic.aggregate_array('latitude')
    )

    return ee.Feature(ee.Geometry.Point([0,0]), sdm_area.combine(sdm_latitude)).set('species', species)

def get_sdm_latitude_elevation_climate_change(sdm):
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
        mask_sdm(sdm.select(['covariates_1981_2010'],['sdm'])).set({'climate': '1981_2010', 'min_tree_cover': 0}),
        mask_sdm(sdm.select(['covariates_1981_2010'],['sdm']).multiply(forest10_image)).set({'climate': '1981_2010', 'min_tree_cover': 10}),
        mask_sdm(sdm.select(['covariates_2071_2100_ssp585'],['sdm'])).set({'climate': '2071_2100_ssp585', 'min_tree_cover': 0})
    ])

    sdm_ic = sdm_ic.map(lambda img: img.set({
        'area': img.multiply(ee.Image.pixelArea()).reduceRegion(
		    reducer = ee.Reducer.sum(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
	    ).get('sdm'),
        'median_lat': img.multiply(ee.Image.pixelLonLat().select('latitude')).reduceRegion(
            reducer = ee.Reducer.median(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
        ).get('sdm'),
        'median_elev': img.multiply(elevation).reduceRegion(
            reducer = ee.Reducer.median(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
        ).get('sdm')
    })).map(lambda img: img.set({
        'median_lat': ee.Algorithms.If(img.getNumber('area').eq(0), -999, img.getNumber('median_lat')),
        'median_elev': ee.Algorithms.If(img.getNumber('area').eq(0), -999, img.getNumber('median_elev')),
    }))

    return ee.FeatureCollection(sdm_ic.map(
        lambda img: ee.Feature(ee.Geometry.Point([0,0]), img.toDictionary(['area','climate','median_lat','median_elev','min_tree_cover'])).set('species', species)
    ))

if __name__ == '__main__':
    print(sdms.size().getInfo(), 'sdms in analysis')

    # print(get_sdm_area_latitude_min_tree_cover(sdms.first()).getInfo())
    # sdm_area_latitude = ee.FeatureCollection(sdms.map(get_sdm_area_latitude_min_tree_cover))
    ### export_table_to_drive(sdm_area_latitude, sdm_area_latitude_drive_filename)
    # export_table_to_asset(sdm_area_latitude, sdm_area_latitude_asset_filename)

    # print(get_sdm_latitude_elevation_climate_change(sdms.first()).getInfo())
    # sdms_lat_elev = ee.FeatureCollection(sdms.map(get_sdm_latitude_elevation_climate_change))
    # export_table_to_drive(sdms_lat_elev, sdms_lat_elev_drive_filename) 
    # export_table_to_asset(sdms_lat_elev.map(lambda f: f.setGeometry(ee.Geometry.Point([0,0]))), sdms_lat_elev_asset_filename)


    # SDMS area, latitude and elevation globally for climate 1981-2010 and 2071-2100 ssp 5.58 and restricted to min 10 and 20% tree cover for climate 1981-2010
    sdms_area_lat_elev = sdms.map(get_sdm_area_latitude_elevation).flatten()
    print(sdms_area_lat_elev.first().getInfo())
    export_table_to_asset(sdms_area_lat_elev, sdms_area_lat_elev_filename)

    # sdms_area_lat_elev = ee.FeatureCollection(earthengine_folder + sdms_area_lat_elev_asset)
    # print(sdms_area_lat_elev.first().getInfo())
    export_table_to_drive(sdms_area_lat_elev, sdms_area_lat_elev_filename) 


