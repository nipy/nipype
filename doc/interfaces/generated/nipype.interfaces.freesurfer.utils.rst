.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.freesurfer.utils
===========================


.. _nipype.interfaces.freesurfer.utils.ApplyMask:


.. index:: ApplyMask

ApplyMask
---------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L472>`__

Wraps command **mri_mask**

Use Freesurfer's mri_mask to apply a mask to an image.

The mask file need not be binarized; it can be thresholded above a given
value before application. It can also optionally be transformed into input
space with an LTA matrix.

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input image (will be masked)
                flag: %s, position: -3
        mask_file: (an existing file name)
                image defining mask space
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
        invert_xfm: (a boolean)
                invert transformation
                flag: -invert
        mask_thresh: (a float)
                threshold mask before applying
                flag: -T %.4f
        out_file: (a file name)
                final image to write
                flag: %s, position: -1
        subjects_dir: (an existing directory name)
                subjects directory
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        use_abs: (a boolean)
                take absolute value of mask before applying
                flag: -abs
        xfm_file: (an existing file name)
                LTA-format transformation matrix to align mask with input
                flag: -xform %s
        xfm_source: (an existing file name)
                image defining transform source space
                flag: -lta_src %s
        xfm_target: (an existing file name)
                image defining transform target space
                flag: -lta_dst %s

Outputs::

        out_file: (an existing file name)
                masked image

.. _nipype.interfaces.freesurfer.utils.ExtractMainComponent:


.. index:: ExtractMainComponent

ExtractMainComponent
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L1175>`__

Wraps command **mris_extract_main_component**

Extract the main component of a tesselated surface

Examples
~~~~~~~~

>>> from nipype.interfaces.freesurfer import ExtractMainComponent
>>> mcmp = ExtractMainComponent(in_file='lh.pial')
>>> mcmp.cmdline
'mris_extract_main_component lh.pial lh.maincmp'

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                input surface file
                flag: %s, position: 1

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
        out_file: (a file name)
                surface containing main component
                flag: %s, position: 2
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        out_file: (an existing file name)
                surface containing main component

.. _nipype.interfaces.freesurfer.utils.MRIMarchingCubes:


.. index:: MRIMarchingCubes

MRIMarchingCubes
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L1016>`__

Wraps command **mri_mc**

Uses Freesurfer's mri_mc to create surfaces by tessellating a given input volume

Example
~~~~~~~

>>> import nipype.interfaces.freesurfer as fs
>>> mc = fs.MRIMarchingCubes()
>>> mc.inputs.in_file = 'aseg.mgz'
>>> mc.inputs.label_value = 17
>>> mc.inputs.out_file = 'lh.hippocampus'
>>> mc.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                Input volume to tesselate voxels from.
                flag: %s, position: 1
        label_value: (an integer (int or long))
                Label value which to tesselate from the input volume. (integer, if
                input is "filled.mgz" volume, 127 is rh, 255 is lh)
                flag: %d, position: 2

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        connectivity_value: (an integer (int or long), nipype default value:
                 1)
                Alter the marching cubes connectivity: 1=6+,2=18,3=6,4=26
                (default=1)
                flag: %d, position: -1
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        out_file: (a file name)
                output filename or True to generate one
                flag: ./%s, position: -2
        subjects_dir: (an existing directory name)
                subjects directory
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        surface: (an existing file name)
                binary surface of the tessellation

.. _nipype.interfaces.freesurfer.utils.MRIPretess:


.. index:: MRIPretess

MRIPretess
----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L951>`__

Wraps command **mri_pretess**

Uses Freesurfer's mri_pretess to prepare volumes to be tessellated.

Description
~~~~~~~~~~~

Changes white matter (WM) segmentation so that the neighbors of all
voxels labeled as WM have a face in common - no edges or corners
allowed.

Example
~~~~~~~

