.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.diffusion.gtract
====================================


.. _nipype.interfaces.semtools.diffusion.gtract.compareTractInclusion:


.. index:: compareTractInclusion

compareTractInclusion
---------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L581>`__

Wraps command ** compareTractInclusion **

title: Compare Tracts

category: Diffusion.GTRACT

description: This program will halt with a status code indicating whether a test tract is nearly enough included in a standard tract in the sense that every fiber in the test tract has a low enough sum of squares distance to some fiber in the standard tract modulo spline resampling of every fiber to a fixed number of points.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        closeness: (a float)
                Closeness of every test fiber to some fiber in the standard tract,
                computed as a sum of squares of spatial differences of standard
                points
                flag: --closeness %f
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        numberOfPoints: (an integer (int or long))
                Number of points in comparison fiber pairs
                flag: --numberOfPoints %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        standardFiber: (an existing file name)
                Required: standard fiber tract file name
                flag: --standardFiber %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        testFiber: (an existing file name)
                Required: test fiber tract file name
                flag: --testFiber %s
        testForBijection: (a boolean)
                Flag to apply the closeness criterion both ways
                flag: --testForBijection
        testForFiberCardinality: (a boolean)
                Flag to require the same number of fibers in both tracts
                flag: --testForFiberCardinality
        writeXMLPolyDataFile: (a boolean)
                Flag to make use of XML files when reading and writing vtkPolyData.
                flag: --writeXMLPolyDataFile

Outputs::

        None

.. _nipype.interfaces.semtools.diffusion.gtract.extractNrrdVectorIndex:


.. index:: extractNrrdVectorIndex

extractNrrdVectorIndex
----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L922>`__

Wraps command ** extractNrrdVectorIndex **

title: Extract Nrrd Index

category: Diffusion.GTRACT

description: This program will extract a 3D image (single vector) from a vector 3D image at a given vector index.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
                Required: input file containing the vector that will be extracted
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: name of output NRRD file containing the vector image at
                the given index
                flag: --outputVolume %s
        setImageOrientation: ('AsAcquired' or 'Axial' or 'Coronal' or
                 'Sagittal')
                Sets the image orientation of the extracted vector (Axial, Coronal,
                Sagittal)
                flag: --setImageOrientation %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        vectorIndex: (an integer (int or long))
                Index in the vector image to extract
                flag: --vectorIndex %d

Outputs::

        outputVolume: (an existing file name)
                Required: name of output NRRD file containing the vector image at
                the given index

.. _nipype.interfaces.semtools.diffusion.gtract.gtractAnisotropyMap:


.. index:: gtractAnisotropyMap

gtractAnisotropyMap
-------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L384>`__

Wraps command ** gtractAnisotropyMap **

title: Anisotropy Map

category: Diffusion.GTRACT

description: This program will generate a scalar map of anisotropy, given a tensor representation. Anisotropy images are used for fiber tracking, but the anisotropy scalars are not defined along the path. Instead, the tensor representation is included as point data allowing all of these metrics to be computed using only the fiber tract point data. The images can be saved in any ITK supported format, but it is suggested that you use an image format that supports the definition of the image origin. This includes NRRD, NifTI, and Meta formats. These images can also be used for scalar analysis including regional anisotropy measures or VBM style analysis.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        anisotropyType: ('ADC' or 'FA' or 'RA' or 'VR' or 'AD' or 'RD' or
                 'LI')
                Anisotropy Mapping Type: ADC, FA, RA, VR, AD, RD, LI
                flag: --anisotropyType %s
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
        inputTensorVolume: (an existing file name)
                Required: input file containing the diffusion tensor image
                flag: --inputTensorVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: name of output NRRD file containing the selected kind of
                anisotropy scalar.
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: name of output NRRD file containing the selected kind of
                anisotropy scalar.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractAverageBvalues:


.. index:: gtractAverageBvalues

gtractAverageBvalues
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L136>`__

Wraps command ** gtractAverageBvalues **

title: Average B-Values

category: Diffusion.GTRACT

description: This program will directly average together the baseline gradients (b value equals 0) within a DWI scan. This is usually used after gtractCoregBvalues.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        averageB0only: (a boolean)
                Average only baseline gradients. All other gradient directions are
                not averaged, but retained in the outputVolume
                flag: --averageB0only
        directionsTolerance: (a float)
                Tolerance for matching identical gradient direction pairs
                flag: --directionsTolerance %f
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                Required: input image file name containing multiple baseline
                gradients to average
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: name of output NRRD file containing directly averaged
                baseline images
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: name of output NRRD file containing directly averaged
                baseline images

.. _nipype.interfaces.semtools.diffusion.gtract.gtractClipAnisotropy:


.. index:: gtractClipAnisotropy

gtractClipAnisotropy
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L423>`__

Wraps command ** gtractClipAnisotropy **

title: Clip Anisotropy

category: Diffusion.GTRACT

description: This program will zero the first and/or last slice of an anisotropy image, creating a clipped anisotropy image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        clipFirstSlice: (a boolean)
                Clip the first slice of the anisotropy image
                flag: --clipFirstSlice
        clipLastSlice: (a boolean)
                Clip the last slice of the anisotropy image
                flag: --clipLastSlice
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                Required: input image file name
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: name of output NRRD file containing the clipped anisotropy
                image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: name of output NRRD file containing the clipped anisotropy
                image

.. _nipype.interfaces.semtools.diffusion.gtract.gtractCoRegAnatomy:


.. index:: gtractCoRegAnatomy

gtractCoRegAnatomy
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L732>`__

Wraps command ** gtractCoRegAnatomy **

title: Coregister B0 to Anatomy B-Spline

category: Diffusion.GTRACT

