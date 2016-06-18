.. _model_spec:

===================================================
 Model Specification for First Level fMRI Analysis
===================================================

Nipype provides a general purpose model specification mechanism with
specialized subclasses for package specific extensions.


General purpose model specification
===================================

The :class:`SpecifyModel` provides a generic mechanism for model
specification. A mandatory input called subject_info provides paradigm
specification for each run corresponding to a subject. This has to be in
the form of a :class:`Bunch` or a list of Bunch objects (one for each
run). Each Bunch object contains the following attribules.

Required for most designs
-------------------------

- conditions : list of names

- onsets : lists of onsets corresponding to each condition

- durations : lists of durations corresponding to each condition. Should be
            left to a single 0 if all events are being modelled as impulses.

Optional
--------

- regressor_names : list of names corresponding to each column. Should be None if  automatically assigned.

- regressors : list of lists. values for each regressor - must correspond to the number of volumes in the functional run

- amplitudes : lists of amplitudes for each event. This will be ignored by
      SPM's Level1Design.

The following two (tmod, pmod) will be ignored by any
Level1Design class other than SPM:

- tmod : lists of conditions that should be temporally modulated. Should
     default to None if not being used.

- pmod : list of Bunch corresponding to conditions
   - name : name of parametric modulator
   - param : values of the modulator
   - poly : degree of modulation


An example Bunch definition::

  from nipype.interfaces.base import Bunch
  condnames = ['Tapping', 'Speaking', 'Yawning']
  event_onsets = [[0, 10, 50], [20, 60, 80], [30, 40, 70]]
  durations = [[0],[0],[0]]

  subject_info = Bunch(conditions=condnames,
                                     onsets = event_onsets,
                                     durations = durations)

Alternatively, you can provide condition, onset, duration and amplitude
information through event files. The event files have to be in 1,2 or 3
column format with the columns corresponding to Onsets, Durations and
Amplitudes and they have to have the name event_name.run<anything else>
e.g.: Words.run001.txt. The event_name part will be used to create the
condition names. Words.run001.txt may look like::

      # Word Onsets Durations
       0   10
       20   10
       ...

or with amplitudes::

       # Word Onsets Durations Amplitudes
       0    10     1
       20   10    1
       ...

Together with this information, one needs to specify:

- whether the durations and event onsets are specified in terms of scan volumes
  or secs.

- the high-pass filter cutoff,

- the repetition time per scan

- functional data files corresponding to each run.

Optionally you can specify realignment parameters, outlier indices.
Outlier files should contain a list of numbers, one per row indicating
which scans should not be included in the analysis. The numbers are
0-based.

SPM specific attributes
=======================

in addition to the generic specification options, several SPM specific
options can be provided. In particular, the subject_info function can
provide temporal and parametric modulators in the Bunch attributes tmod
and pmod. The following example adds a linear parametric modulator for
speaking rate for the events specified earlier::

 pmod = [None, Bunch(name=['Rate'], param=[[.300, .500, .600]],
                                      poly=[1]), None]
 subject_info = Bunch(conditions=condnames,
                                     onsets = event_onsets,
                                     durations = durations,
                                     pmod = pmod)

:class:`SpecifySPMModel` also allows specifying additional components.
If you have a study with multiple runs, you can choose to concatenate
conditions from different runs. by setting the input
option **concatenate_runs** to True. You can also choose to set the
output options for this class to be in terms of 'scans'.

Sparse model specification
==========================

In addition to standard models, :class:`SpecifySparseModel` allows model
generation for sparse and sparse-clustered acquisition experiments.
Details of the model generation and utility are provided in `Ghosh et
al. (2009) OHBM 2009. <http://dl.dropbox.com/u/363467/OHBM2009_HRF.pdf>`_

.. include:: ../links_names.txt
