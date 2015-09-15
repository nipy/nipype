.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.registration.specialized
============================================


.. _nipype.interfaces.semtools.registration.specialized.BRAINSDemonWarp:


.. index:: BRAINSDemonWarp

BRAINSDemonWarp
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/registration/specialized.py#L138>`__

Wraps command ** BRAINSDemonWarp **

title: Demon Registration (BRAINS)

category: Registration.Specialized

description: This program finds a deformation field to warp a moving image onto a fixed image.  The images must be of the same signal kind, and contain an image of the same kind of object.  This program uses the Thirion Demons warp software in ITK, the Insight Toolkit.  Additional information is available at: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/BRAINSDemonWarp.

version: 3.0.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/BRAINSDemonWarp

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Hans J. Johnson and Greg Harris.

acknowledgements: The development of this tool was supported by funding from grants NS050568 and NS40068 from the National Institute of Neurological Disorders and Stroke and grants MH31593, MH40856, from the National Institute of Mental Health.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        arrayOfPyramidLevelIterations: (a list of items which are an integer
                 (int or long))
                The number of iterations for each pyramid level
                flag: --arrayOfPyramidLevelIterations %s
        backgroundFillValue: (an integer (int or long))
                Replacement value to overwrite background when performing BOBF
                flag: --backgroundFillValue %d
        checkerboardPatternSubdivisions: (a list of items which are an
                 integer (int or long))
                Number of Checkerboard subdivisions in all 3 directions
                flag: --checkerboardPatternSubdivisions %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fixedBinaryVolume: (an existing file name)
                Mask filename for desired region of interest in the Fixed image.
                flag: --fixedBinaryVolume %s
        fixedVolume: (an existing file name)
                Required: input fixed (target) image
                flag: --fixedVolume %s
        gradient_type: ('0' or '1' or '2')
                Type of gradient used for computing the demons force (0 is
                symmetrized, 1 is fixed image, 2 is moving image)
                flag: --gradient_type %s
        gui: (a boolean)
                Display intermediate image volumes for debugging
                flag: --gui
        histogramMatch: (a boolean)
                Histogram Match the input images. This is suitable for images of the
                same modality that may have different absolute scales, but the same
                overall intensity profile.
                flag: --histogramMatch
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        initializeWithDisplacementField: (an existing file name)
                Initial deformation field vector image file name
                flag: --initializeWithDisplacementField %s
        initializeWithTransform: (an existing file name)
                Initial Transform filename
                flag: --initializeWithTransform %s
        inputPixelType: ('float' or 'short' or 'ushort' or 'int' or 'uchar')
                Input volumes will be typecast to this format:
                float|short|ushort|int|uchar
                flag: --inputPixelType %s
        interpolationMode: ('NearestNeighbor' or 'Linear' or
                 'ResampleInPlace' or 'BSpline' or 'WindowedSinc' or 'Hamming' or
                 'Cosine' or 'Welch' or 'Lanczos' or 'Blackman')
                Type of interpolation to be used when applying transform to moving
                volume. Options are Linear, ResampleInPlace, NearestNeighbor,
                BSpline, or WindowedSinc
                flag: --interpolationMode %s
        lowerThresholdForBOBF: (an integer (int or long))
                Lower threshold for performing BOBF
                flag: --lowerThresholdForBOBF %d
        maskProcessingMode: ('NOMASK' or 'ROIAUTO' or 'ROI' or 'BOBF')
                What mode to use for using the masks: NOMASK|ROIAUTO|ROI|BOBF. If
                ROIAUTO is choosen, then the mask is implicitly defined using a otsu
                forground and hole filling algorithm. Where the Region Of Interest
                mode uses the masks to define what parts of the image should be used
                for computing the deformation field. Brain Only Background Fill uses
                the masks to pre-process the input images by clipping and filling in
                the background with a predefined value.
                flag: --maskProcessingMode %s
        max_step_length: (a float)
                Maximum length of an update vector (0: no restriction)
                flag: --max_step_length %f
        medianFilterSize: (a list of items which are an integer (int or
                 long))
                Median filter radius in all 3 directions. When images have a lot of
                salt and pepper noise, this step can improve the registration.
                flag: --medianFilterSize %s
        minimumFixedPyramid: (a list of items which are an integer (int or
                 long))
                The shrink factor for the first level of the fixed image pyramid.
                (i.e. start at 1/16 scale, then 1/8, then 1/4, then 1/2, and finally
                full scale)
                flag: --minimumFixedPyramid %s
        minimumMovingPyramid: (a list of items which are an integer (int or
                 long))
                The shrink factor for the first level of the moving image pyramid.
                (i.e. start at 1/16 scale, then 1/8, then 1/4, then 1/2, and finally
                full scale)
                flag: --minimumMovingPyramid %s
        movingBinaryVolume: (an existing file name)
                Mask filename for desired region of interest in the Moving image.
                flag: --movingBinaryVolume %s
        movingVolume: (an existing file name)
                Required: input moving image
                flag: --movingVolume %s
        neighborhoodForBOBF: (a list of items which are an integer (int or
                 long))
                neighborhood in all 3 directions to be included when performing BOBF
                flag: --neighborhoodForBOBF %s
        numberOfBCHApproximationTerms: (an integer (int or long))
                Number of terms in the BCH expansion
                flag: --numberOfBCHApproximationTerms %d
        numberOfHistogramBins: (an integer (int or long))
                The number of histogram levels
                flag: --numberOfHistogramBins %d
        numberOfMatchPoints: (an integer (int or long))
                The number of match points for histrogramMatch
                flag: --numberOfMatchPoints %d
        numberOfPyramidLevels: (an integer (int or long))
                Number of image pyramid levels to use in the multi-resolution
                registration.
                flag: --numberOfPyramidLevels %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputCheckerboardVolume: (a boolean or a file name)
                Genete a checkerboard image volume between the fixedVolume and the
                deformed movingVolume.
                flag: --outputCheckerboardVolume %s
        outputDebug: (a boolean)
                Flag to write debugging images after each step.
                flag: --outputDebug
        outputDisplacementFieldPrefix: (a string)
                Displacement field filename prefix for writing separate x, y, and z
                component images
                flag: --outputDisplacementFieldPrefix %s
        outputDisplacementFieldVolume: (a boolean or a file name)
                Output deformation field vector image (will have the same physical
                space as the fixedVolume).
                flag: --outputDisplacementFieldVolume %s
        outputNormalized: (a boolean)
                Flag to warp and write the normalized images to output. In
                normalized images the image values are fit-scaled to be between 0
                and the maximum storage type value.
                flag: --outputNormalized
        outputPixelType: ('float' or 'short' or 'ushort' or 'int' or 'uchar')
                outputVolume will be typecast to this format:
                float|short|ushort|int|uchar
                flag: --outputPixelType %s
        outputVolume: (a boolean or a file name)
                Required: output resampled moving image (will have the same physical
                space as the fixedVolume).
                flag: --outputVolume %s
        promptUser: (a boolean)
                Prompt the user to hit enter each time an image is sent to the
                DebugImageViewer
                flag: --promptUser
        registrationFilterType: ('Demons' or 'FastSymmetricForces' or
                 'Diffeomorphic')
                Registration Filter Type: Demons|FastSymmetricForces|Diffeomorphic
                flag: --registrationFilterType %s
        seedForBOBF: (a list of items which are an integer (int or long))
                coordinates in all 3 directions for Seed when performing BOBF
                flag: --seedForBOBF %s
        smoothDisplacementFieldSigma: (a float)
                A gaussian smoothing value to be applied to the deformation feild at
                each iteration.
                flag: --smoothDisplacementFieldSigma %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        upFieldSmoothing: (a float)
                Smoothing sigma for the update field at each iteration
                flag: --upFieldSmoothing %f
        upperThresholdForBOBF: (an integer (int or long))
                Upper threshold for performing BOBF
                flag: --upperThresholdForBOBF %d
        use_vanilla_dem: (a boolean)
                Run vanilla demons algorithm
                flag: --use_vanilla_dem

