"""Autogenerated file - DO NOT EDIT
If you spot a bug, please report it on the mailing list and/or change the generator."""

from nipype.interfaces.base import (
    CommandLineInputSpec,
    SEMLikeCommandLine,
    TraitedSpec,
    File,
    traits,
)


class IntensityDifferenceMetricInputSpec(CommandLineInputSpec):
    sensitivityThreshold = traits.Float(
        desc="This parameter should be between 0 and 1, and defines how sensitive the metric should be to the intensity changes.",
        argstr="--sensitivityThreshold %f",
    )
    changingBandSize = traits.Int(
        desc="How far (in mm) from the boundary of the segmentation should the intensity changes be considered.",
        argstr="--changingBandSize %d",
    )
    baselineVolume = File(
        position=-4, desc="Baseline volume to be compared to", exists=True, argstr="%s"
    )
    baselineSegmentationVolume = File(
        position=-3,
        desc="Label volume that contains segmentation of the structure of interest in the baseline volume.",
        exists=True,
        argstr="%s",
    )
    followupVolume = File(
        position=-2,
        desc="Followup volume to be compare to the baseline",
        exists=True,
        argstr="%s",
    )
    outputVolume = traits.Either(
        traits.Bool,
        File(),
        position=-1,
        hash_files=False,
        desc="Output volume to keep the results of change quantification.",
        argstr="%s",
    )
    reportFileName = traits.Either(
        traits.Bool,
        File(),
        hash_files=False,
        desc="Report file name",
        argstr="--reportFileName %s",
    )


class IntensityDifferenceMetricOutputSpec(TraitedSpec):
    outputVolume = File(
        position=-1,
        desc="Output volume to keep the results of change quantification.",
        exists=True,
    )
    reportFileName = File(desc="Report file name", exists=True)


class IntensityDifferenceMetric(SEMLikeCommandLine):
    """title:
      Intensity Difference Change Detection (FAST)


    category:
      Quantification.ChangeQuantification


    description:
      Quantifies the changes between two spatially aligned images based on the pixel-wise difference of image intensities.


    version: 0.1

    contributor: Andrey Fedorov

    acknowledgements:

    """

    input_spec = IntensityDifferenceMetricInputSpec
    output_spec = IntensityDifferenceMetricOutputSpec
    _cmd = "IntensityDifferenceMetric "
    _outputs_filenames = {
        "outputVolume": "outputVolume.nii",
        "reportFileName": "reportFileName",
    }