>>> import nipype.interfaces.freesurfer as fs
>>> pretess = fs.MRIPretess()
>>> pretess.inputs.in_filled = 'wm.mgz'
>>> pretess.inputs.in_norm = 'norm.mgz'
>>> pretess.inputs.nocorners = True
>>> pretess.cmdline
'mri_pretess -nocorners wm.mgz wm norm.mgz wm_pretesswm.mgz'
>>> pretess.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        in_filled: (an existing file name)
                filled volume, usually wm.mgz
                flag: %s, position: -4
        in_norm: (an existing file name)
                the normalized, brain-extracted T1w image. Usually norm.mgz
                flag: %s, position: -2
        label: (a string or an integer (int or long), nipype default value:
                 wm)
                label to be picked up, can be a Freesurfer's string like 'wm' or a
                label value (e.g. 127 for rh or 255 for lh)
                flag: %s, position: -3

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
        keep: (a boolean)
                keep WM edits
                flag: -keep
        nocorners: (a boolean)
                do not remove corner configurations in addition to edge ones.
                flag: -nocorners
        out_file: (a file name)
                the output file after mri_pretess.
                flag: %s, position: -1
        subjects_dir: (an existing directory name)
                subjects directory
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        test: (a boolean)
                adds a voxel that should be removed by mri_pretess. The value of the
                voxel is set to that of an ON-edited WM, so it should be kept with
                -keep. The output will NOT be saved.
                flag: -test

Outputs::

        out_file: (an existing file name)
                output file after mri_pretess

.. _nipype.interfaces.freesurfer.utils.MRITessellate:


.. index:: MRITessellate

MRITessellate
-------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L890>`__

Wraps command **mri_tessellate**

Uses Freesurfer's mri_tessellate to create surfaces by tessellating a given input volume

Example
~~~~~~~

>>> import nipype.interfaces.freesurfer as fs
>>> tess = fs.MRITessellate()
>>> tess.inputs.in_file = 'aseg.mgz'
>>> tess.inputs.label_value = 17
>>> tess.inputs.out_file = 'lh.hippocampus'
>>> tess.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                Input volume to tesselate voxels from.
                flag: %s, position: -3
        label_value: (an integer (int or long))
                Label value which to tesselate from the input volume. (integer, if
                input is "filled.mgz" volume, 127 is rh, 255 is lh)
                flag: %d, position: -2

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
        out_file: (a file name)
                output filename or True to generate one
                flag: ./%s, position: -1
        subjects_dir: (an existing directory name)
                subjects directory
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        tesselate_all_voxels: (a boolean)
                Tessellate the surface of all voxels with different labels
                flag: -a
        use_real_RAS_coordinates: (a boolean)
                Saves surface with real RAS coordinates where c_(r,a,s) != 0
                flag: -n

Outputs::

        surface: (an existing file name)
                binary surface of the tessellation

.. _nipype.interfaces.freesurfer.utils.MRIsConvert:


.. index:: MRIsConvert

MRIsConvert
-----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L827>`__

Wraps command **mris_convert**

Uses Freesurfer's mris_convert to convert surface files to various formats

Example
~~~~~~~

>>> import nipype.interfaces.freesurfer as fs
>>> mris = fs.MRIsConvert()
>>> mris.inputs.in_file = 'lh.pial'
>>> mris.inputs.out_datatype = 'gii'
>>> mris.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                File to read/convert
                flag: %s, position: -2
        out_datatype: ('ico' or 'tri' or 'stl' or 'vtk' or 'gii' or 'mgh' or
                 'mgz')
                These file formats are supported: ASCII: .ascICO: .ico, .tri GEO:
                .geo STL: .stl VTK: .vtk GIFTI: .gii MGH surface-encoded 'volume':
                .mgh, .mgz

        [Optional]
        annot_file: (an existing file name)
                input is annotation or gifti label data
                flag: --annot %s
        args: (a string)
                Additional parameters to the command
                flag: %s
        dataarray_num: (an integer (int or long))
                if input is gifti, 'num' specifies which data array to use
                flag: --da_num %d
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        functional_file: (an existing file name)
                input is functional time-series or other multi-frame data (must
                specify surface)
                flag: -f %s
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        label_file: (an existing file name)
                infile is .label file, label is name of this label
                flag: --label %s
        labelstats_outfile: (a file name)
                outfile is name of gifti file to which label stats will be written
                flag: --labelstats %s
        normal: (a boolean)
                output is an ascii file where vertex data
                flag: -n
        origname: (a string)
                read orig positions
                flag: -o %s
        out_file: (a file name)
                output filename or True to generate one
                flag: ./%s, position: -1
        parcstats_file: (an existing file name)
                infile is name of text file containing label/val pairs
                flag: --parcstats %s
        patch: (a boolean)
                input is a patch, not a full surface
                flag: -p
        rescale: (a boolean)
                rescale vertex xyz so total area is same as group average
                flag: -r
        scalarcurv_file: (an existing file name)
                input is scalar curv overlay file (must still specify surface)
                flag: -c %s
        scale: (a float)
                scale vertex xyz by scale
                flag: -s %.3f
        subjects_dir: (an existing directory name)
                subjects directory
        talairachxfm_subjid: (a string)
                apply talairach xfm of subject to vertex xyz
                flag: -t %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        vertex: (a boolean)
                Writes out neighbors of a vertex in each row
                flag: -v
        xyz_ascii: (a boolean)
                Print only surface xyz to ascii file
                flag: -a

