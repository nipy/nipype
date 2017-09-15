.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.filtering.featuredetection
==============================================


.. _nipype.interfaces.semtools.filtering.featuredetection.CannyEdge:


.. index:: CannyEdge

CannyEdge
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L631>`__

Wraps command ** CannyEdge **

title: Canny Edge Detection

category: Filtering.FeatureDetection

description: Get the distance from a voxel to the nearest voxel of a given tissue type.

version: 0.1.0.(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was written by Hans J. Johnson.

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
                Required: input tissue label image
                flag: --inputVolume %s
        lowerThreshold: (a float)
                Threshold is the lowest allowed value in the output image. Its data
                type is the same as the data type of the output image. Any values
                below the Threshold level will be replaced with the OutsideValue
                parameter value, whose default is zero.
                flag: --lowerThreshold %f
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        upperThreshold: (a float)
                Threshold is the lowest allowed value in the output image. Its data
                type is the same as the data type of the output image. Any values
                below the Threshold level will be replaced with the OutsideValue
                parameter value, whose default is zero.
                flag: --upperThreshold %f
        variance: (a float)
                Variance and Maximum error are used in the Gaussian smoothing of the
                input image. See itkDiscreteGaussianImageFilter for information on
                these parameters.
                flag: --variance %f

Outputs::

        outputVolume: (an existing file name)
                Required: output image

.. _nipype.interfaces.semtools.filtering.featuredetection.CannySegmentationLevelSetImageFilter:


.. index:: CannySegmentationLevelSetImageFilter

CannySegmentationLevelSetImageFilter
------------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L61>`__

Wraps command ** CannySegmentationLevelSetImageFilter **

title: Canny Level Set Image Filter

category: Filtering.FeatureDetection

description: The CannySegmentationLevelSet is commonly used to refine a manually generated manual mask.

version: 0.3.0

license: CC

contributor: Regina Kim

acknowledgements: This command module was derived from Insight/Examples/Segmentation/CannySegmentationLevelSetImageFilter.cxx (copyright) Insight Software Consortium.  See http://wiki.na-mic.org/Wiki/index.php/Slicer3:Execution_Model_Documentation for more detailed descriptions.

Inputs::

        [Mandatory]

        [Optional]
        advectionWeight: (a float)
                Controls the smoothness of the resulting mask, small number are more
                smooth, large numbers allow more sharp corners.
                flag: --advectionWeight %f
        args: (a string)
                Additional parameters to the command
                flag: %s
        cannyThreshold: (a float)
                Canny Threshold Value
                flag: --cannyThreshold %f
        cannyVariance: (a float)
                Canny variance
                flag: --cannyVariance %f
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        initialModel: (an existing file name)
                flag: --initialModel %s
        initialModelIsovalue: (a float)
                The identification of the input model iso-surface. (for a binary
                image with 0s and 1s use 0.5) (for a binary image with 0s and 255's
                use 127.5).
                flag: --initialModelIsovalue %f
        inputVolume: (an existing file name)
                flag: --inputVolume %s
        maxIterations: (an integer (int or long))
                The
                flag: --maxIterations %d
        outputSpeedVolume: (a boolean or a file name)
                flag: --outputSpeedVolume %s
        outputVolume: (a boolean or a file name)
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputSpeedVolume: (an existing file name)
        outputVolume: (an existing file name)

.. _nipype.interfaces.semtools.filtering.featuredetection.DilateImage:


.. index:: DilateImage

DilateImage
-----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L97>`__

Wraps command ** DilateImage **

title: Dilate Image

category: Filtering.FeatureDetection

description: Uses mathematical morphology to dilate the input images.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Mark Scully and Jeremy Bockholt.

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
        inputMaskVolume: (an existing file name)
                Required: input brain mask image
                flag: --inputMaskVolume %s
        inputRadius: (an integer (int or long))
                Required: input neighborhood radius
                flag: --inputRadius %d
        inputVolume: (an existing file name)
                Required: input image
                flag: --inputVolume %s
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: output image

.. _nipype.interfaces.semtools.filtering.featuredetection.DilateMask:


.. index:: DilateMask

DilateMask
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L456>`__

