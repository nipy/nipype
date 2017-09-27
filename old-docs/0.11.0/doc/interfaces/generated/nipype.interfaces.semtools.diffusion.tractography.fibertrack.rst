.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.semtools.diffusion.tractography.fibertrack
=====================================================


.. _nipype.interfaces.semtools.diffusion.tractography.fibertrack.fibertrack:


.. index:: fibertrack

fibertrack
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/semtools/diffusion/tractography/fibertrack.py#L29>`__

Wraps command ** fibertrack **

title: FiberTrack (DTIProcess)

category: Diffusion.Tractography

description: This program implements a simple streamline tractography method based on the principal eigenvector of the tensor field. A fourth order Runge-Kutta integration rule used to advance the streamlines.
As a first parameter you have to input the tensor field (with the --input_tensor_file option). Then the region of interest image file is set with the --input_roi_file. Next you want to set the output fiber file name after the --output_fiber_file option.
You can specify the label value in the input_roi_file with the --target_label, --source_label and  --fobidden_label options. By default target label is 1, source label is 2 and forbidden label is 0. The source label is where the streamlines are seeded, the target label defines the voxels through which the fibers must pass by to be kept in the final fiber file and the forbidden label defines the voxels where the streamlines are stopped if they pass through it. There is also a --whole_brain option which, if enabled, consider both target and source labels of the roi image as target labels and all the voxels of the image are considered as sources.
During the tractography, the --fa_min parameter is used as the minimum value needed at different voxel for the tracking to keep going along a streamline. The --step_size parameter is used for each iteration of the tracking algorithm and defines the length of each step. The --max_angle option defines the maximum angle allowed between two successive segments along the tracked fiber.

version: 1.1.0

documentation-url: http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/DTIProcess

license: Copyright (c)  Casey Goodlett. All rights reserved.
  See http://www.ia.unc.edu/dev/Copyright.htm for details.
     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notices for more information.

contributor: Casey Goodlett

acknowledgements: Hans Johnson(1,3,4); Kent Williams(1); (1=University of Iowa Department of Psychiatry, 3=University of Iowa Department of Biomedical Engineering, 4=University of Iowa Department of Electrical and Computer Engineering) provided conversions to make DTIProcess compatible with Slicer execution, and simplified the stand-alone build requirements by removing the dependancies on boost and a fortran compiler.

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
        forbidden_label: (an integer (int or long))
                Forbidden label
                flag: --forbidden_label %d
        force: (a boolean)
                Ignore sanity checks.
                flag: --force
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        input_roi_file: (an existing file name)
                The filename of the image which contains the labels used for seeding
                and constraining the algorithm.
                flag: --input_roi_file %s
        input_tensor_file: (an existing file name)
                Tensor Image
                flag: --input_tensor_file %s
        max_angle: (a float)
                Maximum angle of change in radians
                flag: --max_angle %f
        min_fa: (a float)
                The minimum FA threshold to continue tractography
                flag: --min_fa %f
        output_fiber_file: (a boolean or a file name)
                The filename for the fiber file produced by the algorithm. This file
                must end in a .fib or .vtk extension for ITK spatial object and
                vtkPolyData formats respectively.
                flag: --output_fiber_file %s
        really_verbose: (a boolean)
                Follow detail of fiber tracking algorithm
                flag: --really_verbose
        source_label: (an integer (int or long))
                The label of voxels in the labelfile to use for seeding
                tractography. One tract is seeded from the center of each voxel with
                this label
                flag: --source_label %d
        step_size: (a float)
                Step size in mm for the tracking algorithm
                flag: --step_size %f
        target_label: (an integer (int or long))
                The label of voxels in the labelfile used to constrain tractography.
                Tracts that do not pass through a voxel with this label are
                rejected. Set this keep all tracts.
                flag: --target_label %d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        verbose: (a boolean)
                produce verbose output
                flag: --verbose
        whole_brain: (a boolean)
                If this option is enabled all voxels in the image are used to seed
                tractography. When this option is enabled both source and target
                labels function as target labels
                flag: --whole_brain

Outputs::

        output_fiber_file: (an existing file name)
                The filename for the fiber file produced by the algorithm. This file
                must end in a .fib or .vtk extension for ITK spatial object and
                vtkPolyData formats respectively.