Outputs::

        converted: (an existing file name)
                converted output surface

.. _nipype.interfaces.freesurfer.utils.MakeAverageSubject:


.. index:: MakeAverageSubject

MakeAverageSubject
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L1143>`__

Wraps command **make_average_subject**

Make an average freesurfer subject

Examples
~~~~~~~~

>>> from nipype.interfaces.freesurfer import MakeAverageSubject
>>> avg = MakeAverageSubject(subjects_ids=['s1', 's2'])
>>> avg.cmdline
'make_average_subject --out average --subjects s1 s2'

Inputs::

        [Mandatory]
        subjects_ids: (a list of items which are a string)
                freesurfer subjects ids to average
                flag: --subjects %s

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
        out_name: (a file name, nipype default value: average)
                name for the average subject
                flag: --out %s
        subjects_dir: (an existing directory name)
                subjects directory
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        average_subject_name: (a string)
                Output registration file

.. _nipype.interfaces.freesurfer.utils.SampleToSurface:


.. index:: SampleToSurface

SampleToSurface
---------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L123>`__

Wraps command **mri_vol2surf**

Sample a volume to the cortical surface using Freesurfer's mri_vol2surf.

You must supply a sampling method, range, and units.  You can project
either a given distance (in mm) or a given fraction of the cortical
thickness at that vertex along the surface normal from the target surface,
and then set the value of that vertex to be either the value at that point
or the average or maximum value found along the projection vector.

By default, the surface will be saved as a vector with a length equal to the
number of vertices on the target surface.  This is not a problem for Freesurfer
programs, but if you intend to use the file with interfaces to another package,
you must set the ``reshape`` input to True, which will factor the surface vector
into a matrix with dimensions compatible with proper Nifti files.

Examples
~~~~~~~~

