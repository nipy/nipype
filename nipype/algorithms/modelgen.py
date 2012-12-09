# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The modelgen module provides classes for specifying designs for individual
subject analysis of task-based fMRI experiments. In particular it also includes
algorithms for generating regressors for sparse and sparse-clustered acquisition
experiments.

These functions include:

  * SpecifyModel: allows specification of sparse and non-sparse models

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
   >>> os.chdir(datadir)

"""

from copy import deepcopy
import os

from nibabel import load
import numpy as np
from scipy.special import gammaln

from nipype.interfaces.base import (BaseInterface, TraitedSpec, InputMultiPath,
                                    traits, File, Bunch, BaseInterfaceInputSpec,
                                    isdefined)
from nipype.utils.filemanip import filename_to_list
from .. import config, logging
iflogger = logging.getLogger('interface')

def gcd(a, b):
    """Returns the greatest common divisor of two integers

    uses Euclid's algorithm

    >>> gcd(4, 5)
    1
    >>> gcd(4, 8)
    4
    >>> gcd(22, 55)
    11

    """
    while b > 0: a, b = b, a % b
    return a


def spm_hrf(RT, P=None, fMRI_T=16):
    """ python implementation of spm_hrf

    see spm_hrf for implementation details

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

    the following code using scipy.stats.distributions.gamma
    doesn't return the same result as the spm_Gpdf function
    hrf   = gamma.pdf(u, p[0]/p[2], scale=dt/p[2]) - gamma.pdf(u, p[1]/p[3], scale=dt/p[3])/p[4]

    >>> print spm_hrf(2)
    [  0.00000000e+00   8.65660810e-02   3.74888236e-01   3.84923382e-01
       2.16117316e-01   7.68695653e-02   1.62017720e-03  -3.06078117e-02
      -3.73060781e-02  -3.08373716e-02  -2.05161334e-02  -1.16441637e-02
      -5.82063147e-03  -2.61854250e-03  -1.07732374e-03  -4.10443522e-04
      -1.46257507e-04]

    """
    p     = np.array([6, 16, 1, 1, 6, 0, 32], dtype=float)
    if P is not None:
        p[0:len(P)] = P

    _spm_Gpdf = lambda x, h, l: np.exp(h * np.log(l) + (h - 1) * np.log(x) - (l * x) - gammaln(h))
    # modelled hemodynamic response function - {mixture of Gammas}
    dt    = RT/float(fMRI_T)
    u     = np.arange(0, int(p[6]/dt+1)) - p[5]/dt
    hrf   = _spm_Gpdf(u, p[0]/p[2], dt/p[2]) - _spm_Gpdf(u, p[1]/p[3], dt/p[3])/p[4]
    idx   = np.arange(0, int((p[6]/RT)+1))*fMRI_T
    hrf   = hrf[idx]
    hrf   = hrf/np.sum(hrf)
    return hrf


def orth(x_in, y_in):
    """Orthoganlize y_in with respect to x_in

    >>> err = np.abs(np.array(orth([1, 2, 3],[4, 5, 6]) - np.array([1.7142857142857144, 0.42857142857142883, -0.85714285714285676])))
    >>> all(err<np.finfo(float).eps)
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
    """Scales timings given input and output units (scans/secs)

    Parameters
    ----------

    timelist: list of times to scale
    input_units: 'secs' or 'scans'
    output_units: Ibid.
    time_repetition: float in seconds

    """
    if input_units==output_units:
        _scalefactor = 1.
    if (input_units == 'scans') and (output_units == 'secs'):
        _scalefactor = time_repetition
    if (input_units == 'secs') and (output_units == 'scans'):
        _scalefactor = 1./time_repetition
    timelist = [np.max([0., _scalefactor*t]) for t in timelist]
    return timelist


