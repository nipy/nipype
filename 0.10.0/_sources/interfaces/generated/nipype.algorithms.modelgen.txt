.. AUTO-GENERATED FILE -- DO NOT EDIT!

algorithms.modelgen
===================


.. _nipype.algorithms.modelgen.SpecifyModel:


.. index:: SpecifyModel

SpecifyModel
------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/algorithms/modelgen.py#L204>`__

Makes a model specification compatible with spm/fsl designers.

The subject_info field should contain paradigm information in the form of
a Bunch or a list of Bunch. The Bunch should contain the following
information::

 [Mandatory]

 - conditions : list of names
 - onsets : lists of onsets corresponding to each condition
 - durations : lists of durations corresponding to each condition. Should be left to a single 0 if all events are being modelled as impulses.

 [Optional]
 - regressor_names : list of str
     list of names corresponding to each column. Should be None if
     automatically assigned.
 - regressors : list of lists
    values for each regressor - must correspond to the number of
    volumes in the functional run
 - amplitudes : lists of amplitudes for each event. This will be ignored by
   SPM's Level1Design.

 The following two (tmod, pmod) will be ignored by any Level1Design class
 other than SPM:

 - tmod : lists of conditions that should be temporally modulated. Should
   default to None if not being used.
 - pmod : list of Bunch corresponding to conditions
   - name : name of parametric modulator
   - param : values of the modulator
   - poly : degree of modulation

Alternatively, you can provide information through event files.

The event files have to be in 1, 2 or 3 column format with the columns
corresponding to Onsets, Durations and Amplitudes and they have to have the
name event_name.runXXX... e.g.: Words.run001.txt. The event_name part will
be used to create the condition names.

Examples
~~~~~~~~

>>> from nipype.interfaces.base import Bunch
>>> s = SpecifyModel()
>>> s.inputs.input_units = 'secs'
>>> s.inputs.functional_runs = ['functional2.nii', 'functional3.nii']
>>> s.inputs.time_repetition = 6
>>> s.inputs.high_pass_filter_cutoff = 128.
>>> info = [Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]], durations=[[1]]),             Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]], durations=[[1]])]
>>> s.inputs.subject_info = info

Using pmod:

>>> info = [Bunch(conditions=['cond1', 'cond2'], onsets=[[2, 50],[100, 180]], durations=[[0],[0]], pmod=[Bunch(name=['amp'], poly=[2], param=[[1, 2]]), None]),         Bunch(conditions=['cond1', 'cond2'], onsets=[[20, 120],[80, 160]], durations=[[0],[0]], pmod=[Bunch(name=['amp'], poly=[2], param=[[1, 2]]), None])]
>>> s.inputs.subject_info = info

Inputs::

        [Mandatory]
        event_files: (a list of items which are an existing file name)
                list of event description files 1, 2 or 3 column format
                corresponding to onsets, durations and amplitudes
                mutually_exclusive: subject_info, event_files
        functional_runs: (a list of items which are an existing file name or
                 an existing file name)
                Data files for model. List of 4D files or list oflist of 3D files
                per session
        high_pass_filter_cutoff: (a float)
                High-pass filter cutoff in secs
        input_units: ('secs' or 'scans')
                Units of event onsets and durations (secs or scans)Output units are
                always in secs
        subject_info
                Bunch or List(Bunch) subject specific condition information. see
                :ref:`SpecifyModel` or SpecifyModel.__doc__ for details
                mutually_exclusive: subject_info, event_files
        time_repetition: (a float)
                Time between the start of one volume to the start of the next image
                volume.

        [Optional]
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        outlier_files: (an existing file name)
                Files containing scan outlier indices that should be tossed
        realignment_parameters: (an existing file name)
                Realignment parameters returned by motion correction algorithm

Outputs::

        session_info
                session info for level1designs

.. _nipype.algorithms.modelgen.SpecifySPMModel:


.. index:: SpecifySPMModel

SpecifySPMModel
---------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/algorithms/modelgen.py#L395>`__

