.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.segmentation.specialized
============================================


.. _nipype.interfaces.semtools.segmentation.specialized.BRAINSABC:


.. index:: BRAINSABC

BRAINSABC
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/segmentation/specialized.py#L340>`__

Wraps command ** BRAINSABC **

title: Intra-subject registration, bias Correction, and tissue classification (BRAINS)

category: Segmentation.Specialized

description: Atlas-based tissue segmentation method.  This is an algorithmic extension of work done by XXXX at UNC and Utah XXXX need more description here.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        atlasDefinition: (an existing file name)
                Contains all parameters for Atlas
                flag: --atlasDefinition %s
        atlasToSubjectInitialTransform: (a boolean or a file name)
                The initial transform from atlas to the subject
                flag: --atlasToSubjectInitialTransform %s
        atlasToSubjectTransform: (a boolean or a file name)
                The transform from atlas to the subject
                flag: --atlasToSubjectTransform %s
        atlasToSubjectTransformType: ('Identity' or 'Rigid' or 'Affine' or
                 'BSpline' or 'SyN')
                 What type of linear transform type do you want to use to register
                the atlas to the reference subject image.
                flag: --atlasToSubjectTransformType %s
        atlasWarpingOff: (a boolean)
                Deformable registration of atlas to subject
                flag: --atlasWarpingOff
        debuglevel: (an integer (int or long))
                Display debug messages, and produce debug intermediate results.
                0=OFF, 1=Minimal, 10=Maximum debugging.
                flag: --debuglevel %d
        defaultSuffix: (a string)
                flag: --defaultSuffix %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        filterIteration: (an integer (int or long))
                Filter iterations
                flag: --filterIteration %d
        filterMethod: ('None' or 'CurvatureFlow' or
                 'GradientAnisotropicDiffusion' or 'Median')
                Filter method for preprocessing of registration
                flag: --filterMethod %s
        filterTimeStep: (a float)
                Filter time step should be less than (PixelSpacing/(1^(DIM+1)),
                value is set to negative, then allow automatic setting of this
                value.
                flag: --filterTimeStep %f
        gridSize: (a list of items which are an integer (int or long))
                Grid size for atlas warping with BSplines
                flag: --gridSize %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        implicitOutputs: (a boolean or a list of items which are a file name)
                Outputs to be made available to NiPype. Needed because not all
                BRAINSABC outputs have command line arguments.
                flag: --implicitOutputs %s...
        inputVolumeTypes: (a list of items which are a string)
                The list of input image types corresponding to the inputVolumes.
                flag: --inputVolumeTypes %s
        inputVolumes: (a list of items which are an existing file name)
                The list of input image files to be segmented.
                flag: --inputVolumes %s...
        interpolationMode: ('BSpline' or 'NearestNeighbor' or 'WindowedSinc'
                 or 'Linear' or 'ResampleInPlace' or 'Hamming' or 'Cosine' or
                 'Welch' or 'Lanczos' or 'Blackman')
                Type of interpolation to be used when applying transform to moving
                volume. Options are Linear, NearestNeighbor, BSpline, WindowedSinc,
                or ResampleInPlace. The ResampleInPlace option will create an image
                with the same discrete voxel values and will adjust the origin and
                direction of the physical space interpretation.
                flag: --interpolationMode %s
        maxBiasDegree: (an integer (int or long))
                Maximum bias degree
                flag: --maxBiasDegree %d
        maxIterations: (an integer (int or long))
                Filter iterations
                flag: --maxIterations %d
        medianFilterSize: (a list of items which are an integer (int or
                 long))
                The radius for the optional MedianImageFilter preprocessing in all 3
                directions.
                flag: --medianFilterSize %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputDir: (a boolean or a directory name)
                Ouput directory
                flag: --outputDir %s
        outputDirtyLabels: (a boolean or a file name)
                Output Dirty Label Image
                flag: --outputDirtyLabels %s
        outputFormat: ('NIFTI' or 'Meta' or 'Nrrd')
                Output format
                flag: --outputFormat %s
        outputLabels: (a boolean or a file name)
                Output Label Image
                flag: --outputLabels %s
        outputVolumes: (a boolean or a list of items which are a file name)
                Corrected Output Images: should specify the same number of images as
                inputVolume, if only one element is given, then it is used as a file
                pattern where %s is replaced by the imageVolumeType, and %d by the
                index list location.
                flag: --outputVolumes %s...
        posteriorTemplate: (a string)
                filename template for Posterior output files
                flag: --posteriorTemplate %s
        restoreState: (an existing file name)
                The initial state for the registration process
                flag: --restoreState %s
        saveState: (a boolean or a file name)
                (optional) Filename to which save the final state of the
                registration
                flag: --saveState %s
        subjectIntermodeTransformType: ('Identity' or 'Rigid' or 'Affine' or
                 'BSpline')
                 What type of linear transform type do you want to use to register
                the atlas to the reference subject image.
                flag: --subjectIntermodeTransformType %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        useKNN: (a boolean)
                Use the KNN stage of estimating posteriors.
                flag: --useKNN
        writeLess: (a boolean)
                Does not write posteriors and filtered, bias corrected images
                flag: --writeLess

Outputs::

        atlasToSubjectInitialTransform: (an existing file name)
                The initial transform from atlas to the subject
        atlasToSubjectTransform: (an existing file name)
                The transform from atlas to the subject
        implicitOutputs: (a list of items which are an existing file name)
                Outputs to be made available to NiPype. Needed because not all
                BRAINSABC outputs have command line arguments.
        outputDir: (an existing directory name)
                Ouput directory
        outputDirtyLabels: (an existing file name)
                Output Dirty Label Image
        outputLabels: (an existing file name)
                Output Label Image
        outputVolumes: (a list of items which are an existing file name)
                Corrected Output Images: should specify the same number of images as
                inputVolume, if only one element is given, then it is used as a file
                pattern where %s is replaced by the imageVolumeType, and %d by the
                index list location.
        saveState: (an existing file name)
                (optional) Filename to which save the final state of the
                registration

.. _nipype.interfaces.semtools.segmentation.specialized.BRAINSConstellationDetector:


.. index:: BRAINSConstellationDetector

BRAINSConstellationDetector
---------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/segmentation/specialized.py#L171>`__

Wraps command ** BRAINSConstellationDetector **

title: Brain Landmark Constellation Detector (BRAINS)

category: Segmentation.Specialized

description: This program will find the mid-sagittal plane, a constellation of landmarks in a volume, and create an AC/PC aligned data set with the AC point at the center of the voxel lattice (labeled at the origin of the image physical space.)  Part of this work is an extention of the algorithms originally described by Dr. Babak A. Ardekani, Alvin H. Bachman, Model-based automatic detection of the anterior and posterior commissures on MRI scans, NeuroImage, Volume 46, Issue 3, 1 July 2009, Pages 677-682, ISSN 1053-8119, DOI: 10.1016/j.neuroimage.2009.02.030.  (http://www.sciencedirect.com/science/article/B6WNP-4VRP25C-4/2/8207b962a38aa83c822c6379bc43fe4c)

version: 1.0

documentation-url: http://www.nitrc.org/projects/brainscdetector/

Inputs::

        [Mandatory]

        [Optional]
        BackgroundFillValue: (a string)
                Fill the background of image with specified short int value. Enter
                number or use BIGNEG for a large negative number.
                flag: --BackgroundFillValue %s
        LLSModel: (an existing file name)
                Linear least squares model filename in HD5 format
                flag: --LLSModel %s
        acLowerBound: (a float)
                , When generating a resampled output image, replace the image with
                the BackgroundFillValue everywhere below the plane This Far in
                physical units (millimeters) below (inferior to) the AC point (as
                found by the model.) The oversize default was chosen to have no
                effect. Based on visualizing a thousand masks in the IPIG study, we
                recommend a limit no smaller than 80.0 mm.,
                flag: --acLowerBound %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        atlasLandmarkWeights: (an existing file name)
                Weights associated with atlas landmarks to be used for BRAINSFit
                registration initialization,
                flag: --atlasLandmarkWeights %s
        atlasLandmarks: (an existing file name)
                Atlas landmarks to be used for BRAINSFit registration
                initialization,
                flag: --atlasLandmarks %s
        atlasVolume: (an existing file name)
                Atlas volume image to be used for BRAINSFit registration
                flag: --atlasVolume %s
        cutOutHeadInOutputVolume: (a boolean)
                , Flag to cut out just the head tissue when producing an
                (un)transformed clipped volume.,
                flag: --cutOutHeadInOutputVolume
        debug: (a boolean)
                , Show internal debugging information.,
                flag: --debug
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        forceACPoint: (a list of items which are a float)
                , Use this flag to manually specify the AC point from the original
                image on the command line.,
                flag: --forceACPoint %s
        forceHoughEyeDetectorReportFailure: (a boolean)
                , Flag indicates whether the Hough eye detector should report
                failure,
                flag: --forceHoughEyeDetectorReportFailure
        forcePCPoint: (a list of items which are a float)
                , Use this flag to manually specify the PC point from the original
                image on the command line.,
                flag: --forcePCPoint %s
        forceRPPoint: (a list of items which are a float)
                , Use this flag to manually specify the RP point from the original
                image on the command line.,
                flag: --forceRPPoint %s
        forceVN4Point: (a list of items which are a float)
                , Use this flag to manually specify the VN4 point from the original
                image on the command line.,
                flag: --forceVN4Point %s
        houghEyeDetectorMode: (an integer (int or long))
                , This flag controls the mode of Hough eye detector. By default,
                value of 1 is for T1W images, while the value of 0 is for T2W and PD
                images.,
                flag: --houghEyeDetectorMode %d
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputLandmarksEMSP: (an existing file name)
                , The filename for the new subject-specific landmark definition file
                in the same format produced by Slicer3 (in .fcsv) with the landmarks
                in the estimated MSP aligned space to be loaded. The detector will
                only process landmarks not enlisted on the file.,
                flag: --inputLandmarksEMSP %s
        inputTemplateModel: (an existing file name)
                User-specified template model.,
                flag: --inputTemplateModel %s
        inputVolume: (an existing file name)
                Input image in which to find ACPC points
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
                seconds), 3=best estimate (58 seconds), NOTE: -1= Prealigned so no
                estimate!.,
                flag: --mspQualityLevel %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        otsuPercentileThreshold: (a float)
                , This is a parameter to FindLargestForegroundFilledMask, which is
                employed when acLowerBound is set and an
                outputUntransformedClippedVolume is requested.,
                flag: --otsuPercentileThreshold %f
        outputLandmarksInACPCAlignedSpace: (a boolean or a file name)
                , The filename for the new subject-specific landmark definition file
                in the same format produced by Slicer3 (.fcsv) with the landmarks in
                the output image space (the detected RP, AC, PC, and VN4) in it to
                be written.,
                flag: --outputLandmarksInACPCAlignedSpace %s
        outputLandmarksInInputSpace: (a boolean or a file name)
                , The filename for the new subject-specific landmark definition file
                in the same format produced by Slicer3 (.fcsv) with the landmarks in
                the original image space (the detected RP, AC, PC, and VN4) in it to
                be written.,
                flag: --outputLandmarksInInputSpace %s
        outputMRML: (a boolean or a file name)
                , The filename for the new subject-specific scene definition file in
                the same format produced by Slicer3 (in .mrml format). Only the
                components that were specified by the user on command line would be
                generated. Compatible components include inputVolume, outputVolume,
                outputLandmarksInInputSpace, outputLandmarksInACPCAlignedSpace, and
                outputTransform.,
                flag: --outputMRML %s
        outputResampledVolume: (a boolean or a file name)
                ACPC-aligned output image in a resampled unifor space. Currently
                this is a 1mm, 256^3, Identity direction image.
                flag: --outputResampledVolume %s
        outputTransform: (a boolean or a file name)
                The filename for the original space to ACPC alignment to be written
                (in .h5 format).,
                flag: --outputTransform %s
        outputUntransformedClippedVolume: (a boolean or a file name)
                Output image in which to store neck-clipped input image, with the
                use of --acLowerBound and maybe --cutOutHeadInUntransformedVolume.
                flag: --outputUntransformedClippedVolume %s
        outputVerificationScript: (a boolean or a file name)
                , The filename for the Slicer3 script that verifies the aligned
                landmarks against the aligned image file. This will happen only in
                conjunction with saveOutputLandmarks and an outputVolume.,
                flag: --outputVerificationScript %s
        outputVolume: (a boolean or a file name)
                ACPC-aligned output image with the same voxels, but updated origin,
                and direction cosign so that the AC point would fall at the physical
                location (0.0,0.0,0.0), and the mid-sagital plane is the plane where
                physical L/R coordinate is 0.0.
                flag: --outputVolume %s
        rVN4: (a float)
                , Search radius for VN4 in unit of mm,
                flag: --rVN4 %f
        rac: (a float)
                , Search radius for AC in unit of mm,
                flag: --rac %f
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
                , The directory for the debuging images to be written.,
                flag: --resultsDir %s
        rmpj: (a float)
                , Search radius for MPJ in unit of mm,
                flag: --rmpj %f
        rpc: (a float)
                , Search radius for PC in unit of mm,
                flag: --rpc %f
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
        writeBranded2DImage: (a boolean or a file name)
                , The filename for the 2D .png branded midline debugging image. This
                will happen only in conjunction with requesting an outputVolume.,
                flag: --writeBranded2DImage %s
        writedebuggingImagesLevel: (an integer (int or long))
                , This flag controls if debugging images are produced. By default
                value of 0 is no images. Anything greater than zero will be
                increasing level of debugging images.,
                flag: --writedebuggingImagesLevel %d

Outputs::

        outputLandmarksInACPCAlignedSpace: (an existing file name)
                , The filename for the new subject-specific landmark definition file
                in the same format produced by Slicer3 (.fcsv) with the landmarks in
                the output image space (the detected RP, AC, PC, and VN4) in it to
                be written.,
        outputLandmarksInInputSpace: (an existing file name)
                , The filename for the new subject-specific landmark definition file
                in the same format produced by Slicer3 (.fcsv) with the landmarks in
                the original image space (the detected RP, AC, PC, and VN4) in it to
                be written.,
        outputMRML: (an existing file name)
                , The filename for the new subject-specific scene definition file in
                the same format produced by Slicer3 (in .mrml format). Only the
                components that were specified by the user on command line would be
                generated. Compatible components include inputVolume, outputVolume,
                outputLandmarksInInputSpace, outputLandmarksInACPCAlignedSpace, and
                outputTransform.,
        outputResampledVolume: (an existing file name)
                ACPC-aligned output image in a resampled unifor space. Currently
                this is a 1mm, 256^3, Identity direction image.
        outputTransform: (an existing file name)
                The filename for the original space to ACPC alignment to be written
                (in .h5 format).,
        outputUntransformedClippedVolume: (an existing file name)
                Output image in which to store neck-clipped input image, with the
                use of --acLowerBound and maybe --cutOutHeadInUntransformedVolume.
        outputVerificationScript: (an existing file name)
                , The filename for the Slicer3 script that verifies the aligned
                landmarks against the aligned image file. This will happen only in
                conjunction with saveOutputLandmarks and an outputVolume.,
        outputVolume: (an existing file name)
                ACPC-aligned output image with the same voxels, but updated origin,
                and direction cosign so that the AC point would fall at the physical
                location (0.0,0.0,0.0), and the mid-sagital plane is the plane where
                physical L/R coordinate is 0.0.
        resultsDir: (an existing directory name)
                , The directory for the debuging images to be written.,
        writeBranded2DImage: (an existing file name)
                , The filename for the 2D .png branded midline debugging image. This
                will happen only in conjunction with requesting an outputVolume.,

.. _nipype.interfaces.semtools.segmentation.specialized.BRAINSCreateLabelMapFromProbabilityMaps:


.. index:: BRAINSCreateLabelMapFromProbabilityMaps

BRAINSCreateLabelMapFromProbabilityMaps
---------------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/segmentation/specialized.py#L208>`__

Wraps command ** BRAINSCreateLabelMapFromProbabilityMaps **

title: Create Label Map From Probability Maps (BRAINS)

category: Segmentation.Specialized

description: Given A list of Probability Maps, generate a LabelMap.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        cleanLabelVolume: (a boolean or a file name)
                the foreground labels volume
                flag: --cleanLabelVolume %s
        dirtyLabelVolume: (a boolean or a file name)
                the labels prior to cleaning
                flag: --dirtyLabelVolume %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        foregroundPriors: (a list of items which are an integer (int or
                 long))
                A list: For each Prior Label, 1 if foreground, 0 if background
                flag: --foregroundPriors %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inclusionThreshold: (a float)
                tolerance for inclusion
                flag: --inclusionThreshold %f
        inputProbabilityVolume: (a list of items which are an existing file
                 name)
                The list of proobabilityimages.
                flag: --inputProbabilityVolume %s...
        nonAirRegionMask: (an existing file name)
                a mask representing the 'NonAirRegion' -- Just force pixels in this
                region to zero
                flag: --nonAirRegionMask %s
        priorLabelCodes: (a list of items which are an integer (int or long))
                A list of PriorLabelCode values used for coding the output label
                images
                flag: --priorLabelCodes %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        cleanLabelVolume: (an existing file name)
                the foreground labels volume
        dirtyLabelVolume: (an existing file name)
                the labels prior to cleaning

.. _nipype.interfaces.semtools.segmentation.specialized.BRAINSCut:


.. index:: BRAINSCut

BRAINSCut
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/segmentation/specialized.py#L33>`__

Wraps command ** BRAINSCut **

title: BRAINSCut (BRAINS)

category: Segmentation.Specialized

description: Automatic Segmentation using neural networks

version: 1.0

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Vince Magnotta, Hans Johnson, Greg Harris, Kent Williams, Eunyoung Regina Kim

Inputs::

        [Mandatory]

        [Optional]
        NoTrainingVectorShuffling: (a boolean)
                If this flag is on, there will be no shuffling.
                flag: --NoTrainingVectorShuffling
        applyModel: (a boolean)
                apply the neural net
                flag: --applyModel
        args: (a string)
                Additional parameters to the command
                flag: %s
        computeSSEOn: (a boolean)
                compute Sum of Square Error (SSE) along the trained model until the
                number of iteration given in the modelConfigurationFilename file
                flag: --computeSSEOn
        createVectors: (a boolean)
                create vectors for training neural net
                flag: --createVectors
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        generateProbability: (a boolean)
                Generate probability map
                flag: --generateProbability
        histogramEqualization: (a boolean)
                A Histogram Equalization process could be added to the
                creating/applying process from Subject To Atlas. Default is false,
                which genreate input vectors without Histogram Equalization.
                flag: --histogramEqualization
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        method: ('RandomForest' or 'ANN')
                flag: --method %s
        modelConfigurationFilename: (an existing file name)
                XML File defining BRAINSCut parameters
                flag: --modelConfigurationFilename %s
        modelFilename: (a string)
                 model file name given from user (not by xml configuration file)
                flag: --modelFilename %s
        multiStructureThreshold: (a boolean)
                multiStructureThreshold module to deal with overlaping area
                flag: --multiStructureThreshold
        netConfiguration: (an existing file name)
                XML File defining BRAINSCut parameters. OLD NAME. PLEASE USE
                modelConfigurationFilename instead.
                flag: --netConfiguration %s
        numberOfTrees: (an integer (int or long))
                 Random tree: number of trees. This is to be used when only one
                model with specified depth wish to be created.
                flag: --numberOfTrees %d
        randomTreeDepth: (an integer (int or long))
                 Random tree depth. This is to be used when only one model with
                specified depth wish to be created.
                flag: --randomTreeDepth %d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        trainModel: (a boolean)
                train the neural net
                flag: --trainModel
        trainModelStartIndex: (an integer (int or long))
                Starting iteration for training
                flag: --trainModelStartIndex %d
        validate: (a boolean)
                validate data set.Just need for the first time run ( This is for
                validation of xml file and not working yet )
                flag: --validate
        verbose: (an integer (int or long))
                print out some debugging information
                flag: --verbose %d

Outputs::

        None

.. _nipype.interfaces.semtools.segmentation.specialized.BRAINSMultiSTAPLE:


.. index:: BRAINSMultiSTAPLE

BRAINSMultiSTAPLE
-----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/segmentation/specialized.py#L276>`__

Wraps command ** BRAINSMultiSTAPLE **

title: Create best representative label map)