>>> import nipype.interfaces.freesurfer as fs
>>> sampler = fs.SampleToSurface(hemi="lh")
>>> sampler.inputs.source_file = "cope1.nii.gz"
>>> sampler.inputs.reg_file = "register.dat"
>>> sampler.inputs.sampling_method = "average"
>>> sampler.inputs.sampling_range = 1
>>> sampler.inputs.sampling_units = "frac"
>>> res = sampler.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        hemi: ('lh' or 'rh')
                target hemisphere
                flag: --hemi %s
        mni152reg: (a boolean)
                source volume is in MNI152 space
                flag: --mni152reg
                mutually_exclusive: reg_file, reg_header, mni152reg
        projection_stem: (a string)
                stem for precomputed linear estimates and volume fractions
                mutually_exclusive: sampling_method
        reg_file: (an existing file name)
                source-to-reference registration file
                flag: --reg %s
                mutually_exclusive: reg_file, reg_header, mni152reg
        reg_header: (a boolean)
                register based on header geometry
                flag: --regheader %s
                mutually_exclusive: reg_file, reg_header, mni152reg
                requires: subject_id
        sampling_method: ('point' or 'max' or 'average')
                how to sample -- at a point or at the max or average over a range
                flag: %s
                mutually_exclusive: projection_stem
                requires: sampling_range, sampling_units
        source_file: (an existing file name)
                volume to sample values from
                flag: --mov %s

        [Optional]
        apply_rot: (a tuple of the form: (a float, a float, a float))
                rotation angles (in degrees) to apply to reg matrix
                flag: --rot %.3f %.3f %.3f
        apply_trans: (a tuple of the form: (a float, a float, a float))
                translation (in mm) to apply to reg matrix
                flag: --trans %.3f %.3f %.3f
        args: (a string)
                Additional parameters to the command
                flag: %s
        cortex_mask: (a boolean)
                mask the target surface with hemi.cortex.label
                flag: --cortex
                mutually_exclusive: mask_label
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fix_tk_reg: (a boolean)
                make reg matrix round-compatible
                flag: --fixtkreg
        float2int_method: ('round' or 'tkregister')
                method to convert reg matrix values (default is round)
                flag: --float2int %s
        frame: (an integer (int or long))
                save only one frame (0-based)
                flag: --frame %d
        hits_file: (a boolean or an existing file name)
                save image with number of hits at each voxel
                flag: --srchit %s
        hits_type: ('cor' or 'mgh' or 'mgz' or 'minc' or 'analyze' or
                 'analyze4d' or 'spm' or 'afni' or 'brik' or 'bshort' or 'bfloat' or
                 'sdt' or 'outline' or 'otl' or 'gdf' or 'nifti1' or 'nii' or
                 'niigz')
                hits file type
                flag: --srchit_type
        ico_order: (an integer (int or long))
                icosahedron order when target_subject is 'ico'
                flag: --icoorder %d
                requires: target_subject
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        interp_method: ('nearest' or 'trilinear')
                interpolation method
                flag: --interp %s
        mask_label: (an existing file name)
                label file to mask output with
                flag: --mask %s
                mutually_exclusive: cortex_mask
        no_reshape: (a boolean)
                do not reshape surface vector (default)
                flag: --noreshape
                mutually_exclusive: reshape
        out_file: (a file name)
                surface file to write
                flag: --o %s
        out_type: ('cor' or 'mgh' or 'mgz' or 'minc' or 'analyze' or
                 'analyze4d' or 'spm' or 'afni' or 'brik' or 'bshort' or 'bfloat' or
                 'sdt' or 'outline' or 'otl' or 'gdf' or 'nifti1' or 'nii' or
                 'niigz')
                output file type
                flag: --out_type %s
        override_reg_subj: (a boolean)
                override the subject in the reg file header
                flag: --srcsubject %s
                requires: subject_id
        reference_file: (an existing file name)
                reference volume (default is orig.mgz)
                flag: --ref %s
        reshape: (a boolean)
                reshape surface vector to fit in non-mgh format
                flag: --reshape
                mutually_exclusive: no_reshape
        reshape_slices: (an integer (int or long))
                number of 'slices' for reshaping
                flag: --rf %d
        sampling_range: (a float or a tuple of the form: (a float, a float, a
                 float))
                sampling range - a point or a tuple of (min, max, step)
        sampling_units: ('mm' or 'frac')
                sampling range type -- either 'mm' or 'frac'
        scale_input: (a float)
                multiple all intensities by scale factor
                flag: --scale %.3f
        smooth_surf: (a float)
                smooth output surface (mm fwhm)
                flag: --surf-fwhm %.3f
        smooth_vol: (a float)
                smooth input volume (mm fwhm)
                flag: --fwhm %.3f
        subject_id: (a string)
                subject id
        subjects_dir: (an existing directory name)
                subjects directory
        surf_reg: (a boolean)
                use surface registration to target subject
                flag: --surfreg
                requires: target_subject
        surface: (a string)
                target surface (default is white)
                flag: --surf %s
        target_subject: (a string)
                sample to surface of different subject than source
                flag: --trgsubject %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        vox_file: (a boolean or a file name)
                text file with the number of voxels intersecting the surface
                flag: --nvox %s

Outputs::

        hits_file: (an existing file name)
                image with number of hits at each voxel
        out_file: (an existing file name)
                surface file
        vox_file: (an existing file name)
                text file with the number of voxels intersecting the surface

.. _nipype.interfaces.freesurfer.utils.SmoothTessellation:


.. index:: SmoothTessellation

