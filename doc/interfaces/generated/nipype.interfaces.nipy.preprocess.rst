.. AUTO-GENERATED FILE -- DO NOT EDIT!

interfaces.nipy.preprocess
==========================


.. _nipype.interfaces.nipy.preprocess.ComputeMask:


.. index:: ComputeMask

ComputeMask
-----------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/nipy/preprocess.py#L49>`__

Inputs::

        [Mandatory]
        mean_volume: (an existing file name)
                mean EPI image, used to compute the threshold for the mask

        [Optional]
        M: (a float)
                upper fraction of the histogram to be discarded
        cc: (a boolean)
                Keep only the largest connected component
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        m: (a float)
                lower fraction of the histogram to be discarded
        reference_volume: (an existing file name)
                reference volume used to compute the mask. If none is give, the mean
                volume is used.

Outputs::

        brain_mask: (an existing file name)

.. _nipype.interfaces.nipy.preprocess.FmriRealign4d:


.. index:: FmriRealign4d

FmriRealign4d
-------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/nipy/preprocess.py#L121>`__

Simultaneous motion and slice timing correction algorithm

This interface wraps nipy's FmriRealign4d algorithm [1]_.

Examples
~~~~~~~~
>>> from nipype.interfaces.nipy.preprocess import FmriRealign4d
>>> realigner = FmriRealign4d()
>>> realigner.inputs.in_file = ['functional.nii']
>>> realigner.inputs.tr = 2
>>> realigner.inputs.slice_order = range(0,67)
>>> res = realigner.run() # doctest: +SKIP

References
~~~~~~~~~~
.. [1] Roche A. A four-dimensional registration algorithm with        application to joint correction of motion and slice timing        in fMRI. IEEE Trans Med Imaging. 2011 Aug;30(8):1546-54. DOI_.

.. _DOI: http://dx.doi.org/10.1109/TMI.2011.2131152

Inputs::

        [Mandatory]
        in_file: (a list of items which are an existing file name)
                File to realign
        tr: (a float)
                TR in seconds

        [Optional]
        between_loops: (a list of items which are an integer (int or long),
                 nipype default value: [5])
                loops used to realign different runs
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        loops: (a list of items which are an integer (int or long), nipype
                 default value: [5])
                loops within each run
        slice_order: (a list of items which are an integer (int or long))
                0 based slice order. This would be equivalent to
                enteringnp.argsort(spm_slice_order) for this field. This
                effectsinterleaved acquisition. This field will be deprecated
                infuture Nipy releases and be replaced by actual sliceacquisition
                times.
                requires: time_interp
        speedup: (a list of items which are an integer (int or long), nipype
                 default value: [5])
                successive image sub-sampling factors for acceleration
        start: (a float, nipype default value: 0.0)
                time offset into TR to align slices to
        time_interp: (True)
                Assume smooth changes across time e.g., fmri series. If you don't
                want slice timing correction set this to undefined
                requires: slice_order
        tr_slices: (a float)
                TR slices
                requires: time_interp

Outputs::

        out_file: (a list of items which are an existing file name)
                Realigned files
        par_file: (a list of items which are an existing file name)
                Motion parameter files

.. _nipype.interfaces.nipy.preprocess.SpaceTimeRealigner:


.. index:: SpaceTimeRealigner

SpaceTimeRealigner
------------------

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/nipy/preprocess.py#L239>`__

Simultaneous motion and slice timing correction algorithm

If slice_times is not specified, this algorithm performs spatial motion
correction

This interface wraps nipy's SpaceTimeRealign algorithm [Roche2011]_ or simply the
SpatialRealign algorithm when timing info is not provided.

Examples
~~~~~~~~
>>> from nipype.interfaces.nipy import SpaceTimeRealigner
>>> #Run spatial realignment only
>>> realigner = SpaceTimeRealigner()
>>> realigner.inputs.in_file = ['functional.nii']
>>> res = realigner.run() # doctest: +SKIP

>>> realigner = SpaceTimeRealigner()
>>> realigner.inputs.in_file = ['functional.nii']
>>> realigner.inputs.tr = 2
>>> realigner.inputs.slice_times = range(0, 3, 67)
>>> realigner.inputs.slice_info = 2
>>> res = realigner.run() # doctest: +SKIP


References
~~~~~~~~~~
.. [Roche2011] Roche A. A four-dimensional registration algorithm with        application to joint correction of motion and slice timing        in fMRI. IEEE Trans Med Imaging. 2011 Aug;30(8):1546-54. DOI_.

.. _DOI: http://dx.doi.org/10.1109/TMI.2011.2131152

Inputs::

        [Mandatory]
        in_file: (a list of items which are an existing file name)
                File to realign

        [Optional]
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        slice_info: (an integer (int or long) or a list of items which are
                 any value)
                Single integer or length 2 sequence If int, the axis in `images`
                that is the slice axis. In a 4D image, this will often be axis = 2.
                If a 2 sequence, then elements are ``(slice_axis,
                slice_direction)``, where ``slice_axis`` is the slice axis in the
                image as above, and ``slice_direction`` is 1 if the slices were
                acquired slice 0 first, slice -1 last, or -1 if acquired slice -1
                first, slice 0 last. If `slice_info` is an int, assume
                ``slice_direction`` == 1.
                requires: slice_times
        slice_times: (a list of items which are a float or 'asc_alt_2' or
                 'asc_alt_2_1' or 'asc_alt_half' or 'asc_alt_siemens' or 'ascending'
                 or 'desc_alt_2' or 'desc_alt_half' or 'descending')
                Actual slice acquisition times.
        tr: (a float)
                TR in seconds
                requires: slice_times

Outputs::

        out_file: (a list of items which are an existing file name)
                Realigned files
        par_file: (a list of items which are an existing file name)
                Motion parameter files. Angles are not euler angles

.. _nipype.interfaces.nipy.preprocess.Trim:


.. index:: Trim

Trim
----

`Link to code <http://github.com/nipy/nipype/tree/f9c98ba/nipype/interfaces/nipy/preprocess.py#L351>`__

Simple interface to trim a few volumes from a 4d fmri nifti file

Examples
~~~~~~~~
>>> from nipype.interfaces.nipy.preprocess import Trim
>>> trim = Trim()
>>> trim.inputs.in_file = 'functional.nii'
>>> trim.inputs.begin_index = 3 # remove 3 first volumes
>>> res = trim.run() # doctest: +SKIP

Inputs::

        [Mandatory]
        in_file: (an existing file name)
                EPI image to trim

        [Optional]
        begin_index: (an integer (int or long), nipype default value: 0)
                first volume
        end_index: (an integer (int or long), nipype default value: 0)
                last volume indexed as in python (and 0 for last)
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        out_file: (a file name)
                output filename
        suffix: (a string, nipype default value: _trim)
                suffix for out_file to use if no out_file provided

Outputs::

        out_file: (an existing file name)
