from nipype.interfaces.slicer.generate_classes import generate_all_classes


if __name__ == "__main__":
    ## NOTE:  For now either the launcher needs to be found on the default path, or
    ##        every tool in the modules list must be found on the default path
    ##        AND calling the module with --xml must be supported and compliant.
    modules_list = ['edu.jhu.bme.smile.demo.RandomVol',
                    'de.mpg.cbs.jist.laminar.JistLaminarProfileCalculator',
                     'de.mpg.cbs.jist.laminar.JistLaminarProfileSampling',
                     'de.mpg.cbs.jist.laminar.JistLaminarROIAveraging',
                     #'de.mpg.cbs.jist.laminar.JistLaminarVolumetricLayering',
                     'de.mpg.cbs.jist.laminar.JistLaminarProfileGeometry',
                     #'de.mpg.cbs.jist.brain.JistBrainMgdmSegmentation',
                     'de.mpg.cbs.jist.brain.JistBrainMp2rageSkullStripping',
                     'de.mpg.cbs.jist.brain.JistBrainPartialVolumeFilter',
                     'de.mpg.cbs.jist.brain.JistBrainMp2rageDuraEstimation',
                     'de.mpg.cbs.jist.tools.JistToolsExtractBrainRegion',
                     'de.mpg.cbs.jist.tools.JistToolsIntensityBounds',
                     #'de.mpg.cbs.jist.tools.JistToolsSegmentationStatistics', Insufficient XML specification: each element of type 'file', 'directory', 'image', 'geometry', 'transform',  or 'table' requires 'channel' field.{'desc': u'Spreadsheet file directory', 'argstr': u'--inSpreadsheet %s'}
                     'de.mpg.cbs.jist.tools.JistToolsCopyHeader',
                     #'de.mpg.cbs.jist.tools.JistToolsMultiCropToROI', not well formed XML
                     'de.mpg.cbs.jist.tools.JistToolsRelabelSegmentation',
                     #'de.mpg.cbs.jist.tools.JistToolsAdjustSegmentation',
                     'de.mpg.cbs.jist.tools.JistToolsLevelsetToMesh',
                     'de.mpg.cbs.jist.tools.JistToolsMeshToLevelset',
                     'de.mpg.cbs.jist.tools.JistToolsIntensityNormalization',
                     'de.mpg.cbs.jist.tools.JistToolsImageCombinations',
                     #'de.mpg.cbs.jist.tools.JistToolsComposeTransMatrices', not well formed XML
                     #'de.mpg.cbs.jist.modules.JistModuleMp2rageCortexSegmentation2',
                     'de.mpg.cbs.jist.modules.JistModuleCorticalProfileSampling',
                     #'de.mpg.cbs.jist.modules.JistModuleContinuousCorticalLayeringIterative',
                     #'de.mpg.cbs.jist.modules.JistModuleMp2rageCortexSegmentation',
                     'de.mpg.cbs.jist.modules.JistModuleRelabelSegmentation',
                     'de.mpg.cbs.jist.modules.JistModuleAggregativeSliceClustering',
                     #'de.mpg.cbs.jist.modules.JistModuleMgdmMultiSegmentation',
                     'de.mpg.cbs.jist.modules.JistModuleCorticalProfileFeatures',
                     'de.mpg.cbs.jist.modules.JistModuleCorticalProfileMeshSampling',
                     'de.mpg.cbs.jist.modules.JistModuleIntensityBounds',
                     'de.mpg.cbs.jist.modules.JistModuleCorticalMeshMapping',
                     'de.mpg.cbs.jist.modules.JistModuleNormalizeToRegisteredTemplate',
                     'de.mpg.cbs.jist.modules.JistModuleCorticalProfileCalculator',
                     'de.mpg.cbs.jist.modules.JistModuleCorticalProfileMesh',
                     'de.mpg.cbs.jist.modules.JistModuleMp2rageSimulator',
                     'de.mpg.cbs.jist.modules.JistModuleEmbeddedSyN',
                     'de.mpg.cbs.jist.modules.JistModuleTubularVolumeFilter',
                     #'de.mpg.cbs.jist.modules.JistModuleSmoothCRUISE',
                     #'de.mpg.cbs.jist.modules.JistModuleCorticalLayering',
                     #'de.mpg.cbs.jist.modules.JistModuleCorticalRegionGrowing',
                     #'de.mpg.cbs.jist.modules.JistModuleLevelsetAveraging',
                     #'de.mpg.cbs.jist.modules.JistModuleContinuousCorticalLayering',
                     'de.mpg.cbs.jist.modules.JistModuleNormalizeIntensityTemplate',
                     'de.mpg.cbs.jist.modules.JistModuleSmoothCorticalData2',
                     'de.mpg.cbs.jist.modules.JistModuleAnatomicallyConsistentEnhance',
                     'de.mpg.cbs.jist.modules.JistModuleT2sSlabCombination',
                     #'de.mpg.cbs.jist.modules.JistModuleComposeTransMatrices', not well formed
                     'de.mpg.cbs.jist.modules.JistModuleLevelsetToMesh',
                     'de.mpg.cbs.jist.modules.JistModuleBackgroundEstimator',
                     #'de.mpg.cbs.jist.modules.JistModuleLevelsetAppearancePCA', not well formed
                     'de.mpg.cbs.jist.modules.JistModuleFastClusteringND',
                     #'de.mpg.cbs.jist.modules.JistModuleVolumeStatistics', directory without a channel 
                     #'de.mpg.cbs.jist.modules.JistModuleRefineSegmentation',
                     #'de.mpg.cbs.jist.modules.JistModuleBatchImageCalculator', XML not well formed
                     #'de.mpg.cbs.jist.modules.JistModuleMultiscaleSurfaceRegistration',
                     #'de.mpg.cbs.jist.modules.MiriamsContinuousCorticalLayering',
                     'de.mpg.cbs.jist.modules.JistModuleCorticalProfileStatistics',
                     #'de.mpg.cbs.jist.modules.JistModuleCorticalProfileSurfaces',
                     'de.mpg.cbs.jist.modules.JistModuleSimpleSliceLabelsClustering',
                     #'de.mpg.cbs.jist.modules.JistModuleTwoBandProfileAveraging', directory without a channel
                     'de.mpg.cbs.jist.modules.JistModuleAssignMGDMSliceLabels',
                     #'de.mpg.cbs.jist.modules.JistModuleCorticalProfileSegmentation',
                     #'de.mpg.cbs.jist.modules.JistModuleLevelsetPCASegmentation', XML not well formed
                     #'de.mpg.cbs.jist.modules.JistModulePrimaryAreaClassification',
                     #'de.mpg.cbs.jist.modules.JistModuleCopyData', XML not well formed
                     #'de.mpg.cbs.jist.modules.JistModuleCorticalInflation', 
                     'de.mpg.cbs.jist.modules.JistModuleExtractBrainRegion',
                     'de.mpg.cbs.jist.modules.JistModuleAtlasBasedSimulator',
                     'de.mpg.cbs.jist.modules.JistModuleProbabilityToLevelset',
                     #'de.mpg.cbs.jist.modules.JistModuleROISimilarity',
                     'de.mpg.cbs.jist.modules.JistModuleROIMembership',
                     'de.mpg.cbs.jist.modules.JistModuleRenameImage',
                     'de.mpg.cbs.jist.modules.JistModuleMapProfileSampling2T1map',
                     #'de.mpg.cbs.jist.modules.JistModuleFmriCorticalSmoothing',
                     'de.mpg.cbs.jist.modules.JistModuleHeatKernelCorticalSmoothing',
                     'de.mpg.cbs.jist.modules.JistModuleMp2rageSkullStripping',
                     #'de.mpg.cbs.jist.modules.JistModuleContinuousCorticalLayeringForProfiles',
                     'de.mpg.cbs.jist.modules.JistModuleNormalizeComplexImage',
                     'de.mpg.cbs.jist.modules.JistModuleFastMatrixClustering',
                     'de.mpg.cbs.jist.modules.JistModuleSmoothCorticalData',
                     'de.mpg.cbs.jist.modules.JistModuleROIAveragingProfile',
                     #'de.mpg.cbs.jist.modules.JistModuleMipavFullReorient', XML not well formed
                     #'de.mpg.cbs.jist.modules.JistModuleRescaleVolume', XML not well formed
                     'de.mpg.cbs.jist.modules.JistModuleT2Fitting',
                     'de.mpg.cbs.jist.modules.JistModuleExtractMultiObjectData',
                     'de.mpg.cbs.jist.modules.JistModuleFrangiVesselness',
                     'de.mpg.cbs.jist.modules.JistModulePVCSFandArteriesFilter',
                     'de.mpg.cbs.jist.modules.JistModuleMp2rageArteriesFilter',
                     #'de.mpg.cbs.jist.modules.JistModuleFmriRegionSmoothing',
                     #'de.mpg.cbs.jist.modules.JistModuleMGDMRepresentation',
                     #'de.mpg.cbs.jist.modules.JistModuleLevelsetPCAApproximation', XML not well formed
                     #'de.mpg.cbs.jist.modules.JistModuleCorticalProfileGeometry3', XML not well formed
                     'de.mpg.cbs.jist.modules.JistModuleImageBoundary',
                     'de.mpg.cbs.jist.modules.JistModuleSmoothCorticalData4D',
                     'de.mpg.cbs.jist.modules.JistModuleCorticalProfileFeatureSetCalculator']
    
    modules_from_chris = ['edu.jhu.ece.iacl.plugins.segmentation.skull_strip.MedicAlgorithmSPECTRE2010',
                         #'edu.jhu.ece.iacl.plugins.registration.MedicAlgorithmFLIRT', XML not well formed
                         #'edu.jhu.ece.iacl.plugins.utilities.volume.MedicAlgorithmMipavReorient', # not well formed "<file collection: semi-colon delimited list>"
                         'edu.jhu.ece.iacl.plugins.utilities.math.MedicAlgorithmImageCalculator',
                         'de.mpg.cbs.jist.brain.JistBrainMp2rageDuraEstimation',
                         #'de.mpg.cbs.jist.modules.JistModuleFilterStacking', not found
                         'de.mpg.cbs.jist.brain.JistBrainPartialVolumeFilter',
                         #'de.mpg.cbs.jist.modules.JistModuleTubularVolumeFilter', # not found
                         #'de.mpg.cbs.jist.modules.JistModuleMgdmMultiSegmentation',
                         #'de.mpg.cbs.jist.tools.JistToolsIntensityNormalization', # not found
                         #'de.mpg.cbs.jist.modules.JistModuleCopyData', XML not well formed
                         #'de.mpg.cbs.jist.tools.JistToolsIntensityNormalization',
                         #'de.mpg.cbs.jist.tools.JistToolsExtractBrainRegion',
                         'edu.jhu.ece.iacl.plugins.utilities.volume.MedicAlgorithmThresholdToBinaryMask',# XML not well formed
                         #'de.mpg.cbs.jist.cortex.JistCortexFullCRUISE',
                         'de.mpg.cbs.jist.cortex.JistCortexSurfaceMeshInflation']
    
    modules_from_julia = ['de.mpg.cbs.jist.intensity.JistIntensityMp2rageMasking',
                          'edu.jhu.ece.iacl.plugins.segmentation.skull_strip.MedicAlgorithmSPECTRE2010']
    
    #modules_list = list(set(modules_list).union(set(modules_from_chris)))
    modules_list = modules_from_julia

    ## SlicerExecutionModel compliant tools that are usually statically built, and don't need the Slicer3 --launcher
    generate_all_classes(modules_list=modules_list,launcher=["java edu.jhu.ece.iacl.jist.cli.run" ], redirect_x = True)
    ## Tools compliant with SlicerExecutionModel called from the Slicer environment (for shared lib compatibility)
    #launcher = ['/home/raid3/gorgolewski/software/slicer/Slicer', '--launch']
    #generate_all_classes(modules_list=modules_list, launcher=launcher)
    #generate_all_classes(modules_list=['BRAINSABC'], launcher=[] )])
    ## Tools compliant with SlicerExecutionModel called from the Slicer environment (for shared lib compatibility)
    #launcher = ['/home/raid3/gorgolewski/software/slicer/Slicer', '--launch']
    #generate_all_classes(modules_list=modules_list, launcher=launcher)
    #generate_all_classes(modules_list=['BRAINSABC'], launcher=[] )