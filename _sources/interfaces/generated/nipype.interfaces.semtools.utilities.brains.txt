.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.utilities.brains
====================================


.. _nipype.interfaces.semtools.utilities.brains.BRAINSAlignMSP:


.. index:: BRAINSAlignMSP

BRAINSAlignMSP
--------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L482>`__

Wraps command ** BRAINSAlignMSP **

title: Align Mid Saggital Brain (BRAINS)

category: Utilities.BRAINS

description: Resample an image into ACPC alignement ACPCDetect

Inputs::

        [Mandatory]

        [Optional]
        BackgroundFillValue: (a string)
                Fill the background of image with specified short int value. Enter
                number or use BIGNEG for a large negative number.
                flag: --BackgroundFillValue %s
        OutputresampleMSP: (a boolean or a file name)
                , The image to be output.,
                flag: --OutputresampleMSP %s
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                , The Image to be resampled,
                flag: --inputVolume %s
        interpolationMode: ('NearestNeighbor' or 'Linear' or
                 'ResampleInPlace' or 'BSpline' or 'WindowedSinc' or 'Hamming' or
                 'Cosine' or 'Welch' or 'Lanczos' or 'Blackman')
                Type of interpolation to be used when applying transform to moving
                volume. Options are Linear, ResampleInPlace, NearestNeighbor,
                BSpline, or WindowedSinc
                flag: --interpolationMode %s
        mspQualityLevel: (an integer (int or long))
                , Flag cotrols how agressive the MSP is estimated. 0=quick estimate
                (9 seconds), 1=normal estimate (11 seconds), 2=great estimate (22
                seconds), 3=best estimate (58 seconds).,
                flag: --mspQualityLevel %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        rescaleIntensities: (a boolean)
                , Flag to turn on rescaling image intensities on input.,
                flag: --rescaleIntensities
        rescaleIntensitiesOutputRange: (a list of items which are an integer
                 (int or long))
                , This pair of integers gives the lower and upper bounds on the
                signal portion of the output image. Out-of-field voxels are taken
                from BackgroundFillValue.,
                flag: --rescaleIntensitiesOutputRange %s
        resultsDir: (a boolean or a directory name)
                , The directory for the results to be written.,
                flag: --resultsDir %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        trimRescaledIntensities: (a float)
                , Turn on clipping the rescaled image one-tailed on input. Units of
                standard deviations above the mean. Very large values are very
                permissive. Non-positive value turns clipping off. Defaults to
                removing 0.00001 of a normal tail above the mean.,
                flag: --trimRescaledIntensities %f
        verbose: (a boolean)
                , Show more verbose output,
                flag: --verbose
        writedebuggingImagesLevel: (an integer (int or long))
                , This flag controls if debugging images are produced. By default
                value of 0 is no images. Anything greater than zero will be
                increasing level of debugging images.,
                flag: --writedebuggingImagesLevel %d

Outputs::

        OutputresampleMSP: (an existing file name)
                , The image to be output.,
        resultsDir: (an existing directory name)
                , The directory for the results to be written.,

.. _nipype.interfaces.semtools.utilities.brains.BRAINSClipInferior:


.. index:: BRAINSClipInferior

BRAINSClipInferior
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L410>`__

Wraps command ** BRAINSClipInferior **

title: Clip Inferior of Center of Brain (BRAINS)

category: Utilities.BRAINS

description: This program will read the inputVolume as a short int image, write the BackgroundFillValue everywhere inferior to the lower bound, and write the resulting clipped short int image in the outputVolume.

version: 1.0

Inputs::

        [Mandatory]

        [Optional]
        BackgroundFillValue: (a string)
                Fill the background of image with specified short int value. Enter
                number or use BIGNEG for a large negative number.
                flag: --BackgroundFillValue %s
        acLowerBound: (a float)
                , When the input image to the output image, replace the image with
                the BackgroundFillValue everywhere below the plane This Far in
                physical units (millimeters) below (inferior to) the AC point
                (assumed to be the voxel field middle.) The oversize default was
                chosen to have no effect. Based on visualizing a thousand masks in
                the IPIG study, we recommend a limit no smaller than 80.0 mm.,
                flag: --acLowerBound %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                Input image to make a clipped short int copy from.
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Output image, a short int copy of the upper portion of the input
                image, filled with BackgroundFillValue.
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Output image, a short int copy of the upper portion of the input
                image, filled with BackgroundFillValue.