Outputs::

        outputCheckerboardVolume: (an existing file name)
                Genete a checkerboard image volume between the fixedVolume and the
                deformed movingVolume.
        outputDisplacementFieldVolume: (an existing file name)
                Output deformation field vector image (will have the same physical
                space as the fixedVolume).
        outputVolume: (an existing file name)
                Required: output resampled moving image (will have the same physical
                space as the fixedVolume).

.. _nipype.interfaces.semtools.registration.specialized.BRAINSTransformFromFiducials:


.. index:: BRAINSTransformFromFiducials

BRAINSTransformFromFiducials
----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/registration/specialized.py#L179>`__

Wraps command ** BRAINSTransformFromFiducials **

title: Fiducial Registration (BRAINS)

category: Registration.Specialized

description: Computes a rigid, similarity or affine transform from a matched list of fiducials

version: 0.1.0.$Revision$

documentation-url: http://www.slicer.org/slicerWiki/index.php/Modules:TransformFromFiducials-Documentation-3.6

contributor: Casey B Goodlett

acknowledgements: This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149.

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
        fixedLandmarks: (a list of items which are a list of from 3 to 3
                 items which are a float)
                Ordered list of landmarks in the fixed image
                flag: --fixedLandmarks %s...
        fixedLandmarksFile: (an existing file name)
                An fcsv formatted file with a list of landmark points.
                flag: --fixedLandmarksFile %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        movingLandmarks: (a list of items which are a list of from 3 to 3
                 items which are a float)
                Ordered list of landmarks in the moving image
                flag: --movingLandmarks %s...
        movingLandmarksFile: (an existing file name)
                An fcsv formatted file with a list of landmark points.
                flag: --movingLandmarksFile %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        saveTransform: (a boolean or a file name)
                Save the transform that results from registration
                flag: --saveTransform %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformType: ('Translation' or 'Rigid' or 'Similarity')
                Type of transform to produce
                flag: --transformType %s

