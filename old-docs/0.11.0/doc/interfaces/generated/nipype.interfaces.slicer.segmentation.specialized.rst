.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.slicer.segmentation.specialized
==========================================


.. _nipype.interfaces.slicer.segmentation.specialized.BRAINSROIAuto:


.. index:: BRAINSROIAuto

BRAINSROIAuto
-------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/slicer/segmentation/specialized.py#L122>`__

Wraps command **BRAINSROIAuto **

title: Foreground masking (BRAINS)

category: Segmentation.Specialized

description: This tool uses a combination of otsu thresholding and a closing operations to identify the most prominant foreground region in an image.


version: 2.4.1

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Hans J. Johnson, hans-johnson -at- uiowa.edu, http://wwww.psychiatry.uiowa.edu

acknowledgements: Hans Johnson(1,3,4); Kent Williams(1); Gregory Harris(1), Vincent Magnotta(1,2,3);  Andriy Fedorov(5), fedorov -at- bwh.harvard.edu (Slicer integration); (1=University of Iowa Department of Psychiatry, 2=University of Iowa Department of Radiology, 3=University of Iowa Department of Biomedical Engineering, 4=University of Iowa Department of Electrical and Computer Engineering, 5=Surgical Planning Lab, Harvard)

Inputs::

        [Mandatory]

        [Optional]
        ROIAutoDilateSize: (a float)
                This flag is only relavent when using ROIAUTO mode for initializing
                masks. It defines the final dilation size to capture a bit of
                background outside the tissue region. At setting of 10mm has been
                shown to help regularize a BSpline registration type so that there
                is some background constraints to match the edges of the head
                better.
                flag: --ROIAutoDilateSize %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        closingSize: (a float)
                The Closing Size (in millimeters) for largest connected filled mask.
                This value is divided by image spacing and rounded to the next
                largest voxel number.
                flag: --closingSize %f
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                The input image for finding the largest region filled mask.
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        otsuPercentileThreshold: (a float)
                Parameter to the Otsu threshold algorithm.
                flag: --otsuPercentileThreshold %f
        outputClippedVolumeROI: (a boolean or a file name)
                The inputVolume clipped to the region of the brain mask.
                flag: --outputClippedVolumeROI %s
        outputROIMaskVolume: (a boolean or a file name)
                The ROI automatically found from the input image.
                flag: --outputROIMaskVolume %s
        outputVolumePixelType: ('float' or 'short' or 'ushort' or 'int' or
                 'uint' or 'uchar')
                The output image Pixel Type is the scalar datatype for
                representation of the Output Volume.
                flag: --outputVolumePixelType %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        thresholdCorrectionFactor: (a float)
                A factor to scale the Otsu algorithm's result threshold, in case
                clipping mangles the image.
                flag: --thresholdCorrectionFactor %f

Outputs::

        outputClippedVolumeROI: (an existing file name)
                The inputVolume clipped to the region of the brain mask.
        outputROIMaskVolume: (an existing file name)
                The ROI automatically found from the input image.

.. _nipype.interfaces.slicer.segmentation.specialized.EMSegmentCommandLine:


.. index:: EMSegmentCommandLine

EMSegmentCommandLine
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/slicer/segmentation/specialized.py#L77>`__

Wraps command **EMSegmentCommandLine **

title:
  EMSegment Command-line


category:
  Segmentation.Specialized


description:
  This module is used to simplify the process of segmenting large collections of images by providing a command line interface to the EMSegment algorithm for script and batch processing.


documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/4.0/EMSegment_Command-line

contributor: Sebastien Barre, Brad Davis, Kilian Pohl, Polina Golland, Yumin Yuan, Daniel Haehn

