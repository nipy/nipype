.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.registration.brainsfit
==========================================


.. _nipype.interfaces.semtools.registration.brainsfit.BRAINSFit:


.. index:: BRAINSFit

BRAINSFit
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/registration/brainsfit.py#L109>`__

Wraps command ** BRAINSFit **

title: General Registration (BRAINS)

category: Registration

description: Register a three-dimensional volume to a reference volume (Mattes Mutual Information by default). Full documentation avalable here: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/BRAINSFit. Method described in BRAINSFit: Mutual Information Registrations of Whole-Brain 3D Images, Using the Insight Toolkit, Johnson H.J., Harris G., Williams K., The Insight Journal, 2007. http://hdl.handle.net/1926/1291

version: 3.0.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/BRAINSFit

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Hans J. Johnson, hans-johnson -at- uiowa.edu, http://www.psychiatry.uiowa.edu

acknowledgements: Hans Johnson(1,3,4); Kent Williams(1); Gregory Harris(1), Vincent Magnotta(1,2,3);  Andriy Fedorov(5) 1=University of Iowa Department of Psychiatry, 2=University of Iowa Department of Radiology, 3=University of Iowa Department of Biomedical Engineering, 4=University of Iowa Department of Electrical and Computer Engineering, 5=Surgical Planning Lab, Harvard

