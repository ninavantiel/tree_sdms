from config_figures import *

def get_sdm_area_medianlat(sdm):
    species = sdm.get('system:index')
    sdm_ic = ee.ImageCollection([
        mask_sdm(sdm.select(['covariates_1981_2010'],['sdm']).set('sdm', 'covariates_1981_2010')),
        mask_sdm(sdm.select(['covariates_2071_2100_ssp585'],['sdm']).set('sdm', 'covariates_2071_2100_ssp585'))
    ])
    sdm_ic = sdm_ic.map(lambda img: img.set(
        'area', img.multiply(ee.Image.pixelArea()).reduceRegion(
		    reducer = ee.Reducer.sum(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
	    ).get('sdm'),
        'medianlat', img.multiply(ee.Image.pixelLonLat().select('latitude')).reduceRegion(
            reducer = ee.Reducer.median(), geometry = unbounded_geo, maxPixels = 1e13, scale = scale_to_use
        ).get('sdm')
    )).map(lambda img: img.set('medianlat', ee.Algorithms.If(img.getNumber('area').eq(0), -999, img.getNumber('medianlat'))))

    sdm_area = ee.Dictionary.fromLists(sdm_ic.aggregate_array('sdm').map(lambda x: ee.String(x).replace('covariates', 'area')), sdm_ic.aggregate_array('area'))
    sdm_medianlat = ee.Dictionary.fromLists(sdm_ic.aggregate_array('sdm').map(lambda x: ee.String(x).replace('covariates', 'medianlat')), sdm_ic.aggregate_array('medianlat'))
    return ee.Feature(None, sdm_area.combine(sdm_medianlat)).set('species', species)


if __name__ == '__main__':
    print(sdms.size().getInfo(), 'sdms in analysis')

    sdms_area_medianlat = sdms.map(get_sdm_area_medianlat)
    export_table_to_drive(sdms_area_medianlat, sdms_area_medianlat_drive_filename) 

    sdms_area_medianlat_fc = sdms_area_medianlat.map(lambda f: ee.Feature(f).setGeometry(ee.Geometry.Point([0,0])))
    export_table_to_asset(sdms_area_medianlat_fc, sdms_area_medianlat_asset_filename)