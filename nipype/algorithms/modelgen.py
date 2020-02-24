# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The modelgen module provides classes for specifying designs for individual
subject analysis of task-based fMRI experiments. In particular it also includes
algorithms for generating regressors for sparse and sparse-clustered acquisition
experiments.
"""
from copy import deepcopy
import csv, math, os

from nibabel import load
import numpy as np

from ..interfaces.base import (
    BaseInterface,
    TraitedSpec,
    InputMultiPath,
    traits,
    File,
    Bunch,
    BaseInterfaceInputSpec,
    isdefined,
)
from ..utils.filemanip import ensure_list
from ..utils.misc import normalize_mc_params
from .. import config, logging

iflogger = logging.getLogger("nipype.interface")


def spm_hrf(RT, P=None, fMRI_T=16):
    """
    python implementation of spm_hrf

    See ``spm_hrf`` for implementation details::

      % RT   - scan repeat time
      % p    - parameters of the response function (two gamma
      % functions)
      % defaults  (seconds)
      %	p(0) - delay of response (relative to onset)	   6
      %	p(1) - delay of undershoot (relative to onset)    16
      %	p(2) - dispersion of response			   1
      %	p(3) - dispersion of undershoot			   1
      %	p(4) - ratio of response to undershoot		   6
      %	p(5) - onset (seconds)				   0
      %	p(6) - length of kernel (seconds)		  32
      %
      % hrf  - hemodynamic response function
      % p    - parameters of the response function

    The following code using ``scipy.stats.distributions.gamma``
    doesn't return the same result as the ``spm_Gpdf`` function::

        hrf = gamma.pdf(u, p[0]/p[2], scale=dt/p[2]) -
              gamma.pdf(u, p[1]/p[3], scale=dt/p[3])/p[4]

    Example
    -------
    >>> print(spm_hrf(2))
    [  0.00000000e+00   8.65660810e-02   3.74888236e-01   3.84923382e-01
       2.16117316e-01   7.68695653e-02   1.62017720e-03  -3.06078117e-02
      -3.73060781e-02  -3.08373716e-02  -2.05161334e-02  -1.16441637e-02
      -5.82063147e-03  -2.61854250e-03  -1.07732374e-03  -4.10443522e-04
      -1.46257507e-04]

    """
    from scipy.special import gammaln

    p = np.array([6, 16, 1, 1, 6, 0, 32], dtype=float)
    if P is not None:
        p[0 : len(P)] = P

    _spm_Gpdf = lambda x, h, l: np.exp(
        h * np.log(l) + (h - 1) * np.log(x) - (l * x) - gammaln(h)
    )
    # modelled hemodynamic response function - {mixture of Gammas}
    dt = RT / float(fMRI_T)
    u = np.arange(0, int(p[6] / dt + 1)) - p[5] / dt
    with np.errstate(divide="ignore"):  # Known division-by-zero
        hrf = (
            _spm_Gpdf(u, p[0] / p[2], dt / p[2])
            - _spm_Gpdf(u, p[1] / p[3], dt / p[3]) / p[4]
        )
    idx = np.arange(0, int((p[6] / RT) + 1)) * fMRI_T
    hrf = hrf[idx]
    hrf = hrf / np.sum(hrf)
    return hrf


def orth(x_in, y_in):
    """Orthogonalize y_in with respect to x_in.

    >>> orth_expected = np.array([1.7142857142857144, 0.42857142857142883, \
                                  -0.85714285714285676])
    >>> err = np.abs(np.array(orth([1, 2, 3],[4, 5, 6]) - orth_expected))
    >>> all(err < np.finfo(float).eps)
    True

    """
    x = np.array(x_in)[:, None]
    y = np.array(y_in)[:, None]
    y = y - np.dot(x, np.dot(np.linalg.inv(np.dot(x.T, x)), np.dot(x.T, y)))
    if np.linalg.norm(y, 1) > np.exp(-32):
        y = y[:, 0].tolist()
    else:
        y = y_in
    return y


def scale_timings(timelist, input_units, output_units, time_repetition):
    """
    Scale timings given input and output units (scans/secs).

    Parameters
    ----------
    timelist: list of times to scale
    input_units: 'secs' or 'scans'
    output_units: Ibid.
    time_repetition: float in seconds

    """
    if input_units == output_units:
        _scalefactor = 1.0

    if (input_units == "scans") and (output_units == "secs"):
        _scalefactor = time_repetition

    if (input_units == "secs") and (output_units == "scans"):
        _scalefactor = 1.0 / time_repetition
    timelist = [np.max([0.0, _scalefactor * t]) for t in timelist]
    return timelist


def bids_gen_info(
    bids_event_files, condition_column="", amplitude_column=None, time_repetition=False,
):
    """
    Generate a subject_info structure from a list of BIDS .tsv event files.

    Parameters
    ----------
    bids_event_files : list of str
        Filenames of BIDS .tsv event files containing columns including:
        'onset', 'duration', and 'trial_type' or the `condition_column` value.
    condition_column : str
        Column of files in `bids_event_files` based on the values of which
        events will be sorted into different regressors
    amplitude_column : str
        Column of files in `bids_event_files` based on the values of which
        to apply amplitudes to events. If unspecified, all events will be
        represented with an amplitude of 1.

    Returns
    -------
    subject_info: list of Bunch

    """
    info = []
    for bids_event_file in bids_event_files:
        with open(bids_event_file) as f:
            f_events = csv.DictReader(f, skipinitialspace=True, delimiter="\t")
            events = [{k: v for k, v in row.items()} for row in f_events]
        if not condition_column:
            condition_column = "_trial_type"
            for i in events:
                i.update({condition_column: "ev0"})
        conditions = sorted(set([i[condition_column] for i in events]))
        runinfo = Bunch(conditions=[], onsets=[], durations=[], amplitudes=[])
        for condition in conditions:
            selected_events = [i for i in events if i[condition_column] == condition]
            onsets = [float(i["onset"]) for i in selected_events]
            durations = [float(i["duration"]) for i in selected_events]
            if time_repetition:
                decimals = math.ceil(-math.log10(time_repetition))
                onsets = [np.round(i, decimals) for i in onsets]
                durations = [np.round(i, decimals) for i in durations]
            runinfo.conditions.append(condition)
            runinfo.onsets.append(onsets)
            runinfo.durations.append(durations)
            try:
                amplitudes = [float(i[amplitude_column]) for i in selected_events]
                runinfo.amplitudes.append(amplitudes)
            except KeyError:
                runinfo.amplitudes.append([1] * len(onsets))
        info.append(runinfo)
    return info


def gen_info(run_event_files):
    """Generate subject_info structure from a list of event files."""
    info = []
    for i, event_files in enumerate(run_event_files):
        runinfo = Bunch(conditions=[], onsets=[], durations=[], amplitudes=[])
        for event_file in event_files:
            _, name = os.path.split(event_file)
            if ".run" in name:
                name, _ = name.split(".run%03d" % (i + 1))
            elif ".txt" in name:
                name, _ = name.split(".txt")

            runinfo.conditions.append(name)
            event_info = np.atleast_2d(np.loadtxt(event_file))
            runinfo.onsets.append(event_info[:, 0].tolist())
            if event_info.shape[1] > 1:
                runinfo.durations.append(event_info[:, 1].tolist())
            else:
                runinfo.durations.append([0])

            if event_info.shape[1] > 2:
                runinfo.amplitudes.append(event_info[:, 2].tolist())
            else:
                delattr(runinfo, "amplitudes")
        info.append(runinfo)
    return info


class SpecifyModelInputSpec(BaseInterfaceInputSpec):
    subject_info = InputMultiPath(
        Bunch,
        mandatory=True,
        xor=["subject_info", "event_files", "bids_event_file"],
        desc="Bunch or List(Bunch) subject-specific "
        "condition information. see "
        ":ref:`nipype.algorithms.modelgen.SpecifyModel` or for details",
    )
    event_files = InputMultiPath(
        traits.List(File(exists=True)),
        mandatory=True,
        xor=["subject_info", "event_files", "bids_event_file"],
        desc="List of event description files 1, 2 or 3 "
        "column format corresponding to onsets, "
        "durations and amplitudes",
    )
    bids_event_file = InputMultiPath(
        File(exists=True),
        mandatory=True,
        xor=["subject_info", "event_files", "bids_event_file"],
        desc="TSV event file containing common BIDS fields: `onset`,"
        "`duration`, and categorization and amplitude columns",
    )
    bids_condition_column = traits.Str(
        default_value="trial_type",
        usedefault=True,
        desc="Column of the file passed to ``bids_event_file`` to the "
        "unique values of which events will be assigned"
        "to regressors",
    )
    bids_amplitude_column = traits.Str(
        desc="Column of the file passed to ``bids_event_file`` "
        "according to which to assign amplitudes to events"
    )
    realignment_parameters = InputMultiPath(
        File(exists=True),
        desc="Realignment parameters returned by motion correction algorithm",
        copyfile=False,
    )
    parameter_source = traits.Enum(
        "SPM",
        "FSL",
        "AFNI",
        "FSFAST",
        "NIPY",
        usedefault=True,
        desc="Source of motion parameters",
    )
    outlier_files = InputMultiPath(
        File(exists=True),
        desc="Files containing scan outlier indices that should be tossed",
        copyfile=False,
    )
    functional_runs = InputMultiPath(
        traits.Either(traits.List(File(exists=True)), File(exists=True)),
        mandatory=True,
        desc="Data files for model. List of 4D "
        "files or list of list of 3D "
        "files per session",
        copyfile=False,
    )
    input_units = traits.Enum(
        "secs",
        "scans",
        mandatory=True,
        desc="Units of event onsets and durations (secs "
        "or scans). Output units are always in secs",
    )
    high_pass_filter_cutoff = traits.Float(
        mandatory=True, desc="High-pass filter cutoff in secs"
    )
    time_repetition = traits.Float(
        mandatory=True,
        desc="Time between the start of one volume "
        "to the start of  the next image volume.",
    )
    # Not implemented yet
    # polynomial_order = traits.Range(0, low=0,
    #        desc ='Number of polynomial functions to model high pass filter.')


class SpecifyModelOutputSpec(TraitedSpec):
    session_info = traits.Any(desc="Session info for level1designs")


class SpecifyModel(BaseInterface):
    """
    Makes a model specification compatible with spm/fsl designers.

    The subject_info field should contain paradigm information in the form of
    a Bunch or a list of Bunch. The Bunch should contain the following
    information::

        [Mandatory]
        conditions : list of names
        onsets : lists of onsets corresponding to each condition
        durations : lists of durations corresponding to each condition. Should be
            left to a single 0 if all events are being modelled as impulses.

        [Optional]
        regressor_names : list of str
            list of names corresponding to each column. Should be None if
            automatically assigned.
        regressors : list of lists
            values for each regressor - must correspond to the number of
            volumes in the functional run
        amplitudes : lists of amplitudes for each event. This will be ignored by
            SPM's Level1Design.

        The following two (tmod, pmod) will be ignored by any Level1Design class
        other than SPM:

        tmod : lists of conditions that should be temporally modulated. Should
            default to None if not being used.
        pmod : list of Bunch corresponding to conditions
          - name : name of parametric modulator
          - param : values of the modulator
          - poly : degree of modulation

    Alternatively, you can provide information through event files.

    The event files have to be in 1, 2 or 3 column format with the columns
    corresponding to Onsets, Durations and Amplitudes and they have to have the
    name event_name.runXXX... e.g.: Words.run001.txt. The event_name part will
    be used to create the condition names.

    Examples
    --------
    >>> from nipype.algorithms import modelgen
    >>> from nipype.interfaces.base import Bunch
    >>> s = modelgen.SpecifyModel()
    >>> s.inputs.input_units = 'secs'
    >>> s.inputs.functional_runs = ['functional2.nii', 'functional3.nii']
    >>> s.inputs.time_repetition = 6
    >>> s.inputs.high_pass_filter_cutoff = 128.
    >>> evs_run2 = Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]], durations=[[1]])
    >>> evs_run3 = Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]], durations=[[1]])
    >>> s.inputs.subject_info = [evs_run2, evs_run3]

    >>> # Using pmod
    >>> evs_run2 = Bunch(conditions=['cond1', 'cond2'], onsets=[[2, 50], [100, 180]], \
durations=[[0], [0]], pmod=[Bunch(name=['amp'], poly=[2], param=[[1, 2]]), \
None])
    >>> evs_run3 = Bunch(conditions=['cond1', 'cond2'], onsets=[[20, 120], [80, 160]], \
durations=[[0], [0]], pmod=[Bunch(name=['amp'], poly=[2], param=[[1, 2]]), \
None])
    >>> s.inputs.subject_info = [evs_run2, evs_run3]

    """

    input_spec = SpecifyModelInputSpec
    output_spec = SpecifyModelOutputSpec

    def _generate_standard_design(
        self, infolist, functional_runs=None, realignment_parameters=None, outliers=None
    ):
        """Generate a standard design matrix paradigm given information about each run."""
        sessinfo = []
        output_units = "secs"
        if "output_units" in self.inputs.traits():
            output_units = self.inputs.output_units

        for i, info in enumerate(infolist):
            sessinfo.insert(i, dict(cond=[]))
            if isdefined(self.inputs.high_pass_filter_cutoff):
                sessinfo[i]["hpf"] = np.float(self.inputs.high_pass_filter_cutoff)

            if hasattr(info, "conditions") and info.conditions is not None:
                for cid, cond in enumerate(info.conditions):
                    sessinfo[i]["cond"].insert(cid, dict())
                    sessinfo[i]["cond"][cid]["name"] = info.conditions[cid]
                    scaled_onset = scale_timings(
                        info.onsets[cid],
                        self.inputs.input_units,
                        output_units,
                        self.inputs.time_repetition,
                    )
                    sessinfo[i]["cond"][cid]["onset"] = scaled_onset
                    scaled_duration = scale_timings(
                        info.durations[cid],
                        self.inputs.input_units,
                        output_units,
                        self.inputs.time_repetition,
                    )
                    sessinfo[i]["cond"][cid]["duration"] = scaled_duration
                    if hasattr(info, "amplitudes") and info.amplitudes:
                        sessinfo[i]["cond"][cid]["amplitudes"] = info.amplitudes[cid]

                    if hasattr(info, "tmod") and info.tmod and len(info.tmod) > cid:
                        sessinfo[i]["cond"][cid]["tmod"] = info.tmod[cid]

                    if hasattr(info, "pmod") and info.pmod and len(info.pmod) > cid:
                        if info.pmod[cid]:
                            sessinfo[i]["cond"][cid]["pmod"] = []
                            for j, name in enumerate(info.pmod[cid].name):
                                sessinfo[i]["cond"][cid]["pmod"].insert(j, {})
                                sessinfo[i]["cond"][cid]["pmod"][j]["name"] = name
                                sessinfo[i]["cond"][cid]["pmod"][j]["poly"] = info.pmod[
                                    cid
                                ].poly[j]
                                sessinfo[i]["cond"][cid]["pmod"][j][
                                    "param"
                                ] = info.pmod[cid].param[j]

            sessinfo[i]["regress"] = []
            if hasattr(info, "regressors") and info.regressors is not None:
                for j, r in enumerate(info.regressors):
                    sessinfo[i]["regress"].insert(j, dict(name="", val=[]))
                    if (
                        hasattr(info, "regressor_names")
                        and info.regressor_names is not None
                    ):
                        sessinfo[i]["regress"][j]["name"] = info.regressor_names[j]
                    else:
                        sessinfo[i]["regress"][j]["name"] = "UR%d" % (j + 1)
                    sessinfo[i]["regress"][j]["val"] = info.regressors[j]
            sessinfo[i]["scans"] = functional_runs[i]

        if realignment_parameters is not None:
            for i, rp in enumerate(realignment_parameters):
                mc = realignment_parameters[i]
                for col in range(mc.shape[1]):
                    colidx = len(sessinfo[i]["regress"])
                    sessinfo[i]["regress"].insert(colidx, dict(name="", val=[]))
                    sessinfo[i]["regress"][colidx]["name"] = "Realign%d" % (col + 1)
                    sessinfo[i]["regress"][colidx]["val"] = mc[:, col].tolist()

        if outliers is not None:
            for i, out in enumerate(outliers):
                numscans = 0
                for f in ensure_list(sessinfo[i]["scans"]):
                    shape = load(f).shape
                    if len(shape) == 3 or shape[3] == 1:
                        iflogger.warning(
                            "You are using 3D instead of 4D "
                            "files. Are you sure this was "
                            "intended?"
                        )
                        numscans += 1
                    else:
                        numscans += shape[3]

                for j, scanno in enumerate(out):
                    colidx = len(sessinfo[i]["regress"])
                    sessinfo[i]["regress"].insert(colidx, dict(name="", val=[]))
                    sessinfo[i]["regress"][colidx]["name"] = "Outlier%d" % (j + 1)
                    sessinfo[i]["regress"][colidx]["val"] = np.zeros((1, numscans))[
                        0
                    ].tolist()
                    sessinfo[i]["regress"][colidx]["val"][int(scanno)] = 1
        return sessinfo

    def _generate_design(self, infolist=None):
        """Generate design specification for a typical fmri paradigm
        """
        realignment_parameters = []
        if isdefined(self.inputs.realignment_parameters):
            for parfile in self.inputs.realignment_parameters:
                realignment_parameters.append(
                    np.apply_along_axis(
                        func1d=normalize_mc_params,
                        axis=1,
                        arr=np.loadtxt(parfile),
                        source=self.inputs.parameter_source,
                    )
                )
        outliers = []
        if isdefined(self.inputs.outlier_files):
            for filename in self.inputs.outlier_files:
                try:
                    outindices = np.loadtxt(filename, dtype=int)
                except IOError:
                    outliers.append([])
                else:
                    if outindices.size == 1:
                        outliers.append([outindices.tolist()])
                    else:
                        outliers.append(outindices.tolist())

        if infolist is None:
            if isdefined(self.inputs.subject_info):
                infolist = self.inputs.subject_info
            elif isdefined(self.inputs.event_files):
                infolist = gen_info(self.inputs.event_files)
            elif isdefined(self.inputs.bids_event_file):
                infolist = bids_gen_info(
                    self.inputs.bids_event_file,
                    self.inputs.bids_condition_column,
                    self.inputs.bids_amplitude_column,
                    self.inputs.time_repetition,
                )
        self._sessinfo = self._generate_standard_design(
            infolist,
            functional_runs=self.inputs.functional_runs,
            realignment_parameters=realignment_parameters,
            outliers=outliers,
        )

    def _run_interface(self, runtime):
        """
        """
        self._sessioninfo = None
        self._generate_design()
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        if not hasattr(self, "_sessinfo"):
            self._generate_design()
        outputs["session_info"] = self._sessinfo

        return outputs


class SpecifySPMModelInputSpec(SpecifyModelInputSpec):
    concatenate_runs = traits.Bool(
        False,
        usedefault=True,
        desc="Concatenate all runs to look like a single session.",
    )
    output_units = traits.Enum(
        "secs",
        "scans",
        usedefault=True,
        desc="Units of design event onsets and durations (secs or scans)",
    )


class SpecifySPMModel(SpecifyModel):
    """Add SPM specific options to SpecifyModel

    Adds:

       - concatenate_runs
       - output_units

    Examples
    --------
    >>> from nipype.algorithms import modelgen
    >>> from nipype.interfaces.base import Bunch
    >>> s = modelgen.SpecifySPMModel()
    >>> s.inputs.input_units = 'secs'
    >>> s.inputs.output_units = 'scans'
    >>> s.inputs.high_pass_filter_cutoff = 128.
    >>> s.inputs.functional_runs = ['functional2.nii', 'functional3.nii']
    >>> s.inputs.time_repetition = 6
    >>> s.inputs.concatenate_runs = True
    >>> evs_run2 = Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]], durations=[[1]])
    >>> evs_run3 = Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]], durations=[[1]])
    >>> s.inputs.subject_info = [evs_run2, evs_run3]

    """

    input_spec = SpecifySPMModelInputSpec

    def _concatenate_info(self, infolist):
        nscans = []
        for i, f in enumerate(self.inputs.functional_runs):
            if isinstance(f, list):
                numscans = len(f)
            elif isinstance(f, (str, bytes)):
                img = load(f)
                numscans = img.shape[3]
            else:
                raise Exception("Functional input not specified correctly")
            nscans.insert(i, numscans)

        # now combine all fields into 1
        # names, onsets, durations, amplitudes, pmod, tmod, regressor_names,
        # regressors
        infoout = infolist[0]
        for j, val in enumerate(infolist[0].durations):
            if len(infolist[0].onsets[j]) > 1 and len(val) == 1:
                infoout.durations[j] = infolist[0].durations[j] * len(
                    infolist[0].onsets[j]
                )

        for i, info in enumerate(infolist[1:]):
            # info.[conditions, tmod] remain the same
            if info.onsets:
                for j, val in enumerate(info.onsets):
                    if self.inputs.input_units == "secs":
                        onsets = np.array(
                            info.onsets[j]
                        ) + self.inputs.time_repetition * sum(nscans[0 : (i + 1)])
                        infoout.onsets[j].extend(onsets.tolist())
                    else:
                        onsets = np.array(info.onsets[j]) + sum(nscans[0 : (i + 1)])
                        infoout.onsets[j].extend(onsets.tolist())

                for j, val in enumerate(info.durations):
                    if len(info.onsets[j]) > 1 and len(val) == 1:
                        infoout.durations[j].extend(
                            info.durations[j] * len(info.onsets[j])
                        )
                    elif len(info.onsets[j]) == len(val):
                        infoout.durations[j].extend(info.durations[j])
                    else:
                        raise ValueError(
                            "Mismatch in number of onsets and \
                                          durations for run {0}, condition \
                                          {1}".format(
                                i + 2, j + 1
                            )
                        )

                if hasattr(info, "amplitudes") and info.amplitudes:
                    for j, val in enumerate(info.amplitudes):
                        infoout.amplitudes[j].extend(info.amplitudes[j])

                if hasattr(info, "pmod") and info.pmod:
                    for j, val in enumerate(info.pmod):
                        if val:
                            for key, data in enumerate(val.param):
                                infoout.pmod[j].param[key].extend(data)

            if hasattr(info, "regressors") and info.regressors:
                # assumes same ordering of regressors across different
                # runs and the same names for the regressors
                for j, v in enumerate(info.regressors):
                    infoout.regressors[j].extend(info.regressors[j])

            # insert session regressors
            if not hasattr(infoout, "regressors") or not infoout.regressors:
                infoout.regressors = []
            onelist = np.zeros((1, sum(nscans)))
            onelist[0, sum(nscans[0:i]) : sum(nscans[0 : (i + 1)])] = 1
            infoout.regressors.insert(len(infoout.regressors), onelist.tolist()[0])
        return [infoout], nscans

    def _generate_design(self, infolist=None):
        if (
            not isdefined(self.inputs.concatenate_runs)
            or not self.inputs.concatenate_runs
        ):
            super(SpecifySPMModel, self)._generate_design(infolist=infolist)
            return

        if isdefined(self.inputs.subject_info):
            infolist = self.inputs.subject_info
        else:
            infolist = gen_info(self.inputs.event_files)
        concatlist, nscans = self._concatenate_info(infolist)
        functional_runs = [ensure_list(self.inputs.functional_runs)]
        realignment_parameters = []
        if isdefined(self.inputs.realignment_parameters):
            realignment_parameters = []
            for parfile in self.inputs.realignment_parameters:
                mc = np.apply_along_axis(
                    func1d=normalize_mc_params,
                    axis=1,
                    arr=np.loadtxt(parfile),
                    source=self.inputs.parameter_source,
                )
                if not realignment_parameters:
                    realignment_parameters.insert(0, mc)
                else:
                    realignment_parameters[0] = np.concatenate(
                        (realignment_parameters[0], mc)
                    )
        outliers = []
        if isdefined(self.inputs.outlier_files):
            outliers = [[]]
            for i, filename in enumerate(self.inputs.outlier_files):
                try:
                    out = np.loadtxt(filename)
                except IOError:
                    iflogger.warning("Error reading outliers file %s", filename)
                    out = np.array([])

                if out.size > 0:
                    iflogger.debug(
                        "fname=%s, out=%s, nscans=%d", filename, out, sum(nscans[0:i])
                    )
                    sumscans = out.astype(int) + sum(nscans[0:i])

                    if out.size == 1:
                        outliers[0] += [np.array(sumscans, dtype=int).tolist()]
                    else:
                        outliers[0] += np.array(sumscans, dtype=int).tolist()

        self._sessinfo = self._generate_standard_design(
            concatlist,
            functional_runs=functional_runs,
            realignment_parameters=realignment_parameters,
            outliers=outliers,
        )


class SpecifySparseModelInputSpec(SpecifyModelInputSpec):
    time_acquisition = traits.Float(
        0, mandatory=True, desc="Time in seconds to acquire a single image volume"
    )
    volumes_in_cluster = traits.Range(
        1, usedefault=True, desc="Number of scan volumes in a cluster"
    )
    model_hrf = traits.Bool(desc="Model sparse events with hrf")
    stimuli_as_impulses = traits.Bool(
        True, desc="Treat each stimulus to be impulse-like", usedefault=True
    )
    use_temporal_deriv = traits.Bool(
        requires=["model_hrf"],
        desc="Create a temporal derivative in addition to regular regressor",
    )
    scale_regressors = traits.Bool(
        True, desc="Scale regressors by the peak", usedefault=True
    )
    scan_onset = traits.Float(
        0.0, desc="Start of scanning relative to onset of run in secs", usedefault=True
    )
    save_plot = traits.Bool(
        desc=("Save plot of sparse design calculation (requires matplotlib)")
    )


class SpecifySparseModelOutputSpec(SpecifyModelOutputSpec):
    sparse_png_file = File(desc="PNG file showing sparse design")
    sparse_svg_file = File(desc="SVG file showing sparse design")


class SpecifySparseModel(SpecifyModel):
    """ Specify a sparse model that is compatible with SPM/FSL designers [1]_.

    Examples
    --------
    >>> from nipype.algorithms import modelgen
    >>> from nipype.interfaces.base import Bunch
    >>> s = modelgen.SpecifySparseModel()
    >>> s.inputs.input_units = 'secs'
    >>> s.inputs.functional_runs = ['functional2.nii', 'functional3.nii']
    >>> s.inputs.time_repetition = 6
    >>> s.inputs.time_acquisition = 2
    >>> s.inputs.high_pass_filter_cutoff = 128.
    >>> s.inputs.model_hrf = True
    >>> evs_run2 = Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]],
    ...                  durations=[[1]])
    >>> evs_run3 = Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]],
    ...                  durations=[[1]])
    >>> s.inputs.subject_info = [evs_run2, evs_run3]  # doctest: +SKIP

    References
    ----------
    .. [1] Perrachione TK and Ghosh SS (2013) Optimized design and analysis of
       sparse-sampling fMRI experiments. Front. Neurosci. 7:55
       http://journal.frontiersin.org/Journal/10.3389/fnins.2013.00055/abstract

    """

    input_spec = SpecifySparseModelInputSpec
    output_spec = SpecifySparseModelOutputSpec

    def _gen_regress(self, i_onsets, i_durations, i_amplitudes, nscans):
        """Generates a regressor for a sparse/clustered-sparse acquisition
        """
        bplot = False
        if isdefined(self.inputs.save_plot) and self.inputs.save_plot:
            bplot = True
            import matplotlib

            matplotlib.use(config.get("execution", "matplotlib_backend"))
            import matplotlib.pyplot as plt

        TR = int(np.round(self.inputs.time_repetition * 1000))  # in ms
        if self.inputs.time_acquisition:
            TA = int(np.round(self.inputs.time_acquisition * 1000))  # in ms
        else:
            TA = TR  # in ms
        nvol = self.inputs.volumes_in_cluster
        SCANONSET = np.round(self.inputs.scan_onset * 1000)
        total_time = TR * (nscans - nvol) / nvol + TA * nvol + SCANONSET
        SILENCE = TR - TA * nvol
        dt = TA / 10.0
        durations = np.round(np.array(i_durations) * 1000)
        if len(durations) == 1:
            durations = durations * np.ones((len(i_onsets)))
        onsets = np.round(np.array(i_onsets) * 1000)
        dttemp = math.gcd(TA, math.gcd(SILENCE, TR))
        if dt < dttemp:
            if dttemp % dt != 0:
                dt = float(math.gcd(dttemp, int(dt)))

        if dt < 1:
            raise Exception("Time multiple less than 1 ms")
        iflogger.info("Setting dt = %d ms\n", dt)
        npts = int(np.ceil(total_time / dt))
        times = np.arange(0, total_time, dt) * 1e-3
        timeline = np.zeros((npts))
        timeline2 = np.zeros((npts))
        if isdefined(self.inputs.model_hrf) and self.inputs.model_hrf:
            hrf = spm_hrf(dt * 1e-3)
        reg_scale = 1.0
        if self.inputs.scale_regressors:
            boxcar = np.zeros(int(50.0 * 1e3 / dt))
            if self.inputs.stimuli_as_impulses:
                boxcar[int(1.0 * 1e3 / dt)] = 1.0
                reg_scale = float(TA / dt)
            else:
                boxcar[int(1.0 * 1e3 / dt) : int(2.0 * 1e3 / dt)] = 1.0

            if isdefined(self.inputs.model_hrf) and self.inputs.model_hrf:
                response = np.convolve(boxcar, hrf)
                reg_scale = 1.0 / response.max()
                iflogger.info(
                    "response sum: %.4f max: %.4f", response.sum(), response.max()
                )
            iflogger.info("reg_scale: %.4f", reg_scale)

        for i, t in enumerate(onsets):
            idx = int(np.round(t / dt))
            if i_amplitudes:
                if len(i_amplitudes) > 1:
                    timeline2[idx] = i_amplitudes[i]
                else:
                    timeline2[idx] = i_amplitudes[0]
            else:
                timeline2[idx] = 1

            if bplot:
                plt.subplot(4, 1, 1)
                plt.plot(times, timeline2)

            if not self.inputs.stimuli_as_impulses:
                if durations[i] == 0:
                    durations[i] = TA * nvol
                stimdur = np.ones((int(durations[i] / dt)))
                timeline2 = np.convolve(timeline2, stimdur)[0 : len(timeline2)]
            timeline += timeline2
            timeline2[:] = 0

        if bplot:
            plt.subplot(4, 1, 2)
            plt.plot(times, timeline)

        if isdefined(self.inputs.model_hrf) and self.inputs.model_hrf:
            timeline = np.convolve(timeline, hrf)[0 : len(timeline)]
            if (
                isdefined(self.inputs.use_temporal_deriv)
                and self.inputs.use_temporal_deriv
            ):
                # create temporal deriv
                timederiv = np.concatenate(([0], np.diff(timeline)))

        if bplot:
            plt.subplot(4, 1, 3)
            plt.plot(times, timeline)
            if (
                isdefined(self.inputs.use_temporal_deriv)
                and self.inputs.use_temporal_deriv
            ):
                plt.plot(times, timederiv)
        # sample timeline
        timeline2 = np.zeros((npts))
        reg = []
        regderiv = []
        for i, trial in enumerate(np.arange(nscans) / nvol):
            scanstart = int((SCANONSET + trial * TR + (i % nvol) * TA) / dt)
            scanidx = scanstart + np.arange(int(TA / dt))
            timeline2[scanidx] = np.max(timeline)
            reg.insert(i, np.mean(timeline[scanidx]) * reg_scale)
            if (
                isdefined(self.inputs.use_temporal_deriv)
                and self.inputs.use_temporal_deriv
            ):
                regderiv.insert(i, np.mean(timederiv[scanidx]) * reg_scale)

        if isdefined(self.inputs.use_temporal_deriv) and self.inputs.use_temporal_deriv:
            iflogger.info("orthoganlizing derivative w.r.t. main regressor")
            regderiv = orth(reg, regderiv)

        if bplot:
            plt.subplot(4, 1, 3)
            plt.plot(times, timeline2)
            plt.subplot(4, 1, 4)
            plt.bar(np.arange(len(reg)), reg, width=0.5)
            plt.savefig("sparse.png")
            plt.savefig("sparse.svg")

        if regderiv:
            return [reg, regderiv]
        else:
            return reg

    def _cond_to_regress(self, info, nscans):
        """Converts condition information to full regressors
        """
        reg = []
        regnames = []
        for i, cond in enumerate(info.conditions):
            if hasattr(info, "amplitudes") and info.amplitudes:
                amplitudes = info.amplitudes[i]
            else:
                amplitudes = None
            regnames.insert(len(regnames), cond)
            scaled_onsets = scale_timings(
                info.onsets[i],
                self.inputs.input_units,
                "secs",
                self.inputs.time_repetition,
            )
            scaled_durations = scale_timings(
                info.durations[i],
                self.inputs.input_units,
                "secs",
                self.inputs.time_repetition,
            )
            regressor = self._gen_regress(
                scaled_onsets, scaled_durations, amplitudes, nscans
            )
            if (
                isdefined(self.inputs.use_temporal_deriv)
                and self.inputs.use_temporal_deriv
            ):
                reg.insert(len(reg), regressor[0])
                regnames.insert(len(regnames), cond + "_D")
                reg.insert(len(reg), regressor[1])
            else:
                reg.insert(len(reg), regressor)
        # need to deal with temporal and parametric modulators
        # for sparse-clustered acquisitions enter T1-effect regressors
        nvol = self.inputs.volumes_in_cluster
        if nvol > 1:
            for i in range(nvol - 1):
                treg = np.zeros((nscans / nvol, nvol))
                treg[:, i] = 1
                reg.insert(len(reg), treg.ravel().tolist())
                regnames.insert(len(regnames), "T1effect_%d" % i)
        return reg, regnames

    def _generate_clustered_design(self, infolist):
        """Generates condition information for sparse-clustered
        designs.

        """
        infoout = deepcopy(infolist)
        for i, info in enumerate(infolist):
            infoout[i].conditions = None
            infoout[i].onsets = None
            infoout[i].durations = None
            if info.conditions:
                img = load(self.inputs.functional_runs[i])
                nscans = img.shape[3]
                reg, regnames = self._cond_to_regress(info, nscans)
                if hasattr(infoout[i], "regressors") and infoout[i].regressors:
                    if not infoout[i].regressor_names:
                        infoout[i].regressor_names = [
                            "R%d" % j for j in range(len(infoout[i].regressors))
                        ]
                else:
                    infoout[i].regressors = []
                    infoout[i].regressor_names = []

                for j, r in enumerate(reg):
                    regidx = len(infoout[i].regressors)
                    infoout[i].regressor_names.insert(regidx, regnames[j])
                    infoout[i].regressors.insert(regidx, r)
        return infoout

    def _generate_design(self, infolist=None):
        if isdefined(self.inputs.subject_info):
            infolist = self.inputs.subject_info
        else:
            infolist = gen_info(self.inputs.event_files)
        sparselist = self._generate_clustered_design(infolist)
        super(SpecifySparseModel, self)._generate_design(infolist=sparselist)

    def _list_outputs(self):
        outputs = self._outputs().get()
        if not hasattr(self, "_sessinfo"):
            self._generate_design()
        outputs["session_info"] = self._sessinfo

        if isdefined(self.inputs.save_plot) and self.inputs.save_plot:
            outputs["sparse_png_file"] = os.path.join(os.getcwd(), "sparse.png")
            outputs["sparse_svg_file"] = os.path.join(os.getcwd(), "sparse.svg")
        return outputs
