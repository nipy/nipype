.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.registration.brainsresize
=============================================


.. _nipype.interfaces.semtools.registration.brainsresize.BRAINSResize:


.. index:: BRAINSResize

BRAINSResize
------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/registration/brainsresize.py#L21>`__

Wraps command ** BRAINSResize **

title: Resize Image (BRAINS)

category: Registration

description: This program is useful for downsampling an image by a constant scale factor.

version: 3.0.0

license: https://www.nitrc.org/svn/brains/BuildScripts/trunk/License.txt

contributor: This tool was developed by Hans Johnson.

acknowledgements: The development of this tool was supported by funding from grants NS050568 and NS40068 from the National Institute of Neurological Disorders and Stroke and grants MH31593, MH40856, from the National Institute of Mental Health.

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
                Image To Scale
                flag: --inputVolume %s
        outputVolume: (a boolean or a file name)
                Resulting scaled image
                flag: --outputVolume %s
        pixelType: ('float' or 'short' or 'ushort' or 'int' or 'uint' or
                 'uchar' or 'binary')
                Specifies the pixel type for the input/output images. The 'binary'
                pixel type uses a modified algorithm whereby the image is read in as
                unsigned char, a signed distance map is created, signed distance map
                is resampled, and then a thresholded image of type unsigned char is
                written to disk.
                flag: --pixelType %s
        scaleFactor: (a float)
                The scale factor for the image spacing.
                flag: --scaleFactor %f
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        outputVolume: (an existing file name)
                Resulting scaled image
