.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.ants.visualization
=============================


.. _nipype.interfaces.ants.visualization.ConvertScalarImageToRGB:


.. index:: ConvertScalarImageToRGB

ConvertScalarImageToRGB
-----------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/ants/visualization.py#L47>`__

Wraps command **ConvertScalarImageToRGB**

Examples
~~~~~~~~
>>> from nipype.interfaces.ants.visualization import ConvertScalarImageToRGB
>>> converter = ConvertScalarImageToRGB()
>>> converter.inputs.dimension = 3
>>> converter.inputs.input_image = 'T1.nii.gz'
>>> converter.inputs.colormap = 'jet'
>>> converter.inputs.minimum_input = 0
>>> converter.inputs.maximum_input = 6
>>> converter.cmdline
'ConvertScalarImageToRGB 3 T1.nii.gz rgb.nii.gz none jet none 0 6 0 255'

Inputs::

        [Mandatory]
        colormap: (a string, nipype default value: )
                Possible colormaps: grey, red, green, blue, copper, jet, hsv,
                spring, summer, autumn, winter, hot, cool, overunder, custom
                flag: %s, position: 4
        dimension: (3 or 2, nipype default value: 3)
                image dimension (2 or 3)
                flag: %d, position: 0
        input_image: (an existing file name)
                Main input is a 3-D grayscale image.
                flag: %s, position: 1
        maximum_input: (an integer (int or long))
                maximum input
                flag: %d, position: 7
        minimum_input: (an integer (int or long))
                minimum input
                flag: %d, position: 6

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        custom_color_map_file: (a string, nipype default value: none)
                custom color map file
                flag: %s, position: 5
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        mask_image: (an existing file name, nipype default value: none)
                mask image
                flag: %s, position: 3
        maximum_RGB_output: (an integer (int or long), nipype default value:
                 255)
                flag: %d, position: 9
        minimum_RGB_output: (an integer (int or long), nipype default value:
                 0)
                flag: %d, position: 8
        num_threads: (an integer (int or long), nipype default value: 1)
                Number of ITK threads to use
        output_image: (a string, nipype default value: rgb.nii.gz)
                rgb output image
                flag: %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        output_image: (an existing file name)
                converted RGB image

.. _nipype.interfaces.ants.visualization.CreateTiledMosaic:


.. index:: CreateTiledMosaic

CreateTiledMosaic
-----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/ants/visualization.py#L126>`__

Wraps command **CreateTiledMosaic**

The program CreateTiledMosaic in conjunction with ConvertScalarImageToRGB
provides useful functionality for common image analysis tasks. The basic
usage of CreateTiledMosaic is to tile a 3-D image volume slice-wise into
a 2-D image.

Examples
~~~~~~~~

>>> from nipype.interfaces.ants.visualization import CreateTiledMosaic
>>> mosaic_slicer = CreateTiledMosaic()
>>> mosaic_slicer.inputs.input_image = 'T1.nii.gz'
>>> mosaic_slicer.inputs.rgb_image = 'rgb.nii.gz'
>>> mosaic_slicer.inputs.mask_image = 'mask.nii.gz'
>>> mosaic_slicer.inputs.output_image = 'output.png'
>>> mosaic_slicer.inputs.alpha_value = 0.5
>>> mosaic_slicer.inputs.direction = 2
>>> mosaic_slicer.inputs.pad_or_crop = '[ -15x -50 , -15x -30 ,0]'
>>> mosaic_slicer.inputs.slices = '[2 ,100 ,160]'
>>> mosaic_slicer.cmdline
'CreateTiledMosaic -a 0.50 -d 2 -i T1.nii.gz -x mask.nii.gz -o output.png -p [ -15x -50 , -15x -30 ,0] -r rgb.nii.gz -s [2 ,100 ,160]'

Inputs::

        [Mandatory]
        input_image: (an existing file name)
                Main input is a 3-D grayscale image.
                flag: -i %s
        rgb_image: (an existing file name)
                An optional Rgb image can be added as an overlay.It must have the
                same imagegeometry as the input grayscale image.
                flag: -r %s

        [Optional]
        alpha_value: (a float)
                If an Rgb image is provided, render the overlay using the specified
                alpha parameter.
                flag: -a %.2f
        args: (a string)
                Additional parameters to the command
                flag: %s
        direction: (an integer (int or long))
                Specifies the direction of the slices. If no direction is specified,
                the direction with the coarsest spacing is chosen.
                flag: -d %d
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        flip_slice: (a string)
                flipXxflipY
                flag: -f %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        mask_image: (an existing file name)
                Specifies the ROI of the RGB voxels used.
                flag: -x %s
        num_threads: (an integer (int or long), nipype default value: 1)
                Number of ITK threads to use
        output_image: (a string, nipype default value: output.png)
                The output consists of the tiled mosaic image.
                flag: -o %s
        pad_or_crop: (a string)
                argument passed to -p flag:[padVoxelWidth,<constantValue=0>][lowerPa
                dding[0]xlowerPadding[1],upperPadding[0]xupperPadding[1],constantVal
                ue]The user can specify whether to pad or crop a specified voxel-
                width boundary of each individual slice. For this program, cropping
                is simply padding with negative voxel-widths.If one pads (+), the
                user can also specify a constant pad value (default = 0). If a mask
                is specified, the user can use the mask to define the region, by
                using the keyword "mask" plus an offset, e.g. "-p mask+3".
                flag: -p %s
        permute_axes: (a boolean)
                doPermute
                flag: -g
        slices: (a string)
                Number of slices to increment Slice1xSlice2xSlice3[numberOfSlicesToI
                ncrement,<minSlice=0>,<maxSlice=lastSlice>]
                flag: -s %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tile_geometry: (a string)
                The tile geometry specifies the number of rows and columnsin the
                output image. For example, if the user specifies "5x10", then 5 rows
                by 10 columns of slices are rendered. If R < 0 and C > 0 (or vice
                versa), the negative value is selectedbased on direction.
                flag: -t %s

Outputs::

        output_image: (an existing file name)
                image file
