import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from config_figures import *

def get_sdm_area_latitude_elevation(sdm):
    """Compute area covered and median latitude  and elevation of
    SDM 1981-2010 unconstrained and clipped to at least 10% tree cover and
    SDM 2071-2100 SSP 5.85 unconstrained """
    
    # get species name
    species = sdm.get('system:index')

    # create image collection with images for (i) 1981-2010 unconstrained, 
    # (ii) 1981-2010, >= 10% tree cover, (iii) 2071-2100 SSP 5.85 unconstrained
    sdm_ic = ee.ImageCollection([
        mask_sdm(sdm.select(['covariates_1981_2010'],['sdm'])).set({
            'climate': '1981_2010', 'min_tree_cover': 0
        }), 
        mask_sdm(sdm.select(['covariates_1981_2010'],['sdm']).multiply(forest10_image)).set({
            'climate': '1981_2010', 'min_tree_cover': 10
        }),
        mask_sdm(sdm.select(['covariates_2071_2100_ssp585'],['sdm'])).set({
            'climate': '2071_2100_ssp585', 'min_tree_cover': 0
        })
    ])

    # for each image get area covered by SDM, median latitude and elevation of SDM
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
    sdms_area_lat_elev = sdms.map(get_sdm_area_latitude_elevation).flatten()
    export_table_to_asset(sdms_area_lat_elev, sdms_area_lat_elev_filename, folder=sdms_area_lat_elev_folder)
    export_table_to_drive(sdms_area_lat_elev, sdms_area_lat_elev_filename) 