Wraps command ** DilateMask **

title: Dilate Image

category: Filtering.FeatureDetection

description: Uses mathematical morphology to dilate the input images.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Mark Scully and Jeremy Bockholt.

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
                Required: input brain mask image
                flag: --inputBinaryVolume %s
        inputVolume: (an existing file name)
                Required: input image
                flag: --inputVolume %s
        lowerThreshold: (a float)
                Required: lowerThreshold value
                flag: --lowerThreshold %f
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        sizeStructuralElement: (an integer (int or long))
                size of structural element. sizeStructuralElement=1 means that 3x3x3
                structuring element for 3D
                flag: --sizeStructuralElement %d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: output image

.. _nipype.interfaces.semtools.filtering.featuredetection.DistanceMaps:


.. index:: DistanceMaps

DistanceMaps
------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L526>`__

Wraps command ** DistanceMaps **

title: Mauerer Distance

category: Filtering.FeatureDetection

description: Get the distance from a voxel to the nearest voxel of a given tissue type.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Mark Scully and Jeremy Bockholt.

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
        inputLabelVolume: (an existing file name)
                Required: input tissue label image
                flag: --inputLabelVolume %s
        inputMaskVolume: (an existing file name)
                Required: input brain mask image
                flag: --inputMaskVolume %s
        inputTissueLabel: (an integer (int or long))
                Required: input integer value of tissue type used to calculate
                distance
                flag: --inputTissueLabel %d
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: output image

.. _nipype.interfaces.semtools.filtering.featuredetection.DumpBinaryTrainingVectors:


.. index:: DumpBinaryTrainingVectors

DumpBinaryTrainingVectors
-------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L490>`__

Wraps command ** DumpBinaryTrainingVectors **

title: Erode Image

category: Filtering.FeatureDetection

description: Uses mathematical morphology to erode the input images.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Mark Scully and Jeremy Bockholt.

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
        inputHeaderFilename: (an existing file name)
                Required: input header file name
                flag: --inputHeaderFilename %s
        inputVectorFilename: (an existing file name)
                Required: input vector filename
                flag: --inputVectorFilename %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        None

.. _nipype.interfaces.semtools.filtering.featuredetection.ErodeImage:


.. index:: ErodeImage

ErodeImage
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L203>`__

Wraps command ** ErodeImage **

title: Erode Image

category: Filtering.FeatureDetection

description: Uses mathematical morphology to erode the input images.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Mark Scully and Jeremy Bockholt.

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
        inputMaskVolume: (an existing file name)
                Required: input brain mask image
                flag: --inputMaskVolume %s
        inputRadius: (an integer (int or long))
                Required: input neighborhood radius
                flag: --inputRadius %d
        inputVolume: (an existing file name)
                Required: input image
                flag: --inputVolume %s
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: output image

.. _nipype.interfaces.semtools.filtering.featuredetection.FlippedDifference:


.. index:: FlippedDifference

FlippedDifference
-----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L167>`__

Wraps command ** FlippedDifference **

title: Flip Image

category: Filtering.FeatureDetection

description: Difference between an image and the axially flipped version of that image.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Mark Scully and Jeremy Bockholt.

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
        inputMaskVolume: (an existing file name)
                Required: input brain mask image
                flag: --inputMaskVolume %s
        inputVolume: (an existing file name)
                Required: input image
                flag: --inputVolume %s
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: output image

.. _nipype.interfaces.semtools.filtering.featuredetection.GenerateBrainClippedImage:


.. index:: GenerateBrainClippedImage

GenerateBrainClippedImage
-------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L239>`__

Wraps command ** GenerateBrainClippedImage **

title: GenerateBrainClippedImage

category: Filtering.FeatureDetection

description: Automatic FeatureImages using neural networks

version: 1.0

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

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
        inputImg: (an existing file name)
                input volume 1, usally t1 image
                flag: --inputImg %s
        inputMsk: (an existing file name)
                input volume 2, usally t2 image
                flag: --inputMsk %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputFileName: (a boolean or a file name)
                (required) output file name
                flag: --outputFileName %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputFileName: (an existing file name)
                (required) output file name

.. _nipype.interfaces.semtools.filtering.featuredetection.GenerateSummedGradientImage:


.. index:: GenerateSummedGradientImage

GenerateSummedGradientImage
---------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L21>`__

