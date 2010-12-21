# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
The rapidart module provides routines for artifact detection and region of
interest analysis.

These functions include:

  * SpecifyModel: allows specification of sparse and non-sparse models
"""

import os
from copy import deepcopy

import numpy as np
from scipy.signal import convolve
from scipy.special import gammaln
#from scipy.stats.distributions import gamma

from nibabel import load
from nipype.interfaces.base import BaseInterface, TraitedSpec,\
 InputMultiPath, traits, File
from nipype.utils.misc import isdefined
from nipype.utils.filemanip import filename_to_list, loadflat

class SpecifyModelInputSpec(TraitedSpec):
    subject_id = traits.Either(traits.Str(),traits.Int(),
        desc ="This input is deprecated and will be removed in the future releases. Update your code.")
    subject_info = traits.List(mandatory=True,
                          desc= "List subject specific condition information")
    """    . If all
            subjects had the same stimulus presentation schedule,
            then this function can return the same structure
            independent of the subject. This function must return a
            list of dicts with the list length equal to the number of
            sessions. The dicts should contain the following
            information.

            conditions : list of names

            onsets : lists of onsets corresponding to each
                condition

            durations : lists of durations corresponding to each
                condition. Should be left to a single 0 if all
                events are being modelled as impulses.

            amplitudes : lists of amplitudes for each event. This
                is ignored by SPM

            tmod : lists of conditions that should be temporally
               modulated. Should default to None if not being used.

            pmod : list of dicts corresponding to conditions
                name : name of parametric modulator

                param : values of the modulator

                poly : degree of modulation

            regressors : list of dicts or matfile
                names : list of names corresponding to each
                   column. Should be None if automatically
                   assigned.
                values : lists of values for each regressor
                kernel : list of convolution kernel

    """
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
             desc = "Units of event onsets and durations (secs or scans)")
    output_units = traits.Enum('secs', 'scans', mandatory=True,
             desc = "Units of design event onsets and durations " \
                                   "(secs or scans)")
    high_pass_filter_cutoff = traits.Float(desc = \
                                     "High-pass filter cutoff in secs")
    concatenate_runs = traits.Bool(False, usedefault=True,
            desc="Concatenating all runs to look like a single session.")
    time_repetition = traits.Float(mandatory=True,
        desc = "Time between the start of one volume to the start of " \
                                       "the next image volume.")
    
    # Not implemented yet
    #polynomial_order = traits.Range(-1, low=-1, 
    #        desc ="Number of polynomial functions to model high pass filter.")
    #generate_design = traits.Bool(False, usedefault=True,
    #      desc="Generate a design matrix")

        #Sparse and clustered-sparse specific options
    is_sparse = traits.Bool(False, usedefault = True,
                            desc="indicates whether paradigm is sparse")
    time_acquisition = traits.Float(0,
                  desc = "Time in seconds to acquire a single image volume")
    volumes_in_cluster = traits.Range(low=0,
            desc="Number of scan volumes in a cluster")
    model_hrf = traits.Bool(desc="model sparse events with hrf")
    stimuli_as_impulses = traits.Bool(True,
              desc = "Treat each stimulus to be impulse like.",
                                      usedefault=True)
    scan_onset = traits.Float(0.0,
              desc="Start of scanning relative to onset of run in secs",
                              usedefault=True)
    
class SpecifyModelOutputSpec(TraitedSpec):
    session_info = traits.Any(desc="session info for level1designs")
    #design_file = File(desc="design file")

class SpecifyModel(BaseInterface):
    """Makes a model specification

    Parameters
    ----------
    inputs : dict
        key, value pairs that will update the SpecifyModel.inputs
        attributes. See self.inputs_help() for a list attributes.
    
    Attributes
    ----------
    inputs : :class:`nipype.interfaces.base.Bunch`
        Options that can be passed to spm_spm via a job structure
    cmdline : str
        String used to call matlab/spm via SpmMatlabCommandLine
        interface
        
    Other Parameters
    ----------------
    To see optional arguments SpecifyModel().inputs_help()

    """
    input_spec = SpecifyModelInputSpec
    output_spec = SpecifyModelOutputSpec
    
    def _scaletimings(self,timelist,input_units=None,output_units=None):
        if input_units is None:
            input_units = self.inputs.input_units
        if output_units is None:
            output_units = self.inputs.output_units
        if input_units==output_units:
            self._scalefactor = 1.
        if (input_units == 'scans') and (output_units == 'secs'):
            if isdefined(self.inputs.volumes_in_cluster) and (self.inputs.volumes_in_cluster > 1):
                raise NotImplementedError("cannot scale timings if times are scans and acquisition is clustered")
            else:
                self._scalefactor = self.inputs.time_repetition
        if (input_units == 'secs') and (output_units == 'scans'):
            self._scalefactor = 1./self.inputs.time_repetition

        #if self._scalefactor > 1:
        timelist = [np.max([0.,self._scalefactor*t]) for t in timelist]
        #else:
        #    timelist = [round(self._scalefactor*t) for t in timelist]
            
        return timelist
    
    def _gcd(self,a,b):
        """Returns the greates common divisor of two integers

        uses Euclid's algorithm
        """
        while b > 0: a,b = b, a%b
        return a

    def _spm_hrf(self,RT,P=[],fMRI_T=16):
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
        
        >>> import nipype.algorithms.modelgen as model
        >>> print model.SpecifyModel()._spm_hrf(2)
        [  0.00000000e+00   8.65660810e-02   3.74888236e-01   3.84923382e-01
           2.16117316e-01   7.68695653e-02   1.62017720e-03  -3.06078117e-02
          -3.73060781e-02  -3.08373716e-02  -2.05161334e-02  -1.16441637e-02
          -5.82063147e-03  -2.61854250e-03  -1.07732374e-03  -4.10443522e-04
          -1.46257507e-04]
        """
        p     = np.array([6,16,1,1,6,0,32],dtype=float)
        if len(P)>0:
            p[0:len(P)] = P

        _spm_Gpdf = lambda x,h,l: np.exp(h*np.log(l)+(h-1)*np.log(x)-(l*x)-gammaln(h))
        # modelled hemodynamic response function - {mixture of Gammas}
        dt    = RT/float(fMRI_T)
        u     = np.arange(0,int(p[6]/dt+1)) - p[5]/dt
        # the following code using scipy.stats.distributions.gamma
        # doesn't return the same result as the spm_Gpdf function
        # hrf   = gamma.pdf(u,p[0]/p[2],scale=dt/p[2]) - gamma.pdf(u,p[1]/p[3],scale=dt/p[3])/p[4]
        hrf   = _spm_Gpdf(u,p[0]/p[2],dt/p[2]) - _spm_Gpdf(u,p[1]/p[3],dt/p[3])/p[4]
        idx   = np.arange(0,int((p[6]/RT)+1))*fMRI_T
        hrf   = hrf[idx]
        hrf   = hrf/np.sum(hrf)
        return hrf
        
    def _gen_regress(self,i_onsets,i_durations,i_amplitudes,nscans,bplot=False):
        """Generates a regressor for a sparse/clustered-sparse acquisition

           see Ghosh et al. (2009) OHBM 2009
        """
        if bplot:
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
        dttemp = self._gcd(TA,self._gcd(SILENCE,TR))
        if dt < dttemp:
            if dttemp % dt != 0:
                dt = self._gcd(dttemp,dt)
        if dt < 1:
            raise Exception("Time multiple less than 1 ms")
        print "Setting dt = %d ms\n" % dt
        npts = int(total_time/dt)
        times = np.arange(0,total_time,dt)*1e-3
        timeline = np.zeros((npts))
        timeline2 = np.zeros((npts))
        hrf = self._spm_hrf(dt*1e-3)
        for i,t in enumerate(onsets):
            idx = int(t/dt)
            if i_amplitudes:
                if len(i_amplitudes)>1:
                    timeline2[idx] = i_amplitudes[i]
                else:
                    timeline2[idx] = i_amplitudes[0]
            else:
                timeline2[idx] = 1
            if bplot:
                plt.subplot(4,1,1)
                plt.plot(times,timeline2)
            if not self.inputs.stimuli_as_impulses:
                if durations[i] == 0:
                    durations[i] = TA*nvol
                stimdur = np.ones((int(durations[i]/dt)))
                timeline2 = convolve(timeline2,stimdur)[0:len(timeline2)]
            timeline += timeline2
            timeline2[:] = 0
        if bplot:
            plt.subplot(4,1,2)
            plt.plot(times,timeline)
        if self.inputs.model_hrf:
            timeline = convolve(timeline,hrf)[0:len(timeline)]
        if bplot:
            plt.subplot(4,1,3)
            plt.plot(times,timeline)
        # sample timeline
        timeline2 = np.zeros((npts))
        reg = []
        for i,trial in enumerate(np.arange(nscans)/nvol):
            scanstart = int((SCANONSET + trial*TR + (i%nvol)*TA)/dt)
            #print total_time/dt, SCANONSET, TR, TA, scanstart, trial, i%2, int(TA/dt)
            scanidx = scanstart+np.arange(int(TA/dt))
            timeline2[scanidx] = np.max(timeline)
            reg.insert(i,np.mean(timeline[scanidx]))
        if bplot:
            plt.subplot(4,1,3)
            plt.plot(times,timeline2)
            plt.subplot(4,1,4)
            plt.bar(np.arange(len(reg)),reg,width=0.5)
        return reg

    def _cond_to_regress(self,info,nscans):
        """Converts condition information to full regressors
        """
        reg = []
        regnames = info.conditions
        for i,c in enumerate(info.conditions):
            if info.amplitudes:
                amplitudes = info.amplitudes[i]
            else:
                amplitudes = None
            reg.insert(i,self._gen_regress(self._scaletimings(info.onsets[i],output_units='secs'),
                                           self._scaletimings(info.durations[i],output_units='secs'),
                                           amplitudes,
                                           nscans))
            # need to deal with temporal and parametric modulators
        # for sparse-clustered acquisitions enter T1-effect regressors
        nvol = self.inputs.volumes_in_cluster
        if nvol > 1:
            for i in range(nvol-1):
                treg = np.zeros((nscans/nvol,nvol))
                treg[:,i] = 1
                reg.insert(len(reg),treg.ravel().tolist())
        return reg,regnames
    
    def _generate_clustered_design(self,infolist):
        """Generates condition information for sparse-clustered
        designs.
        
        """
        infoout = deepcopy(infolist)
        for i,info in enumerate(infolist):
            infoout[i].conditions = None
            infoout[i].onsets = None
            infoout[i].durations = None
            if info.conditions:
                img = load(self.inputs.functional_runs[i])
                nscans = img.get_shape()[3]
                reg,regnames = self._cond_to_regress(info,nscans)
                if not infoout[i].regressors:
                    infoout[i].regressors = []
                    infoout[i].regressor_names = []
                else:
                    if not infoout[i].regressor_names:
                        infoout[i].regressor_names = ['R%d'%j for j in range(len(infoout[i].regressors))] 
                for j,r in enumerate(reg):
                    regidx = len(infoout[i].regressors)
                    infoout[i].regressor_names.insert(regidx,regnames[j])
                    infoout[i].regressors.insert(regidx,r)
        return infoout
    
    def _generate_standard_design(self,infolist,
                                  functional_runs=None,
                                  realignment_parameters=None,
                                  outliers=None):
        """ Generates a standard design matrix paradigm
        """
        sessinfo = []
        #                dt = np.dtype({'names':['name', 'param', 'poly'],
        #                               'formats':[object, object, object]})
        #                sessinfo[i]['pmod'] = np.zeros((len(info.pmod),), dtype=dt)
        for i,info in enumerate(infolist):
            sessinfo.insert(i,dict(cond=[]))
            if isdefined(self.inputs.high_pass_filter_cutoff):
                sessinfo[i]['hpf'] = np.float(self.inputs.high_pass_filter_cutoff)
            if info.conditions:
                for cid,cond in enumerate(info.conditions):
                    sessinfo[i]['cond'].insert(cid,dict())
                    sessinfo[i]['cond'][cid]['name']  = info.conditions[cid]
                    sessinfo[i]['cond'][cid]['onset'] = self._scaletimings(info.onsets[cid])
                    sessinfo[i]['cond'][cid]['duration'] = self._scaletimings(info.durations[cid])
                    if info.tmod and len(info.tmod)>cid:
                        sessinfo[i]['cond'][cid]['tmod'] = info.tmod[cid]
                    if info.pmod and len(info.pmod)>cid:
                        if info.pmod[cid]:
                            sessinfo[i]['cond'][cid]['pmod'] = []
                            for j,name in enumerate(info.pmod[cid].name):
                                sessinfo[i]['cond'][cid]['pmod'].insert(j,{})
                                sessinfo[i]['cond'][cid]['pmod'][j]['name'] = name
                                sessinfo[i]['cond'][cid]['pmod'][j]['poly'] = info.pmod[cid].poly[j]
                                sessinfo[i]['cond'][cid]['pmod'][j]['param'] = info.pmod[cid].param[j]
            sessinfo[i]['regress']= []
            if info.regressors is not None:
                for j,r in enumerate(info.regressors):
                    sessinfo[i]['regress'].insert(j,dict(name='',val=[]))
                    if info.regressor_names is not None:
                        sessinfo[i]['regress'][j]['name'] = info.regressor_names[j]
                    else:
                        sessinfo[i]['regress'][j]['name'] = 'UR%d'%(j+1)
                    sessinfo[i]['regress'][j]['val'] = info.regressors[j]
            if isdefined(functional_runs):
                sessinfo[i]['scans'] = functional_runs[i]#scans_for_fnames(filename_to_list(functional_runs[i]),keep4d=False)
            else:
                raise Exception("No functional data information provided for model")
        if isdefined(realignment_parameters):
            for i,rp in enumerate(realignment_parameters):
                mc = realignment_parameters[i]
                for col in range(mc.shape[1]):
                    colidx = len(sessinfo[i]['regress'])
                    sessinfo[i]['regress'].insert(colidx,dict(name='',val=[]))
                    sessinfo[i]['regress'][colidx]['name'] = 'Realign%d'%(col+1)
                    sessinfo[i]['regress'][colidx]['val']  = mc[:,col].tolist()
        if isdefined(outliers):
            for i,out in enumerate(outliers):
                numscans = 0
                for f in filename_to_list(sessinfo[i]['scans']):
                    numscans += load(f).get_shape()[3]
                for j,scanno in enumerate(out):
                    if True:
                        colidx = len(sessinfo[i]['regress'])
                        sessinfo[i]['regress'].insert(colidx,dict(name='',val=[]))
                        sessinfo[i]['regress'][colidx]['name'] = 'Outlier%d'%(j+1)
                        sessinfo[i]['regress'][colidx]['val']  = np.zeros((1,numscans))[0].tolist()
                        sessinfo[i]['regress'][colidx]['val'][int(scanno)] = 1
                    else:
                        cid = len(sessinfo[i]['cond'])
                        sessinfo[i]['cond'].insert(cid,dict())
                        sessinfo[i]['cond'][cid]['name'] = "O%d"%(j+1)
                        sessinfo[i]['cond'][cid]['onset'] = self._scaletimings([scanno])
                        sessinfo[i]['cond'][cid]['duration'] = [0]
        return sessinfo
    
    def _concatenate_info(self,infolist):
        nscans = []
        for i,f in enumerate(filename_to_list(self.inputs.functional_runs)):
            if isinstance(f,list):
                numscans = len(f)
            elif isinstance(f,str):
                img = load(f)
                numscans = img.get_shape()[3]
            else:
                raise Exception('Functional input not specified correctly')
            nscans.insert(i, numscans)
        # now combine all fields into 1
        # names,onsets,durations,amplitudes,pmod,tmod,regressor_names,regressors
        infoout = infolist[0]
        for i,info in enumerate(infolist[1:]):
                #info.[conditions,tmod] remain the same
            if info.onsets:
                for j,val in enumerate(info.onsets):
                    if self.inputs.input_units == 'secs':
                        infoout.onsets[j].extend((np.array(info.onsets[j])+
                                                  self.inputs.time_repetition*sum(nscans[0:(i+1)])).tolist())
                    else:
                        infoout.onsets[j].extend((np.array(info.onsets[j])+sum(nscans[0:(i+1)])).tolist())
                for j,val in enumerate(info.durations):
                    if len(val) > 1:
                        infoout.durations[j].extend(info.durations[j])
                if info.pmod:
                    for j,val in enumerate(info.pmod):
                        if val:
                            for key,data in enumerate(val.param):
                                infoout.pmod[j].param[key].extend(data)
            if info.regressors:
                #assumes same ordering of regressors across different
                #runs and the same names for the regressors
                for j,v in enumerate(info.regressors):
                    infoout.regressors[j].extend(info.regressors[j])
            #insert session regressors
            if not infoout.regressors:
                infoout.regressors = []
            onelist = np.zeros((1,sum(nscans)))
            onelist[0,sum(nscans[0:(i)]):sum(nscans[0:(i+1)])] = 1
            infoout.regressors.insert(len(infoout.regressors),onelist.tolist()[0])
        return [infoout],nscans
    
    def _generate_design(self):
        infolist = self.inputs.subject_info
        if self.inputs.concatenate_runs:
            infolist,nscans = self._concatenate_info(infolist)
            functional_runs = [filename_to_list(self.inputs.functional_runs)]
        else:
            functional_runs = filename_to_list(self.inputs.functional_runs)
        realignment_parameters = []
        if isdefined(self.inputs.realignment_parameters):
            rpfiles = filename_to_list(self.inputs.realignment_parameters)
            realignment_parameters.insert(0,np.loadtxt(rpfiles[0]))
            for rpf in rpfiles[1:]:
                mc = np.loadtxt(rpf)
                if self.inputs.concatenate_runs:
                    realignment_parameters[0] = np.concatenate((realignment_parameters[0],mc))
                else:
                    realignment_parameters.insert(len(realignment_parameters),mc)
        outliers = []
        if isdefined(self.inputs.outlier_files):
            outfiles = filename_to_list(self.inputs.outlier_files)
            try:
                outindices = np.loadtxt(outfiles[0],dtype=int)
                if outindices.size == 1:
                    outliers.insert(0,[outindices.tolist()])
                else:
                    outliers.insert(0,outindices.tolist())
            except IOError:
                outliers.insert(0,[])
            for i,rpf in enumerate(outfiles[1:]):
                try:
                    out = np.loadtxt(rpf,dtype=int)
                except IOError:
                    out = np.array([])
                if self.inputs.concatenate_runs:
                    if out.size>0:
                        if out.size == 1:
                            outliers[0].extend([(np.array(out)+sum(nscans[0:(i+1)])).tolist()])
                        else:
                            outliers[0].extend((np.array(out)+sum(nscans[0:(i+1)])).tolist())
                else:
                    if out.size == 1:
                        outliers.insert(len(outliers),[out.tolist()])
                    else:
                        outliers.insert(len(outliers),out.tolist())
        if self.inputs.is_sparse:
            infolist = self._generate_clustered_design(infolist)
            
        self.sessinfo = self._generate_standard_design(infolist,
                                                  functional_runs=functional_runs,
                                                  realignment_parameters=realignment_parameters,
                                                  outliers=outliers)

    def _run_interface(self, runtime):
        """
        """
        self._generate_design()
        runtime.returncode = 0
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        if not hasattr(self, 'sessinfo'): #backwards compatibility
            try:
                data = loadflat(os.path.join(os.getcwd(),'%s_modelspec.npz'%self.inputs.subject_id))
                if isinstance(data['session_info'], dict):
                    self.sessinfo = [data['session_info']]
                else:
                    self.sessinfo = data['session_info']
            except IOError:
                self._generate_design()
        outputs['session_info'] = self.sessinfo
        
        return outputs