.. _nipype.interfaces.semtools.utilities.brains.BRAINSConstellationModeler:


.. index:: BRAINSConstellationModeler

BRAINSConstellationModeler
--------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L33>`__

Wraps command ** BRAINSConstellationModeler **

title: Generate Landmarks Model (BRAINS)

category: Utilities.BRAINS

description: Train up a model for BRAINSConstellationDetector

Inputs::

        [Mandatory]

        [Optional]
        BackgroundFillValue: (a string)
                Fill the background of image with specified short int value. Enter
                number or use BIGNEG for a large negative number.
                flag: --BackgroundFillValue %s
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputTrainingList: (an existing file name)
                , Setup file, giving all parameters for training up a template model
                for each landmark.,
                flag: --inputTrainingList %s
        mspQualityLevel: (an integer (int or long))
                , Flag cotrols how agressive the MSP is estimated. 0=quick estimate
                (9 seconds), 1=normal estimate (11 seconds), 2=great estimate (22
                seconds), 3=best estimate (58 seconds).,
                flag: --mspQualityLevel %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        optimizedLandmarksFilenameExtender: (a string)
                , If the trainingList is (indexFullPathName) and contains landmark
                data filenames [path]/[filename].fcsv , make the optimized landmarks
                filenames out of [path]/[filename](thisExtender) and the optimized
                version of the input trainingList out of
                (indexFullPathName)(thisExtender) , when you rewrite all the
                landmarks according to the saveOptimizedLandmarks flag.,
                flag: --optimizedLandmarksFilenameExtender %s
        outputModel: (a boolean or a file name)
                , The full filename of the output model file.,
                flag: --outputModel %s
        rescaleIntensities: (a boolean)
                , Flag to turn on rescaling image intensities on input.,
                flag: --rescaleIntensities
        rescaleIntensitiesOutputRange: (a list of items which are an integer
                 (int or long))
                , This pair of integers gives the lower and upper bounds on the
                signal portion of the output image. Out-of-field voxels are taken
                from BackgroundFillValue.,
                flag: --rescaleIntensitiesOutputRange %s
        resultsDir: (a boolean or a directory name)
                , The directory for the results to be written.,
                flag: --resultsDir %s
        saveOptimizedLandmarks: (a boolean)
                , Flag to make a new subject-specific landmark definition file in
                the same format produced by Slicer3 with the optimized landmark (the
                detected RP, AC, and PC) in it. Useful to tighten the variances in
                the ConstellationModeler.,
                flag: --saveOptimizedLandmarks
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        trimRescaledIntensities: (a float)
                , Turn on clipping the rescaled image one-tailed on input. Units of
                standard deviations above the mean. Very large values are very
                permissive. Non-positive value turns clipping off. Defaults to
                removing 0.00001 of a normal tail above the mean.,
                flag: --trimRescaledIntensities %f
        verbose: (a boolean)
                , Show more verbose output,
                flag: --verbose
        writedebuggingImagesLevel: (an integer (int or long))
                , This flag controls if debugging images are produced. By default
                value of 0 is no images. Anything greater than zero will be
                increasing level of debugging images.,
                flag: --writedebuggingImagesLevel %d

Outputs::

        outputModel: (an existing file name)
                , The full filename of the output model file.,
        resultsDir: (an existing directory name)
                , The directory for the results to be written.,

.. _nipype.interfaces.semtools.utilities.brains.BRAINSEyeDetector:


.. index:: BRAINSEyeDetector

BRAINSEyeDetector
-----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L280>`__

Wraps command ** BRAINSEyeDetector **

title: Eye Detector (BRAINS)

category: Utilities.BRAINS

version: 1.0

documentation-url: http://www.nitrc.org/projects/brainscdetector/

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        debugDir: (a string)
                A place for debug information
                flag: --debugDir %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                The input volume
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                The output volume
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                The output volume

.. _nipype.interfaces.semtools.utilities.brains.BRAINSInitializedControlPoints:


