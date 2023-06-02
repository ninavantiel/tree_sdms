from config_figures import *

if __name__ == '__main__':
    evopca_img = ee.ImageCollection([
        nmds_evopca_fc.reduceToImage(['Axis1'], ee.Reducer.first()),
        nmds_evopca_fc.reduceToImage(['Axis2'], ee.Reducer.first()),
        nmds_evopca_fc.reduceToImage(['Axis3'], ee.Reducer.first())
    ]).toBands()
    # export_image_to_drive(evopca_img, 'evopca_img')

    nmds_img = ee.ImageCollection([
        nmds_evopca_fc.reduceToImage(['MDS1'], ee.Reducer.first()),
        nmds_evopca_fc.reduceToImage(['MDS2'], ee.Reducer.first()),
        nmds_evopca_fc.reduceToImage(['MDS3'], ee.Reducer.first())
    ]).toBands()
    # export_image_to_drive(nmds_img, 'nmds_img')

    evopca_cluster = nmds_evopca_fc.cluster(ee.Clusterer.wekaCascadeKMeans().train(
        nmds_evopca_fc, ['Axis1', 'Axis2', 'Axis3']
    ), 'evopca_cluster').reduceToImage(['evopca_cluster'], ee.Reducer.first())
    export_image_to_drive(evopca_cluster, 'evopca_cluster')

    nmds_cluster = nmds_evopca_fc.cluster(ee.Clusterer.wekaCascadeKMeans().train(
        nmds_evopca_fc, ['MDS1', 'MDS2', 'MDS3']
    ), 'nmds_cluster').reduceToImage(['nmds_cluster'], ee.Reducer.first())
    export_image_to_drive(nmds_cluster, 'nmds_cluster')