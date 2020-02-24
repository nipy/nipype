# -*- coding: utf-8 -*-

if __name__ == "__main__":
    from nipype.interfaces.slicer.generate_classes import generate_all_classes

    # NOTE:  For now either the launcher needs to be found on the default path, or
    # every tool in the modules list must be found on the default path
    # AND calling the module with --xml must be supported and compliant.
    modules_list = [
        "edu.jhu.bme.smile.demo.RandomVol",
        "de.mpg.cbs.jist.laminar.JistLaminarProfileCalculator",
        "de.mpg.cbs.jist.laminar.JistLaminarProfileSampling",
        "de.mpg.cbs.jist.laminar.JistLaminarROIAveraging",
        "de.mpg.cbs.jist.laminar.JistLaminarVolumetricLayering",
        "de.mpg.cbs.jist.laminar.JistLaminarProfileGeometry",
        "de.mpg.cbs.jist.brain.JistBrainMgdmSegmentation",
        "de.mpg.cbs.jist.brain.JistBrainMp2rageSkullStripping",
        "de.mpg.cbs.jist.brain.JistBrainPartialVolumeFilter",
        "de.mpg.cbs.jist.brain.JistBrainMp2rageDuraEstimation",
    ]

    modules_from_chris = [
        "edu.jhu.ece.iacl.plugins.segmentation.skull_strip.MedicAlgorithmSPECTRE2010",
        "edu.jhu.ece.iacl.plugins.utilities.volume.MedicAlgorithmMipavReorient",
        "edu.jhu.ece.iacl.plugins.utilities.math.MedicAlgorithmImageCalculator",
        "de.mpg.cbs.jist.brain.JistBrainMp2rageDuraEstimation",
        "de.mpg.cbs.jist.brain.JistBrainPartialVolumeFilter",
        "edu.jhu.ece.iacl.plugins.utilities.volume.MedicAlgorithmThresholdToBinaryMask",
        # 'de.mpg.cbs.jist.cortex.JistCortexFullCRUISE', # waiting for http://www.nitrc.org/tracker/index.php?func=detail&aid=7236&group_id=228&atid=942 to be fixed
        "de.mpg.cbs.jist.cortex.JistCortexSurfaceMeshInflation",
    ]

    modules_from_julia = [
        "de.mpg.cbs.jist.intensity.JistIntensityMp2rageMasking",
        "edu.jhu.ece.iacl.plugins.segmentation.skull_strip.MedicAlgorithmSPECTRE2010",
    ]

    modules_from_leonie = [
        "edu.jhu.ece.iacl.plugins.classification.MedicAlgorithmLesionToads"
    ]

    modules_from_yasinyazici = [
        "edu.jhu.ece.iacl.plugins.classification.MedicAlgorithmN3"
    ]

    modules_list = list(
        set(modules_list)
        .union(modules_from_chris)
        .union(modules_from_leonie)
        .union(modules_from_julia)
        .union(modules_from_yasinyazici)
        .union(modules_list)
    )

    generate_all_classes(
        modules_list=modules_list,
        launcher=["java edu.jhu.ece.iacl.jist.cli.run"],
        redirect_x=True,
        mipav_hacks=True,
    )
