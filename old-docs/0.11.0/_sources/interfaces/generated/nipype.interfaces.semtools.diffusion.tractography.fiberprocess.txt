.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.diffusion.tractography.fiberprocess
=======================================================


.. _nipype.interfaces.semtools.diffusion.tractography.fiberprocess.fiberprocess:


.. index:: fiberprocess

fiberprocess
------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/tractography/fiberprocess.py#L32>`__

Wraps command ** fiberprocess **

title: FiberProcess (DTIProcess)

category: Diffusion.Tractography

description: fiberprocess is a tool that manage fiber files extracted from the fibertrack tool or any fiber tracking algorithm. It takes as an input .fib and .vtk files (--fiber_file) and saves the changed fibers (--fiber_output) into the 2 same formats. The main purpose of this tool is to deform the fiber file with a transformation field as an input (--displacement_field or --h_field depending if you deal with dfield or hfield). To use that option you need to specify the tensor field from which the fiber file was extracted with the option --tensor_volume. The transformation applied on the fiber file is the inverse of the one input. If the transformation is from one case to an atlas, fiberprocess assumes that the fiber file is in the atlas space and you want it in the original case space, so it's the inverse of the transformation which has been computed.
You have 2 options for fiber modification. You can either deform the fibers (their geometry) into the space OR you can keep the same geometry but map the diffusion properties (fa, md, lbd's...) of the original tensor field along the fibers at the corresponding locations. This is triggered by the --no_warp option. To use the previous example: when you have a tensor field in the original space and the deformed tensor field in the atlas space, you want to track the fibers in the atlas space, keeping this geometry but with the original case diffusion properties. Then you can specify the transformations field (from original case -> atlas) and the original tensor field with the --tensor_volume option.
With fiberprocess you can also binarize a fiber file. Using the --voxelize option will create an image where each voxel through which a fiber is passing is set to 1. The output is going to be a binary image with the values 0 or 1 by default but the 1 value voxel can be set to any number with the --voxel_label option. Finally you can create an image where the value at the voxel is the number of fiber passing through. (--voxelize_count_fibers)

version: 1.0.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/DTIProcess

license: Copyright (c)  Casey Goodlett. All rights reserved.
    See http://www.ia.unc.edu/dev/Copyright.htm for details.
    This software is distributed WITHOUT ANY WARRANTY; without even
    the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
    PURPOSE.  See the above copyright notices for more information.

contributor: Casey Goodlett

Inputs::

        [Mandatory]

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        displacement_field: (an existing file name)
                Displacement Field for warp and statistics lookup. If this option is
                used tensor-volume must also be specified.
                flag: --displacement_field %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fiber_file: (an existing file name)
                DTI fiber file
                flag: --fiber_file %s
        fiber_output: (a boolean or a file name)
                Output fiber file. May be warped or updated with new data depending
                on other options used.
                flag: --fiber_output %s
        fiber_radius: (a float)
                set radius of all fibers to this value
                flag: --fiber_radius %f
        h_field: (an existing file name)
                HField for warp and statistics lookup. If this option is used
                tensor-volume must also be specified.
                flag: --h_field %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        index_space: (a boolean)
                Use index-space for fiber output coordinates, otherwise us world
                space for fiber output coordinates (from tensor file).
                flag: --index_space
        noDataChange: (a boolean)
                Do not change data ???
                flag: --noDataChange
        no_warp: (a boolean)
                Do not warp the geometry of the tensors only obtain the new
                statistics.
                flag: --no_warp
        saveProperties: (a boolean)
                save the tensor property as scalar data into the vtk (only works for
                vtk fiber files).
                flag: --saveProperties
        tensor_volume: (an existing file name)
                Interpolate tensor values from the given field
                flag: --tensor_volume %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        verbose: (a boolean)
                produce verbose output
                flag: --verbose
        voxel_label: (an integer (int or long))
                Label for voxelized fiber
                flag: --voxel_label %d
        voxelize: (a boolean or a file name)
                Voxelize fiber into a label map (the labelmap filename is the
                argument of -V). The tensor file must be specified using -T for
                information about the size, origin, spacing of the image. The
                deformation is applied before the voxelization
                flag: --voxelize %s
        voxelize_count_fibers: (a boolean)
                Count number of fibers per-voxel instead of just setting to 1
                flag: --voxelize_count_fibers

Outputs::

        fiber_output: (an existing file name)
                Output fiber file. May be warped or updated with new data depending
                on other options used.
        voxelize: (an existing file name)
                Voxelize fiber into a label map (the labelmap filename is the
                argument of -V). The tensor file must be specified using -T for
                information about the size, origin, spacing of the image. The
                deformation is applied before the voxelization