Adds SPM specific options to SpecifyModel

 adds:
   - concatenate_runs
   - output_units

Examples
~~~~~~~~

>>> from nipype.interfaces.base import Bunch
>>> s = SpecifySPMModel()
>>> s.inputs.input_units = 'secs'
>>> s.inputs.output_units = 'scans'
>>> s.inputs.high_pass_filter_cutoff = 128.
>>> s.inputs.functional_runs = ['functional2.nii', 'functional3.nii']
>>> s.inputs.time_repetition = 6
>>> s.inputs.concatenate_runs = True
>>> info = [Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]], durations=[[1]]),             Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]], durations=[[1]])]
>>> s.inputs.subject_info = info

Inputs::

        [Mandatory]
        event_files: (a list of items which are an existing file name)
                list of event description files 1, 2 or 3 column format
                corresponding to onsets, durations and amplitudes
                mutually_exclusive: subject_info, event_files
        functional_runs: (a list of items which are an existing file name or
                 an existing file name)
                Data files for model. List of 4D files or list oflist of 3D files
                per session
        high_pass_filter_cutoff: (a float)
                High-pass filter cutoff in secs
        input_units: ('secs' or 'scans')
                Units of event onsets and durations (secs or scans)Output units are
                always in secs
        subject_info
                Bunch or List(Bunch) subject specific condition information. see
                :ref:`SpecifyModel` or SpecifyModel.__doc__ for details
                mutually_exclusive: subject_info, event_files
        time_repetition: (a float)
                Time between the start of one volume to the start of the next image
                volume.

        [Optional]
        concatenate_runs: (a boolean, nipype default value: False)
                Concatenate all runs to look like a single session.
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        outlier_files: (an existing file name)
                Files containing scan outlier indices that should be tossed
        output_units: ('secs' or 'scans', nipype default value: secs)
                Units of design event onsets and durations (secs or scans)
        realignment_parameters: (an existing file name)
                Realignment parameters returned by motion correction algorithm

Outputs::

        session_info
                session info for level1designs

.. _nipype.algorithms.modelgen.SpecifySparseModel:


.. index:: SpecifySparseModel

SpecifySparseModel
------------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/algorithms/modelgen.py#L531>`__

Specify a sparse model that is compatible with spm/fsl designers

References
~~~~~~~~~~

.. [1] Ghosh et al. (2009) OHBM http://dl.dropbox.com/u/363467/OHBM2009_HRF.pdf

Examples
~~~~~~~~

>>> from nipype.interfaces.base import Bunch
>>> s = SpecifySparseModel()
>>> s.inputs.input_units = 'secs'
>>> s.inputs.functional_runs = ['functional2.nii', 'functional3.nii']
>>> s.inputs.time_repetition = 6
>>> s.inputs.time_acquisition = 2
>>> s.inputs.high_pass_filter_cutoff = 128.
>>> s.inputs.model_hrf = True
>>> info = [Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]], durations=[[1]]),             Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]], durations=[[1]])]
>>> s.inputs.subject_info = info

