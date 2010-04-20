"""The spm module provides basic functions for interfacing with matlab
and spm to access spm tools.

These functions include:
    
* Realign: within-modality registration

* Coregister: between modality registration
    
* Normalize: non-linear warping to standard space

* Segment: bias correction, segmentation

* Smooth: smooth with Gaussian kernel

"""
__docformat__ = 'restructuredtext'

# Standard library imports
from glob import glob
from copy import deepcopy

# Third-party imports
import numpy as np

# Local imports
from nipype.interfaces.spm.base import (NEW_SPMCommand, scans_for_fname,
                                   scans_for_fnames)
from nipype.interfaces.base import BaseInterfaceInputSpec, isdefined,\
    OutputMultiPath, TraitedSpec, traits, InputMultiPath, File
from nipype.utils.filemanip import (fname_presuffix, filename_to_list, 
                                    list_to_filename)

class SliceTimingInputSpec(BaseInterfaceInputSpec):
    infile = InputMultiPath(File(exists=True), field='scans',
                          desc='list of filenames to apply slice timing',
                          mandatory=True, copyfile=False)
    num_slices = traits.Int(field='nslices',
                              desc='number of slices in a volume')
    time_repetition = traits.Float(field='tr',
                                   desc='time between volume acquisitions ' \
                                       '(start to start time)')
    time_acquisition = traits.Float(field='ta',
                                    desc='time of volume acquisition. usually ' \
                                        'calculated as TR-(TR/num_slices)')
    slice_order = traits.List(traits.Int(), field='so',
                               desc='1-based order in which slices are acquired')
    ref_slice = traits.Int(field='refslice',
                             desc='1-based Number of the reference slice')

class SliceTimingOutputSpec(TraitedSpec):
    timecorrected_files = OutputMultiPath(File(exist=True, desc='slice time corrected files'))