SmoothTessellation
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L1082>`__

Wraps command **mris_smooth**

This program smooths the tessellation of a surface using 'mris_smooth'

.. seealso::

    SurfaceSmooth() Interface
        For smoothing a scalar field along a surface manifold

Example
~~~~~~~

>>> import nipype.interfaces.freesurfer as fs
>>> smooth = fs.SmoothTessellation()
>>> smooth.inputs.in_file = 'lh.hippocampus.stl'
>>> smooth.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                Input volume to tesselate voxels from.
                flag: %s, position: 1

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        curvature_averaging_iterations: (an integer (int or long), nipype
                 default value: 10)
                Number of curvature averaging iterations (default=10)
                flag: -a %d, position: -1
        disable_estimates: (a boolean)
                Disables the writing of curvature and area estimates
                flag: -nw
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        gaussian_curvature_norm_steps: (an integer (int or long))
                Use Gaussian curvature smoothing
                flag: %d , position: 4
        gaussian_curvature_smoothing_steps: (an integer (int or long))
                Use Gaussian curvature smoothing
                flag: %d, position: 5
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        normalize_area: (a boolean)
                Normalizes the area after smoothing
                flag: -area
        out_area_file: (a file name)
                Write area to ?h.areaname (default "area")
                flag: -b %s
        out_curvature_file: (a file name)
                Write curvature to ?h.curvname (default "curv")
                flag: -c %s
        out_file: (a file name)
                output filename or True to generate one
                flag: %s, position: 2
        smoothing_iterations: (an integer (int or long), nipype default
                 value: 10)
                Number of smoothing iterations (default=10)
                flag: -n %d, position: -2
        snapshot_writing_iterations: (an integer (int or long))
                Write snapshot every "n" iterations
                flag: -w %d
        subjects_dir: (an existing directory name)
                subjects directory
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        use_gaussian_curvature_smoothing: (a boolean)
                Use Gaussian curvature smoothing
                flag: -g, position: 3
        use_momentum: (a boolean)
                Uses momentum
                flag: -m

Outputs::

        surface: (an existing file name)
                Smoothed surface file

.. _nipype.interfaces.freesurfer.utils.Surface2VolTransform:


.. index:: Surface2VolTransform

Surface2VolTransform
--------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L426>`__

Wraps command **mri_surf2vol**

Use FreeSurfer mri_surf2vol to apply a transform.

Examples
~~~~~~~~

>>> from nipype.interfaces.freesurfer import Surface2VolTransform
>>> xfm2vol = Surface2VolTransform()
>>> xfm2vol.inputs.source_file = 'lh.cope1.mgz'
>>> xfm2vol.inputs.reg_file = 'register.mat'
>>> xfm2vol.inputs.hemi = 'lh'
>>> xfm2vol.inputs.template_file = 'cope1.nii.gz'
>>> xfm2vol.inputs.subjects_dir = '.'
>>> xfm2vol.cmdline
'mri_surf2vol --hemi lh --volreg register.mat --surfval lh.cope1.mgz --sd . --template cope1.nii.gz --outvol lh.cope1_asVol.nii --vtxvol lh.cope1_asVol_vertex.nii'
>>> res = xfm2vol.run()# doctest: +SKIP

Inputs::

        [Mandatory]
        hemi: (a string)
                hemisphere of data
                flag: --hemi %s
        reg_file: (an existing file name)
                tkRAS-to-tkRAS matrix (tkregister2 format)
                flag: --volreg %s
                mutually_exclusive: subject_id
        source_file: (an existing file name)
                This is the source of the surface values
                flag: --surfval %s

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
        mkmask: (a boolean)
                make a mask instead of loading surface values
                flag: --mkmask
        projfrac: (a float)
                thickness fraction
                flag: --projfrac %s
        subject_id: (a string)
                subject id
                flag: --identity %s
                mutually_exclusive: reg_file
        subjects_dir: (a string)
                freesurfer subjects directory defaults to $SUBJECTS_DIR
                flag: --sd %s
        surf_name: (a string)
                surfname (default is white)
                flag: --surf %s
        template_file: (an existing file name)
                Output template volume
                flag: --template %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        transformed_file: (a file name)
                Output volume
                flag: --outvol %s
        vertexvol_file: (a file name)
                Path name of the vertex output volume, which is the same as output
                volume except that the value of each voxel is the vertex-id that is
                mapped to that voxel.
                flag: --vtxvol %s

Outputs::

        transformed_file: (an existing file name)
                Path to output file if used normally
        vertexvol_file: (a file name)
                vertex map volume path id. Optional

.. _nipype.interfaces.freesurfer.utils.SurfaceSmooth:


.. index:: SurfaceSmooth

