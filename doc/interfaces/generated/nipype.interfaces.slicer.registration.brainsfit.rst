.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.slicer.registration.brainsfit
========================================


.. _nipype.interfaces.slicer.registration.brainsfit.BRAINSFit:


.. index:: BRAINSFit

BRAINSFit
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/slicer/registration/brainsfit.py#L83>`__

Wraps command **BRAINSFit **

title: General Registration (BRAINS)

category: Registration

description: Register a three-dimensional volume to a reference volume (Mattes Mutual Information by default). Described in BRAINSFit: Mutual Information Registrations of Whole-Brain 3D Images, Using the Insight Toolkit, Johnson H.J., Harris G., Williams K., The Insight Journal, 2007. http://hdl.handle.net/1926/1291

version: 3.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:BRAINSFit

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Hans J. Johnson, hans-johnson -at- uiowa.edu, http://wwww.psychiatry.uiowa.edu

acknowledgements: Hans Johnson(1,3,4); Kent Williams(1); Gregory Harris(1), Vincent Magnotta(1,2,3);  Andriy Fedorov(5) 1=University of Iowa Department of Psychiatry, 2=University of Iowa Department of Radiology, 3=University of Iowa Department of Biomedical Engineering, 4=University of Iowa Department of Electrical and Computer Engineering, 5=Surgical Planning Lab, Harvard