def gen_info(run_event_files):
    """Generate subject_info structure from a list of event files
    """
    info = []
    for i, event_files in enumerate(run_event_files):
        runinfo = Bunch(conditions=[], onsets=[], durations=[], amplitudes=[])
        for event_file in event_files:
            _, name = os.path.split(event_file)
            if '.run' in name:
                name, _ = name.split('.run%03d'%(i+1))
            elif '.txt' in name:
                name, _ = name.split('.txt')
            runinfo.conditions.append(name)
            event_info = np.loadtxt(event_file)
            runinfo.onsets.append(event_info[:, 0].tolist())
            if event_info.shape[1] > 1:
                runinfo.durations.append(event_info[:, 1].tolist())
            else:
                runinfo.durations.append([0])
            if event_info.shape[1] > 2:
                runinfo.amplitudes.append(event_info[:, 2].tolist())
            else:
                delattr(runinfo, 'amplitudes')
        info.append(runinfo)
    return info


class SpecifyModelInputSpec(BaseInterfaceInputSpec):
    subject_info = InputMultiPath(Bunch, mandatory=True, xor=['event_files'],
          desc=("Bunch or List(Bunch) subject specific condition information. "
                "see :ref:`SpecifyModel` or SpecifyModel.__doc__ for details"))
    event_files = InputMultiPath(traits.List(File(exists=True)), mandatory=True,
                                 xor=['subject_info'],
          desc=('list of event description files 1, 2 or 3 column format '
                'corresponding to onsets, durations and amplitudes'))
    realignment_parameters = InputMultiPath(File(exists=True),
       desc = "Realignment parameters returned by motion correction algorithm",
                                         filecopy=False)
    outlier_files = InputMultiPath(File(exists=True),
         desc="Files containing scan outlier indices that should be tossed",
                                filecopy=False)
    functional_runs = InputMultiPath(traits.Either(traits.List(File(exists=True)),
                                                   File(exists=True)),
                                     mandatory=True,
            desc="Data files for model. List of 4D files or list of" \
                                      "list of 3D files per session",
            filecopy=False)
    input_units = traits.Enum('secs', 'scans', mandatory=True,
             desc = "Units of event onsets and durations (secs or scans)" \
                    "Output units are always in secs")
    high_pass_filter_cutoff = traits.Float(mandatory=True,
                                     desc="High-pass filter cutoff in secs")
    time_repetition = traits.Float(mandatory=True,
        desc = "Time between the start of one volume to the start of " \
                                       "the next image volume.")
    # Not implemented yet
    #polynomial_order = traits.Range(0, low=0,
    #        desc ="Number of polynomial functions to model high pass filter.")


class SpecifyModelOutputSpec(TraitedSpec):
    session_info = traits.Any(desc="session info for level1designs")