category: Segmentation.Specialized

description: given a list of label map images, create a representative/average label map.

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
        inputCompositeT1Volume: (an existing file name)
                Composite T1, all label maps transofrmed into the space for this
                image.
                flag: --inputCompositeT1Volume %s
        inputLabelVolume: (a list of items which are an existing file name)
                The list of proobabilityimages.
                flag: --inputLabelVolume %s...
        inputTransform: (a list of items which are an existing file name)
                transforms to apply to label volumes
                flag: --inputTransform %s...
        labelForUndecidedPixels: (an integer (int or long))
                Label for undecided pixels
                flag: --labelForUndecidedPixels %d
        outputConfusionMatrix: (a boolean or a file name)
                Confusion Matrix
                flag: --outputConfusionMatrix %s
        outputMultiSTAPLE: (a boolean or a file name)
                the MultiSTAPLE average of input label volumes
                flag: --outputMultiSTAPLE %s
        resampledVolumePrefix: (a string)
                if given, write out resampled volumes with this prefix
                flag: --resampledVolumePrefix %s
        skipResampling: (a boolean)
                Omit resampling images into reference space
                flag: --skipResampling
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputConfusionMatrix: (an existing file name)
                Confusion Matrix
        outputMultiSTAPLE: (an existing file name)
                the MultiSTAPLE average of input label volumes