description: This program will register a Nrrd diffusion weighted 4D vector image to a fixed anatomical image. Two registration methods are supported for alignment with anatomical images: Rigid and B-Spline. The rigid registration performs a rigid body registration with the anatomical images and should be done as well to initialize the B-Spline transform. The B-SPline transform is the deformable transform, where the user can control the amount of deformation based on the number of control points as well as the maximum distance that these points can move. The B-Spline registration places a low dimensional grid in the image, which is deformed. This allows for some susceptibility related distortions to be removed from the diffusion weighted images. In general the amount of motion in the slice selection and read-out directions direction should be kept low. The distortion is in the phase encoding direction in the images. It is recommended that skull stripped (i.e. image containing only brain with skull removed) images shoud be used for image co-registration with the B-Spline transform.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        borderSize: (an integer (int or long))
                Size of border
                flag: --borderSize %d
        convergence: (a float)
                Convergence Factor
                flag: --convergence %f
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        gradientTolerance: (a float)
                Gradient Tolerance
                flag: --gradientTolerance %f
        gridSize: (a list of items which are an integer (int or long))
                Number of grid subdivisions in all 3 directions
                flag: --gridSize %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputAnatomicalVolume: (an existing file name)
                Required: input anatomical image file name. It is recommended that
                that the input anatomical image has been skull stripped and has the
                same orientation as the DWI scan.
                flag: --inputAnatomicalVolume %s
        inputRigidTransform: (an existing file name)
                Required (for B-Spline type co-registration): input rigid transform
                file name. Used as a starting point for the anatomical B-Spline
                registration.
                flag: --inputRigidTransform %s
        inputVolume: (an existing file name)
                Required: input vector image file name. It is recommended that the
                input volume is the skull stripped baseline image of the DWI scan.
                flag: --inputVolume %s
        maxBSplineDisplacement: (a float)
                 Sets the maximum allowed displacements in image physical
                coordinates for BSpline control grid along each axis. A value of 0.0
                indicates that the problem should be unbounded. NOTE: This only
                constrains the BSpline portion, and does not limit the displacement
                from the associated bulk transform. This can lead to a substantial
                reduction in computation time in the BSpline optimizer.,
                flag: --maxBSplineDisplacement %f
        maximumStepSize: (a float)
                Maximum permitted step size to move in the selected 3D fit
                flag: --maximumStepSize %f
        minimumStepSize: (a float)
                Minimum required step size to move in the selected 3D fit without
                converging -- decrease this to make the fit more exacting
                flag: --minimumStepSize %f
        numberOfHistogramBins: (an integer (int or long))
                Number of histogram bins
                flag: --numberOfHistogramBins %d
        numberOfIterations: (an integer (int or long))
                Number of iterations in the selected 3D fit
                flag: --numberOfIterations %d
        numberOfSamples: (an integer (int or long))
                The number of voxels sampled for mutual information computation.
                Increase this for a slower, more careful fit. NOTE that it is
                suggested to use samplingPercentage instead of this option. However,
                if set, it overwrites the samplingPercentage option.
                flag: --numberOfSamples %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputTransformName: (a boolean or a file name)
                Required: filename for the fit transform.
                flag: --outputTransformName %s
        relaxationFactor: (a float)
                Fraction of gradient from Jacobian to attempt to move in the
                selected 3D fit
                flag: --relaxationFactor %f
        samplingPercentage: (a float)
                This is a number in (0.0,1.0] interval that shows the percentage of
                the input fixed image voxels that are sampled for mutual information
                computation. Increase this for a slower, more careful fit. You can
                also limit the sampling focus with ROI masks and ROIAUTO mask
                generation. The default is to use approximately 5% of voxels (for
                backwards compatibility 5% ~= 500000/(256*256*256)). Typical values
                range from 1% for low detail images to 20% for high detail images.
                flag: --samplingPercentage %f
        spatialScale: (an integer (int or long))
                Scales the number of voxels in the image by this value to specify
                the number of voxels used in the registration
                flag: --spatialScale %d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformType: ('Rigid' or 'Bspline')
                Transform Type: Rigid|Bspline
                flag: --transformType %s
        translationScale: (a float)
                How much to scale up changes in position compared to unit rotational
                changes in radians -- decrease this to put more translation in the
                fit
                flag: --translationScale %f
        useCenterOfHeadAlign: (a boolean)
                CenterOfHeadAlign attempts to find a hemisphere full of foreground
                voxels from the superior direction as an estimate of where the
                center of a head shape would be to drive a center of mass estimate.
                Perform a CenterOfHeadAlign registration as part of the sequential
                registration steps. This option MUST come first, and CAN NOT be used
                with either MomentsAlign, GeometryAlign, or initialTransform file.
                This family of options superceeds the use of transformType if any of
                them are set.
                flag: --useCenterOfHeadAlign
        useGeometryAlign: (a boolean)
                GeometryAlign on assumes that the center of the voxel lattice of the
                images represent similar structures. Perform a GeometryCenterAlign
                registration as part of the sequential registration steps. This
                option MUST come first, and CAN NOT be used with either
                MomentsAlign, CenterOfHeadAlign, or initialTransform file. This
                family of options superceeds the use of transformType if any of them
                are set.
                flag: --useGeometryAlign
        useMomentsAlign: (a boolean)
                MomentsAlign assumes that the center of mass of the images represent
                similar structures. Perform a MomentsAlign registration as part of
                the sequential registration steps. This option MUST come first, and
                CAN NOT be used with either CenterOfHeadLAlign, GeometryAlign, or
                initialTransform file. This family of options superceeds the use of
                transformType if any of them are set.
                flag: --useMomentsAlign
        vectorIndex: (an integer (int or long))
                Vector image index in the moving image (within the DWI) to be used
                for registration.
                flag: --vectorIndex %d