class SpecifyModel(BaseInterface):
    """Makes a model specification compatible with spm/fsl designers.

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
    --------

    >>> from nipype.interfaces.base import Bunch
    >>> s = SpecifyModel()
    >>> s.inputs.input_units = 'secs'
    >>> s.inputs.functional_runs = ['functional2.nii', 'functional3.nii']
    >>> s.inputs.time_repetition = 6
    >>> s.inputs.high_pass_filter_cutoff = 128.
    >>> info = [Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]], durations=[[1]]), \
            Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]], durations=[[1]])]
    >>> s.inputs.subject_info = info

    Using pmod:

    >>> info = [Bunch(conditions=['cond1', 'cond2'], onsets=[[2, 50],[100, 180]], durations=[[0],[0]], pmod=[Bunch(name=['amp'], poly=[2], param=[[1, 2]]), None]), \
        Bunch(conditions=['cond1', 'cond2'], onsets=[[20, 120],[80, 160]], durations=[[0],[0]], pmod=[Bunch(name=['amp'], poly=[2], param=[[1, 2]]), None])]
    >>> s.inputs.subject_info = info

    """
    input_spec = SpecifyModelInputSpec
    output_spec = SpecifyModelOutputSpec

    def _generate_standard_design(self, infolist,
                                  functional_runs=None,
                                  realignment_parameters=None,
                                  outliers=None):
        """ Generates a standard design matrix paradigm given information about
            each run
        """
        sessinfo = []
        output_units = 'secs'
        if 'output_units' in self.inputs.traits():
            output_units = self.inputs.output_units
        for i, info in enumerate(infolist):
            sessinfo.insert(i, dict(cond=[]))
            if isdefined(self.inputs.high_pass_filter_cutoff):
                sessinfo[i]['hpf'] = np.float(self.inputs.high_pass_filter_cutoff)
            if hasattr(info, 'conditions') and info.conditions is not None:
                for cid, cond in enumerate(info.conditions):
                    sessinfo[i]['cond'].insert(cid, dict())
                    sessinfo[i]['cond'][cid]['name']  = info.conditions[cid]
                    sessinfo[i]['cond'][cid]['onset'] = scale_timings(info.onsets[cid],
                                                                     self.inputs.input_units,
                                                                     output_units,
                                                                     self.inputs.time_repetition)
                    sessinfo[i]['cond'][cid]['duration'] = scale_timings(info.durations[cid],
                                                                        self.inputs.input_units,
                                                                        output_units,
                                                                        self.inputs.time_repetition)
                    if hasattr(info, 'amplitudes') and info.amplitudes:
                        sessinfo[i]['cond'][cid]['amplitudes']  = info.amplitudes[cid]
                    if hasattr(info, 'tmod') and info.tmod and len(info.tmod)>cid:
                        sessinfo[i]['cond'][cid]['tmod'] = info.tmod[cid]
                    if hasattr(info, 'pmod') and info.pmod and len(info.pmod)>cid:
                        if info.pmod[cid]:
                            sessinfo[i]['cond'][cid]['pmod'] = []
                            for j, name in enumerate(info.pmod[cid].name):
                                sessinfo[i]['cond'][cid]['pmod'].insert(j,{})
                                sessinfo[i]['cond'][cid]['pmod'][j]['name'] = name
                                sessinfo[i]['cond'][cid]['pmod'][j]['poly'] = info.pmod[cid].poly[j]
                                sessinfo[i]['cond'][cid]['pmod'][j]['param'] = info.pmod[cid].param[j]
            sessinfo[i]['regress']= []
            if hasattr(info, 'regressors') and info.regressors is not None:
                for j, r in enumerate(info.regressors):
                    sessinfo[i]['regress'].insert(j, dict(name='', val=[]))
                    if hasattr(info, 'regressor_names') and info.regressor_names is not None:
                        sessinfo[i]['regress'][j]['name'] = info.regressor_names[j]
                    else:
                        sessinfo[i]['regress'][j]['name'] = 'UR%d'%(j+1)
                    sessinfo[i]['regress'][j]['val'] = info.regressors[j]
            sessinfo[i]['scans'] = functional_runs[i]
        if realignment_parameters is not None:
            for i, rp in enumerate(realignment_parameters):
                mc = realignment_parameters[i]
                for col in range(mc.shape[1]):
                    colidx = len(sessinfo[i]['regress'])
                    sessinfo[i]['regress'].insert(colidx, dict(name='', val=[]))
                    sessinfo[i]['regress'][colidx]['name'] = 'Realign%d'%(col+1)
                    sessinfo[i]['regress'][colidx]['val']  = mc[:, col].tolist()
        if outliers is not None:
            for i, out in enumerate(outliers):
                numscans = 0
                for f in filename_to_list(sessinfo[i]['scans']):
                    numscans += load(f).get_shape()[3]
                for j, scanno in enumerate(out):
                    colidx = len(sessinfo[i]['regress'])
                    sessinfo[i]['regress'].insert(colidx, dict(name='', val=[]))
                    sessinfo[i]['regress'][colidx]['name'] = 'Outlier%d'%(j+1)
                    sessinfo[i]['regress'][colidx]['val']  = np.zeros((1, numscans))[0].tolist()
                    sessinfo[i]['regress'][colidx]['val'][int(scanno)] = 1
        return sessinfo

    def _generate_design(self, infolist=None):
        """Generate design specification for a typical fmri paradigm
        """
        realignment_parameters = []
        if isdefined(self.inputs.realignment_parameters):
            for parfile in self.inputs.realignment_parameters:
                realignment_parameters.append(np.loadtxt(parfile))
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
            else:
                infolist = gen_info(self.inputs.event_files)
        self._sessinfo = self._generate_standard_design(infolist,
                                                  functional_runs=self.inputs.functional_runs,
                                                  realignment_parameters=realignment_parameters,
                                                  outliers=outliers)

    def _run_interface(self, runtime):
        """
        """
        self._sessioninfo = None
        self._generate_design()
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        if not hasattr(self, '_sessinfo'):
            self._generate_design()
        outputs['session_info'] = self._sessinfo

        return outputs