.. _nipype.interfaces.semtools.segmentation.specialized.BRAINSROIAuto:


.. index:: BRAINSROIAuto

BRAINSROIAuto
-------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/segmentation/specialized.py#L76>`__

Wraps command ** BRAINSROIAuto **

title: Foreground masking (BRAINS)

category: Segmentation.Specialized

description: This program is used to create a mask over the most prominant forground region in an image.  This is accomplished via a combination of otsu thresholding and a closing operation.  More documentation is available here: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/ForegroundMasking.

version: 2.4.1

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Hans J. Johnson, hans-johnson -at- uiowa.edu, http://www.psychiatry.uiowa.edu

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
        cropOutput: (a boolean)
                The inputVolume cropped to the region of the ROI mask.
                flag: --cropOutput
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
        maskOutput: (a boolean)
                The inputVolume multiplied by the ROI mask.
                flag: --maskOutput
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        otsuPercentileThreshold: (a float)
                Parameter to the Otsu threshold algorithm.
                flag: --otsuPercentileThreshold %f
        outputROIMaskVolume: (a boolean or a file name)
                The ROI automatically found from the input image.
                flag: --outputROIMaskVolume %s
        outputVolume: (a boolean or a file name)
                The inputVolume with optional [maskOutput|cropOutput] to the region
                of the brain mask.
                flag: --outputVolume %s
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

        outputROIMaskVolume: (an existing file name)
                The ROI automatically found from the input image.
        outputVolume: (an existing file name)
                The inputVolume with optional [maskOutput|cropOutput] to the region
                of the brain mask.