Outputs::

        outputTransformName: (an existing file name)
                Required: filename for the fit transform.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractConcatDwi:


.. index:: gtractConcatDwi

gtractConcatDwi
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L97>`__

Wraps command ** gtractConcatDwi **

title: Concat DWI Images

category: Diffusion.GTRACT

description: This program will concatenate two DTI runs together.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
        ignoreOrigins: (a boolean)
                If image origins are different force all images to origin of first
                image
                flag: --ignoreOrigins
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (a list of items which are an existing file name)
                Required: input file containing the first diffusion weighted image
                flag: --inputVolume %s...
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: name of output NRRD file containing the combined diffusion
                weighted images.
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: name of output NRRD file containing the combined diffusion
                weighted images.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractCopyImageOrientation:


.. index:: gtractCopyImageOrientation

gtractCopyImageOrientation
--------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L307>`__

Wraps command ** gtractCopyImageOrientation **

title: Copy Image Orientation

category: Diffusion.GTRACT

description: This program will copy the orientation from the reference image into the moving image. Currently, the registration process requires that the diffusion weighted images and the anatomical images have the same image orientation (i.e. Axial, Coronal, Sagittal). It is suggested that you copy the image orientation from the diffusion weighted images and apply this to the anatomical image. This image can be subsequently removed after the registration step is complete. We anticipate that this limitation will be removed in future versions of the registration programs.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
        inputReferenceVolume: (an existing file name)
                Required: input file containing orietation that will be cloned.
                flag: --inputReferenceVolume %s
        inputVolume: (an existing file name)
                Required: input file containing the signed short image to reorient
                without resampling.
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: name of output NRRD or Nifti file containing the
                reoriented image in reference image space.
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: name of output NRRD or Nifti file containing the
                reoriented image in reference image space.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractCoregBvalues:


.. index:: gtractCoregBvalues

gtractCoregBvalues
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L189>`__

Wraps command ** gtractCoregBvalues **

title: Coregister B-Values

category: Diffusion.GTRACT

description: This step should be performed after converting DWI scans from DICOM to NRRD format. This program will register all gradients in a NRRD diffusion weighted 4D vector image (moving image) to a specified index in a fixed image. It also supports co-registration with a T2 weighted image or field map in the same plane as the DWI data. The fixed image for the registration should be a b0 image. A mutual information metric cost function is used for the registration because of the differences in signal intensity as a result of the diffusion gradients. The full affine allows the registration procedure to correct for eddy current distortions that may exist in the data. If the eddyCurrentCorrection is enabled, relaxationFactor (0.25) and maximumStepSize (0.1) should be adjusted.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        debugLevel: (an integer (int or long))
                Display debug messages, and produce debug intermediate results.
                0=OFF, 1=Minimal, 10=Maximum debugging.
                flag: --debugLevel %d
        eddyCurrentCorrection: (a boolean)
                Flag to perform eddy current corection in addition to motion
                correction (recommended)
                flag: --eddyCurrentCorrection
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fixedVolume: (an existing file name)
                Required: input fixed image file name. It is recommended that this
                image should either contain or be a b0 image.
                flag: --fixedVolume %s
        fixedVolumeIndex: (an integer (int or long))
                Index in the fixed image for registration. It is recommended that
                this image should be a b0 image.
                flag: --fixedVolumeIndex %d
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        maximumStepSize: (a float)
                Maximum permitted step size to move in each 3D fit step (adjust when
                eddyCurrentCorrection is enabled; suggested value = 0.1)
                flag: --maximumStepSize %f
        minimumStepSize: (a float)
                Minimum required step size to move in each 3D fit step without
                converging -- decrease this to make the fit more exacting
                flag: --minimumStepSize %f
        movingVolume: (an existing file name)
                Required: input moving image file name. In order to register
                gradients within a scan to its first gradient, set the movingVolume
                and fixedVolume as the same image.
                flag: --movingVolume %s
        numberOfIterations: (an integer (int or long))
                Number of iterations in each 3D fit
                flag: --numberOfIterations %d
        numberOfSpatialSamples: (an integer (int or long))
                The number of voxels sampled for mutual information computation.
                Increase this for a slower, more careful fit. NOTE that it is
                suggested to use samplingPercentage instead of this option. However,
                if set, it overwrites the samplingPercentage option.
                flag: --numberOfSpatialSamples %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputTransform: (a boolean or a file name)
                Registration 3D transforms concatenated in a single output file.
                There are no tools that can use this, but can be used for debugging
                purposes.
                flag: --outputTransform %s
        outputVolume: (a boolean or a file name)
                Required: name of output NRRD file containing moving images
                individually resampled and fit to the specified fixed image index.
                flag: --outputVolume %s
        registerB0Only: (a boolean)
                Register the B0 images only
                flag: --registerB0Only
        relaxationFactor: (a float)
                Fraction of gradient from Jacobian to attempt to move in each 3D fit
                step (adjust when eddyCurrentCorrection is enabled; suggested value
                = 0.25)
                flag: --relaxationFactor %f
        samplingPercentage: (a float)
                This is a number in (0.0,1.0] interval that shows the percentage of
                the input fixed image voxels that are sampled for mutual information
                computation. Increase this for a slower, more careful fit. You can
                also limit the sampling focus with ROI masks and ROIAUTO mask
                generation. The default is to use approximately 5% of voxels (for
                backwards compatibility 5% ~= 500000/(256*256*256)). Typical values
                range from 1% for low detail images to 20% for high detail images.
                flag: --samplingPercentage %f
        spatialScale: (a float)
                How much to scale up changes in position compared to unit rotational
                changes in radians -- decrease this to put more rotation in the fit
                flag: --spatialScale %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputTransform: (an existing file name)
                Registration 3D transforms concatenated in a single output file.
                There are no tools that can use this, but can be used for debugging
                purposes.
        outputVolume: (an existing file name)
                Required: name of output NRRD file containing moving images
                individually resampled and fit to the specified fixed image index.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractCostFastMarching:


.. index:: gtractCostFastMarching

gtractCostFastMarching
----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L821>`__