.. index:: BRAINSInitializedControlPoints

BRAINSInitializedControlPoints
------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L342>`__

Wraps command ** BRAINSInitializedControlPoints **

title: Initialized Control Points (BRAINS)

category: Utilities.BRAINS

description: Outputs bspline control points as landmarks

version: 0.1.0.$Revision: 916 $(alpha)

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Mark Scully

acknowledgements: This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.  Additional support for Mark Scully and Hans Johnson at the University of Iowa.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                Input Volume
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputLandmarksFile: (a string)
                Output filename
                flag: --outputLandmarksFile %s
        outputVolume: (a boolean or a file name)
                Output Volume
                flag: --outputVolume %s
        permuteOrder: (a list of items which are an integer (int or long))
                The permutation order for the images. The default is 0,1,2 (i.e. no
                permutation)
                flag: --permuteOrder %s
        splineGridSize: (a list of items which are an integer (int or long))
                The number of subdivisions of the BSpline Grid to be centered on the
                image space. Each dimension must have at least 3 subdivisions for
                the BSpline to be correctly computed.
                flag: --splineGridSize %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Output Volume

.. _nipype.interfaces.semtools.utilities.brains.BRAINSLandmarkInitializer:


.. index:: BRAINSLandmarkInitializer

BRAINSLandmarkInitializer
-------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L510>`__

Wraps command ** BRAINSLandmarkInitializer **

title: BRAINSLandmarkInitializer

category: Utilities.BRAINS

description: Create transformation file (*mat) from a pair of landmarks (*fcsv) files.

version: 1.0

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Eunyoung Regina Kim

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputFixedLandmarkFilename: (an existing file name)
                input fixed landmark. *.fcsv
                flag: --inputFixedLandmarkFilename %s
        inputMovingLandmarkFilename: (an existing file name)
                input moving landmark. *.fcsv
                flag: --inputMovingLandmarkFilename %s
        inputWeightFilename: (an existing file name)
                Input weight file name for landmarks. Higher weighted landmark will
                be considered more heavily. Weights are propotional, that is the
                magnitude of weights will be normalized by its minimum and maximum
                value.
                flag: --inputWeightFilename %s
        outputTransformFilename: (a boolean or a file name)
                output transform file name (ex: ./outputTransform.mat)
                flag: --outputTransformFilename %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputTransformFilename: (an existing file name)
                output transform file name (ex: ./outputTransform.mat)

.. _nipype.interfaces.semtools.utilities.brains.BRAINSLinearModelerEPCA:


.. index:: BRAINSLinearModelerEPCA

BRAINSLinearModelerEPCA
-----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L308>`__

Wraps command ** BRAINSLinearModelerEPCA **

title: Landmark Linear Modeler (BRAINS)

category: Utilities.BRAINS

description: Training linear model using EPCA. Implementation based on my MS thesis, "A METHOD FOR AUTOMATED LANDMARK CONSTELLATION DETECTION USING EVOLUTIONARY PRINCIPAL COMPONENTS AND STATISTICAL SHAPE MODELS"

version: 1.0

documentation-url: http://www.nitrc.org/projects/brainscdetector/

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputTrainingList: (an existing file name)
                Input Training Landmark List Filename,
                flag: --inputTrainingList %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        None

.. _nipype.interfaces.semtools.utilities.brains.BRAINSLmkTransform:


.. index:: BRAINSLmkTransform

BRAINSLmkTransform
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L129>`__

Wraps command ** BRAINSLmkTransform **

title: Landmark Transform (BRAINS)

category: Utilities.BRAINS

description: This utility program estimates the affine transform to align the fixed landmarks to the moving landmarks, and then generate the resampled moving image to the same physical space as that of the reference image.

version: 1.0