Outputs::

        saveTransform: (an existing file name)
                Save the transform that results from registration

.. _nipype.interfaces.semtools.registration.specialized.VBRAINSDemonWarp:


.. index:: VBRAINSDemonWarp

VBRAINSDemonWarp
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/registration/specialized.py#L60>`__

Wraps command ** VBRAINSDemonWarp **

title: Vector Demon Registration (BRAINS)

category: Registration.Specialized

description: This program finds a deformation field to warp a moving image onto a fixed image.  The images must be of the same signal kind, and contain an image of the same kind of object.  This program uses the Thirion Demons warp software in ITK, the Insight Toolkit.  Additional information is available at: http://www.nitrc.org/projects/brainsdemonwarp.

version: 3.0.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/BRAINSDemonWarp

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Hans J. Johnson and Greg Harris.

acknowledgements: The development of this tool was supported by funding from grants NS050568 and NS40068 from the National Institute of Neurological Disorders and Stroke and grants MH31593, MH40856, from the National Institute of Mental Health.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        arrayOfPyramidLevelIterations: (a list of items which are an integer
                 (int or long))
                The number of iterations for each pyramid level
                flag: --arrayOfPyramidLevelIterations %s
        backgroundFillValue: (an integer (int or long))
                Replacement value to overwrite background when performing BOBF
                flag: --backgroundFillValue %d
        checkerboardPatternSubdivisions: (a list of items which are an
                 integer (int or long))
                Number of Checkerboard subdivisions in all 3 directions
                flag: --checkerboardPatternSubdivisions %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fixedBinaryVolume: (an existing file name)
                Mask filename for desired region of interest in the Fixed image.
                flag: --fixedBinaryVolume %s
        fixedVolume: (a list of items which are an existing file name)
                Required: input fixed (target) image
                flag: --fixedVolume %s...
        gradient_type: ('0' or '1' or '2')
                Type of gradient used for computing the demons force (0 is
                symmetrized, 1 is fixed image, 2 is moving image)
                flag: --gradient_type %s
        gui: (a boolean)
                Display intermediate image volumes for debugging
                flag: --gui
        histogramMatch: (a boolean)
                Histogram Match the input images. This is suitable for images of the
                same modality that may have different absolute scales, but the same
                overall intensity profile.
                flag: --histogramMatch
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        initializeWithDisplacementField: (an existing file name)
                Initial deformation field vector image file name
                flag: --initializeWithDisplacementField %s
        initializeWithTransform: (an existing file name)
                Initial Transform filename
                flag: --initializeWithTransform %s
        inputPixelType: ('float' or 'short' or 'ushort' or 'int' or 'uchar')
                Input volumes will be typecast to this format:
                float|short|ushort|int|uchar
                flag: --inputPixelType %s
        interpolationMode: ('NearestNeighbor' or 'Linear' or
                 'ResampleInPlace' or 'BSpline' or 'WindowedSinc' or 'Hamming' or
                 'Cosine' or 'Welch' or 'Lanczos' or 'Blackman')
                Type of interpolation to be used when applying transform to moving
                volume. Options are Linear, ResampleInPlace, NearestNeighbor,
                BSpline, or WindowedSinc
                flag: --interpolationMode %s
        lowerThresholdForBOBF: (an integer (int or long))
                Lower threshold for performing BOBF
                flag: --lowerThresholdForBOBF %d
        makeBOBF: (a boolean)
                Flag to make Brain-Only Background-Filled versions of the input and
                target volumes.
                flag: --makeBOBF
        max_step_length: (a float)
                Maximum length of an update vector (0: no restriction)
                flag: --max_step_length %f
        medianFilterSize: (a list of items which are an integer (int or
                 long))
                Median filter radius in all 3 directions. When images have a lot of
                salt and pepper noise, this step can improve the registration.
                flag: --medianFilterSize %s
        minimumFixedPyramid: (a list of items which are an integer (int or
                 long))
                The shrink factor for the first level of the fixed image pyramid.
                (i.e. start at 1/16 scale, then 1/8, then 1/4, then 1/2, and finally
                full scale)
                flag: --minimumFixedPyramid %s
        minimumMovingPyramid: (a list of items which are an integer (int or
                 long))
                The shrink factor for the first level of the moving image pyramid.
                (i.e. start at 1/16 scale, then 1/8, then 1/4, then 1/2, and finally
                full scale)
                flag: --minimumMovingPyramid %s
        movingBinaryVolume: (an existing file name)
                Mask filename for desired region of interest in the Moving image.
                flag: --movingBinaryVolume %s
        movingVolume: (a list of items which are an existing file name)
                Required: input moving image
                flag: --movingVolume %s...
        neighborhoodForBOBF: (a list of items which are an integer (int or
                 long))
                neighborhood in all 3 directions to be included when performing BOBF
                flag: --neighborhoodForBOBF %s
        numberOfBCHApproximationTerms: (an integer (int or long))
                Number of terms in the BCH expansion
                flag: --numberOfBCHApproximationTerms %d
        numberOfHistogramBins: (an integer (int or long))
                The number of histogram levels
                flag: --numberOfHistogramBins %d
        numberOfMatchPoints: (an integer (int or long))
                The number of match points for histrogramMatch
                flag: --numberOfMatchPoints %d
        numberOfPyramidLevels: (an integer (int or long))
                Number of image pyramid levels to use in the multi-resolution
                registration.
                flag: --numberOfPyramidLevels %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputCheckerboardVolume: (a boolean or a file name)
                Genete a checkerboard image volume between the fixedVolume and the
                deformed movingVolume.
                flag: --outputCheckerboardVolume %s
        outputDebug: (a boolean)
                Flag to write debugging images after each step.
                flag: --outputDebug
        outputDisplacementFieldPrefix: (a string)
                Displacement field filename prefix for writing separate x, y, and z
                component images
                flag: --outputDisplacementFieldPrefix %s
        outputDisplacementFieldVolume: (a boolean or a file name)
                Output deformation field vector image (will have the same physical
                space as the fixedVolume).
                flag: --outputDisplacementFieldVolume %s
        outputNormalized: (a boolean)
                Flag to warp and write the normalized images to output. In
                normalized images the image values are fit-scaled to be between 0
                and the maximum storage type value.
                flag: --outputNormalized
        outputPixelType: ('float' or 'short' or 'ushort' or 'int' or 'uchar')
                outputVolume will be typecast to this format:
                float|short|ushort|int|uchar
                flag: --outputPixelType %s
        outputVolume: (a boolean or a file name)
                Required: output resampled moving image (will have the same physical
                space as the fixedVolume).
                flag: --outputVolume %s
        promptUser: (a boolean)
                Prompt the user to hit enter each time an image is sent to the
                DebugImageViewer
                flag: --promptUser
        registrationFilterType: ('Demons' or 'FastSymmetricForces' or
                 'Diffeomorphic' or 'LogDemons' or 'SymmetricLogDemons')
                Registration Filter Type: Demons|FastSymmetricForces|Diffeomorphic|L
                ogDemons|SymmetricLogDemons
                flag: --registrationFilterType %s
        seedForBOBF: (a list of items which are an integer (int or long))
                coordinates in all 3 directions for Seed when performing BOBF
                flag: --seedForBOBF %s
        smoothDisplacementFieldSigma: (a float)
                A gaussian smoothing value to be applied to the deformation feild at
                each iteration.
                flag: --smoothDisplacementFieldSigma %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        upFieldSmoothing: (a float)
                Smoothing sigma for the update field at each iteration
                flag: --upFieldSmoothing %f
        upperThresholdForBOBF: (an integer (int or long))
                Upper threshold for performing BOBF
                flag: --upperThresholdForBOBF %d
        use_vanilla_dem: (a boolean)
                Run vanilla demons algorithm
                flag: --use_vanilla_dem
        weightFactors: (a list of items which are a float)
                Weight fatctors for each input images
                flag: --weightFactors %s

Outputs::

        outputCheckerboardVolume: (an existing file name)
                Genete a checkerboard image volume between the fixedVolume and the
                deformed movingVolume.
        outputDisplacementFieldVolume: (an existing file name)
                Output deformation field vector image (will have the same physical
                space as the fixedVolume).
        outputVolume: (an existing file name)
                Required: output resampled moving image (will have the same physical
                space as the fixedVolume).
