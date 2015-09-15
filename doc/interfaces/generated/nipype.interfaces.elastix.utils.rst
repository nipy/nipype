.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.elastix.utils
========================


.. _nipype.interfaces.elastix.utils.EditTransform:


.. index:: EditTransform

EditTransform
-------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/elastix/utils.py#L45>`__

Manipulates an existing transform file generated with elastix

Example
~~~~~~~

>>> from nipype.interfaces.elastix import EditTransform
>>> tfm = EditTransform()
>>> tfm.inputs.transform_file = 'TransformParameters.0.txt'
>>> tfm.inputs.reference_image = 'fixed1.nii'
>>> tfm.inputs.output_type = 'unsigned char'
>>> tfm.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        transform_file: (an existing file name)
                transform-parameter file, only 1

        [Optional]
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        interpolation: ('cubic' or 'linear' or 'nearest', nipype default
                 value: cubic)
                set a new interpolator for transformation
                flag: FinalBSplineInterpolationOrder
        output_file: (a file name)
                the filename for the resulting transform file
        output_format: ('nii.gz' or 'nii' or 'mhd' or 'hdr' or 'vtk')
                set a new image format for resampled images
                flag: ResultImageFormat
        output_type: ('float' or 'unsigned char' or 'unsigned short' or
                 'short' or 'unsigned long' or 'long' or 'double')
                set a new output pixel type for resampled images
                flag: ResultImagePixelType
        reference_image: (an existing file name)
                set a new reference image to change the target coordinate system.

Outputs::

        output_file: (an existing file name)
                output transform file
