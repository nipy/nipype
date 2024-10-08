"""Autogenerated file - DO NOT EDIT
If you spot a bug, please report it on the mailing list and/or change the generator."""

from nipype.interfaces.base import (
    CommandLineInputSpec,
    SEMLikeCommandLine,
    TraitedSpec,
    File,
    traits,
    InputMultiPath,
)


class SimpleRegionGrowingSegmentationInputSpec(CommandLineInputSpec):
    smoothingIterations = traits.Int(
        desc="Number of smoothing iterations", argstr="--smoothingIterations %d"
    )
    timestep = traits.Float(desc="Timestep for curvature flow", argstr="--timestep %f")
    iterations = traits.Int(
        desc="Number of iterations of region growing", argstr="--iterations %d"
    )
    multiplier = traits.Float(
        desc="Number of standard deviations to include in intensity model",
        argstr="--multiplier %f",
    )
    neighborhood = traits.Int(
        desc="The radius of the neighborhood over which to calculate intensity model",
        argstr="--neighborhood %d",
    )
    labelvalue = traits.Int(
        desc="The integer value (0-255) to use for the segmentation results. This will determine the color of the segmentation that will be generated by the Region growing algorithm",
        argstr="--labelvalue %d",
    )
    seed = InputMultiPath(
        traits.List(traits.Float(), minlen=3, maxlen=3),
        desc="Seed point(s) for region growing",
        argstr="--seed %s...",
    )
    inputVolume = File(
        position=-2, desc="Input volume to be filtered", exists=True, argstr="%s"
    )
    outputVolume = traits.Either(
        traits.Bool,
        File(),
        position=-1,
        hash_files=False,
        desc="Output filtered",
        argstr="%s",
    )


class SimpleRegionGrowingSegmentationOutputSpec(TraitedSpec):
    outputVolume = File(position=-1, desc="Output filtered", exists=True)


class SimpleRegionGrowingSegmentation(SEMLikeCommandLine):
    """title: Simple Region Growing Segmentation

    category: Segmentation

    description: A simple region growing segmentation algorithm based on intensity statistics. To create a list of fiducials (Seeds) for this algorithm, click on the tool bar icon of an arrow pointing to a starburst fiducial to enter the 'place a new object mode' and then use the fiducials module. This module uses the Slicer Command Line Interface (CLI) and the ITK filters CurvatureFlowImageFilter and ConfidenceConnectedImageFilter.

    version: 0.1.0.$Revision: 19904 $(alpha)

    documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/SimpleRegionGrowingSegmentation

    contributor: Jim Miller (GE)

    acknowledgements: This command module was derived from Insight/Examples (copyright) Insight Software Consortium
    """

    input_spec = SimpleRegionGrowingSegmentationInputSpec
    output_spec = SimpleRegionGrowingSegmentationOutputSpec
    _cmd = "SimpleRegionGrowingSegmentation "
    _outputs_filenames = {"outputVolume": "outputVolume.nii"}
