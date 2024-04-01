import sys
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
from config_figures import *

# geometry
eu_countries = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", 
    "Czech Republic", "Denmark", "Estonia", "Finland", "France", 
    "Germany", "Greece", "Hungary", "Ireland", "Italy", 
    "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands", 
    "Poland", "Portugal", "Romania", "Slovakia", "Slovenia", 
    "Spain", "Sweden", 
    "Turkey", "U.K. of Great Britain and Northern Ireland", "Switzerland", "Norway", "Serbia",
    'Bosnia and Herzegovina', 'The former Yugoslav Republic of Macedonia', 'Albania', 'Montenegro'
]
geometry = FAO_countries.filter(ee.Filter.inList('ADM0_NAME',eu_countries)).union()

def get_area(mask_img, geometry=geometry, ):
    return ee.Image.pixelArea().updateMask(mask_img).reduceRegion(
       reducer = ee.Reducer.sum(), geometry = geometry, scale = scale_to_use, maxPixels = 1E13
    ).get('area')

def get_iou(mhs_img):
    sppName = mhs_img.getString('system:index')
    mhs_img = mhs_img.gte(0.5).selfMask().reproject(covariate_img.projection())
    baseimg = ee.Image(0).setDefaultProjection(covariate_img.projection())
    sdm = ee.Image(ee.Algorithms.If(
        sppName.equals('Betula_sp'), 
        sdms.filter(ee.Filter.inList('system:index',['Betula_pendula','Betula_pubescens'])).first(),
        sdms.filter(ee.Filter.eq('system:index', sppName)).first()
    )).select(['covariates_1981_2010'],['b1'])
    pred_img = baseimg.addBands(sdm).select('b1')
    overlap = ee.Image.pixelArea().updateMask(pred_img).updateMask(mhs_img)
    combined = pred_img.unmask(0).add(mhs_img.unmask(0)).selfMask()

    union = get_area(combined)  
    intersect = get_area(overlap)
    sdm_area = get_area(pred_img)
    mhs_area = get_area(mhs_img)
  
    IoU = ee.Number(intersect).divide(union)
    return ee.Feature(None, {'species': sppName, 'IoU': IoU, 'union': union, 'intersection': intersect, 'sdm_area': sdm_area, 'mhs_area': mhs_area})

if __name__ == '__main__':
    results = mhs_ic.map(get_iou)
    export_table_to_drive(results, 'SDM_MHS_IoU')