Wraps command ** GenerateSummedGradientImage **

title: GenerateSummedGradient

category: Filtering.FeatureDetection

description: Automatic FeatureImages using neural networks

version: 1.0

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: Greg Harris, Eun Young Kim

Inputs::

        [Mandatory]

        [Optional]
        MaximumGradient: (a boolean)
                If set this flag, it will compute maximum gradient between two input
                volumes instead of sum of it.
                flag: --MaximumGradient
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
        inputVolume1: (an existing file name)
                input volume 1, usally t1 image
                flag: --inputVolume1 %s
        inputVolume2: (an existing file name)
                input volume 2, usally t2 image
                flag: --inputVolume2 %s
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputFileName: (a boolean or a file name)
                (required) output file name
                flag: --outputFileName %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputFileName: (an existing file name)
                (required) output file name

.. _nipype.interfaces.semtools.filtering.featuredetection.GenerateTestImage:


.. index:: GenerateTestImage

GenerateTestImage
-----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L310>`__

Wraps command ** GenerateTestImage **

title: DownSampleImage

category: Filtering.FeatureDetection

description: Down sample image for testing

version: 1.0

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

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
        inputVolume: (an existing file name)
                input volume 1, usally t1 image
                flag: --inputVolume %s
        lowerBoundOfOutputVolume: (a float)
                flag: --lowerBoundOfOutputVolume %f
        outputVolume: (a boolean or a file name)
                (required) output file name
                flag: --outputVolume %s
        outputVolumeSize: (a float)
                output Volume Size
                flag: --outputVolumeSize %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        upperBoundOfOutputVolume: (a float)
                flag: --upperBoundOfOutputVolume %f

Outputs::

        outputVolume: (an existing file name)
                (required) output file name

.. _nipype.interfaces.semtools.filtering.featuredetection.GradientAnisotropicDiffusionImageFilter:


.. index:: GradientAnisotropicDiffusionImageFilter

GradientAnisotropicDiffusionImageFilter
---------------------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L598>`__

Wraps command ** GradientAnisotropicDiffusionImageFilter **

title: GradientAnisopropicDiffusionFilter

category: Filtering.FeatureDetection

description: Image Smoothing using Gradient Anisotropic Diffuesion Filer

contributor: This tool was developed by Eun Young Kim by modifying ITK Example

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        conductance: (a float)
                Conductance for diffusion process
                flag: --conductance %f
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                Required: input image
                flag: --inputVolume %s
        numberOfIterations: (an integer (int or long))
                Optional value for number of Iterations
                flag: --numberOfIterations %d
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        timeStep: (a float)
                Time step for diffusion process
                flag: --timeStep %f

Outputs::

        outputVolume: (an existing file name)
                Required: output image

.. _nipype.interfaces.semtools.filtering.featuredetection.HammerAttributeCreator:


.. index:: HammerAttributeCreator

HammerAttributeCreator
----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L382>`__

Wraps command ** HammerAttributeCreator **

title: HAMMER Feature Vectors

category: Filtering.FeatureDetection

description: Create the feature vectors used by HAMMER.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This was extracted from the Hammer Registration source code, and wrapped up by Hans J. Johnson.

Inputs::

        [Mandatory]

        [Optional]
        Scale: (an integer (int or long))
                Determine Scale of Ball
                flag: --Scale %d
        Strength: (a float)
                Determine Strength of Edges
                flag: --Strength %f
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
        inputCSFVolume: (an existing file name)
                Required: input CSF posterior image
                flag: --inputCSFVolume %s
        inputGMVolume: (an existing file name)
                Required: input grey matter posterior image
                flag: --inputGMVolume %s
        inputWMVolume: (an existing file name)
                Required: input white matter posterior image
                flag: --inputWMVolume %s
        outputVolumeBase: (a string)
                Required: output image base name to be appended for each feature
                vector.
                flag: --outputVolumeBase %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        None

.. _nipype.interfaces.semtools.filtering.featuredetection.NeighborhoodMean:


.. index:: NeighborhoodMean

NeighborhoodMean
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L344>`__