Wraps command ** gtractCostFastMarching **

title: Cost Fast Marching

category: Diffusion.GTRACT

description: This program will use a fast marching fiber tracking algorithm to identify fiber tracts from a tensor image. This program is the first portion of the algorithm. The user must first run gtractFastMarchingTracking to generate the actual fiber tracts.  This algorithm is roughly based on the work by G. Parker et al. from IEEE Transactions On Medical Imaging, 21(5): 505-512, 2002. An additional feature of including anisotropy into the vcl_cost function calculation is included.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris. The original code here was developed by Daisy Espino.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        anisotropyWeight: (a float)
                Anisotropy weight used for vcl_cost function calculations
                flag: --anisotropyWeight %f
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
        inputAnisotropyVolume: (an existing file name)
                Required: input anisotropy image file name
                flag: --inputAnisotropyVolume %s
        inputStartingSeedsLabelMapVolume: (an existing file name)
                Required: input starting seeds LabelMap image file name
                flag: --inputStartingSeedsLabelMapVolume %s
        inputTensorVolume: (an existing file name)
                Required: input tensor image file name
                flag: --inputTensorVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputCostVolume: (a boolean or a file name)
                Output vcl_cost image
                flag: --outputCostVolume %s
        outputSpeedVolume: (a boolean or a file name)
                Output speed image
                flag: --outputSpeedVolume %s
        seedThreshold: (a float)
                Anisotropy threshold used for seed selection
                flag: --seedThreshold %f
        startingSeedsLabel: (an integer (int or long))
                Label value for Starting Seeds
                flag: --startingSeedsLabel %d
        stoppingValue: (a float)
                Terminiating value for vcl_cost function estimation
                flag: --stoppingValue %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputCostVolume: (an existing file name)
                Output vcl_cost image
        outputSpeedVolume: (an existing file name)
                Output speed image

.. _nipype.interfaces.semtools.diffusion.gtract.gtractCreateGuideFiber:


.. index:: gtractCreateGuideFiber

gtractCreateGuideFiber
----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L346>`__

Wraps command ** gtractCreateGuideFiber **

title: Create Guide Fiber

category: Diffusion.GTRACT

description: This program will create a guide fiber by averaging fibers from a previously generated tract.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
        inputFiber: (an existing file name)
                Required: input fiber tract file name
                flag: --inputFiber %s
        numberOfPoints: (an integer (int or long))
                Number of points in output guide fiber
                flag: --numberOfPoints %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputFiber: (a boolean or a file name)
                Required: output guide fiber file name
                flag: --outputFiber %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        writeXMLPolyDataFile: (a boolean)
                Flag to make use of XML files when reading and writing vtkPolyData.
                flag: --writeXMLPolyDataFile

Outputs::

        outputFiber: (an existing file name)
                Required: output guide fiber file name

.. _nipype.interfaces.semtools.diffusion.gtract.gtractFastMarchingTracking:


.. index:: gtractFastMarchingTracking

gtractFastMarchingTracking
--------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L629>`__

Wraps command ** gtractFastMarchingTracking **

title: Fast Marching Tracking

category: Diffusion.GTRACT

description: This program will use a fast marching fiber tracking algorithm to identify fiber tracts from a tensor image. This program is the second portion of the algorithm. The user must first run gtractCostFastMarching to generate the vcl_cost image. The second step of the algorithm implemented here is a gradient descent soplution from the defined ending region back to the seed points specified in gtractCostFastMarching. This algorithm is roughly based on the work by G. Parker et al. from IEEE Transactions On Medical Imaging, 21(5): 505-512, 2002. An additional feature of including anisotropy into the vcl_cost function calculation is included.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris. The original code here was developed by Daisy Espino.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        costStepSize: (a float)
                Cost image sub-voxel sampling
                flag: --costStepSize %f
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputAnisotropyVolume: (an existing file name)
                Required: input anisotropy image file name
                flag: --inputAnisotropyVolume %s
        inputCostVolume: (an existing file name)
                Required: input vcl_cost image file name
                flag: --inputCostVolume %s
        inputStartingSeedsLabelMapVolume: (an existing file name)
                Required: input starting seeds LabelMap image file name
                flag: --inputStartingSeedsLabelMapVolume %s
        inputTensorVolume: (an existing file name)
                Required: input tensor image file name
                flag: --inputTensorVolume %s
        maximumStepSize: (a float)
                Maximum step size to move when tracking
                flag: --maximumStepSize %f
        minimumStepSize: (a float)
                Minimum step size to move when tracking
                flag: --minimumStepSize %f
        numberOfIterations: (an integer (int or long))
                Number of iterations used for the optimization
                flag: --numberOfIterations %d
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputTract: (a boolean or a file name)
                Required: name of output vtkPolydata file containing tract lines and
                the point data collected along them.
                flag: --outputTract %s
        seedThreshold: (a float)
                Anisotropy threshold used for seed selection
                flag: --seedThreshold %f
        startingSeedsLabel: (an integer (int or long))
                Label value for Starting Seeds
                flag: --startingSeedsLabel %d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        trackingThreshold: (a float)
                Anisotropy threshold used for fiber tracking
                flag: --trackingThreshold %f
        writeXMLPolyDataFile: (a boolean)
                Flag to make use of the XML format for vtkPolyData fiber tracts.
                flag: --writeXMLPolyDataFile