documentation-url: http://www.nitrc.org/projects/brainscdetector/

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputFixedLandmarks: (an existing file name)
                Input Fixed Landmark list file in fcsv,
                flag: --inputFixedLandmarks %s
        inputMovingLandmarks: (an existing file name)
                Input Moving Landmark list file in fcsv,
                flag: --inputMovingLandmarks %s
        inputMovingVolume: (an existing file name)
                The filename of input moving volume
                flag: --inputMovingVolume %s
        inputReferenceVolume: (an existing file name)
                The filename of the reference volume
                flag: --inputReferenceVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputAffineTransform: (a boolean or a file name)
                The filename for the estimated affine transform,
                flag: --outputAffineTransform %s
        outputResampledVolume: (a boolean or a file name)
                The filename of the output resampled volume
                flag: --outputResampledVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputAffineTransform: (an existing file name)
                The filename for the estimated affine transform,
        outputResampledVolume: (an existing file name)
                The filename of the output resampled volume

.. _nipype.interfaces.semtools.utilities.brains.BRAINSMush:


.. index:: BRAINSMush

BRAINSMush
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L175>`__

Wraps command ** BRAINSMush **

title: Brain Extraction from T1/T2 image (BRAINS)

category: Utilities.BRAINS

description: This program: 1) generates a weighted mixture image optimizing the mean and variance and 2) produces a mask of the brain volume

version: 0.1.0.$Revision: 1.4 $(alpha)

documentation-url: http:://mri.radiology.uiowa.edu

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool is a modification by Steven Dunn of a program developed by Greg Harris and Ron Pierson.

acknowledgements: This work was developed by the University of Iowa Departments of Radiology and Psychiatry. This software was supported in part of NIH/NINDS award NS050568.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        boundingBoxSize: (a list of items which are an integer (int or long))
                Size of the cubic bounding box mask used when no brain mask is
                present
                flag: --boundingBoxSize %s
        boundingBoxStart: (a list of items which are an integer (int or
                 long))
                XYZ point-coordinate for the start of the cubic bounding box mask
                used when no brain mask is present
                flag: --boundingBoxStart %s
        desiredMean: (a float)
                Desired mean within the mask for weighted sum of both images.
                flag: --desiredMean %f
        desiredVariance: (a float)
                Desired variance within the mask for weighted sum of both images.
                flag: --desiredVariance %f
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputFirstVolume: (an existing file name)
                Input image (1) for mixture optimization
                flag: --inputFirstVolume %s
        inputMaskVolume: (an existing file name)
                Input label image for mixture optimization
                flag: --inputMaskVolume %s
        inputSecondVolume: (an existing file name)
                Input image (2) for mixture optimization
                flag: --inputSecondVolume %s
        lowerThresholdFactor: (a float)
                Lower threshold factor for defining the brain mask
                flag: --lowerThresholdFactor %f
        lowerThresholdFactorPre: (a float)
                Lower threshold factor for finding an initial brain mask
                flag: --lowerThresholdFactorPre %f
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputMask: (a boolean or a file name)
                The brain volume mask generated from the MUSH image
                flag: --outputMask %s
        outputVolume: (a boolean or a file name)
                The MUSH image produced from the T1 and T2 weighted images
                flag: --outputVolume %s
        outputWeightsFile: (a boolean or a file name)
                Output Weights File
                flag: --outputWeightsFile %s
        seed: (a list of items which are an integer (int or long))
                Seed Point for Brain Region Filling
                flag: --seed %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        upperThresholdFactor: (a float)
                Upper threshold factor for defining the brain mask
                flag: --upperThresholdFactor %f
        upperThresholdFactorPre: (a float)
                Upper threshold factor for finding an initial brain mask
                flag: --upperThresholdFactorPre %f

Outputs::

        outputMask: (an existing file name)
                The brain volume mask generated from the MUSH image
        outputVolume: (an existing file name)
                The MUSH image produced from the T1 and T2 weighted images
        outputWeightsFile: (an existing file name)
                Output Weights File

.. _nipype.interfaces.semtools.utilities.brains.BRAINSSnapShotWriter:


.. index:: BRAINSSnapShotWriter

BRAINSSnapShotWriter
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L575>`__

Wraps command ** BRAINSSnapShotWriter **

title: BRAINSSnapShotWriter

category: Utilities.BRAINS

description: Create 2D snapshot of input images. Mask images are color-coded