Inputs::

        [Mandatory]

        [Optional]
        NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_00: (a boolean)
                DO NOT USE THIS FLAG
                flag: --NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_00
        NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_01: (a boolean)
                DO NOT USE THIS FLAG
                flag: --NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_01
        NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_02: (a boolean)
                DO NOT USE THIS FLAG
                flag: --NEVER_USE_THIS_FLAG_IT_IS_OUTDATED_02
        ROIAutoClosingSize: (a float)
                This flag is only relavent when using ROIAUTO mode for initializing
                masks. It defines the hole closing size in mm. It is rounded up to
                the nearest whole pixel size in each direction. The default is to
                use a closing size of 9mm. For mouse data this value may need to be
                reset to 0.9 or smaller.
                flag: --ROIAutoClosingSize %f
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
        backgroundFillValue: (a float)
                Background fill value for output image.
                flag: --backgroundFillValue %f
        bsplineTransform: (a boolean or a file name)
                (optional) Filename to which save the estimated transform. NOTE: You
                must set at least one output object (either a deformed image or a
                transform. NOTE: USE THIS ONLY IF THE FINAL TRANSFORM IS BSpline
                flag: --bsplineTransform %s
        costFunctionConvergenceFactor: (a float)
                 From itkLBFGSBOptimizer.h: Set/Get the
                CostFunctionConvergenceFactor. Algorithm terminates when the
                reduction in cost function is less than (factor * epsmcj) where
                epsmch is the machine precision. Typical values for factor: 1e+12
                for low accuracy; 1e+7 for moderate accuracy and 1e+1 for extremely
                high accuracy. 1e+9 seems to work well.,
                flag: --costFunctionConvergenceFactor %f
        costMetric: ('MMI' or 'MSE' or 'NC' or 'MC')
                The cost metric to be used during fitting. Defaults to MMI. Options
                are MMI (Mattes Mutual Information), MSE (Mean Square Error), NC
                (Normalized Correlation), MC (Match Cardinality for binary images)
                flag: --costMetric %s
        debugLevel: (an integer (int or long))
                Display debug messages, and produce debug intermediate results.
                0=OFF, 1=Minimal, 10=Maximum debugging.
                flag: --debugLevel %d
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        failureExitCode: (an integer (int or long))
                If the fit fails, exit with this status code. (It can be used to
                force a successfult exit status of (0) if the registration fails due
                to reaching the maximum number of iterations.
                flag: --failureExitCode %d
        fixedBinaryVolume: (an existing file name)
                Fixed Image binary mask volume, ONLY FOR MANUAL ROI mode.
                flag: --fixedBinaryVolume %s
        fixedVolume: (an existing file name)
                The fixed image for registration by mutual information optimization.
                flag: --fixedVolume %s
        fixedVolumeTimeIndex: (an integer (int or long))
                The index in the time series for the 3D fixed image to fit, if
                4-dimensional.
                flag: --fixedVolumeTimeIndex %d
        forceMINumberOfThreads: (an integer (int or long))
                Force the the maximum number of threads to use for non thread safe
                MI metric. CAUTION: Inconsistent results my arise!
                flag: --forceMINumberOfThreads %d
        gui: (a boolean)
                Display intermediate image volumes for debugging. NOTE: This is not
                part of the standard build sytem, and probably does nothing on your
                installation.
                flag: --gui
        histogramMatch: (a boolean)
                Histogram Match the input images. This is suitable for images of the
                same modality that may have different absolute scales, but the same
                overall intensity profile. Do NOT use if registering images from
                different modailties.
                flag: --histogramMatch
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        initialTransform: (an existing file name)
                Filename of transform used to initialize the registration. This CAN
                NOT be used with either CenterOfHeadLAlign, MomentsAlign,
                GeometryAlign, or initialTransform file.
                flag: --initialTransform %s
        initializeTransformMode: ('Off' or 'useMomentsAlign' or
                 'useCenterOfHeadAlign' or 'useGeometryAlign' or
                 'useCenterOfROIAlign')
                Determine how to initialize the transform center. GeometryAlign on
                assumes that the center of the voxel lattice of the images represent
                similar structures. MomentsAlign assumes that the center of mass of
                the images represent similar structures. useCenterOfHeadAlign
                attempts to use the top of head and shape of neck to drive a center
                of mass estimate. Off assumes that the physical space of the images
                are close, and that centering in terms of the image Origins is a
                good starting point. This flag is mutually exclusive with the
                initialTransform flag.
                flag: --initializeTransformMode %s
        interpolationMode: ('NearestNeighbor' or 'Linear' or
                 'ResampleInPlace' or 'BSpline' or 'WindowedSinc' or 'Hamming' or
                 'Cosine' or 'Welch' or 'Lanczos' or 'Blackman')
                Type of interpolation to be used when applying transform to moving
                volume. Options are Linear, NearestNeighbor, BSpline, WindowedSinc,
                or ResampleInPlace. The ResampleInPlace option will create an image
                with the same discrete voxel values and will adjust the origin and
                direction of the physical space interpretation.
                flag: --interpolationMode %s
        linearTransform: (a boolean or a file name)
                (optional) Filename to which save the estimated transform. NOTE: You
                must set at least one output object (either a deformed image or a
                transform. NOTE: USE THIS ONLY IF THE FINAL TRANSFORM IS ---NOT---
                BSpline
                flag: --linearTransform %s
        maskInferiorCutOffFromCenter: (a float)
                For use with --useCenterOfHeadAlign (and --maskProcessingMode
                ROIAUTO): the cut-off below the image centers, in millimeters,
                flag: --maskInferiorCutOffFromCenter %f
        maskProcessingMode: ('NOMASK' or 'ROIAUTO' or 'ROI')
                What mode to use for using the masks. If ROIAUTO is choosen, then
                the mask is implicitly defined using a otsu forground and hole
                filling algorithm. The Region Of Interest mode (choose ROI) uses the
                masks to define what parts of the image should be used for computing
                the transform.
                flag: --maskProcessingMode %s
        maxBSplineDisplacement: (a float)
                 Sets the maximum allowed displacements in image physical
                coordinates for BSpline control grid along each axis. A value of 0.0
                indicates that the problem should be unbounded. NOTE: This only
                constrains the BSpline portion, and does not limit the displacement
                from the associated bulk transform. This can lead to a substantial
                reduction in computation time in the BSpline optimizer.,
                flag: --maxBSplineDisplacement %f
        maximumStepLength: (a float)
                Internal debugging parameter, and should probably never be used from
                the command line. This will be removed in the future.
                flag: --maximumStepLength %f
        medianFilterSize: (a list of items which are an integer (int or
                 long))
                The radius for the optional MedianImageFilter preprocessing in all 3
                directions.
                flag: --medianFilterSize %s
        minimumStepLength: (a list of items which are a float)
                Each step in the optimization takes steps at least this big. When
                none are possible, registration is complete.
                flag: --minimumStepLength %s
        movingBinaryVolume: (an existing file name)
                Moving Image binary mask volume, ONLY FOR MANUAL ROI mode.
                flag: --movingBinaryVolume %s
        movingVolume: (an existing file name)
                The moving image for registration by mutual information
                optimization.
                flag: --movingVolume %s
        movingVolumeTimeIndex: (an integer (int or long))
                The index in the time series for the 3D moving image to fit, if
                4-dimensional.
                flag: --movingVolumeTimeIndex %d
        numberOfHistogramBins: (an integer (int or long))
                The number of histogram levels
                flag: --numberOfHistogramBins %d
        numberOfIterations: (a list of items which are an integer (int or
                 long))
                The maximum number of iterations to try before failing to converge.
                Use an explicit limit like 500 or 1000 to manage risk of divergence
                flag: --numberOfIterations %s
        numberOfMatchPoints: (an integer (int or long))
                the number of match points
                flag: --numberOfMatchPoints %d
        numberOfSamples: (an integer (int or long))
                The number of voxels sampled for mutual information computation.
                Increase this for a slower, more careful fit. You can also limit the
                sampling focus with ROI masks and ROIAUTO mask generation.
                flag: --numberOfSamples %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use. (default is
                auto-detected)
                flag: --numberOfThreads %d
        outputFixedVolumeROI: (a boolean or a file name)
                The ROI automatically found in fixed image, ONLY FOR ROIAUTO mode.
                flag: --outputFixedVolumeROI %s
        outputMovingVolumeROI: (a boolean or a file name)
                The ROI automatically found in moving image, ONLY FOR ROIAUTO mode.
                flag: --outputMovingVolumeROI %s
        outputTransform: (a boolean or a file name)
                (optional) Filename to which save the (optional) estimated
                transform. NOTE: You must select either the outputTransform or the
                outputVolume option.
                flag: --outputTransform %s
        outputVolume: (a boolean or a file name)
                (optional) Output image for registration. NOTE: You must select
                either the outputTransform or the outputVolume option.
                flag: --outputVolume %s
        outputVolumePixelType: ('float' or 'short' or 'ushort' or 'int' or
                 'uint' or 'uchar')
                The output image Pixel Type is the scalar datatype for
                representation of the Output Volume.
                flag: --outputVolumePixelType %s
        permitParameterVariation: (a list of items which are an integer (int
                 or long))
                A bit vector to permit linear transform parameters to vary under
                optimization. The vector order corresponds with transform
                parameters, and beyond the end ones fill in as a default. For
                instance, you can choose to rotate only in x (pitch) with 1,0,0;
                this is mostly for expert use in turning on and off individual
                degrees of freedom in rotation, translation or scaling without
                multiplying the number of transform representations; this trick is
                probably meaningless when tried with the general affine transform.
                flag: --permitParameterVariation %s
        projectedGradientTolerance: (a float)
                 From itkLBFGSBOptimizer.h: Set/Get the ProjectedGradientTolerance.
                Algorithm terminates when the project gradient is below the
                tolerance. Default lbfgsb value is 1e-5, but 1e-4 seems to work
                well.,
                flag: --projectedGradientTolerance %f
        promptUser: (a boolean)
                Prompt the user to hit enter each time an image is sent to the
                DebugImageViewer
                flag: --promptUser
        relaxationFactor: (a float)
                Internal debugging parameter, and should probably never be used from
                the command line. This will be removed in the future.
                flag: --relaxationFactor %f
        removeIntensityOutliers: (a float)
                The half percentage to decide outliers of image intensities. The
                default value is zero, which means no outlier removal. If the value
                of 0.005 is given, the moduel will throw away 0.005 % of both tails,
                so 0.01% of intensities in total would be ignored in its statistic
                calculation.
                flag: --removeIntensityOutliers %f
        reproportionScale: (a float)
                ScaleVersor3D 'Scale' compensation factor. Increase this to put more
                rescaling in a ScaleVersor3D or ScaleSkewVersor3D search pattern.
                1.0 works well with a translationScale of 1000.0
                flag: --reproportionScale %f
        scaleOutputValues: (a boolean)
                If true, and the voxel values do not fit within the minimum and
                maximum values of the desired outputVolumePixelType, then linearly
                scale the min/max output image voxel values to fit within the
                min/max range of the outputVolumePixelType.
                flag: --scaleOutputValues
        skewScale: (a float)
                ScaleSkewVersor3D Skew compensation factor. Increase this to put
                more skew in a ScaleSkewVersor3D search pattern. 1.0 works well with
                a translationScale of 1000.0
                flag: --skewScale %f
        splineGridSize: (a list of items which are an integer (int or long))
                The number of subdivisions of the BSpline Grid to be centered on the
                image space. Each dimension must have at least 3 subdivisions for
                the BSpline to be correctly computed.
                flag: --splineGridSize %s
        strippedOutputTransform: (a boolean or a file name)
                File name for the rigid component of the estimated affine transform.
                Can be used to rigidly register the moving image to the fixed image.
                NOTE: This value is overwritten if either bsplineTransform or
                linearTransform is set.
                flag: --strippedOutputTransform %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformType: (a list of items which are a string)
                Specifies a list of registration types to be used. The valid types
                are, Rigid, ScaleVersor3D, ScaleSkewVersor3D, Affine, and BSpline.
                Specifiying more than one in a comma separated list will initialize
                the next stage with the previous results. If registrationClass flag
                is used, it overrides this parameter setting.
                flag: --transformType %s
        translationScale: (a float)
                How much to scale up changes in position compared to unit rotational
                changes in radians -- decrease this to put more rotation in the
                search pattern.
                flag: --translationScale %f
        useAffine: (a boolean)
                Perform an Affine registration as part of the sequential
                registration steps. This family of options superceeds the use of
                transformType if any of them are set.
                flag: --useAffine
        useBSpline: (a boolean)
                Perform a BSpline registration as part of the sequential
                registration steps. This family of options superceeds the use of
                transformType if any of them are set.
                flag: --useBSpline
        useCachingOfBSplineWeightsMode: ('ON' or 'OFF')
                This is a 5x speed advantage at the expense of requiring much more
                memory. Only relevant when transformType is BSpline.
                flag: --useCachingOfBSplineWeightsMode %s
        useExplicitPDFDerivativesMode: ('AUTO' or 'ON' or 'OFF')
                Using mode AUTO means OFF for BSplineDeformableTransforms and ON for
                the linear transforms. The ON alternative uses more memory to
                sometimes do a better job.
                flag: --useExplicitPDFDerivativesMode %s
        useRigid: (a boolean)
                Perform a rigid registration as part of the sequential registration
                steps. This family of options superceeds the use of transformType if
                any of them are set.
                flag: --useRigid
        useScaleSkewVersor3D: (a boolean)
                Perform a ScaleSkewVersor3D registration as part of the sequential
                registration steps. This family of options superceeds the use of
                transformType if any of them are set.
                flag: --useScaleSkewVersor3D
        useScaleVersor3D: (a boolean)
                Perform a ScaleVersor3D registration as part of the sequential
                registration steps. This family of options superceeds the use of
                transformType if any of them are set.
                flag: --useScaleVersor3D
        writeOutputTransformInFloat: (a boolean)
                By default, the output registration transforms (either the output
                composite transform or each transform component) are written to the
                disk in double precision. If this flag is ON, the output transforms
                will be written in single (float) precision. It is especially
                important if the output transform is a displacement field transform,
                or it is a composite transform that includes several displacement
                fields.
                flag: --writeOutputTransformInFloat
        writeTransformOnFailure: (a boolean)
                Flag to save the final transform even if the numberOfIterations are
                reached without convergence. (Intended for use when
                --failureExitCode 0 )
                flag: --writeTransformOnFailure

Outputs::

        bsplineTransform: (an existing file name)
                (optional) Filename to which save the estimated transform. NOTE: You
                must set at least one output object (either a deformed image or a
                transform. NOTE: USE THIS ONLY IF THE FINAL TRANSFORM IS BSpline
        linearTransform: (an existing file name)
                (optional) Filename to which save the estimated transform. NOTE: You
                must set at least one output object (either a deformed image or a
                transform. NOTE: USE THIS ONLY IF THE FINAL TRANSFORM IS ---NOT---
                BSpline
        outputFixedVolumeROI: (an existing file name)
                The ROI automatically found in fixed image, ONLY FOR ROIAUTO mode.
        outputMovingVolumeROI: (an existing file name)
                The ROI automatically found in moving image, ONLY FOR ROIAUTO mode.
        outputTransform: (an existing file name)
                (optional) Filename to which save the (optional) estimated
                transform. NOTE: You must select either the outputTransform or the
                outputVolume option.
        outputVolume: (an existing file name)
                (optional) Output image for registration. NOTE: You must select
                either the outputTransform or the outputVolume option.
        strippedOutputTransform: (an existing file name)
                File name for the rigid component of the estimated affine transform.
                Can be used to rigidly register the moving image to the fixed image.
                NOTE: This value is overwritten if either bsplineTransform or
                linearTransform is set.