Outputs::

        outputTract: (an existing file name)
                Required: name of output vtkPolydata file containing tract lines and
                the point data collected along them.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractFiberTracking:


.. index:: gtractFiberTracking

gtractFiberTracking
-------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L883>`__

Wraps command ** gtractFiberTracking **

title: Fiber Tracking

category: Diffusion.GTRACT

description: This program implements four fiber tracking methods (Free, Streamline, GraphSearch, Guided). The output of the fiber tracking is vtkPolyData (i.e. Polylines) that can be loaded into Slicer3 for visualization. The poly data can be saved in either old VTK format files (.vtk) or in the new VTK XML format (.xml). The polylines contain point data that defines ther Tensor at each point along the fiber tract. This can then be used to rendered as glyphs in Slicer3 and can be used to define severeal scalar measures without referencing back to the anisotropy images. (1) Free tracking is a basic streamlines algorithm. This is a direct implementation of the method original proposed by Basser et al. The tracking follows the primarty eigenvector. The tracking begins with seed points in the starting region. Only those voxels above the specified anisotropy threshold in the starting region are used as seed points. Tracking terminates either as a result of maximum fiber length, low ansiotropy, or large curvature. This is a great way to explore your data. (2) The streamlines algorithm is a direct implementation of the method originally proposed by Basser et al. The tracking follows the primary eigenvector. The tracking begins with seed points in the starting region. Only those voxels above the specified anisotropy threshold in the starting region are used as seed points. Tracking terminates either by reaching the ending region or reaching some stopping criteria. Stopping criteria are specified using the following parameters: tracking threshold, curvature threshold, and max length. Only paths terminating in the ending region are kept in this method. The TEND algorithm proposed by Lazar et al. (Human Brain Mapping 18:306-321, 2003) has been instrumented. This can be enabled using the --useTend option while performing Streamlines tracking. This utilizes the entire diffusion tensor to deflect the incoming vector instead of simply following the primary eigenvector. The TEND parameters are set using the --tendF and --tendG options. (3) Graph Search tracking is the first step in the full GTRACT algorithm developed by Cheng et al. (NeuroImage 31(3): 1075-1085, 2006) for finding the tracks in a tensor image. This method was developed to generate fibers in a Tensor representation where crossing fibers occur. The graph search algorithm follows the primary eigenvector in non-ambigous regions and utilizes branching and a graph search algorithm in ambigous regions. Ambiguous tracking regions are defined based on two criteria: Branching Al Threshold (anisotropy values below this value and above the traching threshold) and Curvature Major Eigen (angles of the primary eigenvector direction and the current tracking direction). In regions that meet this criteria, two or three tracking paths are considered. The first is the standard primary eigenvector direction. The second is the seconadary eigenvector direction. This is based on the assumption that these regions may be prolate regions. If the Random Walk option is selected then a third direction is also considered. This direction is defined by a cone pointing from the current position to the centroid of the ending region. The interior angle of the cone is specified by the user with the Branch/Guide Angle parameter. A vector contained inside of the cone is selected at random and used as the third direction. This method can also utilize the TEND option where the primary tracking direction is that specified by the TEND method instead of the primary eigenvector. The parameter '--maximumBranchPoints' allows the tracking to have this number of branches being considered at a time. If this number of branch points is exceeded at any time, then the algorithm will revert back to a streamline alogrithm until the number of branches is reduced. This allows the user to constrain the computational complexity of the algorithm. (4) The second phase of the GTRACT algorithm is Guided Tracking. This method incorporates anatomical information about the track orientation using an initial guess of the fiber track. In the originally proposed GTRACT method, this would be created from the fibers resulting from the Graph Search tracking. However, in practice this can be created using any method and could be defined manually. To create the guide fiber the program gtractCreateGuideFiber can be used. This program will load a fiber tract that has been generated and create a centerline representation of the fiber tract (i.e. a single fiber). In this method, the fiber tracking follows the primary eigenvector direction unless it deviates from the guide fiber track by a angle greater than that specified by the '--guidedCurvatureThreshold' parameter. The user must specify the guide fiber when running this program.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta, Greg Harris and Yongqiang Zhao.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        branchingAngle: (a float)
                Branching angle in degrees (recommended for GraphSearch fiber
                tracking method)
                flag: --branchingAngle %f
        branchingThreshold: (a float)
                Anisotropy Branching threshold (recommended for GraphSearch fiber
                tracking method)
                flag: --branchingThreshold %f
        curvatureThreshold: (a float)
                Curvature threshold in degrees (recommended for Free fiber tracking)
                flag: --curvatureThreshold %f
        endingSeedsLabel: (an integer (int or long))
                Label value for Ending Seeds (required if Label number used to
                create seed point in Slicer was not 1)
                flag: --endingSeedsLabel %d
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        guidedCurvatureThreshold: (a float)
                Guided Curvature Threshold (Degrees)
                flag: --guidedCurvatureThreshold %f
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputAnisotropyVolume: (an existing file name)
                Required (for Free, Streamline, GraphSearch, and Guided fiber
                tracking methods): input anisotropy image file name
                flag: --inputAnisotropyVolume %s
        inputEndingSeedsLabelMapVolume: (an existing file name)
                Required (for Streamline, GraphSearch, and Guided fiber tracking
                methods): input ending seeds LabelMap image file name
                flag: --inputEndingSeedsLabelMapVolume %s
        inputStartingSeedsLabelMapVolume: (an existing file name)
                Required (for Free, Streamline, GraphSearch, and Guided fiber
                tracking methods): input starting seeds LabelMap image file name
                flag: --inputStartingSeedsLabelMapVolume %s
        inputTensorVolume: (an existing file name)
                Required (for Free, Streamline, GraphSearch, and Guided fiber
                tracking methods): input tensor image file name
                flag: --inputTensorVolume %s
        inputTract: (an existing file name)
                Required (for Guided fiber tracking method): guide fiber in
                vtkPolydata file containing one tract line.
                flag: --inputTract %s
        maximumBranchPoints: (an integer (int or long))
                Maximum branch points (recommended for GraphSearch fiber tracking
                method)
                flag: --maximumBranchPoints %d
        maximumGuideDistance: (a float)
                Maximum distance for using the guide fiber direction
                flag: --maximumGuideDistance %f
        maximumLength: (a float)
                Maximum fiber length (voxels)
                flag: --maximumLength %f
        minimumLength: (a float)
                Minimum fiber length. Helpful for filtering invalid tracts.
                flag: --minimumLength %f
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputTract: (a boolean or a file name)
                Required (for Free, Streamline, GraphSearch, and Guided fiber
                tracking methods): name of output vtkPolydata file containing tract
                lines and the point data collected along them.
                flag: --outputTract %s
        randomSeed: (an integer (int or long))
                Random number generator seed
                flag: --randomSeed %d
        seedThreshold: (a float)
                Anisotropy threshold for seed selection (recommended for Free fiber
                tracking)
                flag: --seedThreshold %f
        startingSeedsLabel: (an integer (int or long))
                Label value for Starting Seeds (required if Label number used to
                create seed point in Slicer was not 1)
                flag: --startingSeedsLabel %d
        stepSize: (a float)
                Fiber tracking step size
                flag: --stepSize %f
        tendF: (a float)
                Tend F parameter
                flag: --tendF %f
        tendG: (a float)
                Tend G parameter
                flag: --tendG %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        trackingMethod: ('Guided' or 'Free' or 'Streamline' or 'GraphSearch')
                Fiber tracking Filter Type: Guided|Free|Streamline|GraphSearch
                flag: --trackingMethod %s
        trackingThreshold: (a float)
                Anisotropy threshold for fiber tracking (anisotropy values of the
                next point along the path)
                flag: --trackingThreshold %f
        useLoopDetection: (a boolean)
                Flag to make use of loop detection.
                flag: --useLoopDetection
        useRandomWalk: (a boolean)
                Flag to use random walk.
                flag: --useRandomWalk
        useTend: (a boolean)
                Flag to make use of Tend F and Tend G parameters.
                flag: --useTend
        writeXMLPolyDataFile: (a boolean)
                Flag to make use of the XML format for vtkPolyData fiber tracts.
                flag: --writeXMLPolyDataFile

Outputs::

        outputTract: (an existing file name)
                Required (for Free, Streamline, GraphSearch, and Guided fiber
                tracking methods): name of output vtkPolydata file containing tract
                lines and the point data collected along them.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractImageConformity:


.. index:: gtractImageConformity

gtractImageConformity
---------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L539>`__