Inputs::

        [Mandatory]
        event_files: (a list of items which are an existing file name)
                list of event description files 1, 2 or 3 column format
                corresponding to onsets, durations and amplitudes
                mutually_exclusive: subject_info, event_files
        functional_runs: (a list of items which are an existing file name or
                 an existing file name)
                Data files for model. List of 4D files or list oflist of 3D files
                per session
        high_pass_filter_cutoff: (a float)
                High-pass filter cutoff in secs
        input_units: ('secs' or 'scans')
                Units of event onsets and durations (secs or scans)Output units are
                always in secs
        subject_info
                Bunch or List(Bunch) subject specific condition information. see
                :ref:`SpecifyModel` or SpecifyModel.__doc__ for details
                mutually_exclusive: subject_info, event_files
        time_acquisition: (a float)
                Time in seconds to acquire a single image volume
        time_repetition: (a float)
                Time between the start of one volume to the start of the next image
                volume.

        [Optional]
        ignore_exception: (a boolean, nipype default value: False)
                Print an error message instead of throwing an exception in case the
                interface fails to run
        model_hrf: (a boolean)
                model sparse events with hrf
        outlier_files: (an existing file name)
                Files containing scan outlier indices that should be tossed
        realignment_parameters: (an existing file name)
                Realignment parameters returned by motion correction algorithm
        save_plot: (a boolean)
                save plot of sparse design calculation (Requires matplotlib)
        scale_regressors: (a boolean, nipype default value: True)
                Scale regressors by the peak
        scan_onset: (a float, nipype default value: 0.0)
                Start of scanning relative to onset of run in secs
        stimuli_as_impulses: (a boolean, nipype default value: True)
                Treat each stimulus to be impulse like.
        use_temporal_deriv: (a boolean)
                Create a temporal derivative in addition to regular regressor
                requires: model_hrf
        volumes_in_cluster: (an integer >= 1, nipype default value: 1)
                Number of scan volumes in a cluster

Outputs::

        session_info
                session info for level1designs
        sparse_png_file: (a file name)
                PNG file showing sparse design
        sparse_svg_file: (a file name)
                SVG file showing sparse design

.. module:: nipype.algorithms.modelgen


.. _nipype.algorithms.modelgen.gcd:

:func:`gcd`
-----------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/algorithms/modelgen.py#L36>`__



Returns the greatest common divisor of two integers

uses Euclid's algorithm

>>> gcd(4, 5)
~
>>> gcd(4, 8)
~
>>> gcd(22, 55)
~~


.. _nipype.algorithms.modelgen.gen_info:

:func:`gen_info`
----------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/algorithms/modelgen.py#L140>`__



Generate subject_info structure from a list of event files


.. _nipype.algorithms.modelgen.orth:

:func:`orth`
------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/algorithms/modelgen.py#L100>`__



Orthoganlize y_in with respect to x_in

>>> err = np.abs(np.array(orth([1, 2, 3],[4, 5, 6]) - np.array([1.7142857142857144, 0.42857142857142883, -0.85714285714285676])))
>>> all(err<np.finfo(float).eps)
True


.. _nipype.algorithms.modelgen.scale_timings:

:func:`scale_timings`
---------------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/algorithms/modelgen.py#L118>`__



Scales timings given input and output units (scans/secs)

Parameters
~~~~~~~~~~

timelist: list of times to scale
input_units: 'secs' or 'scans'
output_units: Ibid.
time_repetition: float in seconds


.. _nipype.algorithms.modelgen.spm_hrf:

:func:`spm_hrf`
---------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/algorithms/modelgen.py#L53>`__



python implementation of spm_hrf

see spm_hrf for implementation details

% RT   - scan repeat time
% p    - parameters of the response function (two gamma
% functions)
% defaults  (seconds)
%   p(0) - delay of response (relative to onset)       6
%   p(1) - delay of undershoot (relative to onset)    16
%   p(2) - dispersion of response                      1
%   p(3) - dispersion of undershoot                    1
%   p(4) - ratio of response to undershoot             6
%   p(5) - onset (seconds)                             0
%   p(6) - length of kernel (seconds)                 32
~
% hrf  - hemodynamic response function
% p    - parameters of the response function

the following code using scipy.stats.distributions.gamma
doesn't return the same result as the spm_Gpdf function
hrf   = gamma.pdf(u, p[0]/p[2], scale=dt/p[2]) - gamma.pdf(u, p[1]/p[3], scale=dt/p[3])/p[4]

>>> print spm_hrf(2)
[  0.00000000e+00   8.65660810e-02   3.74888236e-01   3.84923382e-01
   2.16117316e-01   7.68695653e-02   1.62017720e-03  -3.06078117e-02
  -3.73060781e-02  -3.08373716e-02  -2.05161334e-02  -1.16441637e-02
  -5.82063147e-03  -2.61854250e-03  -1.07732374e-03  -4.10443522e-04
  -1.46257507e-04]

