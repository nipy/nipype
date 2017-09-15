.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.slicer.filtering.resamplescalarvectordwivolume
=========================================================


.. _nipype.interfaces.slicer.filtering.resamplescalarvectordwivolume.ResampleScalarVectorDWIVolume:


.. index:: ResampleScalarVectorDWIVolume

ResampleScalarVectorDWIVolume
-----------------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/slicer/filtering/resamplescalarvectordwivolume.py#L40>`__

Wraps command **ResampleScalarVectorDWIVolume **

title: Resample Scalar/Vector/DWI Volume

category: Filtering

description: This module implements image and vector-image resampling through  the use of itk Transforms.It can also handle diffusion weighted MRI image resampling. "Resampling" is performed in space coordinates, not pixel/grid coordinates. It is quite important to ensure that image spacing is properly set on the images involved. The interpolator is required since the mapping from one space to the other will often require evaluation of the intensity of the image at non-grid positions.

Warning: To resample DWMR Images, use nrrd input and output files.

Warning: Do not use to resample Diffusion Tensor Images, tensors would  not be reoriented

version: 0.1

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/4.1/Modules/ResampleScalarVectorDWIVolume

contributor: Francois Budin (UNC)

acknowledgements: This work is part of the National Alliance for Medical Image Computing (NAMIC), funded by the National Institutes of Health through the NIH Roadmap for Medical Research, Grant U54 EB005149. Information on the National Centers for Biomedical Computing can be obtained from http://nihroadmap.nih.gov/bioinformatics

Inputs::

        [Mandatory]

        [Optional]
        Inverse_ITK_Transformation: (a boolean)
                Inverse the transformation before applying it from output image to
                input image
                flag: --Inverse_ITK_Transformation
        Reference: (an existing file name)
                Reference Volume (spacing,size,orientation,origin)
                flag: --Reference %s
        args: (a string)
                Additional parameters to the command
                flag: %s
        centered_transform: (a boolean)
                Set the center of the transformation to the center of the input
                image
                flag: --centered_transform
        defField: (an existing file name)
                File containing the deformation field (3D vector image containing
                vectors with 3 components)
                flag: --defField %s
        default_pixel_value: (a float)
                Default pixel value for samples falling outside of the input region
                flag: --default_pixel_value %f
        direction_matrix: (a list of items which are a float)
                9 parameters of the direction matrix by rows (ijk to LPS if LPS
                transform, ijk to RAS if RAS transform)
                flag: --direction_matrix %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        hfieldtype: ('displacement' or 'h-Field')
                Set if the deformation field is an h-Field
                flag: --hfieldtype %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        image_center: ('input' or 'output')
                Image to use to center the transform (used only if 'Centered
                Transform' is selected)
                flag: --image_center %s
        inputVolume: (an existing file name)
                Input Volume to be resampled
                flag: %s, position: -2
        interpolation: ('linear' or 'nn' or 'ws' or 'bs')
                Sampling algorithm (linear or nn (nearest neighborhoor), ws
                (WindowedSinc), bs (BSpline) )
                flag: --interpolation %s
        notbulk: (a boolean)
                The transform following the BSpline transform is not set as a bulk
                transform for the BSpline transform
                flag: --notbulk
        number_of_thread: (an integer (int or long))
                Number of thread used to compute the output image
                flag: --number_of_thread %d
        origin: (a list of items which are any value)
                Origin of the output Image
                flag: --origin %s
        outputVolume: (a boolean or a file name)
                Resampled Volume
                flag: %s, position: -1
        rotation_point: (a list of items which are any value)
                Rotation Point in case of rotation around a point (otherwise
                useless)
                flag: --rotation_point %s
        size: (a list of items which are a float)
                Size along each dimension (0 means use input size)
                flag: --size %s
        spaceChange: (a boolean)
                Space Orientation between transform and image is different (RAS/LPS)
                (warning: if the transform is a Transform Node in Slicer3, do not
                select)
                flag: --spaceChange
        spacing: (a list of items which are a float)
                Spacing along each dimension (0 means use input spacing)
                flag: --spacing %s
        spline_order: (an integer (int or long))
                Spline Order
                flag: --spline_order %d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transform: ('rt' or 'a')
                Transform algorithm, rt = Rigid Transform, a = Affine Transform
                flag: --transform %s
        transform_matrix: (a list of items which are a float)
                12 parameters of the transform matrix by rows ( --last 3 being
                translation-- )
                flag: --transform_matrix %s
        transform_order: ('input-to-output' or 'output-to-input')
                Select in what order the transforms are read
                flag: --transform_order %s
        transformationFile: (an existing file name)
                flag: --transformationFile %s
        window_function: ('h' or 'c' or 'w' or 'l' or 'b')
                Window Function , h = Hamming , c = Cosine , w = Welch , l = Lanczos
                , b = Blackman
                flag: --window_function %s

Outputs::

        outputVolume: (an existing file name)
                Resampled Volume