Wraps command ** gtractImageConformity **

title: Image Conformity

category: Diffusion.GTRACT

description: This program will straighten out the Direction and Origin to match the Reference Image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
        inputReferenceVolume: (an existing file name)
                Required: input file containing the standard image to clone the
                characteristics of.
                flag: --inputReferenceVolume %s
        inputVolume: (an existing file name)
                Required: input file containing the signed short image to reorient
                without resampling.
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: name of output Nrrd or Nifti file containing the
                reoriented image in reference image space.
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: name of output Nrrd or Nifti file containing the
                reoriented image in reference image space.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractInvertBSplineTransform:


.. index:: gtractInvertBSplineTransform

gtractInvertBSplineTransform
----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L59>`__

Wraps command ** gtractInvertBSplineTransform **

title: B-Spline Transform Inversion

category: Diffusion.GTRACT

description: This program will invert a B-Spline transform using a thin-plate spline approximation.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
        inputReferenceVolume: (an existing file name)
                Required: input image file name to exemplify the anatomical space to
                interpolate over.
                flag: --inputReferenceVolume %s
        inputTransform: (an existing file name)
                Required: input B-Spline transform file name
                flag: --inputTransform %s
        landmarkDensity: (a list of items which are an integer (int or long))
                Number of landmark subdivisions in all 3 directions
                flag: --landmarkDensity %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputTransform: (a boolean or a file name)
                Required: output transform file name
                flag: --outputTransform %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputTransform: (an existing file name)
                Required: output transform file name

.. _nipype.interfaces.semtools.diffusion.gtract.gtractInvertDisplacementField:


.. index:: gtractInvertDisplacementField

gtractInvertDisplacementField
-----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L668>`__

Wraps command ** gtractInvertDisplacementField **

title: Invert Displacement Field

category: Diffusion.GTRACT

description: This program will invert a deformatrion field. The size of the deformation field is defined by an example image provided by the user

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        baseImage: (an existing file name)
                Required: base image used to define the size of the inverse field
                flag: --baseImage %s
        deformationImage: (an existing file name)
                Required: Displacement field image
                flag: --deformationImage %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: Output deformation field
                flag: --outputVolume %s
        subsamplingFactor: (an integer (int or long))
                Subsampling factor for the deformation field
                flag: --subsamplingFactor %d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: Output deformation field

.. _nipype.interfaces.semtools.diffusion.gtract.gtractInvertRigidTransform:


.. index:: gtractInvertRigidTransform

gtractInvertRigidTransform
--------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L501>`__

Wraps command ** gtractInvertRigidTransform **

title: Rigid Transform Inversion

category: Diffusion.GTRACT

description: This program will invert a Rigid transform.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
        inputTransform: (an existing file name)
                Required: input rigid transform file name
                flag: --inputTransform %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputTransform: (a boolean or a file name)
                Required: output transform file name
                flag: --outputTransform %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputTransform: (an existing file name)
                Required: output transform file name

.. _nipype.interfaces.semtools.diffusion.gtract.gtractResampleAnisotropy:


.. index:: gtractResampleAnisotropy

gtractResampleAnisotropy
------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L229>`__

