"""
The rapidart module provides routines for artifact detection and region of
interest analysis.

these functions include 

    ArtifactDetect: performs artifact detection on functional images

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
            (all default to None)

            realigned_files : filename(s)
                Names of realigned functional data files
            realignment_parameters : filename(s)
                Names of realignment parameters corresponding to the
                functional data files
            design_matrix: filename
                Currently limited to SPM design matrices
            use_differences : boolean
                Use differences between successive motion and
                intensity paramter estimates in order to determine
                outliers 
                default :  True
            use_norm : boolean
                Use the norm of the motion parameters in order to
                determine outliers
                default : True

            Specify 
                norm_threshold: float
                    Threshold to use to detect motion-related outliers
                    when normalized motion is being used (see use_norm)
            or these 
                rotation_threshold : float
                    Threshold to use to detect rotation-related outliers
                translation_threshold : float
                    Threshold to use to detect translation-related outliers
            zintensity_threshold :  float
                Intensity Z-threshold use to detection images that
                deviate from the mean
            mask_type : string
                Type of mask that should be used to mask the
                functional data
                spm_global : uses an spm_global like calculation to
                    determine the brain mask
                file : specifies a brain mask file (should be a
                    an image file consisting of 0s and 1s)
                thresh : specifies a threshold to use

                By default all voxels are used, unless one of these
                mask types are defined.
            mask_file : filename
                Mask file to be used is mask_type is 'file'
            mask_threshold : float
                Mask threshold to be used if mask_type is 'thresh'
            intersect_mask : boolean
                Intersect the masks when computed from spm_global
                default: True
        """
        print self.inputs_help.__doc__
        
    def _populate_inputs(self):
        self.inputs = Bunch(realigned_files=None,
                            realignment_parameters=None,
                            design_matrix=None,
                            use_differences=True,
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
        """
            outlier_files : filename(s)
                One file for each functional run containing a list of
                0-based indices corresponding to outlier volumes
            intensity_files : filename(s)
                One file for each functional run containing the global
                intensity values determined from the brainmask
            statistics_files : filename(s)
                One file for each functional run containing
                information about the different types of artifacts and
                if design info is provided then details of stimulus
                correlated motion and a listing or artifacts by event
                type. 
        """
        print self.outputs_help.__doc__
        
    def _get_output_filenames(self,motionfile,output_dir):
        """
        
        Arguments:
        - `self`:
        - `motionfile`:
        - `cwd`:
        """
        (filepath,filename) = os.path.split(motionfile)
        (filename,ext) = os.path.splitext(filename)
        artifactfile  = os.path.join(output_dir,''.join(('art.',filename,'_outliers.txt')))
        intensityfile = os.path.join(output_dir,''.join(('global_intensity.',filename,'.txt')))
        statsfile     = os.path.join(output_dir,''.join(('stats.',filename,'.txt')))
        return artifactfile,intensityfile,statsfile
    
    def aggregate_outputs(self):
        outputs = Bunch(outlier_files=None,
                        intensity_files=None,
                        statistic_files=None)
        for i,f in enumerate(filename_to_list(self.inputs.realigned_files)):
            outlierfile,intensityfile,statsfile = self._get_output_filenames(f,self.inputs.get('cwd','.'))
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

    def _detect_outliers_core(self,imgfile,motionfile,cwd='.'):
        """
        Core routine for detecting outliers
        
        Arguments:
        - `self`:
        - `imgfile`:
        - `motionfile`:
        - `artifactfile`:
        """
        # read in motion parameters
        mc_in = np.loadtxt(motionfile)

        # if using differences recompute mc
        if self.inputs.use_differences:
            mc = np.concatenate( (np.zeros((1,6)),np.diff(mc_in,n=1,axis=0)) , axis=0)
        else:
            mc = mc_in
        
        traval = mc[:,0:3]  # translation parameters (mm)
        rotval = mc[:,3:6]  # rotation parameters (rad)
        if self.inputs.use_norm:
            # calculate the norm of the motion parameters
            normval = np.sqrt(np.sum(mc*mc,1))
            tidx = find_indices(normval>self.inputs.norm_threshold)
            ridx = find_indices(normval<0)
        else:
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
            g = np.mean(data[mask,:],axis=0)
        elif masktype == 'thresh': # uses a fixed signal threshold
            for t0 in range(nim.timepoints):
                vol   = data[:,:,:,t0]
                mask  = vol>self.inputs.mask_threshold
                g[t0] = np.mean(vol[mask])
        else:
            mask = np.ones((x,y,z))
            g = np.mean(data[mask>0,:],1)

        # compute normalized intensity values
        gz = signal.detrend(g,axis=0)       # detrend the signal
        if self.inputs.use_differences:
            gz = np.concatenate( (np.zeros((1,1)),np.diff(gz,n=1,axis=0)) , axis=0)
        gz = (gz-np.mean(gz))/np.std(gz)    # normalize the detrended signal
        iidx = find_indices(abs(gz)>self.inputs.zintensity_threshold)

        outliers = np.unique(np.union1d(iidx,np.union1d(tidx,ridx)))
        artifactfile,intensityfile,statsfile = self._get_output_filenames(imgfile,cwd)
        
        # write output to outputfile
        np.savetxt(artifactfile, outliers, fmt='%d', delimiter=' ')
        np.savetxt(intensityfile, g, fmt='%.2f', delimiter=' ')

        file = open(statsfile,'w')
        file.write("Stats for:\n")
        file.write("Motion file: %s\n" % motionfile)
        file.write("Functional file: %s\n" % imgfile)
        file.write("Motion:\n")
        file.write("Mot-Outliers: %d\n"%len(np.union1d(tidx,ridx)))
        file.write( ''.join(('mean: ',str(np.mean(mc,axis=0)),'\n')))
        file.write( ''.join(('min: ',str(np.min(mc,axis=0)),'\n')))
        file.write( ''.join(('max: ',str(np.max(mc,axis=0)),'\n')))
        file.write( ''.join(('std: ',str(np.std(mc,axis=0)),'\n')))
        file.write("Normalized intensity:\n")
        file.write("Int-Outliers: %d\n"%len(iidx))
        file.write( ''.join(('min: ',str(np.min(gz,axis=0)),'\n')))
        file.write( ''.join(('max: ',str(np.max(gz,axis=0)),'\n')))
        file.write( ''.join(('mean: ',str(np.mean(gz,axis=0)),'\n')))
        file.write( ''.join(('std: ',str(np.std(gz,axis=0)),'\n')))
        file.close()

    def run(self):
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