Inputs::

        [Mandatory]

        [Optional]
        ROIAutoClosingSize: (a float)
                This flag is only relevant when using ROIAUTO mode for initializing
                masks. It defines the hole closing size in mm. It is rounded up to
                the nearest whole pixel size in each direction. The default is to
                use a closing size of 9mm. For mouse data this value may need to be
                reset to 0.9 or smaller.
                flag: --ROIAutoClosingSize %f
        ROIAutoDilateSize: (a float)
                This flag is only relevant when using ROIAUTO mode for initializing
                masks. It defines the final dilation size to capture a bit of
                background outside the tissue region. A setting of 10mm has been
                shown to help regularize a BSpline registration type so that there
                is some background constraints to match the edges of the head
                better.
                flag: --ROIAutoDilateSize %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        backgroundFillValue: (a float)
                This value will be used for filling those areas of the output image
                that have no corresponding voxels in the input moving image.
                flag: --backgroundFillValue %f
        bsplineTransform: (a boolean or a file name)
                (optional) Output estimated transform - in case the computed
                transform is BSpline. NOTE: You must set at least one output object
                (transform and/or output volume).
                flag: --bsplineTransform %s
        costFunctionConvergenceFactor: (a float)
                From itkLBFGSBOptimizer.h: Set/Get the
                CostFunctionConvergenceFactor. Algorithm terminates when the
                reduction in cost function is less than (factor * epsmcj) where
                epsmch is the machine precision. Typical values for factor: 1e+12
                for low accuracy; 1e+7 for moderate accuracy and 1e+1 for extremely
                high accuracy. 1e+9 seems to work well.,
                flag: --costFunctionConvergenceFactor %f
        costMetric: ('MMI' or 'MSE' or 'NC' or 'MIH')
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
                Fixed Image binary mask volume, required if Masking Option is ROI.
                Image areas where the mask volume has zero value are ignored during
                the registration.
                flag: --fixedBinaryVolume %s
        fixedVolume: (an existing file name)
                Input fixed image (the moving image will be transformed into this
                image space).
                flag: --fixedVolume %s
        fixedVolume2: (an existing file name)
                Input fixed image that will be used for multimodal registration.
                (the moving image will be transformed into this image space).
                flag: --fixedVolume2 %s
        fixedVolumeTimeIndex: (an integer (int or long))
                The index in the time series for the 3D fixed image to fit. Only
                allowed if the fixed input volume is 4-dimensional.
                flag: --fixedVolumeTimeIndex %d
        gui: (a boolean)
                Display intermediate image volumes for debugging. NOTE: This is not
                part of the standard build sytem, and probably does nothing on your
                installation.
                flag: --gui
        histogramMatch: (a boolean)
                Apply histogram matching operation for the input images to make them
                more similar. This is suitable for images of the same modality that
                may have different brightness or contrast, but the same overall
                intensity profile. Do NOT use if registering images from different
                modalities.
                flag: --histogramMatch
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        initialTransform: (an existing file name)
                Transform to be applied to the moving image to initialize the
                registration. This can only be used if Initialize Transform Mode is
                Off.
                flag: --initialTransform %s
        initializeRegistrationByCurrentGenericTransform: (a boolean)
                If this flag is ON, the current generic composite transform,
                resulted from the linear registration stages, is set to initialize
                the follow nonlinear registration process. However, by the default
                behaviour, the moving image is first warped based on the existant
                transform before it is passed to the BSpline registration filter. It
                is done to speed up the BSpline registration by reducing the
                computations of composite transform Jacobian.
                flag: --initializeRegistrationByCurrentGenericTransform
        initializeTransformMode: ('Off' or 'useMomentsAlign' or
                 'useCenterOfHeadAlign' or 'useGeometryAlign' or
                 'useCenterOfROIAlign')
                Determine how to initialize the transform center. useMomentsAlign
                assumes that the center of mass of the images represent similar
                structures. useCenterOfHeadAlign attempts to use the top of head and
                shape of neck to drive a center of mass estimate. useGeometryAlign
                on assumes that the center of the voxel lattice of the images
                represent similar structures. Off assumes that the physical space of
                the images are close. This flag is mutually exclusive with the
                Initialization transform.
                flag: --initializeTransformMode %s
        interpolationMode: ('NearestNeighbor' or 'Linear' or
                 'ResampleInPlace' or 'BSpline' or 'WindowedSinc' or 'Hamming' or
                 'Cosine' or 'Welch' or 'Lanczos' or 'Blackman')
                Type of interpolation to be used when applying transform to moving
                volume. Options are Linear, NearestNeighbor, BSpline, WindowedSinc,
                Hamming, Cosine, Welch, Lanczos, or ResampleInPlace. The
                ResampleInPlace option will create an image with the same discrete
                voxel values and will adjust the origin and direction of the
                physical space interpretation.
                flag: --interpolationMode %s
        linearTransform: (a boolean or a file name)
                (optional) Output estimated transform - in case the computed
                transform is not BSpline. NOTE: You must set at least one output
                object (transform and/or output volume).
                flag: --linearTransform %s
        logFileReport: (a boolean or a file name)
                A file to write out final information report in CSV file: MetricName
                ,MetricValue,FixedImageName,FixedMaskName,MovingImageName,MovingMask
                Name
                flag: --logFileReport %s
        maskInferiorCutOffFromCenter: (a float)
                If Initialize Transform Mode is set to useCenterOfHeadAlign or
                Masking Option is ROIAUTO then this value defines the how much is
                cut of from the inferior part of the image. The cut-off distance is
                specified in millimeters, relative to the image center. If the value
                is 1000 or larger then no cut-off performed.
                flag: --maskInferiorCutOffFromCenter %f
        maskProcessingMode: ('NOMASK' or 'ROIAUTO' or 'ROI')
                Specifies a mask to only consider a certain image region for the
                registration. If ROIAUTO is chosen, then the mask is computed using
                Otsu thresholding and hole filling. If ROI is chosen then the mask
                has to be specified as in input.
                flag: --maskProcessingMode %s
        maxBSplineDisplacement: (a float)
                Maximum allowed displacements in image physical coordinates (mm) for
                BSpline control grid along each axis. A value of 0.0 indicates that
                the problem should be unbounded. NOTE: This only constrains the
                BSpline portion, and does not limit the displacement from the
                associated bulk transform. This can lead to a substantial reduction
                in computation time in the BSpline optimizer.,
                flag: --maxBSplineDisplacement %f
        maximumNumberOfCorrections: (an integer (int or long))
                Maximum number of corrections in lbfgsb optimizer.
                flag: --maximumNumberOfCorrections %d
        maximumNumberOfEvaluations: (an integer (int or long))
                Maximum number of evaluations for line search in lbfgsb optimizer.
                flag: --maximumNumberOfEvaluations %d
        maximumStepLength: (a float)
                Starting step length of the optimizer. In general, higher values
                allow for recovering larger initial misalignments but there is an
                increased chance that the registration will not converge.
                flag: --maximumStepLength %f
        medianFilterSize: (a list of items which are an integer (int or
                 long))
                Apply median filtering to reduce noise in the input volumes. The 3
                values specify the radius for the optional MedianImageFilter
                preprocessing in all 3 directions (in voxels).
                flag: --medianFilterSize %s
        metricSamplingStrategy: ('Random')
                It defines the method that registration filter uses to sample the
                input fixed image. Only Random is supported for now.
                flag: --metricSamplingStrategy %s
        minimumStepLength: (a list of items which are a float)
                Each step in the optimization takes steps at least this big. When
                none are possible, registration is complete. Smaller values allows
                the optimizer to make smaller adjustments, but the registration time
                may increase.
                flag: --minimumStepLength %s
        movingBinaryVolume: (an existing file name)
                Moving Image binary mask volume, required if Masking Option is ROI.
                Image areas where the mask volume has zero value are ignored during
                the registration.
                flag: --movingBinaryVolume %s
        movingVolume: (an existing file name)
                Input moving image (this image will be transformed into the fixed
                image space).
                flag: --movingVolume %s
        movingVolume2: (an existing file name)
                Input moving image that will be used for multimodal
                registration(this image will be transformed into the fixed image
                space).
                flag: --movingVolume2 %s
        movingVolumeTimeIndex: (an integer (int or long))
                The index in the time series for the 3D moving image to fit. Only
                allowed if the moving input volume is 4-dimensional
                flag: --movingVolumeTimeIndex %d
        numberOfHistogramBins: (an integer (int or long))
                The number of histogram levels used for mutual information metric
                estimation.
                flag: --numberOfHistogramBins %d
        numberOfIterations: (a list of items which are an integer (int or
                 long))
                The maximum number of iterations to try before stopping the
                optimization. When using a lower value (500-1000) then the
                registration is forced to terminate earlier but there is a higher
                risk of stopping before an optimal solution is reached.
                flag: --numberOfIterations %s
        numberOfMatchPoints: (an integer (int or long))
                Number of histogram match points used for mutual information metric
                estimation.
                flag: --numberOfMatchPoints %d
        numberOfSamples: (an integer (int or long))
                The number of voxels sampled for mutual information computation.
                Increase this for higher accuracy, at the cost of longer computation
                time., NOTE that it is suggested to use samplingPercentage instead
                of this option. However, if set to non-zero, numberOfSamples
                overwrites the samplingPercentage option.
                flag: --numberOfSamples %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use. (default is
                auto-detected)
                flag: --numberOfThreads %d
        outputFixedVolumeROI: (a boolean or a file name)
                ROI that is automatically computed from the fixed image. Only
                available if Masking Option is ROIAUTO. Image areas where the mask
                volume has zero value are ignored during the registration.
                flag: --outputFixedVolumeROI %s
        outputMovingVolumeROI: (a boolean or a file name)
                ROI that is automatically computed from the moving image. Only
                available if Masking Option is ROIAUTO. Image areas where the mask
                volume has zero value are ignored during the registration.
                flag: --outputMovingVolumeROI %s
        outputTransform: (a boolean or a file name)
                (optional) Filename to which save the (optional) estimated
                transform. NOTE: You must select either the outputTransform or the
                outputVolume option.
                flag: --outputTransform %s
        outputVolume: (a boolean or a file name)
                (optional) Output image: the moving image warped to the fixed image
                space. NOTE: You must set at least one output object (transform
                and/or output volume).
                flag: --outputVolume %s
        outputVolumePixelType: ('float' or 'short' or 'ushort' or 'int' or
                 'uint' or 'uchar')
                Data type for representing a voxel of the Output Volume.
                flag: --outputVolumePixelType %s
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
                Specifies how quickly the optimization step length is decreased
                during registration. The value must be larger than 0 and smaller
                than 1. Larger values result in slower step size decrease, which
                allow for recovering larger initial misalignments but it increases
                the registration time and the chance that the registration will not
                converge.
                flag: --relaxationFactor %f
        removeIntensityOutliers: (a float)
                Remove very high and very low intensity voxels from the input
                volumes. The parameter specifies the half percentage to decide
                outliers of image intensities. The default value is zero, which
                means no outlier removal. If the value of 0.005 is given, the 0.005%
                of both tails will be thrown away, so 0.01% of intensities in total
                would be ignored in the statistic calculation.
                flag: --removeIntensityOutliers %f
        reproportionScale: (a float)
                ScaleVersor3D 'Scale' compensation factor. Increase this to allow
                for more rescaling in a ScaleVersor3D or ScaleSkewVersor3D search
                pattern. 1.0 works well with a translationScale of 1000.0
                flag: --reproportionScale %f
        samplingPercentage: (a float)
                Fraction of voxels of the fixed image that will be used for
                registration. The number has to be larger than zero and less or
                equal to one. Higher values increase the computation time but may
                give more accurate results. You can also limit the sampling focus
                with ROI masks and ROIAUTO mask generation. The default is 0.002
                (use approximately 0.2% of voxels, resulting in 100000 samples in a
                512x512x192 volume) to provide a very fast registration in most
                cases. Typical values range from 0.01 (1%) for low detail images to
                0.2 (20%) for high detail images.
                flag: --samplingPercentage %f
        scaleOutputValues: (a boolean)
                If true, and the voxel values do not fit within the minimum and
                maximum values of the desired outputVolumePixelType, then linearly
                scale the min/max output image voxel values to fit within the
                min/max range of the outputVolumePixelType.
                flag: --scaleOutputValues
        skewScale: (a float)
                ScaleSkewVersor3D Skew compensation factor. Increase this to allow
                for more skew in a ScaleSkewVersor3D search pattern. 1.0 works well
                with a translationScale of 1000.0
                flag: --skewScale %f
        splineGridSize: (a list of items which are an integer (int or long))
                Number of BSpline grid subdivisions along each axis of the fixed
                image, centered on the image space. Values must be 3 or higher for
                the BSpline to be correctly computed.
                flag: --splineGridSize %s
        strippedOutputTransform: (a boolean or a file name)
                Rigid component of the estimated affine transform. Can be used to
                rigidly register the moving image to the fixed image. NOTE: This
                value is overridden if either bsplineTransform or linearTransform is
                set.
                flag: --strippedOutputTransform %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformType: (a list of items which are a string)
                Specifies a list of registration types to be used. The valid types
                are, Rigid, ScaleVersor3D, ScaleSkewVersor3D, Affine, BSpline and
                SyN. Specifying more than one in a comma separated list will
                initialize the next stage with the previous results. If
                registrationClass flag is used, it overrides this parameter setting.
                flag: --transformType %s
        translationScale: (a float)
                How much to scale up changes in position (in mm) compared to unit
                rotational changes (in radians) -- decrease this to allow for more
                rotation in the search pattern.
                flag: --translationScale %f
        useAffine: (a boolean)
                Perform an Affine registration as part of the sequential
                registration steps. This family of options overrides the use of
                transformType if any of them are set.
                flag: --useAffine
        useBSpline: (a boolean)
                Perform a BSpline registration as part of the sequential
                registration steps. This family of options overrides the use of
                transformType if any of them are set.
                flag: --useBSpline
        useComposite: (a boolean)
                Perform a Composite registration as part of the sequential
                registration steps. This family of options overrides the use of
                transformType if any of them are set.
                flag: --useComposite
        useROIBSpline: (a boolean)
                If enabled then the bounding box of the input ROIs defines the
                BSpline grid support region. Otherwise the BSpline grid support
                region is the whole fixed image.
                flag: --useROIBSpline
        useRigid: (a boolean)
                Perform a rigid registration as part of the sequential registration
                steps. This family of options overrides the use of transformType if
                any of them are set.
                flag: --useRigid
        useScaleSkewVersor3D: (a boolean)
                Perform a ScaleSkewVersor3D registration as part of the sequential
                registration steps. This family of options overrides the use of
                transformType if any of them are set.
                flag: --useScaleSkewVersor3D
        useScaleVersor3D: (a boolean)
                Perform a ScaleVersor3D registration as part of the sequential
                registration steps. This family of options overrides the use of
                transformType if any of them are set.
                flag: --useScaleVersor3D
        useSyN: (a boolean)
                Perform a SyN registration as part of the sequential registration
                steps. This family of options overrides the use of transformType if
                any of them are set.
                flag: --useSyN
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
                (optional) Output estimated transform - in case the computed
                transform is BSpline. NOTE: You must set at least one output object
                (transform and/or output volume).
        linearTransform: (an existing file name)
                (optional) Output estimated transform - in case the computed
                transform is not BSpline. NOTE: You must set at least one output
                object (transform and/or output volume).
        logFileReport: (an existing file name)
                A file to write out final information report in CSV file: MetricName
                ,MetricValue,FixedImageName,FixedMaskName,MovingImageName,MovingMask
                Name
        outputFixedVolumeROI: (an existing file name)
                ROI that is automatically computed from the fixed image. Only
                available if Masking Option is ROIAUTO. Image areas where the mask
                volume has zero value are ignored during the registration.
        outputMovingVolumeROI: (an existing file name)
                ROI that is automatically computed from the moving image. Only
                available if Masking Option is ROIAUTO. Image areas where the mask
                volume has zero value are ignored during the registration.
        outputTransform: (an existing file name)
                (optional) Filename to which save the (optional) estimated
                transform. NOTE: You must select either the outputTransform or the
                outputVolume option.
        outputVolume: (an existing file name)
                (optional) Output image: the moving image warped to the fixed image
                space. NOTE: You must set at least one output object (transform
                and/or output volume).
        strippedOutputTransform: (an existing file name)
                Rigid component of the estimated affine transform. Can be used to
                rigidly register the moving image to the fixed image. NOTE: This
                value is overridden if either bsplineTransform or linearTransform is
                set.