Wraps command ** gtractResampleAnisotropy **

title: Resample Anisotropy

category: Diffusion.GTRACT

description: This program will resample a floating point image using either the Rigid or B-Spline transform. You may want to save the aligned B0 image after each of the anisotropy map co-registration steps with the anatomical image to check the registration quality with another tool.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
        inputAnatomicalVolume: (an existing file name)
                Required: input file containing the anatomical image whose
                characteristics will be cloned.
                flag: --inputAnatomicalVolume %s
        inputAnisotropyVolume: (an existing file name)
                Required: input file containing the anisotropy image
                flag: --inputAnisotropyVolume %s
        inputTransform: (an existing file name)
                Required: input Rigid OR Bspline transform file name
                flag: --inputTransform %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: name of output NRRD file containing the resampled
                transformed anisotropy image.
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformType: ('Rigid' or 'B-Spline')
                Transform type: Rigid, B-Spline
                flag: --transformType %s

Outputs::

        outputVolume: (an existing file name)
                Required: name of output NRRD file containing the resampled
                transformed anisotropy image.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractResampleB0:


.. index:: gtractResampleB0

gtractResampleB0
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L464>`__

Wraps command ** gtractResampleB0 **

title: Resample B0

category: Diffusion.GTRACT

description: This program will resample a signed short image using either a Rigid or B-Spline transform. The user must specify a template image that will be used to define the origin, orientation, spacing, and size of the resampled image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
        inputAnatomicalVolume: (an existing file name)
                Required: input file containing the anatomical image defining the
                origin, spacing and size of the resampled image (template)
                flag: --inputAnatomicalVolume %s
        inputTransform: (an existing file name)
                Required: input Rigid OR Bspline transform file name
                flag: --inputTransform %s
        inputVolume: (an existing file name)
                Required: input file containing the 4D image
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: name of output NRRD file containing the resampled input
                image.
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformType: ('Rigid' or 'B-Spline')
                Transform type: Rigid, B-Spline
                flag: --transformType %s
        vectorIndex: (an integer (int or long))
                Index in the diffusion weighted image set for the B0 image
                flag: --vectorIndex %d

Outputs::

        outputVolume: (an existing file name)
                Required: name of output NRRD file containing the resampled input
                image.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractResampleCodeImage:


.. index:: gtractResampleCodeImage

gtractResampleCodeImage
-----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L269>`__

Wraps command ** gtractResampleCodeImage **

title: Resample Code Image

category: Diffusion.GTRACT

description: This program will resample a short integer code image using either the Rigid or Inverse-B-Spline transform.  The reference image is the DTI tensor anisotropy image space, and the input code image is in anatomical space.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
        inputCodeVolume: (an existing file name)
                Required: input file containing the code image
                flag: --inputCodeVolume %s
        inputReferenceVolume: (an existing file name)
                Required: input file containing the standard image to clone the
                characteristics of.
                flag: --inputReferenceVolume %s
        inputTransform: (an existing file name)
                Required: input Rigid or Inverse-B-Spline transform file name
                flag: --inputTransform %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: name of output NRRD file containing the resampled code
                image in acquisition space.
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformType: ('Rigid' or 'Affine' or 'B-Spline' or
                 'Inverse-B-Spline' or 'None')
                Transform type: Rigid or Inverse-B-Spline
                flag: --transformType %s

Outputs::

        outputVolume: (an existing file name)
                Required: name of output NRRD file containing the resampled code
                image in acquisition space.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractResampleDWIInPlace:


.. index:: gtractResampleDWIInPlace

gtractResampleDWIInPlace
------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L776>`__

Wraps command ** gtractResampleDWIInPlace **

title: Resample DWI In Place

category: Diffusion.GTRACT

description: Resamples DWI image to structural image.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta, Greg Harris, Hans Johnson, and Joy Matsui.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        debugLevel: (an integer (int or long))
                Display debug messages, and produce debug intermediate results.
                0=OFF, 1=Minimal, 10=Maximum debugging.
                flag: --debugLevel %d
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        imageOutputSize: (a list of items which are an integer (int or long))
                The voxel lattice for the output image, padding is added if
                necessary. NOTE: if 0,0,0, then the inputVolume size is used.
                flag: --imageOutputSize %s
        inputTransform: (an existing file name)
                Required: transform file derived from rigid registration of b0 image
                to reference structural image.
                flag: --inputTransform %s
        inputVolume: (an existing file name)
                Required: input image is a 4D NRRD image.
                flag: --inputVolume %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputResampledB0: (a boolean or a file name)
                Convenience function for extracting the first index location
                (assumed to be the B0)
                flag: --outputResampledB0 %s
        outputVolume: (a boolean or a file name)
                Required: output image (NRRD file) that has been rigidly transformed
                into the space of the structural image and padded if image padding
                was changed from 0,0,0 default.
                flag: --outputVolume %s
        referenceVolume: (an existing file name)
                If provided, resample to the final space of the referenceVolume 3D
                data set.
                flag: --referenceVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        warpDWITransform: (an existing file name)
                Optional: transform file to warp gradient volumes.
                flag: --warpDWITransform %s

Outputs::

        outputResampledB0: (an existing file name)
                Convenience function for extracting the first index location
                (assumed to be the B0)
        outputVolume: (an existing file name)
                Required: output image (NRRD file) that has been rigidly transformed
                into the space of the structural image and padded if image padding
                was changed from 0,0,0 default.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractResampleFibers:


.. index:: gtractResampleFibers

gtractResampleFibers
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L962>`__