acknowledgements: Many people and organizations have contributed to the funding, design, and development of the EMSegment algorithm and its various implementations.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        atlasVolumeFileNames: (a list of items which are an existing file
                 name)
                Use an alternative atlas to the one that is specified by the mrml
                file - note the order matters !
                flag: --atlasVolumeFileNames %s...
        disableCompression: (a boolean)
                Don't use compression when writing result image to disk.
                flag: --disableCompression
        disableMultithreading: (an integer (int or long))
                Disable multithreading for the EMSegmenter algorithm only!
                Preprocessing might still run in multi-threaded mode. -1: Do not
                overwrite default value. 0: Disable. 1: Enable.
                flag: --disableMultithreading %d
        dontUpdateIntermediateData: (an integer (int or long))
                Disable update of intermediate results. -1: Do not overwrite default
                value. 0: Disable. 1: Enable.
                flag: --dontUpdateIntermediateData %d
        dontWriteResults: (a boolean)
                Used for testing. Don't actually write the resulting labelmap to
                disk.
                flag: --dontWriteResults
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        generateEmptyMRMLSceneAndQuit: (a boolean or a file name)
                Used for testing. Only write a scene with default mrml parameters.
                flag: --generateEmptyMRMLSceneAndQuit %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        intermediateResultsDirectory: (an existing directory name)
                Directory where EMSegmenter will write intermediate data (e.g.,
                aligned atlas data).
                flag: --intermediateResultsDirectory %s
        keepTempFiles: (a boolean)
                If flag is set then at the end of command the temporary files are
                not removed
                flag: --keepTempFiles
        loadAtlasNonCentered: (a boolean)
                Read atlas files non-centered.
                flag: --loadAtlasNonCentered
        loadTargetCentered: (a boolean)
                Read target files centered.
                flag: --loadTargetCentered
        mrmlSceneFileName: (an existing file name)
                Active MRML scene that contains EMSegment algorithm parameters.
                flag: --mrmlSceneFileName %s
        parametersMRMLNodeName: (a string)
                The name of the EMSegment parameters node within the active MRML
                scene. Leave blank for default.
                flag: --parametersMRMLNodeName %s
        registrationAffineType: (an integer (int or long))
                specify the accuracy of the affine registration. -2: Do not
                overwrite default, -1: Test, 0: Disable, 1: Fast, 2: Accurate
                flag: --registrationAffineType %d
        registrationDeformableType: (an integer (int or long))
                specify the accuracy of the deformable registration. -2: Do not
                overwrite default, -1: Test, 0: Disable, 1: Fast, 2: Accurate
                flag: --registrationDeformableType %d
        registrationPackage: (a string)
                specify the registration package for preprocessing (CMTK or BRAINS
                or PLASTIMATCH or DEMONS)
                flag: --registrationPackage %s
        resultMRMLSceneFileName: (a boolean or a file name)
                Write out the MRML scene after command line substitutions have been
                made.
                flag: --resultMRMLSceneFileName %s
        resultStandardVolumeFileName: (an existing file name)
                Used for testing. Compare segmentation results to this image and
                return EXIT_FAILURE if they do not match.
                flag: --resultStandardVolumeFileName %s
        resultVolumeFileName: (a boolean or a file name)
                The file name that the segmentation result volume will be written
                to.
                flag: --resultVolumeFileName %s
        targetVolumeFileNames: (a list of items which are an existing file
                 name)
                File names of target volumes (to be segmented). The number of target
                images must be equal to the number of target images specified in the
                parameter set, and these images must be spatially aligned.
                flag: --targetVolumeFileNames %s...
        taskPreProcessingSetting: (a string)
                Specifies the different task parameter. Leave blank for default.
                flag: --taskPreProcessingSetting %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        verbose: (a boolean)
                Enable verbose output.
                flag: --verbose

Outputs::

        generateEmptyMRMLSceneAndQuit: (an existing file name)
                Used for testing. Only write a scene with default mrml parameters.
        resultMRMLSceneFileName: (an existing file name)
                Write out the MRML scene after command line substitutions have been
                made.
        resultVolumeFileName: (an existing file name)
                The file name that the segmentation result volume will be written
                to.

.. _nipype.interfaces.slicer.segmentation.specialized.RobustStatisticsSegmenter:


.. index:: RobustStatisticsSegmenter

RobustStatisticsSegmenter
-------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/slicer/segmentation/specialized.py#L24>`__

Wraps command **RobustStatisticsSegmenter **

title: Robust Statistics Segmenter

category: Segmentation.Specialized

description: Active contour segmentation using robust statistic.

version: 1.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/RobustStatisticsSegmenter

contributor: Yi Gao (gatech), Allen Tannenbaum (gatech), Ron Kikinis (SPL, BWH)

acknowledgements: This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        curvatureWeight: (a float)
                Given sphere 1.0 score and extreme rough bounday/surface 0 score,
                what is the expected smoothness of the object?
                flag: --curvatureWeight %f
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        expectedVolume: (a float)
                The approximate volume of the object, in mL.
                flag: --expectedVolume %f
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        intensityHomogeneity: (a float)
                What is the homogeneity of intensity within the object? Given
                constant intensity at 1.0 score and extreme fluctuating intensity at
                0.
                flag: --intensityHomogeneity %f
        labelImageFileName: (an existing file name)
                Label image for initialization
                flag: %s, position: -2
        labelValue: (an integer (int or long))
                Label value of the output image
                flag: --labelValue %d
        maxRunningTime: (a float)
                The program will stop if this time is reached.
                flag: --maxRunningTime %f
        originalImageFileName: (an existing file name)
                Original image to be segmented
                flag: %s, position: -3
        segmentedImageFileName: (a boolean or a file name)
                Segmented image
                flag: %s, position: -1
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        segmentedImageFileName: (an existing file name)
                Segmented image