Wraps command ** NeighborhoodMean **

title: Neighborhood Mean

category: Filtering.FeatureDetection

description: Calculates the mean, for the given neighborhood size, at each voxel of the T1, T2, and FLAIR.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Mark Scully and Jeremy Bockholt.

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
        inputMaskVolume: (an existing file name)
                Required: input brain mask image
                flag: --inputMaskVolume %s
        inputRadius: (an integer (int or long))
                Required: input neighborhood radius
                flag: --inputRadius %d
        inputVolume: (an existing file name)
                Required: input image
                flag: --inputVolume %s
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: output image

.. _nipype.interfaces.semtools.filtering.featuredetection.NeighborhoodMedian:


.. index:: NeighborhoodMedian

NeighborhoodMedian
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L273>`__

Wraps command ** NeighborhoodMedian **

title: Neighborhood Median

category: Filtering.FeatureDetection

description: Calculates the median, for the given neighborhood size, at each voxel of the input image.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Mark Scully and Jeremy Bockholt.

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
        inputMaskVolume: (an existing file name)
                Required: input brain mask image
                flag: --inputMaskVolume %s
        inputRadius: (an integer (int or long))
                Required: input neighborhood radius
                flag: --inputRadius %d
        inputVolume: (an existing file name)
                Required: input image
                flag: --inputVolume %s
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: output image

.. _nipype.interfaces.semtools.filtering.featuredetection.STAPLEAnalysis:


.. index:: STAPLEAnalysis

STAPLEAnalysis
--------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L561>`__

Wraps command ** STAPLEAnalysis **

title: Dilate Image

category: Filtering.FeatureDetection

description: Uses mathematical morphology to dilate the input images.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Mark Scully and Jeremy Bockholt.

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
        inputDimension: (an integer (int or long))
                Required: input image Dimension 2 or 3
                flag: --inputDimension %d
        inputLabelVolume: (a list of items which are an existing file name)
                Required: input label volume
                flag: --inputLabelVolume %s...
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: output image

.. _nipype.interfaces.semtools.filtering.featuredetection.TextureFromNoiseImageFilter:


.. index:: TextureFromNoiseImageFilter

TextureFromNoiseImageFilter
---------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L132>`__

Wraps command ** TextureFromNoiseImageFilter **

title: TextureFromNoiseImageFilter

category: Filtering.FeatureDetection

description: Calculate the local noise in an image.

version: 0.1.0.$Revision: 1 $(alpha)

documentation-url: http:://www.na-mic.org/

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Eunyoung Regina Kim

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
        inputRadius: (an integer (int or long))
                Required: input neighborhood radius
                flag: --inputRadius %d
        inputVolume: (an existing file name)
                Required: input image
                flag: --inputVolume %s
        outputVolume: (a boolean or a file name)
                Required: output image
                flag: --outputVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Required: output image

.. _nipype.interfaces.semtools.filtering.featuredetection.TextureMeasureFilter:


.. index:: TextureMeasureFilter

TextureMeasureFilter
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/filtering/featuredetection.py#L419>`__

Wraps command ** TextureMeasureFilter **

title: Canny Level Set Image Filter

category: Filtering.FeatureDetection

description: The CannySegmentationLevelSet is commonly used to refine a manually generated manual mask.

version: 0.3.0

license: CC

contributor: Regina Kim

acknowledgements: This command module was derived from Insight/Examples/Segmentation/CannySegmentationLevelSetImageFilter.cxx (copyright) Insight Software Consortium.  See http://wiki.na-mic.org/Wiki/index.php/Slicer3:Execution_Model_Documentation for more detailed descriptions.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        distance: (an integer (int or long))
                flag: --distance %d
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputMaskVolume: (an existing file name)
                flag: --inputMaskVolume %s
        inputVolume: (an existing file name)
                flag: --inputVolume %s
        insideROIValue: (a float)
                flag: --insideROIValue %f
        outputFilename: (a boolean or a file name)
                flag: --outputFilename %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputFilename: (an existing file name)