class SpecifySPMModelInputSpec(SpecifyModelInputSpec):
    concatenate_runs = traits.Bool(False, usedefault=True,
            desc="Concatenate all runs to look like a single session.")
    output_units = traits.Enum('secs', 'scans', usedefault=True,
             desc = "Units of design event onsets and durations " \
                                   "(secs or scans)")


class SpecifySPMModel(SpecifyModel):
    """Adds SPM specific options to SpecifyModel

     adds:
       - concatenate_runs
       - output_units

    Examples
    --------

    >>> from nipype.interfaces.base import Bunch
    >>> s = SpecifySPMModel()
    >>> s.inputs.input_units = 'secs'
    >>> s.inputs.output_units = 'scans'
    >>> s.inputs.high_pass_filter_cutoff = 128.
    >>> s.inputs.functional_runs = ['functional2.nii', 'functional3.nii']
    >>> s.inputs.time_repetition = 6
    >>> s.inputs.concatenate_runs = True
    >>> info = [Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]], durations=[[1]]), \
            Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]], durations=[[1]])]
    >>> s.inputs.subject_info = info

    """

    input_spec = SpecifySPMModelInputSpec

    def _concatenate_info(self, infolist):
        nscans = []
        for i, f in enumerate(self.inputs.functional_runs):
            if isinstance(f, list):
                numscans = len(f)
            elif isinstance(f, str):
                img = load(f)
                numscans = img.get_shape()[3]
            else:
                raise Exception('Functional input not specified correctly')
            nscans.insert(i, numscans)
        # now combine all fields into 1
        # names, onsets, durations, amplitudes, pmod, tmod, regressor_names, regressors
        infoout = infolist[0]
        for i, info in enumerate(infolist[1:]):
            #info.[conditions, tmod] remain the same
            if info.onsets:
                for j, val in enumerate(info.onsets):
                    if self.inputs.input_units == 'secs':
                        infoout.onsets[j].extend((np.array(info.onsets[j])+
                                                  self.inputs.time_repetition*sum(nscans[0:(i+1)])).tolist())
                    else:
                        infoout.onsets[j].extend((np.array(info.onsets[j])+sum(nscans[0:(i+1)])).tolist())
                for j, val in enumerate(info.durations):
                    if len(val) > 1:
                        infoout.durations[j].extend(info.durations[j])
                if hasattr(info, 'amplitudes') and info.amplitudes:
                    for j, val in enumerate(info.amplitudes):
                        infoout.amplitudes[j].extend(info.amplitudes[j])
                if hasattr(info, 'pmod') and info.pmod:
                    for j, val in enumerate(info.pmod):
                        if val:
                            for key, data in enumerate(val.param):
                                infoout.pmod[j].param[key].extend(data)
            if hasattr(info, 'regressors') and info.regressors:
                #assumes same ordering of regressors across different
                #runs and the same names for the regressors
                for j, v in enumerate(info.regressors):
                    infoout.regressors[j].extend(info.regressors[j])
            #insert session regressors
            if not hasattr(infoout, 'regressors') or not infoout.regressors:
                infoout.regressors = []
            onelist = np.zeros((1, sum(nscans)))
            onelist[0, sum(nscans[0:(i)]):sum(nscans[0:(i+1)])] = 1
            infoout.regressors.insert(len(infoout.regressors), onelist.tolist()[0])
        return [infoout], nscans

    def _generate_design(self, infolist=None):
        if not isdefined(self.inputs.concatenate_runs) or not self.inputs.concatenate_runs:
            super(SpecifySPMModel, self)._generate_design(infolist=infolist)
            return
        if isdefined(self.inputs.subject_info):
            infolist = self.inputs.subject_info
        else:
            infolist = gen_info(self.inputs.event_files)
        concatlist, nscans = self._concatenate_info(infolist)
        functional_runs = [filename_to_list(self.inputs.functional_runs)]
        realignment_parameters = []
        if isdefined(self.inputs.realignment_parameters):
            realignment_parameters = []
            for parfile in self.inputs.realignment_parameters:
                mc = np.loadtxt(parfile)
                if not realignment_parameters:
                    realignment_parameters.insert(0, mc)
                else:
                    realignment_parameters[0] = np.concatenate((realignment_parameters[0], mc))
        outliers = []
        if isdefined(self.inputs.outlier_files):
            outliers = [[]]
            for i, filename in enumerate(self.inputs.outlier_files):
                try:
                    out = np.loadtxt(filename, dtype=int)
                except IOError:
                    out = np.array([])
                if out.size>0:
                    if out.size == 1:
                        outliers[0].extend([(np.array(out)+sum(nscans[0:i])).tolist()])
                    else:
                        outliers[0].extend((np.array(out)+sum(nscans[0:i])).tolist())
        self._sessinfo = self._generate_standard_design(concatlist,
                                                  functional_runs=functional_runs,
                                                  realignment_parameters=realignment_parameters,
                                                  outliers=outliers)


