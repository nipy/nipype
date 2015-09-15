.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.mrtrix3.utils
========================


.. _nipype.interfaces.mrtrix3.utils.BrainMask:


.. index:: BrainMask

BrainMask
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/utils.py#L38>`__

Wraps command **dwi2mask**

Convert a mesh surface to a partial volume estimation image


Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> bmsk = mrt.BrainMask()
>>> bmsk.inputs.in_file = 'dwi.mif'
>>> bmsk.cmdline                               # doctest: +ELLIPSIS
'dwi2mask dwi.mif brainmask.mif'
>>> bmsk.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input diffusion weighted images
                flag: %s, position: -2
        out_file: (a file name, nipype default value: brainmask.mif)
                output brain mask
                flag: %s, position: -1

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        bval_scale: ('yes' or 'no')
                specifies whether the b - values should be scaled by the square of
                the corresponding DW gradient norm, as often required for multishell
                or DSI DW acquisition schemes. The default action can also be set in
                the MRtrix config file, under the BValueScaling entry. Valid choices
                are yes / no, true / false, 0 / 1 (default: true).
                flag: -bvalue_scaling %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        grad_file: (an existing file name)
                dw gradient scheme (MRTrix format
                flag: -grad %s
        grad_fsl: (a tuple of the form: (an existing file name, an existing
                 file name))
                (bvecs, bvals) dw gradient scheme (FSL format
                flag: -fslgrad %s %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_bval: (an existing file name)
                bvals file in FSL format
        in_bvec: (an existing file name)
                bvecs file in FSL format
                flag: -fslgrad %s %s
        nthreads: (an integer (int or long))
                number of threads. if zero, the number of available cpus will be
                used
                flag: -nthreads %d
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        out_file: (an existing file name)
                the output response file

.. _nipype.interfaces.mrtrix3.utils.ComputeTDI:


.. index:: ComputeTDI

ComputeTDI
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/utils.py#L291>`__

Wraps command **tckmap**

Use track data as a form of contrast for producing a high-resolution
image.

.. admonition:: References

  * For TDI or DEC TDI: Calamante, F.; Tournier, J.-D.; Jackson, G. D. &
    Connelly, A. Track-density imaging (TDI): Super-resolution white
    matter imaging using whole-brain track-density mapping. NeuroImage,
    2010, 53, 1233-1243

  * If using -contrast length and -stat_vox mean: Pannek, K.; Mathias,
    J. L.; Bigler, E. D.; Brown, G.; Taylor, J. D. & Rose, S. E. The
    average pathlength map: A diffusion MRI tractography-derived index
    for studying brain pathology. NeuroImage, 2011, 55, 133-141

  * If using -dixel option with TDI contrast only: Smith, R.E., Tournier,
    J-D., Calamante, F., Connelly, A. A novel paradigm for automated
    segmentation of very large whole-brain probabilistic tractography
    data sets. In proc. ISMRM, 2011, 19, 673

  * If using -dixel option with any other contrast: Pannek, K., Raffelt,
    D., Salvado, O., Rose, S. Incorporating directional information in
    diffusion tractography derived maps: angular track imaging (ATI).
    In Proc. ISMRM, 2012, 20, 1912

  * If using -tod option: Dhollander, T., Emsell, L., Van Hecke, W., Maes,
    F., Sunaert, S., Suetens, P. Track Orientation Density Imaging (TODI)
    and Track Orientation Distribution (TOD) based tractography.
    NeuroImage, 2014, 94, 312-336

  * If using other contrasts / statistics: Calamante, F.; Tournier, J.-D.;
    Smith, R. E. & Connelly, A. A generalised framework for
    super-resolution track-weighted imaging. NeuroImage, 2012, 59,
    2494-2503

  * If using -precise mapping option: Smith, R. E.; Tournier, J.-D.;
    Calamante, F. & Connelly, A. SIFT: Spherical-deconvolution informed
    filtering of tractograms. NeuroImage, 2013, 67, 298-312 (Appendix 3)



Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> tdi = mrt.ComputeTDI()
>>> tdi.inputs.in_file = 'dti.mif'
>>> tdi.cmdline                               # doctest: +ELLIPSIS
'tckmap dti.mif tdi.mif'
>>> tdi.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input tractography
                flag: %s, position: -2

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        contrast: ('tdi' or 'length' or 'invlength' or 'scalar_map' or
                 'scalar_map_conut' or 'fod_amp' or 'curvature')
                define the desired form of contrast for the output image
                flag: -constrast %s
        data_type: ('float' or 'unsigned int')
                specify output image data type
                flag: -datatype %s
        dixel: (a file name)
                map streamlines todixels within each voxel. Directions are stored
                asazimuth elevation pairs.
                flag: -dixel %s
        ends_only: (a boolean)
                only map the streamline endpoints to the image
                flag: -ends_only
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fwhm_tck: (a float)
                define the statistic for choosing the contribution to be made by
                each streamline as a function of the samples taken along their
                lengths
                flag: -fwhm_tck %f
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_map: (an existing file name)
                provide thescalar image map for generating images with 'scalar_map'
                contrasts, or the SHs image for fod_amp
                flag: -image %s
        map_zero: (a boolean)
                if a streamline has zero contribution based on the contrast &
                statistic, typically it is not mapped; use this option to still
                contribute to the map even if this is the case (these non-
                contributing voxels can then influence the mean value in each voxel
                of the map)
                flag: -map_zero
        max_tod: (an integer (int or long))
                generate a Track Orientation Distribution (TOD) in each voxel.
                flag: -tod %d
        nthreads: (an integer (int or long))
                number of threads. if zero, the number of available cpus will be
                used
                flag: -nthreads %d
        out_file: (a file name, nipype default value: tdi.mif)
                output TDI file
                flag: %s, position: -1
        precise: (a boolean)
                use a more precise streamline mapping strategy, that accurately
                quantifies the length through each voxel (these lengths are then
                taken into account during TWI calculation)
                flag: -precise
        reference: (an existing file name)
                a referenceimage to be used as template
                flag: -template %s
        stat_tck: ('mean' or 'sum' or 'min' or 'max' or 'median' or
                 'mean_nonzero' or 'gaussian' or 'ends_min' or 'ends_mean' or
                 'ends_max' or 'ends_prod')
                define the statistic for choosing the contribution to be made by
                each streamline as a function of the samples taken along their
                lengths.
                flag: -stat_tck %s
        stat_vox: ('sum' or 'min' or 'mean' or 'max')
                define the statistic for choosing the finalvoxel intesities for a
                given contrast
                flag: -stat_vox %s
        tck_weights: (an existing file name)
                specify a text scalar file containing the streamline weights
                flag: -tck_weights_in %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        upsample: (an integer (int or long))
                upsample the tracks by some ratio using Hermite interpolation before
                mappping
                flag: -upsample %d
        use_dec: (a boolean)
                perform mapping in DEC space
                flag: -dec
        vox_size: (a list of items which are an integer (int or long))
                voxel dimensions
                flag: -vox %s

Outputs::

        out_file: (a file name)
                output TDI file

.. _nipype.interfaces.mrtrix3.utils.Generate5tt:


.. index:: Generate5tt

Generate5tt
-----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/utils.py#L128>`__

Wraps command **5ttgen**

Concatenate segmentation results from FSL FAST and FIRST into the 5TT
format required for ACT


Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> seg = mrt.Generate5tt()
>>> seg.inputs.in_fast = ['tpm_00.nii.gz',
...                       'tpm_01.nii.gz', 'tpm_02.nii.gz']
>>> seg.inputs.in_first = 'first_merged.nii.gz'
>>> seg.cmdline                               # doctest: +ELLIPSIS
'5ttgen tpm_00.nii.gz tpm_01.nii.gz tpm_02.nii.gz first_merged.nii.gz act-5tt.mif'
>>> seg.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_fast: (a list of items which are an existing file name)
                list of PVE images from FAST
                flag: %s, position: -3
        out_file: (a file name, nipype default value: act-5tt.mif)
                name of output file
                flag: %s, position: -1

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
        in_first: (an existing file name)
                combined segmentation file from FIRST
                flag: %s, position: -2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        out_file: (an existing file name)
                segmentation for ACT in 5tt format

.. _nipype.interfaces.mrtrix3.utils.Mesh2PVE:


.. index:: Mesh2PVE

Mesh2PVE
--------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/utils.py#L83>`__

Wraps command **mesh2pve**

Convert a mesh surface to a partial volume estimation image


Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> m2p = mrt.Mesh2PVE()
>>> m2p.inputs.in_file = 'surf1.vtk'
>>> m2p.inputs.reference = 'dwi.mif'
>>> m2p.inputs.in_first = 'T1.nii.gz'
>>> m2p.cmdline                               # doctest: +ELLIPSIS
'mesh2pve -first T1.nii.gz surf1.vtk dwi.mif mesh2volume.nii.gz'
>>> m2p.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input mesh
                flag: %s, position: -3
        out_file: (a file name, nipype default value: mesh2volume.nii.gz)
                output file containing SH coefficients
                flag: %s, position: -1
        reference: (an existing file name)
                input reference image
                flag: %s, position: -2

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
        in_first: (an existing file name)
                indicates that the mesh file is provided by FSL FIRST
                flag: -first %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        out_file: (an existing file name)
                the output response file

.. _nipype.interfaces.mrtrix3.utils.TCK2VTK:


.. index:: TCK2VTK

TCK2VTK
-------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/utils.py#L379>`__

Wraps command **tck2vtk**

Convert a track file to a vtk format, cave: coordinates are in XYZ
coordinates not reference

Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> vtk = mrt.TCK2VTK()
>>> vtk.inputs.in_file = 'tracks.tck'
>>> vtk.inputs.reference = 'b0.nii'
>>> vtk.cmdline                               # doctest: +ELLIPSIS
'tck2vtk -image b0.nii tracks.tck tracks.vtk'
>>> vtk.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input tractography
                flag: %s, position: -2

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
        nthreads: (an integer (int or long))
                number of threads. if zero, the number of available cpus will be
                used
                flag: -nthreads %d
        out_file: (a file name, nipype default value: tracks.vtk)
                output VTK file
                flag: %s, position: -1
        reference: (an existing file name)
                if specified, the properties of this image will be used to convert
                track point positions from real (scanner) coordinates into image
                coordinates (in mm).
                flag: -image %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        voxel: (an existing file name)
                if specified, the properties of this image will be used to convert
                track point positions from real (scanner) coordinates into image
                coordinates.
                flag: -image %s

Outputs::

        out_file: (a file name)
                output VTK file

.. _nipype.interfaces.mrtrix3.utils.TensorMetrics:


.. index:: TensorMetrics

TensorMetrics
-------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/mrtrix3/utils.py#L188>`__

Wraps command **tensor2metric**

Compute metrics from tensors


Example
~~~~~~~

>>> import nipype.interfaces.mrtrix3 as mrt
>>> comp = mrt.TensorMetrics()
>>> comp.inputs.in_file = 'dti.mif'
>>> comp.inputs.out_fa = 'fa.mif'
>>> comp.cmdline                               # doctest: +ELLIPSIS
'tensor2metric -fa fa.mif dti.mif'
>>> comp.run()                                 # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input DTI image
                flag: %s, position: -1

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        component: (a list of items which are any value)
                specify the desired eigenvalue/eigenvector(s). Note that several
                eigenvalues can be specified as a number sequence
                flag: -num %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        in_mask: (an existing file name)
                only perform computation within the specified binary brain mask
                image
                flag: -mask %s
        modulate: ('FA' or 'none' or 'eval')
                how to modulate the magnitude of the eigenvectors
                flag: -modulate %s
        out_adc: (a file name)
                output ADC file
                flag: -adc %s
        out_eval: (a file name)
                output selected eigenvalue(s) file
                flag: -value %s
        out_evec: (a file name)
                output selected eigenvector(s) file
                flag: -vector %s
        out_fa: (a file name)
                output FA file
                flag: -fa %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        out_adc: (a file name)
                output ADC file
        out_eval: (a file name)
                output selected eigenvalue(s) file
        out_evec: (a file name)
                output selected eigenvector(s) file
        out_fa: (a file name)
                output FA file