Wraps command ** gtractResampleFibers **

title: Resample Fibers

category: Diffusion.GTRACT

description: This program will resample a fiber tract with respect to a pair of deformation fields that represent the forward and reverse deformation fields.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
        inputForwardDeformationFieldVolume: (an existing file name)
                Required: input forward deformation field image file name
                flag: --inputForwardDeformationFieldVolume %s
        inputReverseDeformationFieldVolume: (an existing file name)
                Required: input reverse deformation field image file name
                flag: --inputReverseDeformationFieldVolume %s
        inputTract: (an existing file name)
                Required: name of input vtkPolydata file containing tract lines.
                flag: --inputTract %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputTract: (a boolean or a file name)
                Required: name of output vtkPolydata file containing tract lines and
                the point data collected along them.
                flag: --outputTract %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        writeXMLPolyDataFile: (a boolean)
                Flag to make use of the XML format for vtkPolyData fiber tracts.
                flag: --writeXMLPolyDataFile

Outputs::

        outputTract: (an existing file name)
                Required: name of output vtkPolydata file containing tract lines and
                the point data collected along them.

.. _nipype.interfaces.semtools.diffusion.gtract.gtractTensor:


.. index:: gtractTensor

gtractTensor
------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L1011>`__

Wraps command ** gtractTensor **

title: Tensor Estimation

category: Diffusion.GTRACT

description: This step will convert a b-value averaged diffusion tensor image to a 3x3 tensor voxel image. This step takes the diffusion tensor image data and generates a tensor representation of the data based on the signal intensity decay, b values applied, and the diffusion difrections. The apparent diffusion coefficient for a given orientation is computed on a pixel-by-pixel basis by fitting the image data (voxel intensities) to the Stejskal-Tanner equation. If at least 6 diffusion directions are used, then the diffusion tensor can be computed. This program uses itk::DiffusionTensor3DReconstructionImageFilter. The user can adjust background threshold, median filter, and isotropic resampling.

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta and Greg Harris.

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

Inputs::

        [Mandatory]

        [Optional]
        applyMeasurementFrame: (a boolean)
                Flag to apply the measurement frame to the gradient directions
                flag: --applyMeasurementFrame
        args: (a string)
                Additional parameters to the command
                flag: %s
        b0Index: (an integer (int or long))
                Index in input vector index to extract
                flag: --b0Index %d
        backgroundSuppressingThreshold: (an integer (int or long))
                Image threshold to suppress background. This sets a threshold used
                on the b0 image to remove background voxels from processing.
                Typically, values of 100 and 500 work well for Siemens and GE DTI
                data, respectively. Check your data particularly in the globus
                pallidus to make sure the brain tissue is not being eliminated with
                this threshold.
                flag: --backgroundSuppressingThreshold %d
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignoreIndex: (a list of items which are an integer (int or long))
                Ignore diffusion gradient index. Used to remove specific gradient
                directions with artifacts.
                flag: --ignoreIndex %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                Required: input image 4D NRRD image. Must contain data based on at
                least 6 distinct diffusion directions. The inputVolume is allowed to
                have multiple b0 and gradient direction images. Averaging of the b0
                image is done internally in this step. Prior averaging of the DWIs
                is not required.
                flag: --inputVolume %s
        maskProcessingMode: ('NOMASK' or 'ROIAUTO' or 'ROI')
                ROIAUTO: mask is implicitly defined using a otsu forground and hole
                filling algorithm. ROI: Uses the masks to define what parts of the
                image should be used for computing the transform. NOMASK: no mask
                used
                flag: --maskProcessingMode %s
        maskVolume: (an existing file name)
                Mask Image, if maskProcessingMode is ROI
                flag: --maskVolume %s
        medianFilterSize: (a list of items which are an integer (int or
                 long))
                Median filter radius in all 3 directions
                flag: --medianFilterSize %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Required: name of output NRRD file containing the Tensor vector
                image
                flag: --outputVolume %s
        resampleIsotropic: (a boolean)
                Flag to resample to isotropic voxels. Enabling this feature is
                recommended if fiber tracking will be performed.
                flag: --resampleIsotropic
        size: (a float)
                Isotropic voxel size to resample to
                flag: --size %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: name of output NRRD file containing the Tensor vector
                image

.. _nipype.interfaces.semtools.diffusion.gtract.gtractTransformToDisplacementField:


.. index:: gtractTransformToDisplacementField

gtractTransformToDisplacementField
----------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/gtract.py#L20>`__

Wraps command ** gtractTransformToDisplacementField **

title: Create Displacement Field

category: Diffusion.GTRACT

description: This program will compute forward deformation from the given Transform. The size of the DF is equal to MNI space

version: 4.0.0

documentation-url: http://wiki.slicer.org/slicerWiki/index.php/Modules:GTRACT

license: http://mri.radiology.uiowa.edu/copyright/GTRACT-Copyright.txt

contributor: This tool was developed by Vincent Magnotta, Madhura Ingalhalikar, and Greg Harris

acknowledgements: Funding for this version of the GTRACT program was provided by NIH/NINDS R01NS050568-01A2S1

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
        inputReferenceVolume: (an existing file name)
                Required: input image file name to exemplify the anatomical space
                over which to vcl_express the transform as a displacement field.
                flag: --inputReferenceVolume %s
        inputTransform: (an existing file name)
                Input Transform File Name
                flag: --inputTransform %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputDeformationFieldVolume: (a boolean or a file name)
                Output deformation field
                flag: --outputDeformationFieldVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputDeformationFieldVolume: (an existing file name)
                Output deformation field