class SpecifySparseModelInputSpec(SpecifyModelInputSpec):
    time_acquisition = traits.Float(0, mandatory=True,
                  desc = "Time in seconds to acquire a single image volume")
    volumes_in_cluster = traits.Range(1, usedefault=True,
            desc="Number of scan volumes in a cluster")
    model_hrf = traits.Bool(desc="model sparse events with hrf")
    stimuli_as_impulses = traits.Bool(True,
              desc = "Treat each stimulus to be impulse like.",
                                      usedefault=True)
    use_temporal_deriv = traits.Bool(requires=['model_hrf'],
           desc = "Create a temporal derivative in addition to regular regressor")
    scale_regressors = traits.Bool(True, desc="Scale regressors by the peak",
                                   usedefault=True)
    scan_onset = traits.Float(0.0,
              desc="Start of scanning relative to onset of run in secs",
                              usedefault=True)
    save_plot = traits.Bool(desc='save plot of sparse design calculation ' \
                            '(Requires matplotlib)')


class SpecifySparseModelOutputSpec(SpecifyModelOutputSpec):
    sparse_png_file = File(desc='PNG file showing sparse design')
    sparse_svg_file = File(desc='SVG file showing sparse design')


class SpecifySparseModel(SpecifyModel):
    """ Specify a sparse model that is compatible with spm/fsl designers

    References
    ----------

    .. [1] Ghosh et al. (2009) OHBM http://dl.dropbox.com/u/363467/OHBM2009_HRF.pdf

    Examples
    --------

    >>> from nipype.interfaces.base import Bunch
    >>> s = SpecifySparseModel()
    >>> s.inputs.input_units = 'secs'
    >>> s.inputs.functional_runs = ['functional2.nii', 'functional3.nii']
    >>> s.inputs.time_repetition = 6
    >>> s.inputs.time_acquisition = 2
    >>> s.inputs.high_pass_filter_cutoff = 128.
    >>> s.inputs.model_hrf = True
    >>> info = [Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]], durations=[[1]]), \
            Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]], durations=[[1]])]
    >>> s.inputs.subject_info = info

    """
    input_spec = SpecifySparseModelInputSpec
    output_spec = SpecifySparseModelOutputSpec

    def _gen_regress(self, i_onsets, i_durations, i_amplitudes, nscans):
        """Generates a regressor for a sparse/clustered-sparse acquisition
        """
        bplot = False
        if isdefined(self.inputs.save_plot) and self.inputs.save_plot:
            bplot=True
            import matplotlib
            matplotlib.use(config.get("execution", "matplotlib_backend"))
            import matplotlib.pyplot as plt
        TR = np.round(self.inputs.time_repetition*1000)  # in ms
        if self.inputs.time_acquisition:
            TA = np.round(self.inputs.time_acquisition*1000) # in ms
        else:
            TA = TR # in ms
        nvol = self.inputs.volumes_in_cluster
        SCANONSET = np.round(self.inputs.scan_onset*1000)
        total_time = TR*(nscans-nvol)/nvol + TA*nvol + SCANONSET
        SILENCE = TR-TA*nvol
        dt = TA/10.;
        durations  = np.round(np.array(i_durations)*1000)
        if len(durations) == 1:
            durations = durations*np.ones((len(i_onsets)))
        onsets = np.round(np.array(i_onsets)*1000)
        dttemp = gcd(TA, gcd(SILENCE, TR))
        if dt < dttemp:
            if dttemp % dt != 0:
                dt = gcd(dttemp, dt)
        if dt < 1:
            raise Exception("Time multiple less than 1 ms")
        iflogger.info("Setting dt = %d ms\n" % dt)
        npts = int(total_time/dt)
        times = np.arange(0, total_time, dt)*1e-3
        timeline = np.zeros((npts))
        timeline2 = np.zeros((npts))
        if isdefined(self.inputs.model_hrf) and self.inputs.model_hrf:
            hrf = spm_hrf(dt*1e-3)
        reg_scale = 1.0
        if self.inputs.scale_regressors:
            boxcar = np.zeros((50.*1e3/dt))
            if self.inputs.stimuli_as_impulses:
                boxcar[1.*1e3/dt] = 1.0
                reg_scale = float(TA/dt)
            else:
                boxcar[1.*1e3/dt:2.*1e3/dt] = 1.0
            if isdefined(self.inputs.model_hrf) and self.inputs.model_hrf:
                response = np.convolve(boxcar, hrf)
                reg_scale = 1./response.max()
                iflogger.info('response sum: %.4f max: %.4f'%(response.sum(), response.max()))
            iflogger.info('reg_scale: %.4f'%reg_scale)
        for i, t in enumerate(onsets):
            idx = int(t/dt)
            if i_amplitudes:
                if len(i_amplitudes)>1:
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
                    durations[i] = TA*nvol
                stimdur = np.ones((int(durations[i]/dt)))
                timeline2 = np.convolve(timeline2, stimdur)[0:len(timeline2)]
            timeline += timeline2
            timeline2[:] = 0
        if bplot:
            plt.subplot(4, 1, 2)
            plt.plot(times, timeline)
        if isdefined(self.inputs.model_hrf) and self.inputs.model_hrf:
            timeline = np.convolve(timeline, hrf)[0:len(timeline)]
            if isdefined(self.inputs.use_temporal_deriv) and self.inputs.use_temporal_deriv:
                #create temporal deriv
                timederiv = np.concatenate(([0], np.diff(timeline)))
        if bplot:
            plt.subplot(4, 1, 3)
            plt.plot(times, timeline)
            if isdefined(self.inputs.use_temporal_deriv) and self.inputs.use_temporal_deriv:
                plt.plot(times, timederiv)
        # sample timeline
        timeline2 = np.zeros((npts))
        reg = []
        regderiv = []
        for i, trial in enumerate(np.arange(nscans)/nvol):
            scanstart = int((SCANONSET + trial*TR + (i%nvol)*TA)/dt)
            #print total_time/dt, SCANONSET, TR, TA, scanstart, trial, i%2, int(TA/dt)
            scanidx = scanstart+np.arange(int(TA/dt))
            timeline2[scanidx] = np.max(timeline)
            reg.insert(i, np.mean(timeline[scanidx])*reg_scale)
            if isdefined(self.inputs.use_temporal_deriv) and self.inputs.use_temporal_deriv:
                regderiv.insert(i, np.mean(timederiv[scanidx])*reg_scale)
        if isdefined(self.inputs.use_temporal_deriv) and self.inputs.use_temporal_deriv:
            iflogger.info('orthoganlizing derivative w.r.t. main regressor')
            regderiv = orth(reg, regderiv)
        if bplot:
            plt.subplot(4, 1, 3)
            plt.plot(times, timeline2)
            plt.subplot(4, 1, 4)
            plt.bar(np.arange(len(reg)), reg, width=0.5)
            plt.savefig('sparse.png')
            plt.savefig('sparse.svg')
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
            if hasattr(info, 'amplitudes') and info.amplitudes:
                amplitudes = info.amplitudes[i]
            else:
                amplitudes = None
            regnames.insert(len(regnames), cond)
            regressor = self._gen_regress(scale_timings(info.onsets[i],
                                                        self.inputs.input_units,
                                                        'secs',
                                                        self.inputs.time_repetition),
                                          scale_timings(info.durations[i],
                                                        self.inputs.input_units,
                                                        'secs',
                                                        self.inputs.time_repetition),
                                           amplitudes,
                                           nscans)
            if isdefined(self.inputs.use_temporal_deriv) and self.inputs.use_temporal_deriv:
                reg.insert(len(reg), regressor[0])
                regnames.insert(len(regnames), cond+'_D')
                reg.insert(len(reg), regressor[1])
            else:
                reg.insert(len(reg), regressor)
            # need to deal with temporal and parametric modulators
        # for sparse-clustered acquisitions enter T1-effect regressors
        nvol = self.inputs.volumes_in_cluster
        if nvol > 1:
            for i in range(nvol-1):
                treg = np.zeros((nscans/nvol, nvol))
                treg[:, i] = 1
                reg.insert(len(reg), treg.ravel().tolist())
                regnames.insert(len(regnames), 'T1effect_%d'%i)
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
                nscans = img.get_shape()[3]
                reg, regnames = self._cond_to_regress(info, nscans)
                if hasattr(infoout[i], 'regressors') and infoout[i].regressors:
                    if not infoout[i].regressor_names:
                        infoout[i].regressor_names = ['R%d'%j for j in range(len(infoout[i].regressors))]
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
        super(SpecifySparseModel, self)._generate_design(infolist = sparselist)

    def _list_outputs(self):
        outputs = self._outputs().get()
        if not hasattr(self, '_sessinfo'):
            self._generate_design()
        outputs['session_info'] = self._sessinfo
        if isdefined(self.inputs.save_plot) and self.inputs.save_plot:
            outputs['sparse_png_file'] = os.path.join(os.getcwd(), 'sparse.png')
            outputs['sparse_svg_file'] = os.path.join(os.getcwd(), 'sparse.svg')
        return outputs

'''

Need to figure out how this component will work!!! multiple inheritence is causing a big headache

class SpecifySparseSPMModelInputSpec(SpecifySPMModelInputSpec, SpecifySparseModelInputSpec):
    pass

class SpecifySparseSPMModel(SpecifySparseModel, SpecifySPMModel):
    """Combines SPM specific options with sparse options
    """
    input_spec = SpecifySparseSPMModelInputSpec
    output_spec = SpecifySparseModelOutputSpec

    def _generate_design(self, infolist=None):
        raise Exception('not working yet')
        if (self.inputs.input_units == 'scans') and (self.inputs.output_units == 'secs'):
            if isdefined(self.inputs.volumes_in_cluster) and (self.inputs.volumes_in_cluster > 1):
                raise NotImplementedError("Cannot scale timings if times are scans and acquisition is clustered")
        if isdefined(self.inputs.subject_info):
            infolist = self.inputs.subject_info
        else:
            infolist = gen_info(self.inputs.event_files)
        clusterlist = self._generate_clustered_design(infolist)
        if not isdefined(self.inputs.concatenate_runs):
            super(SpecifySparseSPMModel, self)._generate_design(infolist=clusterlist)
        else:
            self._generate_spm_design(infolist=clusterlist)
'''