SurfaceSmooth
-------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L246>`__

Wraps command **mri_surf2surf**

Smooth a surface image with mri_surf2surf.

The surface is smoothed by an interative process of averaging the
value at each vertex with those of its adjacent neighbors. You may supply
either the number of iterations to run or a desired effective FWHM of the
smoothing process.  If the latter, the underlying program will calculate
the correct number of iterations internally.

.. seealso::

    SmoothTessellation() Interface
        For smoothing a tessellated surface (e.g. in gifti or .stl)

Examples
~~~~~~~~

>>> import nipype.interfaces.freesurfer as fs
>>> smoother = fs.SurfaceSmooth()
>>> smoother.inputs.in_file = "lh.cope1.mgz"
>>> smoother.inputs.subject_id = "subj_1"
>>> smoother.inputs.hemi = "lh"
>>> smoother.inputs.fwhm = 5
>>> smoother.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        hemi: ('lh' or 'rh')
                hemisphere to operate on
                flag: --hemi %s
        in_file: (a file name)
                source surface file
                flag: --sval %s
        subject_id: (a string)
                subject id of surface file
                flag: --s %s

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        cortex: (a boolean, nipype default value: True)
                only smooth within $hemi.cortex.label
                flag: --cortex
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fwhm: (a float)
                effective FWHM of the smoothing process
                flag: --fwhm %.4f
                mutually_exclusive: smooth_iters
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        out_file: (a file name)
                surface file to write
                flag: --tval %s
        reshape: (a boolean)
                reshape surface vector to fit in non-mgh format
                flag: --reshape
        smooth_iters: (an integer (int or long))
                iterations of the smoothing process
                flag: --smooth %d
                mutually_exclusive: fwhm
        subjects_dir: (an existing directory name)
                subjects directory
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        out_file: (an existing file name)
                smoothed surface file

.. _nipype.interfaces.freesurfer.utils.SurfaceSnapshots:


.. index:: SurfaceSnapshots

SurfaceSnapshots
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L578>`__

Wraps command **tksurfer**

Use Tksurfer to save pictures of the cortical surface.

By default, this takes snapshots of the lateral, medial, ventral,
and dorsal surfaces.  See the ``six_images`` option to add the
anterior and posterior surfaces.

You may also supply your own tcl script (see the Freesurfer wiki for
information on scripting tksurfer). The screenshot stem is set as the
environment variable "_SNAPSHOT_STEM", which you can use in your
own scripts.

Node that this interface will not run if you do not have graphics
enabled on your system.

Examples
~~~~~~~~