class SliceTiming(NEW_SPMCommand):
    """Use spm to perform slice timing correction.

    See SliceTiming().spm_doc() for more information.

    Examples
    --------

    >>> from nipype.interfaces.spm import SliceTiming
    >>> st = SliceTiming()
    >>> st.inputs.infile = 'func.nii'
    >>> st.inputs.num_slices = 32
    >>> st.inputs.time_repetition = 6.0
    >>> st.inputs.time_acquisition = 6. - 6./32.
    >>> st.inputs.slice_order = range(32,0,-1)
    >>> st.inputs.ref_slice = 1
    """

    _jobtype = 'temporal'
    _jobname = 'st'

    def _format_arg(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'infile':
            return scans_for_fnames(filename_to_list(val),
                                    separate_sessions=True)
        return val
        
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['timecorrected_files'] = []
        filelist = filename_to_list(self.inputs.infile)
        for f in filelist:
            s_file = fname_presuffix(f, prefix='a')
            outputs['timecorrected_files'].append(s_file)
        return outputs
    

####################################
#
#   Realign
#
####################################
class RealignInputSpec(BaseInterfaceInputSpec):
    infile = InputMultiPath(File(exists=True), field='data', mandatory=True,
                         desc='list of filenames to realign', copyfile=True)
    jobtype = traits.Enum('estwrite', 'estimate', 'write',
                          desc='one of: estimate, write, estwrite',
                          usedefault=True)
    quality = traits.Range(low=0.0, high=1.0, field = 'eoptions.quality',
                           desc = '0.1 = fast, 1.0 = precise')
    fwhm = traits.Range(low=0.0, field = 'eoptions.fwhm',
                        desc = 'gaussian smoothing kernel width')
    separation = traits.Range(low=0.0, field = 'eoptions.sep',
                              desc = 'sampling separation in mm')
    register_to_mean = traits.Bool(field='eoptions.rtm',
                desc='Indicate whether realignment is done to the mean image')
    weight_img = File(exists=True, field='eoptions.weight',
                             desc='filename of weighting image')
    interp = traits.Range(low=0, high=7, field='eoptions.interp',
                          desc='degree of b-spline used for interpolation')
    wrap = traits.List(traits.Int, field='eoptions.wrap', minlen=3, maxlen=3,
                       desc='Check if interpolation should wrap in [x,y,z]')
    write_which = traits.List(traits.Int, field='roptions.which',
                              minlen=2, maxlen=2,
                              desc = 'determines which images to reslice')
    write_interp = traits.Range(low=0, high=7, field='roptions.interp',
                         desc='degree of b-spline used for interpolation')
    write_wrap = traits.List(traits.Int, field='eoptions.wrap',
                             minlen=3, maxlen=3,
                   desc='Check if interpolation should wrap in [x,y,z]')
    write_mask = traits.Bool(field='roptions.mask',
                             desc='True/False mask output image')


class RealignOutputSpec(TraitedSpec):
    mean_image = File(exists=True, desc='Mean image file from the realignment')
    realigned_files = OutputMultiPath(File(exists=True), desc='Realigned files')
    realignment_parameters = OutputMultiPath(File(exists=True),
                    desc='Estimated translation and rotation parameters')

class Realign(NEW_SPMCommand):
    """Use spm_realign for estimating within modality rigid body alignment

    Examples
    --------

    >>> import nipype.interfaces.spm as spm
    >>> realign = spm.Realign()
    >>> realign.inputs.infile = 'a.nii'
    >>> realign.inputs.register_to_mean = True
    >>> realign.run() # doctest: +SKIP

    """

    input_spec = RealignInputSpec
    output_spec = RealignOutputSpec
    
    _jobtype = 'spatial'
    _jobname = 'realign'

    def _format_arg(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'infile':
            return scans_for_fnames(filename_to_list(val),
                                    keep4d=True,
                                    separate_sessions=True)
        if opt == 'register_to_mean': # XX check if this is necessary
            return int(val)
        return val
    
    def _parse_inputs(self):
        """validate spm realign options if set to None ignore
        """
        einputs = super(Realign, self)._parse_inputs()
        return [{'%s'%(self.inputs.jobtype):einputs[0]}]

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.infile):
            outputs['realignment_parameters'] = []
        for imgf in filename_to_list(self.inputs.infile):
            outputs['realignment_parameters'].append(fname_presuffix(imgf,
                                                                     prefix='rp_',
                                                                     suffix='.txt',
                                                                     use_ext=False))
        if self.inputs.jobtype == "write" or self.inputs.jobtype == "estwrite":
            outputs['mean_image'] = fname_presuffix(filename_to_list(self.inputs.infile)[0], prefix='mean')
            outputs['realigned_files'] = []
            for imgf in filename_to_list(self.inputs.infile):
                outputs['realigned_files'].append(fname_presuffix(imgf, prefix='r'))
        return outputs

####################################
#
#   Coregister
#
####################################
class CoregisterInputSpec(BaseInterfaceInputSpec):
    target = File(exists=True, field='ref', mandatory=True,
                         desc='reference file to register to', copyfile=False)
    source = InputMultiPath(File(exists=True), field='source',
                         desc='file to register to target', copyfile=True)
    jobtype = traits.Enum('estwrite','estimate', 'write',
                          desc='one of: estimate, write, estwrite',
                          usedefault=True)
    apply_to_files = InputMultiPath(File(exists=True), field='other',
                                 desc='files to apply transformation to',
                                 copyfile=True)
    cost_function = traits.Enum('mi', 'nmi', 'ecc', 'ncc',
                                field = 'eoptions.cost_fun',
                 desc = "cost function, one of: 'mi' - Mutual Information, " +
                        "'nmi' - Normalised Mutual Information, " +
                        "'ecc' - Entropy Correlation Coefficient, " +
                        "'ncc' - Normalised Cross Correlation")
    fwhm = traits.Float(field = 'eoptions.fwhm',
                        desc = 'gaussian smoothing kernel width (mm)')
    separation = traits.List(traits.Float(), field = 'eoptions.sep',
                             desc = 'sampling separation in mm')
    tolerance =  traits.List(traits.Float(), field = 'eoptions.tol',
                        desc = 'acceptable tolerance for each of 12 params')
    write_interp = traits.Range(low = 0, hign = 7, field = 'roptions.interp',
                        desc = 'degree of b-spline used for interpolation')
    write_wrap = traits.List(traits.Bool(), minlen = 3, maxlen = 3,
                             field = 'roptions.wrap',
                     desc = 'Check if interpolation should wrap in [x,y,z]')
    write_mask = traits.Bool(field = 'roptions.mask',
                             desc = 'True/False mask output image')

class CoregisterOutputSpec(TraitedSpec):
    coregistered_source = OutputMultiPath(File(exists=True),
                                      desc = 'Coregistered source files')
    coregistered_files = OutputMultiPath(File(exists=True), desc = 'Coregistered other files')
    

class Coregister(NEW_SPMCommand):
    """Use spm_coreg for estimating cross-modality rigid body alignment

    Examples
    --------
    
    >>> import nipype.interfaces.spm as spm
    >>> coreg = spm.Coregister()
    >>> coreg.inputs.target = 'a.nii'
    >>> coreg.inputs.source = 'b.nii'
    >>> coreg.run() # doctest: +SKIP
    
    """

    input_spec = CoregisterInputSpec
    output_spec = CoregisterOutputSpec
    _jobtype = 'spatial'
    _jobname = 'coreg'
    
    def _format_arg(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'target' or opt == 'source':
            return scans_for_fnames(filename_to_list(val),
                                    keep4d=True)
        if opt == 'apply_to_files':
            return scans_for_fnames(filename_to_list(val))
        return val
    
    def _parse_inputs(self):
        """validate spm coregister options if set to None ignore
        """
        einputs = super(Coregister, self)._parse_inputs(skip=('jobtype'))
        jobtype =  self.inputs.jobtype
        return [{'%s'%(jobtype):einputs[0]}]
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        
        if self.inputs.jobtype == "estimate":
            if isdefined(self.inputs.apply_to_files):
                outputs['coregistered_files'] = self.inputs.apply_to_files
            outputs['coregistered_source'] = self.inputs.source
        elif self.inputs.jobtype == "write" or self.inputs.jobtype == "estwrite":
            if isdefined(self.inputs.apply_to_files):
                outputs['coregistered_files'] = []
                for imgf in filename_to_list(self.inputs.apply_to_files):
                    outputs['coregistered_files'].append(fname_presuffix(imgf, prefix='r'))
            
            outputs['coregistered_source'] = []        
            for imgf in filename_to_list(self.inputs.source):
                outputs['coregistered_source'].append(fname_presuffix(imgf, prefix='r'))
                
        return outputs

class NormalizeInputSpec(BaseInterfaceInputSpec):
    template = File(exists=True, field='eoptions.template', desc='template file to normalize to', copyfile=False)
    source = InputMultiPath(File(exists=True), field='subj.source', desc='file to normalize to template', mandatory = True, copyfile=True)
    jobtype = traits.Enum('estwrite', 'estimate', 'write',
                          desc='one of: estimate, write, estwrite (opt, estwrite)', usedefault=True)
    apply_to_files = InputMultiPath(File(exists=True), field='subj.resample',
                               desc='files to apply transformation to (opt)', copyfile=True)
    parameter_file = File(field='subj.matname',
                                  desc='normalization parameter file*_sn.mat', copyfile=False)
    source_weight = File(field='subj.wtsrc',
                                 desc='name of weighting image for source (opt)', copyfile=False)
    template_weight = File(field='eoptions.weight',
                                   desc='name of weighting image for template (opt)', copyfile=False)
    source_image_smoothing = traits.Float(field='eoptions.smosrc',
                                          desc='source smoothing (opt)')
    template_image_smoothing = traits.Float(field='eoptions.smoref',
                                            desc='template smoothing (opt)')
    affine_regularization_type = traits.Enum('mni', 'size', 'none', field='eoptions.regype',
                                              desc='mni, size, none (opt)')
    DCT_period_cutoff = traits.Float(field='eoptions.cutoff',
                                     desc='Cutoff of for DCT bases (opt)')
    nonlinear_iterations = traits.Int(field='eoptions.nits',
                     desc='Number of iterations of nonlinear warping (opt)')
    nonlinear_regularization = traits.Float(field='eoptions.reg',
                                            desc='the amount of the regularization for the nonlinear part of the normalization (opt)')
    write_preserve = traits.Bool(field='roptions.preserve',
                     desc='True/False warped images are modulated (opt,)')
    write_bounding_box = traits.List(traits.Float(), field='roptions.bb', minlen=6, maxlen=6, desc='6-element list (opt)')
    write_voxel_sizes = traits.List(traits.Float(), field='roptions.vox', minlen=3, maxlen=3, desc='3-element list (opt)')
    write_interp = traits.Range(low=0, hign=7, field='roptions.interp',
                        desc='degree of b-spline used for interpolation')
    write_wrap = traits.List(traits.Bool(), field='roptions.wrap',
                        desc='Check if interpolation should wrap in [x,y,z] - list of bools (opt)')

    
class NormalizeOutputSpec(TraitedSpec):
    normalization_parameters = OutputMultiPath(File(exists=True), desc='MAT files containing the normalization parameters')
    normalized_source = OutputMultiPath(File(exists=True), desc='Normalized source files')
    normalized_files = OutputMultiPath(File(exists=True), desc = 'Normalized other files')

class Normalize(NEW_SPMCommand):
    """use spm_normalise for warping an image to a template

    Examples
    --------
    
    """
    
    input_spec = NormalizeInputSpec
    output_spec = NormalizeOutputSpec
    _jobtype = 'spatial'
    _jobname = 'normalise'
    
    def _format_arg(self, opt, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'template':
            return scans_for_fname(filename_to_list(val))
        if opt == 'source':
            return scans_for_fname(filename_to_list(val))
        if opt == 'apply_to_files':
            return scans_for_fnames(filename_to_list(val))
        if opt == 'parameter_file':
            return np.array([list_to_filename(val)],dtype=object)
        if opt in ['write_wrap']:
            if len(val) != 3:
                raise ValueError('%s must have 3 elements'%opt)
        return val
    
    def _parse_inputs(self):
        """validate spm realign options if set to None ignore
        """
        einputs = super(Normalize, self)._parse_inputs(skip=('jobtype',
                                                             'apply_to_files'))
        if self.inputs.apply_to_files:
            inputfiles = deepcopy(filename_to_list(self.inputs.apply_to_files))
            if self.inputs.source:
                inputfiles.append(list_to_filename(self.inputs.source))
            einputs[0]['subj']['resample'] = scans_for_fnames(inputfiles)
        jobtype =  self.inputs.jobtype
        if jobtype in ['estwrite', 'write']:
            if self.inputs.apply_to_files is None:
                if self.inputs.source:
                    einputs[0]['subj']['resample'] = scans_for_fname(self.inputs.source)            
        return [{'%s'%(jobtype):einputs[0]}]
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        
        jobtype =  self.inputs.jobtype
        if jobtype.startswith('est'):
            outputs['normalization_parameters'] = []
            for imgf in filename_to_list(self.inputs.source):
                outputs['normalization_parameters'].append(fname_presuffix(imgf, suffix='_sn.mat',use_ext=False))
            outputs['normalization_parameters'] = list_to_filename(outputs['normalization_parameters'])
        
        if self.inputs.jobtype == "estimate":
            if isdefined(self.inputs.apply_to_files):
                outputs['normalized_files'] = self.inputs.apply_to_files
            outputs['normalized_source'] = self.inputs.source
        elif self.inputs.jobtype == "write" or self.inputs.jobtype == "estwrite":
            outputs['normalized_files'] = []
            if isdefined(self.inputs.apply_to_files):
                for imgf in filename_to_list(self.inputs.apply_to_files):
                    outputs['normalized_files'].append(fname_presuffix(imgf, prefix='w'))
                outputs['normalized_files'] = list_to_filename(outputs['normalized_files'])
            
            outputs['normalized_source'] = []
            for imgf in filename_to_list(self.inputs.source):
                outputs['normalized_source'].append(fname_presuffix(imgf, prefix='w'))
            outputs['normalized_source'] = list_to_filename(outputs['normalized_source'])
                
        return outputs
    
class SegmentInputSpec(BaseInterfaceInputSpec):
    data = InputMultiPath(File(exists=True), field='data', desc='one scan per subject', 
                          copyfile=False, mandatory=True)
    gm_output_type = traits.List(traits.Bool(), minlen=3, maxlen=3, field='output.GM', 
                                 desc="""Options to produce grey matter images: c1*.img, wc1*.img and
mwc1*.img. None: [0,0,0], Native Space: [0,0,1], Unmodulated Normalised:
[0,1,0], Modulated Normalised: [1,0,0], Native + Unmodulated Normalised:
[0,1,1], Native + Modulated Normalised: [1,0,1], Native + Modulated +
Unmodulated: [1,1,1], Modulated + Unmodulated Normalised: [1,1,0]""")
    wm_output_type = traits.List(traits.Bool(), minlen=3, maxlen=3, field='output.WM', 
                                 desc="""Options to produce white matter images: c2*.img, wc2*.img and
mwc2*.img. None: [0,0,0], Native Space: [0,0,1], Unmodulated Normalised:
[0,1,0], Modulated Normalised: [1,0,0], Native + Unmodulated Normalised:
[0,1,1], Native + Modulated Normalised: [1,0,1], Native + Modulated +
Unmodulated: [1,1,1], Modulated + Unmodulated Normalised: [1,1,0]""")
    csf_output_type = traits.List(traits.Bool(), minlen=3, maxlen=3, field='output.CSF', 
                                  desc="""Options to produce CSF images: c3*.img, wc3*.img and
mwc3*.img. None: [0,0,0], Native Space: [0,0,1], Unmodulated Normalised:
[0,1,0], Modulated Normalised: [1,0,0], Native + Unmodulated Normalised:
[0,1,1], Native + Modulated Normalised: [1,0,1], Native + Modulated +
Unmodulated: [1,1,1], Modulated + Unmodulated Normalised: [1,1,0]""")
    save_bias_corrected = traits.Bool(field='output.biascor',
                     desc='True/False produce a bias corrected image')
    clean_masks = traits.Enum('no', 'light', 'thorough', field='output.cleanup',
                     desc="clean using estimated brain mask ('no','light','thorough')")
    tissue_prob_maps = traits.List(File(exists=True), field='opts.tpm',
                     'list of gray, white & csf prob. (opt,)')
    gaussians_per_class = traits.List(traits.Int(), field='opts.ngaus',
                     'num Gaussians capture intensity distribution')
    affine_regularization = traits.Enum('mni', 'eastern', 'subj', 'none', field='opts.regtype',
                      desc='mni, eastern, subj, none ')
    warping_regularization = traits.Float(field='opts.warpreg',
                      desc='Controls balance between parameters and data')
    warp_frequency_cutoff = traits.Float(field='opts.warpco', desc='Cutoff of DCT bases')
    bias_regularization = traits.Enum(0, 0.00001, 0.0001, 0.001, 0.01, 0.1, 1, 10, field='opts.biasreg',
                      desc='no(0) - extremely heavy (10)')
    bias_fwhm = traits.Enum(30, 40, 50, 60, 70 , 80, 90, 100, 110, 120, 130, 'Inf', field='opts.biasfwhm',
                      desc='FWHM of Gaussian smoothness of bias')
    sampling_distance = traits.Float(field='opts.samp',
                      desc='Sampling distance on data for parameter estimation')
    mask_image = File(exists=True, field='opts.msk',
                      desc='Binary image to restrict parameter estimation ')
    
    
class SegmentOutputSpec(TraitedSpec):
    native_gm_image = File(exists=True, desc='native space grey probability map')
    normalized_gm_image = File(exists=True, desc='normalized grey probability map',)
    modulated_gm_image = File(exists=True, desc='modulated, normalized grey probability map')
    native_wm_image = File(exists=True, desc='native space white probability map')
    normalized_wm_image = File(exists=True, desc='normalized white probability map')
    modulated_wm_image = File(exists=True, desc='modulated, normalized white probability map')
    native_csf_image = File(exists=True, desc='native space csf probability map')
    normalized_csf_image = File(exists=True, desc='normalized csf probability map')
    modulated_csf_image = File(exists=True, desc='modulated, normalized csf probability map')
    modulated_input_image = File(exists=True, desc='modulated version of input image')
    transformation_mat = File(exists=True, desc='Normalization transformation')
    inverse_transformation_mat = File(exists=True, desc='Inverse normalization info')

class Segment(NEW_SPMCommand):
    """use spm_segment to separate structural images into different
    tissue classes.

    Examples
    --------
    
    """

    _jobtype = 'spatial'
    _jobname = 'preproc'
    
    def _format_arg(self, opt, val):
        """Convert input to appropriate format for spm
        """
        clean_masks_dict = {'no':0,'light':1,'thorough':2}
        
        if opt in ['data', 'tissue_prob_maps']:
            if isinstance(val, list):
                return scans_for_fnames(val)
            else:
                return scans_for_fname(val)
        if opt == 'save_bias_corrected':
            return int(val)
        if opt == 'mask_image':
            return scans_for_fname(val)
        if opt == 'clean_masks':
            return clean_masks_dict[val]
        return val
        
    def _list_outputs(self):
        outputs = self._outputs().get()
        f = self.inputs.data
        
        c_file = fname_presuffix(f,prefix='c1')
        outputs['native_gm_image'] = c_file
        wc_file = fname_presuffix(f,prefix='wc1')
        outputs['normalized_gm_image'] = wc_file
        mwc_file = fname_presuffix(f,prefix='mwc1')
        outputs['modulated_gm_image'] = mwc_file
        
        c_file = fname_presuffix(f,prefix='c2')
        outputs['native_wm_image'] = c_file
        wc_file = fname_presuffix(f,prefix='wc2')
        outputs['normalized_wm_image'] = wc_file
        mwc_file = fname_presuffix(f,prefix='mwc2')
        outputs['modulated_wm_image'] = mwc_file
        
        c_file = fname_presuffix(f,prefix='c3')
        outputs['native_csf_image'] = c_file
        wc_file = fname_presuffix(f,prefix='wc3')
        outputs['normalized_csf_image'] = wc_file
        mwc_file = fname_presuffix(f,prefix='mwc3')
        outputs['modulated_csf_image'] = mwc_file
        
        t_mat = glob(fname_presuffix(f,suffix='_seg_sn.mat',use_ext=False))
        outputs['transformation_mat'] = t_mat
        invt_mat = glob(fname_presuffix(f,suffix='_seg_inv_sn.mat',use_ext=False))
        outputs['inverse_transformation_mat'] = invt_mat
        return outputs

class SmoothInputSpec(BaseInterfaceInputSpec):
    infile = InputMultiPath(File(exists=True), field='data', desc='list of files to smooth', madatrory=True, copyfile=False)
    fwhm = traits.Either(traits.List(traits.Float(), minlen = 3, maxlen = 3),traits.Float(), field= 'fwhm', desc = '3-list of fwhm for each dimension (opt)')
    data_type =  traits.Int(field = 'dtype', desc = 'Data type of the output images (opt)')

class SmoothOutputSpec(TraitedSpec):
    smoothed_files = OutputMultiPath(File(exists=True), desc ='smoothed files')

class Smooth(NEW_SPMCommand):
    """use spm_smooth for 3D Gaussian smoothing of image volumes.

    Examples
    --------
    
    """

    input_spec = SmoothInputSpec
    output_spec = SmoothOutputSpec
    _jobtype = 'spatial'
    _jobname = 'smooth'

    def _format_arg(self, opt, val):
        if opt in ['infile']:
            return scans_for_fnames(filename_to_list(val))
        if opt == 'fwhm':
            if not isinstance(val, list):
                return [val,val,val]
            if isinstance(val, list):
                if len(val) == 1:
                    return [val[0],val[0],val[0]]
                else:
                    return val
        return val
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['smoothed_files'] = []
        
        for imgf in filename_to_list(self.inputs.infile):
            outputs['smoothed_files'].append(fname_presuffix(imgf, prefix='s'))
        return outputs
