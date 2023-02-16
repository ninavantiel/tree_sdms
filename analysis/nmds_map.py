from config_figures import *

#https://code.earthengine.google.com/334be36959a05bb84af605895d7fd265


if __name__ == '__main__':
  nmds_rectangles = ee.FeatureCollection(earthengine_folder + 'nmds_fc_geos')
  img = ee.ImageCollection([
    nmds_rectangles.reduceToImage(['MDS1'], ee.Reducer.first()),
    nmds_rectangles.reduceToImage(['MDS2'], ee.Reducer.first()),
    nmds_rectangles.reduceToImage(['MDS3'], ee.Reducer.first())
  ]).toBands()

  export_image_to_drive(img, 'nmds_map')