>>> import nipype.interfaces.freesurfer as fs
>>> shots = fs.SurfaceSnapshots(subject_id="fsaverage", hemi="lh", surface="pial")
>>> shots.inputs.overlay = "zstat1.nii.gz"
>>> shots.inputs.overlay_range = (2.3, 6)
>>> shots.inputs.overlay_reg = "register.dat"
>>> res = shots.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        hemi: ('lh' or 'rh')
                hemisphere to visualize
                flag: %s, position: 2
        subject_id: (a string)
                subject to visualize
                flag: %s, position: 1
        surface: (a string)
                surface to visualize
                flag: %s, position: 3

        [Optional]
        annot_file: (an existing file name)
                path to annotation file to display
                flag: -annotation %s
                mutually_exclusive: annot_name
        annot_name: (a string)
                name of annotation to display (must be in $subject/label directory
                flag: -annotation %s
                mutually_exclusive: annot_file
        args: (a string)
                Additional parameters to the command
                flag: %s
        colortable: (an existing file name)
                load colortable file
                flag: -colortable %s
        demean_overlay: (a boolean)
                remove mean from overlay
                flag: -zm
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        identity_reg: (a boolean)
                use the identity matrix to register the overlay to the surface
                flag: -overlay-reg-identity
                mutually_exclusive: overlay_reg, identity_reg, mni152_reg
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        invert_overlay: (a boolean)
                invert the overlay display
                flag: -invphaseflag 1
        label_file: (an existing file name)
                path to label file to display
                flag: -label %s
                mutually_exclusive: label_name
        label_name: (a string)
                name of label to display (must be in $subject/label directory
                flag: -label %s
                mutually_exclusive: label_file
        label_outline: (a boolean)
                draw label/annotation as outline
                flag: -label-outline
        label_under: (a boolean)
                draw label/annotation under overlay
                flag: -labels-under
        mni152_reg: (a boolean)
                use to display a volume in MNI152 space on the average subject
                flag: -mni152reg
                mutually_exclusive: overlay_reg, identity_reg, mni152_reg
        orig_suffix: (a string)
                set the orig surface suffix string
                flag: -orig %s
        overlay: (an existing file name)
                load an overlay volume/surface
                flag: -overlay %s
                requires: overlay_range
        overlay_range: (a float or a tuple of the form: (a float, a float) or
                 a tuple of the form: (a float, a float, a float))
                overlay range--either min, (min, max) or (min, mid, max)
                flag: %s
        overlay_range_offset: (a float)
                overlay range will be symettric around offset value
                flag: -foffset %.3f
        overlay_reg: (a file name)
                registration matrix file to register overlay to surface
                flag: -overlay-reg %s
                mutually_exclusive: overlay_reg, identity_reg, mni152_reg
        patch_file: (an existing file name)
                load a patch
                flag: -patch %s
        reverse_overlay: (a boolean)
                reverse the overlay display
                flag: -revphaseflag 1
        screenshot_stem: (a string)
                stem to use for screenshot file names
        show_color_scale: (a boolean)
                display the color scale bar
                flag: -colscalebarflag 1
        show_color_text: (a boolean)
                display text in the color scale bar
                flag: -colscaletext 1
        show_curv: (a boolean)
                show curvature
                flag: -curv
                mutually_exclusive: show_gray_curv
        show_gray_curv: (a boolean)
                show curvature in gray
                flag: -gray
                mutually_exclusive: show_curv
        six_images: (a boolean)
                also take anterior and posterior snapshots
        sphere_suffix: (a string)
                set the sphere.reg suffix string
                flag: -sphere %s
        stem_template_args: (a list of items which are a string)
                input names to use as arguments for a string-formated stem template
                requires: screenshot_stem
        subjects_dir: (an existing directory name)
                subjects directory
        tcl_script: (an existing file name)
                override default screenshot script
                flag: %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        truncate_overlay: (a boolean)
                truncate the overlay display
                flag: -truncphaseflag 1

Outputs::

        snapshots: (a list of items which are an existing file name)
                tiff images of the surface from different perspectives

.. _nipype.interfaces.freesurfer.utils.SurfaceTransform:


.. index:: SurfaceTransform

SurfaceTransform
----------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L331>`__

Wraps command **mri_surf2surf**

Transform a surface file from one subject to another via a spherical registration.

Both the source and target subject must reside in your Subjects Directory,
and they must have been processed with recon-all, unless you are transforming
to one of the icosahedron meshes.

Examples
~~~~~~~~

>>> from nipype.interfaces.freesurfer import SurfaceTransform
>>> sxfm = SurfaceTransform()
>>> sxfm.inputs.source_file = "lh.cope1.nii.gz"
>>> sxfm.inputs.source_subject = "my_subject"
>>> sxfm.inputs.target_subject = "fsaverage"
>>> sxfm.inputs.hemi = "lh"
>>> sxfm.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        hemi: ('lh' or 'rh')
                hemisphere to transform
                flag: --hemi %s
        source_annot_file: (an existing file name)
                surface annotation file
                flag: --sval-annot %s
                mutually_exclusive: source_file
        source_file: (an existing file name)
                surface file with source values
                flag: --sval %s
                mutually_exclusive: source_annot_file
        source_subject: (a string)
                subject id for source surface
                flag: --srcsubject %s
        target_subject: (a string)
                subject id of target surface
                flag: --trgsubject %s

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
        out_file: (a file name)
                surface file to write
                flag: --tval %s
        reshape: (a boolean)
                reshape output surface to conform with Nifti
                flag: --reshape
        reshape_factor: (an integer (int or long))
                number of slices in reshaped image
                flag: --reshape-factor
        source_type: ('cor' or 'mgh' or 'mgz' or 'minc' or 'analyze' or
                 'analyze4d' or 'spm' or 'afni' or 'brik' or 'bshort' or 'bfloat' or
                 'sdt' or 'outline' or 'otl' or 'gdf' or 'nifti1' or 'nii' or
                 'niigz')
                source file format
                flag: --sfmt %s
                requires: source_file
        subjects_dir: (an existing directory name)
                subjects directory
        target_ico_order: (1 or 2 or 3 or 4 or 5 or 6 or 7)
                order of the icosahedron if target_subject is 'ico'
                flag: --trgicoorder %d
        target_type: ('cor' or 'mgh' or 'mgz' or 'minc' or 'analyze' or
                 'analyze4d' or 'spm' or 'afni' or 'brik' or 'bshort' or 'bfloat' or
                 'sdt' or 'outline' or 'otl' or 'gdf' or 'nifti1' or 'nii' or
                 'niigz')
                output format
                flag: --tfmt %s
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored

Outputs::

        out_file: (an existing file name)
                transformed surface file

.. _nipype.interfaces.freesurfer.utils.Tkregister2:


.. index:: Tkregister2

Tkregister2
-----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/freesurfer/utils.py#L1230>`__

Wraps command **tkregister2**

Examples
~~~~~~~~

Get transform matrix between orig (*tkRAS*) and native (*scannerRAS*)
coordinates in Freesurfer. Implements the first step of mapping surfaces
to native space in `this guide
<http://surfer.nmr.mgh.harvard.edu/fswiki/FsAnat-to-NativeAnat>`_.

>>> from nipype.interfaces.freesurfer import Tkregister2
>>> tk2 = Tkregister2(reg_file='T1_to_native.dat')
>>> tk2.inputs.moving_image = 'T1.mgz'
>>> tk2.inputs.target_image = 'structural.nii'
>>> tk2.inputs.reg_header = True
>>> tk2.cmdline
'tkregister2 --mov T1.mgz --noedit --reg T1_to_native.dat --regheader --targ structural.nii'
>>> tk2.run() # doctest: +SKIP

The example below uses tkregister2 without the manual editing
stage to convert FSL-style registration matrix (.mat) to
FreeSurfer-style registration matrix (.dat)

>>> from nipype.interfaces.freesurfer import Tkregister2
>>> tk2 = Tkregister2()
>>> tk2.inputs.moving_image = 'epi.nii'
>>> tk2.inputs.fsl_in_matrix = 'flirt.mat'
>>> tk2.cmdline
'tkregister2 --fsl flirt.mat --mov epi.nii --noedit --reg register.dat'
>>> tk2.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        moving_image: (an existing file name)
                moving volume
                flag: --mov %s
        reg_file: (a file name, nipype default value: register.dat)
                freesurfer-style registration file
                flag: --reg %s

        [Optional]
        args: (a string)
                Additional parameters to the command
                flag: %s
        environ: (a dictionary with keys which are a value of type 'str' and
                 with values which are a value of type 'str', nipype default value:
                 {})
                Environment variables
        fsl_in_matrix: (an existing file name)
                fsl-style registration input matrix
                flag: --fsl %s
        fsl_out: (a file name)
                compute an FSL-compatible resgitration matrix
                flag: --fslregout %s
        fstal: (a boolean)
                set mov to be tal and reg to be tal xfm
                flag: --fstal
                mutually_exclusive: target_image, moving_image
        fstarg: (a boolean)
                use subject's T1 as reference
                flag: --fstarg
                mutually_exclusive: target_image
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        movscale: (a float)
                adjust registration matrix to scale mov
                flag: --movscale %f
        noedit: (a boolean, nipype default value: True)
                do not open edit window (exit)
                flag: --noedit
        reg_header: (a boolean)
                compute regstration from headers
                flag: --regheader
        subject_id: (a string)
                freesurfer subject ID
                flag: --s %s
        subjects_dir: (an existing directory name)
                subjects directory
        target_image: (an existing file name)
                target volume
                flag: --targ %s
                mutually_exclusive: fstarg
        terminal_output: ('stream' or 'allatonce' or 'file' or 'none')
                Control terminal output: `stream` - displays to terminal immediately
                (default), `allatonce` - waits till command is finished to display
                output, `file` - writes output to file, `none` - output is ignored
        xfm: (an existing file name)
                use a matrix in MNI coordinates as initial registration
                flag: --xfm %s

Outputs::

        fsl_file: (a file name)
                FSL-style registration file
        reg_file: (an existing file name)
                freesurfer-style registration file