version: 1.0

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Eunyoung Regina Kim

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputBinaryVolumes: (a list of items which are an existing file name)
                Input mask (binary) volume list to be extracted as 2D image.
                Multiple input is possible.
                flag: --inputBinaryVolumes %s...
        inputPlaneDirection: (a list of items which are an integer (int or
                 long))
                Plane to display. In general, 0=saggital, 1=coronal, and 2=axial
                plane.
                flag: --inputPlaneDirection %s
        inputSliceToExtractInIndex: (a list of items which are an integer
                 (int or long))
                2D slice number of input images. For size of 256*256*256 image, 128
                is usually used.
                flag: --inputSliceToExtractInIndex %s
        inputSliceToExtractInPercent: (a list of items which are an integer
                 (int or long))
                2D slice number of input images. Percentage input from 0%-100%. (ex.
                --inputSliceToExtractInPercent 50,50,50
                flag: --inputSliceToExtractInPercent %s
        inputSliceToExtractInPhysicalPoint: (a list of items which are a
                 float)
                2D slice number of input images. For autoWorkUp output, which AC-PC
                aligned, 0,0,0 will be the center.
                flag: --inputSliceToExtractInPhysicalPoint %s
        inputVolumes: (a list of items which are an existing file name)
                Input image volume list to be extracted as 2D image. Multiple input
                is possible. At least one input is required.
                flag: --inputVolumes %s...
        outputFilename: (a boolean or a file name)
                2D file name of input images. Required.
                flag: --outputFilename %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputFilename: (an existing file name)
                2D file name of input images. Required.

.. _nipype.interfaces.semtools.utilities.brains.BRAINSTransformConvert:


.. index:: BRAINSTransformConvert

BRAINSTransformConvert
----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L216>`__

Wraps command ** BRAINSTransformConvert **

title: BRAINS Transform Convert

category: Utilities.BRAINS

description: Convert ITK transforms to higher order transforms

version: 1.0

documentation-url: A utility to convert between transform file formats.

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Hans J. Johnson,Kent Williams, Ali Ghayoor

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        displacementVolume: (a boolean or a file name)
                flag: --displacementVolume %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputTransform: (an existing file name)
                flag: --inputTransform %s
        outputPrecisionType: ('double' or 'float')
                Precision type of the output transform. It can be either single
                precision or double precision
                flag: --outputPrecisionType %s
        outputTransform: (a boolean or a file name)
                flag: --outputTransform %s
        outputTransformType: ('Affine' or 'VersorRigid' or 'ScaleVersor' or
                 'ScaleSkewVersor' or 'DisplacementField' or 'Same')
                The target transformation type. Must be conversion-compatible with
                the input transform type
                flag: --outputTransformType %s
        referenceVolume: (an existing file name)
                flag: --referenceVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        displacementVolume: (an existing file name)
        outputTransform: (an existing file name)

.. _nipype.interfaces.semtools.utilities.brains.BRAINSTrimForegroundInDirection:


.. index:: BRAINSTrimForegroundInDirection

BRAINSTrimForegroundInDirection
-------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L93>`__

Wraps command ** BRAINSTrimForegroundInDirection **

title: Trim Foreground In Direction (BRAINS)

category: Utilities.BRAINS

description: This program will trim off the neck and also air-filling noise from the inputImage.

version: 0.1

documentation-url: http://www.nitrc.org/projects/art/

Inputs::

        [Mandatory]

        [Optional]
        BackgroundFillValue: (a string)
                Fill the background of image with specified short int value. Enter
                number or use BIGNEG for a large negative number.
                flag: --BackgroundFillValue %s
        args: (a string)
                Additional parameters to the command
                flag: %s
        closingSize: (an integer (int or long))
                , This is a parameter to FindLargestForegroundFilledMask,
                flag: --closingSize %d
        directionCode: (an integer (int or long))
                , This flag chooses which dimension to compare. The sign lets you
                flip direction.,
                flag: --directionCode %d
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        headSizeLimit: (a float)
                , Use this to vary from the command line our search for how much
                upper tissue is head for the center-of-mass calculation. Units are
                CCs, not cubic millimeters.,
                flag: --headSizeLimit %f
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                Input image to trim off the neck (and also air-filling noise.)
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        otsuPercentileThreshold: (a float)
                , This is a parameter to FindLargestForegroundFilledMask, which is
                employed to trim off air-filling noise.,
                flag: --otsuPercentileThreshold %f
        outputVolume: (a boolean or a file name)
                Output image with neck and air-filling noise trimmed isotropic image
                with AC at center of image.
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Output image with neck and air-filling noise trimmed isotropic image
                with AC at center of image.

.. _nipype.interfaces.semtools.utilities.brains.CleanUpOverlapLabels:


.. index:: CleanUpOverlapLabels

CleanUpOverlapLabels
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L376>`__

Wraps command ** CleanUpOverlapLabels **

title: Clean Up Overla Labels

category: Utilities.BRAINS

description: Take a series of input binary images and clean up for those overlapped area. Binary volumes given first always wins out

version: 0.1.0

contributor: Eun Young Kim

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputBinaryVolumes: (a list of items which are an existing file name)
                The list of binary images to be checked and cleaned up. Order is
                important. Binary volume given first always wins out.
                flag: --inputBinaryVolumes %s...
        outputBinaryVolumes: (a boolean or a list of items which are a file
                 name)
                The output label map images, with integer values in it. Each label
                value specified in the inputLabels is combined into this output
                label map volume
                flag: --outputBinaryVolumes %s...
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputBinaryVolumes: (a list of items which are an existing file
                 name)
                The output label map images, with integer values in it. Each label
                value specified in the inputLabels is combined into this output
                label map volume

.. _nipype.interfaces.semtools.utilities.brains.FindCenterOfBrain:


.. index:: FindCenterOfBrain

FindCenterOfBrain
-----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L761>`__

Wraps command ** FindCenterOfBrain **

title: Center Of Brain (BRAINS)

category: Utilities.BRAINS

description: Finds the center point of a brain

version: 3.0.0

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Hans J. Johnson, hans-johnson -at- uiowa.edu, http://wwww.psychiatry.uiowa.edu

acknowledgements: Hans Johnson(1,3,4); Kent Williams(1);  (1=University of Iowa Department of Psychiatry, 3=University of Iowa Department of Biomedical Engineering, 4=University of Iowa Department of Electrical and Computer Engineering

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        axis: (an integer (int or long))
                flag: --axis %d
        backgroundValue: (an integer (int or long))
                flag: --backgroundValue %d
        clippedImageMask: (a boolean or a file name)
                flag: --clippedImageMask %s
        closingSize: (an integer (int or long))
                flag: --closingSize %d
        debugAfterGridComputationsForegroundImage: (a boolean or a file name)
                flag: --debugAfterGridComputationsForegroundImage %s
        debugClippedImageMask: (a boolean or a file name)
                flag: --debugClippedImageMask %s
        debugDistanceImage: (a boolean or a file name)
                flag: --debugDistanceImage %s
        debugGridImage: (a boolean or a file name)
                flag: --debugGridImage %s
        debugTrimmedImage: (a boolean or a file name)
                flag: --debugTrimmedImage %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        generateDebugImages: (a boolean)
                flag: --generateDebugImages
        headSizeEstimate: (a float)
                flag: --headSizeEstimate %f
        headSizeLimit: (a float)
                flag: --headSizeLimit %f
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        imageMask: (an existing file name)
                flag: --imageMask %s
        inputVolume: (an existing file name)
                The image in which to find the center.
                flag: --inputVolume %s
        maximize: (a boolean)
                flag: --maximize
        otsuPercentileThreshold: (a float)
                flag: --otsuPercentileThreshold %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        clippedImageMask: (an existing file name)
        debugAfterGridComputationsForegroundImage: (an existing file name)
        debugClippedImageMask: (an existing file name)
        debugDistanceImage: (an existing file name)
        debugGridImage: (an existing file name)
        debugTrimmedImage: (an existing file name)

.. _nipype.interfaces.semtools.utilities.brains.GenerateLabelMapFromProbabilityMap:


.. index:: GenerateLabelMapFromProbabilityMap

GenerateLabelMapFromProbabilityMap
----------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L439>`__

Wraps command ** GenerateLabelMapFromProbabilityMap **

title: Label Map from Probability Images

category: Utilities.BRAINS

description: Given a list of probability maps for labels, create a discrete label map where only the highest probability region is used for the labeling.

version: 0.1

contributor: University of Iowa Department of Psychiatry, http:://www.psychiatry.uiowa.edu

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolumes: (a list of items which are an existing file name)
                The Input probaiblity images to be computed for lable maps
                flag: --inputVolumes %s...
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputLabelVolume: (a boolean or a file name)
                The Input binary image for region of interest
                flag: --outputLabelVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputLabelVolume: (an existing file name)
                The Input binary image for region of interest

.. _nipype.interfaces.semtools.utilities.brains.ImageRegionPlotter:


.. index:: ImageRegionPlotter

ImageRegionPlotter
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L681>`__

Wraps command ** ImageRegionPlotter **

title: Write Out Image Intensities

category: Utilities.BRAINS

description: For Analysis

version: 0.1

contributor: University of Iowa Department of Psychiatry, http:://www.psychiatry.uiowa.edu

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputBinaryROIVolume: (an existing file name)
                The Input binary image for region of interest
                flag: --inputBinaryROIVolume %s
        inputLabelVolume: (an existing file name)
                The Label Image
                flag: --inputLabelVolume %s
        inputVolume1: (an existing file name)
                The Input image to be computed for statistics
                flag: --inputVolume1 %s
        inputVolume2: (an existing file name)
                The Input image to be computed for statistics
                flag: --inputVolume2 %s
        numberOfHistogramBins: (an integer (int or long))
                 the number of histogram levels
                flag: --numberOfHistogramBins %d
        outputJointHistogramData: (a string)
                 output data file name
                flag: --outputJointHistogramData %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        useIntensityForHistogram: (a boolean)
                 Create Intensity Joint Histogram instead of Quantile Joint
                Histogram
                flag: --useIntensityForHistogram
        useROIAUTO: (a boolean)
                 Use ROIAUTO to compute region of interest. This cannot be used with
                inputLabelVolume
                flag: --useROIAUTO
        verbose: (a boolean)
                 print debugging information,
                flag: --verbose

Outputs::

        None

.. _nipype.interfaces.semtools.utilities.brains.JointHistogram:


.. index:: JointHistogram

JointHistogram
--------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L611>`__

Wraps command ** JointHistogram **

title: Write Out Image Intensities

category: Utilities.BRAINS

description: For Analysis

version: 0.1

contributor: University of Iowa Department of Psychiatry, http:://www.psychiatry.uiowa.edu

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputMaskVolumeInXAxis: (an existing file name)
                Input mask volume for inputVolumeInXAxis. Histogram will be computed
                just for the masked region
                flag: --inputMaskVolumeInXAxis %s
        inputMaskVolumeInYAxis: (an existing file name)
                Input mask volume for inputVolumeInYAxis. Histogram will be computed
                just for the masked region
                flag: --inputMaskVolumeInYAxis %s
        inputVolumeInXAxis: (an existing file name)
                The Input image to be computed for statistics
                flag: --inputVolumeInXAxis %s
        inputVolumeInYAxis: (an existing file name)
                The Input image to be computed for statistics
                flag: --inputVolumeInYAxis %s
        outputJointHistogramImage: (a string)
                 output joint histogram image file name. Histogram is usually 2D
                image.
                flag: --outputJointHistogramImage %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        verbose: (a boolean)
                 print debugging information,
                flag: --verbose

Outputs::

        None

.. _nipype.interfaces.semtools.utilities.brains.ShuffleVectorsModule:


.. index:: ShuffleVectorsModule

ShuffleVectorsModule
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L642>`__

Wraps command ** ShuffleVectorsModule **

title: ShuffleVectors

category: Utilities.BRAINS

description: Automatic Segmentation using neural networks

version: 1.0

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Hans Johnson

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVectorFileBaseName: (an existing file name)
                input vector file name prefix. Usually end with .txt and header file
                has prost fix of .txt.hdr
                flag: --inputVectorFileBaseName %s
        outputVectorFileBaseName: (a boolean or a file name)
                output vector file name prefix. Usually end with .txt and header
                file has prost fix of .txt.hdr
                flag: --outputVectorFileBaseName %s
        resampleProportion: (a float)
                downsample size of 1 will be the same size as the input images,
                downsample size of 3 will throw 2/3 the vectors away.
                flag: --resampleProportion %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVectorFileBaseName: (an existing file name)
                output vector file name prefix. Usually end with .txt and header
                file has prost fix of .txt.hdr

.. _nipype.interfaces.semtools.utilities.brains.fcsv_to_hdf5:


.. index:: fcsv_to_hdf5

fcsv_to_hdf5
------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L716>`__

Wraps command ** fcsv_to_hdf5 **

title: fcsv_to_hdf5 (BRAINS)

category: Utilities.BRAINS

description: Convert a collection of fcsv files to a HDF5 format file

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        landmarkGlobPattern: (a string)
                Glob pattern to select fcsv files
                flag: --landmarkGlobPattern %s
        landmarkTypesList: (an existing file name)
                , file containing list of landmark types,
                flag: --landmarkTypesList %s
        landmarksInformationFile: (a boolean or a file name)
                , name of HDF5 file to write matrices into,
                flag: --landmarksInformationFile %s
        modelFile: (a boolean or a file name)
                , name of HDF5 file containing BRAINSConstellationDetector Model
                file (LLSMatrices, LLSMeans and LLSSearchRadii),
                flag: --modelFile %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        versionID: (a string)
                , Current version ID. It should be match with the version of BCD
                that will be using the output model file,
                flag: --versionID %s

Outputs::

        landmarksInformationFile: (an existing file name)
                , name of HDF5 file to write matrices into,
        modelFile: (an existing file name)
                , name of HDF5 file containing BRAINSConstellationDetector Model
                file (LLSMatrices, LLSMeans and LLSSearchRadii),

.. _nipype.interfaces.semtools.utilities.brains.insertMidACPCpoint:


.. index:: insertMidACPCpoint

insertMidACPCpoint
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L542>`__

Wraps command ** insertMidACPCpoint **

title: MidACPC Landmark Insertion

category: Utilities.BRAINS

description: This program gets a landmark fcsv file and adds a new landmark as the midpoint between AC and PC points to the output landmark fcsv file

contributor: Ali Ghayoor

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputLandmarkFile: (an existing file name)
                Input landmark file (.fcsv)
                flag: --inputLandmarkFile %s
        outputLandmarkFile: (a boolean or a file name)
                Output landmark file (.fcsv)
                flag: --outputLandmarkFile %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputLandmarkFile: (an existing file name)
                Output landmark file (.fcsv)

.. _nipype.interfaces.semtools.utilities.brains.landmarksConstellationAligner:


.. index:: landmarksConstellationAligner

landmarksConstellationAligner
-----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L250>`__

Wraps command ** landmarksConstellationAligner **

title: MidACPC Landmark Insertion

category: Utilities.BRAINS

description: This program converts the original landmark files to the acpc-aligned landmark files

contributor: Ali Ghayoor

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputLandmarksPaired: (an existing file name)
                Input landmark file (.fcsv)
                flag: --inputLandmarksPaired %s
        outputLandmarksPaired: (a boolean or a file name)
                Output landmark file (.fcsv)
                flag: --outputLandmarksPaired %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputLandmarksPaired: (an existing file name)
                Output landmark file (.fcsv)

.. _nipype.interfaces.semtools.utilities.brains.landmarksConstellationWeights:


.. index:: landmarksConstellationWeights

landmarksConstellationWeights
-----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/utilities/brains.py#L61>`__

Wraps command ** landmarksConstellationWeights **

title: Generate Landmarks Weights (BRAINS)

category: Utilities.BRAINS

description: Train up a list of Weights for the Landmarks in BRAINSConstellationDetector

Inputs::

        [Mandatory]

        [Optional]
        LLSModel: (an existing file name)
                Linear least squares model filename in HD5 format
                flag: --LLSModel %s
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputTemplateModel: (an existing file name)
                User-specified template model.,
                flag: --inputTemplateModel %s
        inputTrainingList: (an existing file name)
                , Setup file, giving all parameters for training up a Weight list
                for landmark.,
                flag: --inputTrainingList %s
        outputWeightsList: (a boolean or a file name)
                , The filename of a csv file which is a list of landmarks and their
                corresponding weights.,
                flag: --outputWeightsList %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputWeightsList: (an existing file name)
                , The filename of a csv file which is a list of landmarks and their
                corresponding weights.,
