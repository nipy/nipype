.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.registration.brainsresample
===============================================


.. _nipype.interfaces.semtools.registration.brainsresample.BRAINSResample:


.. index:: BRAINSResample

BRAINSResample
--------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/registration/brainsresample.py#L30>`__

Wraps command ** BRAINSResample **

title: Resample Image (BRAINS)

category: Registration

description: This program collects together three common image processing tasks that all involve resampling an image volume: Resampling to a new resolution and spacing, applying a transformation (using an ITK transform IO mechanisms) and Warping (using a vector image deformation field).  Full documentation available here: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/BRAINSResample.

version: 3.0.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/BRAINSResample

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Vincent Magnotta, Greg Harris, and Hans Johnson.

acknowledgements: The development of this tool was supported by funding from grants NS050568 and NS40068 from the National Institute of Neurological Disorders and Stroke and grants MH31593, MH40856, from the National Institute of Mental Health.

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        defaultValue: (a float)
                Default voxel value
                flag: --defaultValue %f
        deformationVolume: (an existing file name)
                Displacement Field to be used to warp the image (ITKv3 or earlier)
                flag: --deformationVolume %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        gridSpacing: (a list of items which are an integer (int or long))
                Add warped grid to output image to help show the deformation that
                occured with specified spacing. A spacing of 0 in a dimension
                indicates that grid lines should be rendered to fall exactly (i.e.
                do not allow displacements off that plane). This is useful for
                makeing a 2D image of grid lines from the 3D space
                flag: --gridSpacing %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        inputVolume: (an existing file name)
                Image To Warp
                flag: --inputVolume %s
        interpolationMode: ('NearestNeighbor' or 'Linear' or
                 'ResampleInPlace' or 'BSpline' or 'WindowedSinc' or 'Hamming' or
                 'Cosine' or 'Welch' or 'Lanczos' or 'Blackman')
                Type of interpolation to be used when applying transform to moving
                volume. Options are Linear, ResampleInPlace, NearestNeighbor,
                BSpline, or WindowedSinc
                flag: --interpolationMode %s
        inverseTransform: (a boolean)
                True/False is to compute inverse of given transformation. Default is
                false
                flag: --inverseTransform
        numberOfThreads: (an integer (int or long))
                Explicitly specify the maximum number of threads to use.
                flag: --numberOfThreads %d
        outputVolume: (a boolean or a file name)
                Resulting deformed image
                flag: --outputVolume %s
        pixelType: ('float' or 'short' or 'ushort' or 'int' or 'uint' or
                 'uchar' or 'binary')
                Specifies the pixel type for the input/output images. The 'binary'
                pixel type uses a modified algorithm whereby the image is read in as
                unsigned char, a signed distance map is created, signed distance map
                is resampled, and then a thresholded image of type unsigned char is
                written to disk.
                flag: --pixelType %s
        referenceVolume: (an existing file name)
                Reference image used only to define the output space. If not
                specified, the warping is done in the same space as the image to
                warp.
                flag: --referenceVolume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        warpTransform: (an existing file name)
                Filename for the BRAINSFit transform (ITKv3 or earlier) or composite
                transform file (ITKv4)
                flag: --warpTransform %s

Outputs::

        outputVolume: (an existing file name)
                Resulting deformed image