.. _nipype.interfaces.semtools.segmentation.specialized.BinaryMaskEditorBasedOnLandmarks:


.. index:: BinaryMaskEditorBasedOnLandmarks

BinaryMaskEditorBasedOnLandmarks
--------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/segmentation/specialized.py#L241>`__

Wraps command ** BinaryMaskEditorBasedOnLandmarks **

title: BRAINS Binary Mask Editor Based On Landmarks(BRAINS)

category: Segmentation.Specialized

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
        inputBinaryVolume: (an existing file name)
                Input binary image in which to be edited
                flag: --inputBinaryVolume %s
        inputLandmarkNames: (a list of items which are a string)
                 A target input landmark name to be edited. This should be listed in
                the inputLandmakrFilename Given.
                flag: --inputLandmarkNames %s
        inputLandmarkNamesForObliquePlane: (a list of items which are a
                 string)
                 Three subset landmark names of inputLandmarksFilename for a oblique
                plane computation. The plane computed for binary volume editing.
                flag: --inputLandmarkNamesForObliquePlane %s
        inputLandmarksFilename: (an existing file name)
                 The filename for the landmark definition file in the same format
                produced by Slicer3 (.fcsv).
                flag: --inputLandmarksFilename %s
        outputBinaryVolume: (a boolean or a file name)
                Output binary image in which to be edited
                flag: --outputBinaryVolume %s
        setCutDirectionForLandmark: (a list of items which are a string)
                Setting the cutting out direction of the input binary image to the
                one of anterior, posterior, left, right, superior or posterior.
                (ENUMERATION: ANTERIOR, POSTERIOR, LEFT, RIGHT, SUPERIOR, POSTERIOR)
                flag: --setCutDirectionForLandmark %s
        setCutDirectionForObliquePlane: (a list of items which are a string)
                If this is true, the mask will be thresholded out to the direction
                of inferior, posterior, and/or left. Default behavrior is that
                cutting out to the direction of superior, anterior and/or right.
                flag: --setCutDirectionForObliquePlane %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputBinaryVolume: (an existing file name)
                Output binary image in which to be edited

.. _nipype.interfaces.semtools.segmentation.specialized.ESLR:


.. index:: ESLR

ESLR
----

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/segmentation/specialized.py#L374>`__

Wraps command ** ESLR **

title: Clean Contiguous Label Map (BRAINS)

category: Segmentation.Specialized

description: From a range of label map values, extract the largest contiguous region of those labels

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        closingSize: (an integer (int or long))
                The closing size for hole filling.
                flag: --closingSize %d
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        high: (an integer (int or long))
                The higher bound of the labels to be used.
                flag: --high %d
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                Input Label Volume
                flag: --inputVolume %s
        low: (an integer (int or long))
                The lower bound of the labels to be used.
                flag: --low %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        openingSize: (an integer (int or long))
                The opening size for hole filling.
                flag: --openingSize %d
        outputVolume: (a boolean or a file name)
                Output Label Volume
                flag: --outputVolume %s
        preserveOutside: (a boolean)
                For values outside the specified range, preserve those values.
                flag: --preserveOutside
        safetySize: (an integer (int or long))
                The safetySize size for the clipping region.
                flag: --safetySize %d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Output Label Volume
