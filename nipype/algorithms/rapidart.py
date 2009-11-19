"""
The rapidart module provides routines for artifact detection and region of
interest analysis.

These functions include:

  * ArtifactDetect: performs artifact detection on functional images
    
  * StimulusCorrelation: determines correlation between stimuli
    schedule and movement/intensity parameters

"""

from nipype.interfaces.base import Bunch, InterfaceResult, Interface
from nipype.externals.pynifti import load
from nipype.utils.filemanip import fname_presuffix, fnames_presuffix, filename_to_list, list_to_filename
from nipype.utils.misc import find_indices
import os
from glob import glob
from copy import deepcopy
import numpy as np
from scipy import signal
import scipy.io as sio
#import matplotlib as mpl
#import matplotlib.pyplot as plt
#import traceback


class ArtifactDetect(Interface):
    """Detects outliers in a functional imaging series depending on
    the intensity and motion parameters. It also generates stimulus
    correlated motion information and other statistics.
    """

    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)

    def inputs_help(self):
        """
        Parameters
        ----------
        realigned_files : filename(s)
            Names of realigned functional data files
        realignment_parameters : filename(s)
            Names of realignment parameters corresponding to the
            functional data files
        parameter_source : string
            Are the movement parameters from SPM or FSL or from
            Siemens PACE data. Options: SPM, FSL or Siemens
        use_differences : 2-element boolean list
            Use differences between successive motion (first element)
            and intensity paramter (second element) estimates in order
            to determine outliers.  (default is [True, True])
        use_norm : boolean, optional
            Use the norm of the motion parameters in order to
            determine outliers.  Requires ``norm_threshold`` to be set.
            (default is True)
        norm_threshold: float
            Threshold to use to detect motion-related outliers when
            normalized motion is being used (see ``use_norm``)
        rotation_threshold : float
            Threshold to use to detect rotation-related outliers
        translation_threshold : float
            Threshold to use to detect translation-related outliers
        zintensity_threshold : float
            Intensity Z-threshold use to detection images that
            deviate from the mean
        mask_type : {'spm_global', 'file', 'thresh'}
            Type of mask that should be used to mask the functional
            data.  *spm_global* uses an spm_global like calculation to
            determine the brain mask.  *file* specifies a brain mask
            file (should be an image file consisting of 0s and 1s).
            *thresh* specifies a threshold to use.  By default all
            voxels are used, unless one of these mask types are
            defined.
        mask_file : filename
            Mask file to be used is mask_type is 'file'.
        mask_threshold : float
            Mask threshold to be used if mask_type is 'thresh'.
        intersect_mask : boolean
            Intersect the masks when computed from spm_global.
            (default is True)

        """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(realigned_files=None,
                            realignment_parameters=None,
                            parameter_source=None,
                            use_differences=[True,True],
                            use_norm=True,
                            norm_threshold=None,
                            rotation_threshold=None,
                            translation_threshold=None,
                            zintensity_threshold=None,
                            mask_type=None,
                            mask_file=None,
                            mask_threshold=None,
                            intersect_mask=True)
        
    def outputs_help(self):
        """print out the help from the outputs routine
        """
        print self.outputs.__doc__
        
    def _get_output_filenames(self,motionfile,output_dir):
        """Generate output files based on motion filenames

        Parameters
        ----------

        motionfile: file/string
            Filename for motion parameter file
        output_dir: string
            output directory in which the files will be generated 
        """
        (filepath,filename) = os.path.split(motionfile)
        (filename,ext) = os.path.splitext(filename)
        artifactfile  = os.path.join(output_dir,''.join(('art.',filename,'_outliers.txt')))
        intensityfile = os.path.join(output_dir,''.join(('global_intensity.',filename,'.txt')))
        statsfile     = os.path.join(output_dir,''.join(('stats.',filename,'.txt')))
        normfile     = os.path.join(output_dir,''.join(('norm.',filename,'.txt')))
        return artifactfile,intensityfile,statsfile,normfile

    def outputs(self):
        """Generate a bunch containing the output fields.

        Parameters
        ----------
        outlier_files : filename(s)
            One file for each functional run containing a list of
            0-based indices corresponding to outlier volumes
        intensity_files : filename(s)
            One file for each functional run containing the global
            intensity values determined from the brainmask
        statistic_files : filename(s)
            One file for each functional run containing
            information about the different types of artifacts and
            if design info is provided then details of stimulus
            correlated motion and a listing or artifacts by event
            type. 
        """
        outputs = Bunch(outlier_files=None,
                        intensity_files=None,
                        statistic_files=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        for i,f in enumerate(filename_to_list(self.inputs.realigned_files)):
            outlierfile,intensityfile,statsfile,normfile = self._get_output_filenames(f,self.inputs.get('cwd','.'))
            outlierfile = glob(outlierfile)
            assert len(outlierfile)==1, 'Outlier file %s not found'%outlierfile
            if outputs.outlier_files is None:
                outputs.outlier_files = []
            outputs.outlier_files.insert(i,outlierfile[0])
            intensityfile = glob(intensityfile)
            assert len(intensityfile)==1, 'Outlier file %s not found'%intensityfile
            if outputs.intensity_files is None:
                outputs.intensity_files = []
            outputs.intensity_files.insert(i,intensityfile[0])
            statsfile = glob(statsfile)
            assert len(statsfile)==1, 'Outlier file %s not found'%statsfile
            if outputs.statistic_files is None:
                outputs.statistic_files = []
            outputs.statistic_files.insert(i,statsfile[0])
        if outputs.outlier_files is not None:
            outputs.outlier_files = list_to_filename(outputs.outlier_files)
            outputs.intensity_files = list_to_filename(outputs.intensity_files)
            outputs.statistic_files = list_to_filename(outputs.statistic_files)
        return outputs

    def get_input_info(self):
        return []

    def _get_affine_matrix(self,params):
        """Returns an affine matrix given a set of parameters

        params : np.array (upto 12 long)
        [translation (3), rotation (3,xyz, radians), scaling (3),
        shear/affine (3)]
        
        """
        rotfunc = lambda x : np.array([[np.cos(x), np.sin(x)],[-np.sin(x),np.cos(x)]])
        q = np.array([0,0,0,0,0,0,1,1,1,0,0,0])
        if len(params)<12:
            params=np.hstack((params,q[len(params):]))
        params.shape = (len(params),)
        # Translation
        T = np.eye(4)
        T[0:3,-1] = params[0:3] #np.vstack((np.hstack((np.eye(3),params[0:3,])),np.array([0,0,0,1])))
        # Rotation
        Rx = np.eye(4)
        Rx[1:3,1:3] = rotfunc(params[3])
        Ry = np.eye(4)
        Ry[(0,0,2,2),(0,2,0,2)] = rotfunc(params[4]).ravel()
        Rz = np.eye(4)
        Rz[0:2,0:2] = rotfunc(params[5])
        # Scaling
        S = np.eye(4)
        S[0:3,0:3] = np.diag(params[6:9])
        # Shear
        Sh = np.eye(4)
        Sh[(0,0,1),(1,2,2)] = params[9:12]

        return np.dot(T,np.dot(Rx,np.dot(Ry,np.dot(Rz,np.dot(S,Sh)))))
        

    def _calc_norm(self,mc,use_differences):
        """Calculates the maximum overall displacement of the midpoints
        of the faces of a cube due to translation and rotation.

        Parameters
        ----------
        mc : motion parameter estimates
            [3 translation, 3 rotation (radians)]
        use_differences : boolean

        Returns
        -------

        norm : at each time point
        
        """
        respos=np.diag([70,70,75]);resneg=np.diag([-70,-110,-45]);
        # respos=np.diag([50,50,50]);resneg=np.diag([-50,-50,-50]);
        # XXX - SG why not the above box
        cube_pts = np.vstack((np.hstack((respos,resneg)),np.ones((1,6))))
        newpos = np.zeros((mc.shape[0],18))
        for i in range(mc.shape[0]):
            newpos[i,:] = np.dot(self._get_affine_matrix(mc[i,:]),cube_pts)[0:3,:].ravel()
        normdata = np.zeros(mc.shape[0])
        if use_differences:
            newpos = np.concatenate((np.zeros((1,18)),np.diff(newpos,n=1,axis=0)),axis=0)
            for i in range(newpos.shape[0]):
                normdata[i] = np.max(np.sqrt(np.sum(np.reshape(np.power(np.abs(newpos[i,:]),2),(3,6)),axis=0)))
        else:
            #if not registered to mean we may want to use this
            #mc_sum = np.sum(np.abs(mc),axis=1)
            #ref_idx = find_indices(mc_sum == np.min(mc_sum))
            #ref_idx = ref_idx[0]
            #newpos = np.abs(newpos-np.kron(np.ones((newpos.shape[0],1)),newpos[ref_idx,:]))
            newpos = np.abs(signal.detrend(newpos,axis=0,type='constant'))
            normdata = np.sqrt(np.mean(np.power(newpos,2),axis=1))
        return normdata
    
    def _detect_outliers_core(self,imgfile,motionfile,cwd='.'):
        """
        Core routine for detecting outliers
        
        Parameters
        ----------
        imgfile :
        motionfile :
        """
        # read in motion parameters
        mc_in = np.loadtxt(motionfile)
        mc = deepcopy(mc_in)
        if self.inputs.parameter_source == 'SPM':
            pass
        elif self.inputs.parameter_source == 'FSL':
            mc = mc[:,[3,4,5,0,1,2]]
        elif self.inputs.parameter_source == 'Siemens':
            Exception("Siemens PACE format not implemented yet")
        else:
            Exception("Unknown source for movement parameters")
            
        if self.inputs.use_norm:
            # calculate the norm of the motion parameters
            normval = self._calc_norm(mc,self.inputs.use_differences[0])
            tidx = find_indices(normval>self.inputs.norm_threshold)
            ridx = find_indices(normval<0)
        else:
            if self.inputs.use_differences[0]:
                mc = np.concatenate( (np.zeros((1,6)),np.diff(mc_in,n=1,axis=0)) , axis=0)
            traval = mc[:,0:3]  # translation parameters (mm)
            rotval = mc[:,3:6]  # rotation parameters (rad)
            tidx = find_indices(np.sum(abs(traval)>self.inputs.translation_threshold,1)>0)
            ridx = find_indices(np.sum(abs(rotval)>self.inputs.rotation_threshold,1)>0)

        # read in functional image
        nim = load(imgfile)

        # compute global intensity signal
        (x,y,z,timepoints) = nim.get_shape()

        data = nim.get_data()
        g = np.zeros((timepoints,1))
        masktype = self.inputs.mask_type
        if  masktype == 'spm_global':  # spm_global like calculation
            intersect_mask = self.inputs.intersect_mask
            if intersect_mask:
                mask = np.ones((x,y,z),dtype=bool)
                for t0 in range(timepoints):
                    vol   = data[:,:,:,t0]
                    mask  = mask*(vol>(np.mean(vol)/8))
                for t0 in range(timepoints):
                    vol   = data[:,:,:,t0]                    
                    g[t0] = np.mean(vol[mask])
                if len(find_indices(mask))<(np.prod((x,y,z))/10):
                    intersect_mask = False
                    g = np.zeros((timepoints,1))
            if not intersect_mask:
                for t0 in range(timepoints):
                    vol   = data[:,:,:,t0]
                    mask  = vol>(np.mean(vol)/8)
                    g[t0] = np.mean(vol[mask])
        elif masktype == 'file': # uses a mask image to determine intensity
            mask = load(self.inputs.mask_file).get_data()
            mask = mask>0.5
            for t0 in range(timepoints):
                vol = data[:,:,:,t0]
                g[t0] = np.mean(vol[mask])
        elif masktype == 'thresh': # uses a fixed signal threshold
            for t0 in range(timepoints):
                vol   = data[:,:,:,t0]
                mask  = vol>self.inputs.mask_threshold
                g[t0] = np.mean(vol[mask])
        else:
            mask = np.ones((x,y,z))
            g = np.mean(data[mask>0,:],1)

        # compute normalized intensity values
        gz = signal.detrend(g,axis=0)       # detrend the signal
        if self.inputs.use_differences[1]:
            gz = np.concatenate( (np.zeros((1,1)),np.diff(gz,n=1,axis=0)) , axis=0)
        gz = (gz-np.mean(gz))/np.std(gz)    # normalize the detrended signal
        iidx = find_indices(abs(gz)>self.inputs.zintensity_threshold)

        outliers = np.unique(np.union1d(iidx,np.union1d(tidx,ridx)))
        artifactfile,intensityfile,statsfile,normfile = self._get_output_filenames(imgfile,cwd)
        
        # write output to outputfile
        np.savetxt(artifactfile, outliers, fmt='%d', delimiter=' ')
        np.savetxt(intensityfile, g, fmt='%.2f', delimiter=' ')
        if self.inputs.use_norm:
            np.savetxt(normfile, normval, fmt='%.4f', delimiter=' ')

        file = open(statsfile,'w')
        file.write("Stats for:\n")
        file.write("Motion file: %s\n" % motionfile)
        file.write("Functional file: %s\n" % imgfile)
        file.write("Motion:\n")
        file.write("Number of Motion Outliers: %d\n"%len(np.union1d(tidx,ridx)))
        file.write("Motion (original):\n")
        file.write( ''.join(('mean: ',str(np.mean(mc_in,axis=0)),'\n')))
        file.write( ''.join(('min: ',str(np.min(mc_in,axis=0)),'\n')))
        file.write( ''.join(('max: ',str(np.max(mc_in,axis=0)),'\n')))
        file.write( ''.join(('std: ',str(np.std(mc_in,axis=0)),'\n')))
        if self.inputs.use_norm:
            if self.inputs.use_differences[0]:
                file.write("Motion (norm-differences):\n")
            else:
                file.write("Motion (norm):\n")
            file.write( ''.join(('mean: ',str(np.mean(normval,axis=0)),'\n')))
            file.write( ''.join(('min: ',str(np.min(normval,axis=0)),'\n')))
            file.write( ''.join(('max: ',str(np.max(normval,axis=0)),'\n')))
            file.write( ''.join(('std: ',str(np.std(normval,axis=0)),'\n')))
        elif self.inputs.use_differences[0]:
            file.write("Motion (differences):\n")
            file.write( ''.join(('mean: ',str(np.mean(mc,axis=0)),'\n')))
            file.write( ''.join(('min: ',str(np.min(mc,axis=0)),'\n')))
            file.write( ''.join(('max: ',str(np.max(mc,axis=0)),'\n')))
            file.write( ''.join(('std: ',str(np.std(mc,axis=0)),'\n')))
        if self.inputs.use_differences[1]:
            file.write("Normalized intensity:\n")
        else:
            file.write("Intensity:\n")
        file.write("Number of Intensity Outliers: %d\n"%len(iidx))
        file.write( ''.join(('min: ',str(np.min(gz,axis=0)),'\n')))
        file.write( ''.join(('max: ',str(np.max(gz,axis=0)),'\n')))
        file.write( ''.join(('mean: ',str(np.mean(gz,axis=0)),'\n')))
        file.write( ''.join(('std: ',str(np.std(gz,axis=0)),'\n')))
        file.close()

    def run(self, **inputs):
        """Execute this module.
        """
        funcfilelist = filename_to_list(self.inputs.realigned_files)
        motparamlist = filename_to_list(self.inputs.realignment_parameters)
        for i,imgf in enumerate(funcfilelist):
            self._detect_outliers_core(imgf,motparamlist[i],
                                       self.inputs.get('cwd','.'))
        runtime = Bunch(returncode=0,
                        messages=None,
                        errmessages=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)

class StimulusCorrelation(Interface):
    """Determines if stimuli are correlated with motion or intensity
    parameters.

    Currently this class supports an SPM generated design matrix and
    requires intensity parameters. This implies that one must run
    ArtifactDetect and :class:`nipype.interfaces.spm.Level1Design`
    prior to running this or provide an SPM.mat file and intensity
    parameters through some other means.
    """

    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)

    def inputs_help(self):
        """
        Parameters
        ----------
        realignment_parameters : filename(s)
            Names of realignment parameters corresponding to the
            functional data files
        intensity_values : filename(s)
            Name of file containing intensity values
        spm_mat_file : filename
            SPM mat file (use pre-estimate SPM.mat file)
        concatenated_design : boolean
            state if the design matrix contains concatenated sessions
        """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(realignment_parameters=None,
                            intensity_values=None,
                            spm_mat_file=None,
                            concatenated_design=None)
        
    def outputs_help(self):
        """print out the help from the outputs routine
        """
        print self.outputs.__doc__
        
    def _get_output_filenames(self,motionfile,output_dir):
        """Generate output files based on motion filenames

        Parameters
        ----------
        motionfile: file/string
            Filename for motion parameter file
        output_dir: string
            output directory in which the files will be generated 
        """
        (filepath,filename) = os.path.split(motionfile)
        (filename,ext) = os.path.splitext(filename)
        corrfile  = os.path.join(output_dir,''.join(('qa.',filename,'_stimcorr.txt')))
        return corrfile

    def outputs(self):
        """Generate a bunch containing the output fields.

        Parameters
        ----------
        stimcorr_files: file/string
            List of files containing correlation values
        """
        outputs = Bunch(stimcorr_files=None)
        return outputs
        
    def aggregate_outputs(self):
        outputs = self.outputs()
        for i,f in enumerate(filename_to_list(self.inputs.realignment_parameters)):
            corrfile = self._get_output_filenames(f,self.inputs.get('cwd','.'))
            stimcorrfile = glob(corrfile)
            if outputs.stimcorr_files is None:
                outputs.stimcorr_files = []
            outputs.stimcorr_files.insert(i,stimcorrfile[0])
        if outputs.stimcorr_files is not None:
            outputs.stimcorr_files = list_to_filename(outputs.stimcorr_files)
        return outputs

    def get_input_info(self):
        return []

    def _stimcorr_core(self,motionfile,intensityfile,designmatrix,cwd='.'):
        """
        Core routine for determining stimulus correlation
        
        """
        # read in motion parameters
        mc_in = np.loadtxt(motionfile)
        g_in  = np.loadtxt(intensityfile)
        g_in.shape = g_in.shape[0],1
        dcol = designmatrix.shape[1]
        mccol= mc_in.shape[1]
        concat_matrix = np.hstack((np.hstack((designmatrix,mc_in)),g_in))
        cm = np.corrcoef(concat_matrix,rowvar=0)
        corrfile = self._get_output_filenames(motionfile,cwd)
        # write output to outputfile
        file = open(corrfile,'w')
        file.write("Stats for:\n")
        file.write("Stimulus correlated motion:\n%s\n" % motionfile)
        for i in range(dcol):
            file.write("SCM.%d:"%i)
            for v in cm[i,dcol+np.arange(mccol)]:
                file.write(" %.2f"%v)
            file.write('\n')
        file.write("Stimulus correlated intensity:\n%s\n" % intensityfile)
        for i in range(dcol):
            file.write("SCI.%d: %.2f\n"%(i,cm[i,-1]))
        file.close()

    def _get_spm_submatrix(self,spmmat,sessidx,rows=None):
        """
        Parameters
        ----------
        spmmat: scipy matlab object
            full SPM.mat file loaded into a scipy object
        sessidx: int
            index to session that needs to be extracted.
        """
        designmatrix = spmmat['SPM'][0][0].xX[0][0].X
        U = spmmat['SPM'][0][0].Sess[0][sessidx].U[0]
        if rows is None:
            rows = spmmat['SPM'][0][0].Sess[0][sessidx].row[0]-1
        cols = spmmat['SPM'][0][0].Sess[0][sessidx].col[0][range(len(U))]-1
        outmatrix = designmatrix.take(rows.tolist(),axis=0).take(cols.tolist(),axis=1)
        return outmatrix

    def run(self, **inputs):
        """Execute this module.
        """
        motparamlist = filename_to_list(self.inputs.realignment_parameters)
        intensityfiles = filename_to_list(self.inputs.intensity_values)
        spmmat = sio.loadmat(list_to_filename(self.inputs.spm_mat_file))
        nrows = []
        for i,imgf in enumerate(motparamlist):
            sessidx = i
            rows=None
            if self.inputs.concatenated_design:
                sessidx = 0
                mc_in = np.loadtxt(motparamlist[i])
                rows = np.sum(nrows)+np.arange(mc_in.shape[0])
                nrows.append(mc_in.shape[0])
            matrix = self._get_spm_submatrix(spmmat,sessidx,rows)
            self._stimcorr_core(motparamlist[i],intensityfiles[i],
                                matrix,self.inputs.get('cwd','.'))
        runtime = Bunch(returncode=0,
                        messages=None,
                        errmessages=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)
