# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os
import warnings

import numpy as np

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
from nipype.interfaces.base import (TraitedSpec, File, InputMultiPath,
                                    OutputMultiPath, Undefined, traits)
from nipype.utils.filemanip import split_filename
from nipype.utils.misc import isdefined

from nipype.externals.pynifti import load


warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class BETInputSpec(FSLCommandInputSpec):
    """Note: Currently we don't support -R, -S, -Z,-A or -A2"""
    # We use position args here as list indices - so a negative number
    # will put something on the end
    in_file = File(exists=True,
                  desc = 'input file to skull strip',
                  argstr='%s', position=0, mandatory=True)
    out_file = File(desc = 'name of output skull stripped image',
                   argstr='%s', position=1, genfile=True)
    outline = traits.Bool(desc = 'create surface outline image',
                          argstr='-o')
    mask = traits.Bool(desc = 'create binary mask image',
                       argstr='-m')
    skull = traits.Bool(desc = 'create skull image',
                        argstr='-s')
    no_output = traits.Bool(argstr='-n',
                           desc="Don't generate segmented output")
    frac = traits.Float(desc = 'fractional intensity threshold',
                        argstr='-f %.2f')
    vertical_gradient = traits.Float(argstr='-g %.2f',
             desc='vertical gradient in fractional intensity ' \
                                         'threshold (-1, 1)')
    radius = traits.Int(argstr='-r %d', units='mm',
                        desc="head radius")
    center = traits.List(traits.Int, desc = 'center of gravity in voxels',
                         argstr='-c %s', minlen=0, maxlen=3,
                         units='voxels')
    threshold = traits.Bool(argstr='-t',
                   desc="apply thresholding to segmented brain image and mask")
    mesh = traits.Bool(argstr='-e',
                       desc="generate a vtk mesh brain surface")
    # XXX how do we know these two are mutually exclusive?
    _xor_inputs = ('functional', 'reduce_bias')
    functional = traits.Bool(argstr='-F', xor=_xor_inputs,
                             desc="apply to 4D fMRI data")
    reduce_bias = traits.Bool(argstr='-B', xor=_xor_inputs,
                              desc="bias field and neck cleanup")

class BETOutputSpec(TraitedSpec):
    out_file = File(desc="path/name of skullstripped file")
    mask_file = File(
        desc="path/name of binary brain mask (if generated)")
    outline_file = File(
        desc="path/name of outline file (if generated)")
    meshfile = File(
        desc="path/name of vtk mesh file (if generated)")

class BET(FSLCommand):
    """Use FSL BET command for skull stripping.

    For complete details, see the `BET Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/bet2/index.html>`_

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import  example_data
    >>> btr = fsl.BET()
    >>> btr.inputs.in_file = example_data('structural.nii')
    >>> btr.inputs.frac = 0.7
    >>> res = btr.run() # doctest: +SKIP

    """

    _cmd = 'bet'
    input_spec = BETInputSpec
    output_spec = BETOutputSpec

    def _run_interface(self, runtime):
        # The returncode is meaningless in BET.  So check the output
        # in stderr and if it's set, then update the returncode
        # accordingly.
        runtime = super(BET, self)._run_interface(runtime)
        if runtime.stderr:
            runtime.returncode = 1
        return runtime

    def _gen_outfilename(self):
        out_file = self.inputs.out_file
        if not isdefined(out_file) and isdefined(self.inputs.in_file):
            out_file = self._gen_fname(self.inputs.in_file,
                                       suffix = '_brain')
        return out_file

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        if isdefined(self.inputs.mesh) and self.inputs.mesh:
            outputs['meshfile'] = self._gen_fname(outputs['out_file'],
                                               suffix = '_mesh.vtk',
                                               change_ext = False)
        if (isdefined(self.inputs.mask) and self.inputs.mask) or \
                (isdefined(self.inputs.reduce_bias) and \
                     self.inputs.reduce_bias):
            outputs['mask_file'] = self._gen_fname(outputs['out_file'],
                                               suffix = '_mask')
        if isdefined(self.inputs.no_output) and self.inputs.no_output:
            outputs['out_file'] = Undefined
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_outfilename()
        return None


class FASTInputSpec(FSLCommandInputSpec):
    """ Defines inputs (trait classes) for FAST """
    in_files = InputMultiPath(File(exists=True), copyfile=False,
                          desc = 'image, or multi-channel set of images, ' \
                              'to be segmented',
                          argstr='%s', position=-1, mandatory=True)
    out_basename = File(desc = 'base name of output files',
                        argstr='-o %s') #uses in_file name as basename if none given
    number_classes = traits.Range(low=1, high=10, argstr = '-n %d',
                                  desc = 'number of tissue-type classes')
    output_biasfield = traits.Bool(desc = 'output estimated bias field',
                                   argstr = '-b')
    output_biascorrected = traits.Bool(desc = 'output restored image ' \
                                           '(bias-corrected image)',
                                       argstr = '-B')
    img_type = traits.Enum((1,2,3), desc = 'int specifying type of image: ' \
                               '(1 = T1, 2 = T2, 3 = PD)',
                           argstr = '-t %d')
    bias_iters = traits.Range(low = 1, high = 10, argstr = '-I %d',
                              desc = 'number of main-loop iterations during ' \
                                  'bias-field removal')
    bias_lowpass = traits.Range(low = 4, high = 40,
                                desc = 'bias field smoothing extent (FWHM) ' \
                                    'in mm',
                                argstr = '-l %d', units = 'mm')
    init_seg_smooth = traits.Range(low=0.0001, high = 0.1,
                                   desc = 'initial segmentation spatial ' \
                                       'smoothness (during bias field ' \
                                       'estimation)',
                                   argstr = '-f %.3f')
    segments = traits.Bool(desc = 'outputs a separate binary image for each ' \
                               'tissue type',
                           argstr = '-g')
    init_transform = File(exists=True, desc = '<standard2input.mat> initialise'\
                              ' using priors',
                          argstr = '-a %s')
    other_priors = InputMultiPath(File(exist=True), desc = 'alternative prior images',
                               argstr = '-A %s', minlen=3, maxlen=3)
    no_pve = traits.Bool(desc = 'turn off PVE (partial volume estimation)',
                        argstr = '--nopve')
    no_bias = traits.Bool(desc = 'do not remove bias field',
                         argstr = '-N')
    use_priors = traits.Bool(desc = 'use priors throughout',
                             argstr = '-P')   # must also set -a!,
                                              # mutually inclusive??
                                              # No, conditional
                                              # mandatory... need to
                                              # figure out how to
                                              # handle with traits.
    segment_iters = traits.Range(low=1, high=50,
                                 desc = 'number of segmentation-initialisation'\
                                     ' iterations',
                                 argstr = '-W %d')
    mixel_smooth = traits.Range(low = 0.0, high=1.0,
                                desc = 'spatial smoothness for mixeltype',
                                argstr = '-R %.2f')
    iters_afterbias = traits.Range(low = 1, hight = 20,
                                   desc = 'number of main-loop iterations ' \
                                       'after bias-field removal',
                                   argstr = '-O %d')
    hyper = traits.Range(low = 0.0, high = 1.0,
                         desc = 'segmentation spatial smoothness',
                         argstr = '-H %.2f')
    verbose = traits.Bool(desc = 'switch on diagnostic messages',
                          argstr = '-v')
    manual_seg = File(exists=True, desc = 'Filename containing intensities',
                     argstr = '-s %s')
    probability_maps = traits.Bool(desc = 'outputs individual probability maps',
                                   argstr = '-p')


class FASTOutputSpec(TraitedSpec):
    """Specify possible outputs from FAST"""
    tissue_class_map = File(exists=True,
                            desc = 'path/name of binary segmented volume file' \
                            ' one val for each class  _seg')
    tissue_class_files = OutputMultiPath(File(desc = 'path/name of binary segmented volumes ' \
                                  'one file for each class  _seg_x'))
    restored_image = OutputMultiPath(File(desc = 'restored images (one for each input image) ' \
                              'named according to the input images _restore'))

    mixeltype  = File(desc = "path/name of mixeltype volume file _mixeltype")

    partial_volume_map = File(desc = "path/name of partial volume file _pveseg")
    partial_volume_files  = OutputMultiPath(File(desc = 'path/name of partial volumes files ' \
                                     'one for each class, _pve_x'))

    bias_field = OutputMultiPath(File(desc = 'Estimated bias field _bias'))
    probability_maps = OutputMultiPath(File(desc= 'filenames, one for each class, for each ' \
                                'input, prob_x'))


class FAST(FSLCommand):
    """ Use FSL FAST for segmenting and bias correction.

    For complete details, see the `FAST Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/fast4/index.html>`_

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data

    Assign options through the ``inputs`` attribute:

    >>> fastr = fsl.FAST()
    >>> fastr.inputs.in_files = example_data('structural.nii')
    >>> out = fastr.run() #doctest: +SKIP

    """
    _cmd = 'fast'
    input_spec = FASTInputSpec
    output_spec = FASTOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.number_classes):
            nclasses = 3
        else:
            nclasses = self.inputs.number_classes
        # when using multichannel, results basename is based on last
        # input filename
        if isdefined(self.inputs.out_basename):
            basefile = self.inputs.out_basename
        else:
            basefile = self.inputs.in_files[-1]

        outputs['tissue_class_map'] = self._gen_fname(basefile,
                                                      suffix = '_seg')
        outputs['tissue_class_files'] = []
        for  i in range(nclasses):
            outputs['tissue_class_files'].append(self._gen_fname(basefile,
                                                                 suffix = '_seg_%d'%(i)))
        if isdefined(self.inputs.output_biascorrected):
            outputs['restored_image'] = []
            for val,f in enumerate(self.inputs.in_files):
                outputs['restored_image'].append(self._gen_fname(f,
                                                                 suffix = '_restore_%d'%(val)))
        outputs['mixeltype'] = self._gen_fname(basefile, suffix = '_mixeltype')
        if not self.inputs.no_pve:
            outputs['partial_volume_map'] = self._gen_fname(basefile, suffix = '_pveseg')
            outputs['partial_volume_files'] = []
            for i in range(nclasses):
                outputs['partial_volume_files'].append(self._gen_fname(basefile,
                                                                       suffix='_pve_%d'%(i)))
        if self.inputs.output_biasfield:
            outputs['bias_field'] = []
            for val,f in enumerate(self.inputs.in_files):
                outputs['bias_field'].append(self._gen_fname(basefile, suffix='_bias_%d'%val))
        #if self.inputs.probability_maps:
        return outputs

class FLIRTInputSpec(FSLCommandInputSpec):
    in_file = File(exists = True, argstr = '-in %s', mandatory = True,
                  position = 0, desc = 'input file')
    # XXX Not clear if position is required for mandatory flirt inputs
    # since they are prefixed with argstrs.  But doing it to follow
    # our previous convention and so we can test the generated command
    # line.
    reference = File(exists = True, argstr = '-ref %s', mandatory = True,
                     position = 1, desc = 'reference file')
    out_file = File(argstr = '-out %s', desc = 'registered output file',
                   genfile = True, position = 2)
    out_matrix_file = File(argstr = '-omat %s',
                     desc = 'output affine matrix in 4x4 asciii format',
                     genfile = True, position = 3)
    in_matrix_file = File(argstr = '-init %s', desc = 'input 4x4 affine matrix')
    apply_xfm = traits.Bool(argstr = '-applyxfm', requires=['in_matrix_file'],
                     desc='apply transformation supplied by in_matrix_file')
    datatype = traits.Enum('char', 'short', 'int', 'float', 'double',
                           argstr = '-datatype %s',
                           desc = 'force output data type')
    cost = traits.Enum('mutualinfo', 'corratio', 'normcorr', 'normmi',
                       'leastsq', 'labeldiff',
                       argstr = '-cost %s',
                       desc = 'cost function')
    # XXX What is the difference between 'cost' and 'searchcost'?  Are
    # these both necessary or do they map to the same variable.
    cost_func = traits.Enum('mutualinfo', 'corratio', 'normcorr', 'normmi',
                             'leastsq', 'labeldiff',
                             argstr = '-searchcost %s',
                             desc = 'cost function')
    uses_qform = traits.Bool(argstr = '-usesqform',
                            desc = 'initialize using sform or qform')
    display_init = traits.Bool(argstr = '-displayinit',
                              desc = 'display initial matrix')
    angle_rep = traits.Enum('quaternion', 'euler',
                           argstr = '-anglerep %s',
                           desc = 'representation of rotation angles')
    interp = traits.Enum('trilinear', 'nearestneighbour', 'sinc',
                         argstr = '-interp %s',
                         desc = 'final interpolation method used in reslicing')
    sinc_width = traits.Int(argstr = '-sincwidth %d', units = 'voxels',
                           desc = 'full-width in voxels')
    sinc_window = traits.Enum('rectangular', 'hanning', 'blackman',
                             argstr = '-sincwindow %s',
                             desc = 'sinc window') # XXX better doc
    bins = traits.Int(argstr = '-bins %d', desc = 'number of histogram bins')
    dof = traits.Int(argstr = '-dof %d',
                     desc = 'number of transform degrees of freedom')
    no_resample = traits.Bool(argstr = '-noresample',
                             desc = 'do not change input sampling')
    force_scaling = traits.Bool(argstr = '-forcescaling',
                               desc = 'force rescaling even for low-res images')
    min_sampling = traits.Float(argstr = '-minsampling %f', units = 'mm',
                               desc ='set minimum voxel dimension for sampling')
    padding_size = traits.Int(argstr = '-paddingsize %d', units = 'voxels',
                             desc = 'for applyxfm: interpolates outside image '\
                                 'by size')
    searchr_x = traits.List(traits.Int, minlen = 2, maxlen = 2, units ='degrees',
                           argstr = '-searchrx %s',
                           desc = 'search angles along x-axis, in degrees')
    searchr_y = traits.List(traits.Int, minlen = 2, maxlen = 2, units ='degrees',
                           argstr = '-searchry %s',
                           desc = 'search angles along y-axis, in degrees')
    searchr_z = traits.List(traits.Int, minlen = 2, maxlen = 2, units ='degrees',
                           argstr = '-searchrz %s',
                           desc = 'search angles along z-axis, in degrees')
    no_search = traits.Bool(argstr = '-nosearch',
                           desc = 'set all angular searches to ranges 0 to 0')
    coarse_search = traits.Int(argstr = '-coarsesearch %d', units = 'degrees',
                              desc = 'coarse search delta angle')
    fine_search = traits.Int(argstr = '-finesearch %d', units = 'degrees',
                            desc = 'fine search delta angle')
    schedule = File(exists = True, argstr = '-schedule %s',
                    desc = 'replaces default schedule')
    ref_weight = File(exists = True, argstr = '-refweight %s',
                     desc = 'File for reference weighting volume')
    in_weight = File(exists = True, argstr = '-inweight %s',
                    desc = 'File for input weighting volume')
    no_clamp = traits.Bool(argstr = '-noclamp',
                          desc = 'do not use intensity clamping')
    no_resample_blur = traits.Bool(argstr = '-noresampblur',
                               desc = 'do not use blurring on downsampling')
    rigid2D = traits.Bool(argstr = '-2D',
                          desc = 'use 2D rigid body mode - ignores dof')
    verbose = traits.Int(argstr = '-verbose %d',
                         desc = 'verbose mode, 0 is least')

class FLIRTOutputSpec(TraitedSpec):
    out_file = File(exists = True,
                   desc = 'path/name of registered file (if generated)')
    out_matrix_file = File(exists = True,
                           desc = 'path/name of calculated affine transform ' \
                         '(if generated)')

class FLIRT(FSLCommand):
    """Use FSL FLIRT for coregistration.

    For complete details, see the `FLIRT Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/flirt/index.html>`_

    To print out the command line help, use:
        fsl.FLIRT().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> flt = fsl.FLIRT(bins=640, cost_func='mutualinfo')
    >>> flt.inputs.in_file = example_data('structural.nii')
    >>> flt.inputs.reference = example_data('mni.nii')
    >>> flt.inputs.out_file = 'moved_subject.nii'
    >>> flt.inputs.out_matrix_file = 'subject_to_template.mat'
    >>> res = flt.run() #doctest: +SKIP

    """
    _cmd = 'flirt'
    input_spec = FLIRTInputSpec
    output_spec = FLIRTOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        # Generate an out_file if one is not provided
        if not isdefined(outputs['out_file']) and isdefined(self.inputs.in_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                                 suffix = '_flirt')
        outputs['out_matrix_file'] = self.inputs.out_matrix_file
        # Generate an out_matrix file if one is not provided
        if not isdefined(outputs['out_matrix_file']) and \
                isdefined(self.inputs.in_file):
            outputs['out_matrix_file'] = self._gen_fname(self.inputs.in_file,
                                                   suffix = '_flirt.mat',
                                                   change_ext = False)
        return outputs

    def _gen_filename(self, name):
        if name in ('out_file', 'out_matrix_file'):
            return self._list_outputs()[name]
        else:
            return None


class ApplyXfm(FLIRT):
    """Currently just a light wrapper around FLIRT,
    with no modifications

    ApplyXfm is used to apply an existing tranform to an image


    Examples
    --------

    >>> import nipype.interfaces.fsl as fsl
    >>> from nipype.testing import example_data
    >>> applyxfm = fsl.ApplyXfm()
    >>> applyxfm.inputs.in_file = example_data('structural.nii')
    >>> applyxfm.inputs.in_matrix_file = example_data('trans.mat')
    >>> applyxfm.inputs.out_file = 'newfile.nii'
    >>> applyxfm.inputs.reference = example_data('mni.nii')
    >>> applyxfm.inputs.apply_xfm = True
    >>> result = applyxfm.run() # doctest: +SKIP

    """
    pass


class MCFLIRTInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, position= 0, argstr="-in %s", mandatory=True)
    out_file = File(argstr='-out %s', genfile=True)
    cost = traits.Enum('mutualinfo','woods','corratio','normcorr','normmi','leastsquares', argstr='-cost %s')
    bins = traits.Int(argstr='-bins %d')
    dof = traits.Int(argstr='-dof %d')
    ref_vol = traits.Int(argstr='-refvol %d')
    scaling = traits.Float(argstr='-scaling %.2f')
    smooth = traits.Float(argstr='-smooth %.2f')
    rotation = traits.Int(argstr='-rotation %d')
    stages = traits.Int(argstr='-stages %d')
    init = File(exists=True, argstr='-init %s')
    use_gradient = traits.Bool(argstr='-gdt')
    use_contour = traits.Bool(argstr='-edge')
    mean_vol = traits.Bool(argstr='-meanvol')
    stats_imgs = traits.Bool(argstr='-stats')
    save_mats = traits.Bool(argstr='-mats')
    save_plots = traits.Bool(argstr='-plots')
    ref_file = File(exists=True, argstr='-reffile %s')

class MCFLIRTOutputSpec(TraitedSpec):
    out_file = File(exists=True)
    variance_img = File(exists=True)
    std_img = File(exists=True)
    mean_img = File(exists=True)
    par_file = File(exists=True)
    mat_file = OutputMultiPath(File(exists=True))

class MCFLIRT(FSLCommand):
    """Use FSL MCFLIRT to do within-modality motion correction.

    For complete details, see the `MCFLIRT Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/mcflirt/index.html>`_

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> mcflt = fsl.MCFLIRT(in_file=example_data('functional.nii'), cost='mutualinfo')
    >>> res = mcflt.run() # doctest: +SKIP

    """
    _cmd = 'mcflirt'
    input_spec = MCFLIRTInputSpec
    output_spec = MCFLIRTOutputSpec

    def _list_outputs(self):
        cwd = os.getcwd()
        outputs = self._outputs().get()

        outputs['out_file'] = self._gen_outfilename()

        # XXX Need to change 'item' below to something that exists
        # out_file? in_file?
        # These could be handled similarly to default values for inputs
        if isdefined(self.inputs.stats_imgs) and self.inputs.stats_imgs:
            outputs['variance_img'] = self._gen_fname(self.inputs.in_file,
                                                      cwd=cwd,
                                                      suffix='_variance')
            outputs['std_img'] = self._gen_fname(self.inputs.in_file,
                                                 cwd=cwd, suffix='_sigma')
            outputs['mean_img'] = self._gen_fname(self.inputs.in_file,
                                                  cwd=cwd, suffix='_meanvol')
        if isdefined(self.inputs.save_mats) and self.inputs.save_mats:
            _, filename = os.path.split(outputs['out_file'])
            matpathname = os.path.join(cwd, filename + '.mat')
            _,_,_,timepoints = load(self.inputs.in_file).get_shape()
            outputs['mat_file'] = []
            for t in range(timepoints):
                outputs['mat_file'].append(os.path.join(matpathname,
                                                        'MAT_%04d'%t))
        if isdefined(self.inputs.save_plots) and self.inputs.save_plots:
            # Note - if e.g. out_file has .nii.gz, you get .nii.gz.par,
            # which is what mcflirt does!
            outputs['par_file'] = outputs['out_file'] + '.par'
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._gen_outfilename()
        return None

    def _gen_outfilename(self):
        out_file = self.inputs.out_file
        if not isdefined(out_file) and isdefined(self.inputs.in_file):
            out_file = self._gen_fname(self.inputs.in_file,
                                       suffix = '_mcf')
        return out_file

class FNIRTInputSpec(FSLCommandInputSpec):
    ref_file = File(exists=True, argstr='--ref=%s', mandatory=True,
                    desc='name of reference image')
    in_file = File(exists=True, argstr='--in=%s', mandatory=True,
                  desc='name of input image')
    affine_file = File(exists=True, argstr='--aff=%s',
                       desc='name of file containing affine transform')
    inwarp_file = File(exists=True, argstr='--inwarp=%s',
                       desc='name of file containing initial non-linear warps')
    in_intensitymap_file = File(exists=True, argstr='--intin=%s',
                             desc='name of file/files containing initial intensity maping'\
                                'usually generated by previos fnirt run')
    fieldcoeff_file = File(genfile=True, argstr='--cout=%s',
                           desc='name of output file with field coefficients or true')
    warped_file = File(genfile=True,
                       argstr='--iout=%s',
                       desc='name of output image')
    field_file = traits.Either(traits.Bool, File, genfile=True,
                               argstr='--fout=%s',
                               desc='name of output file with field or true')
    jacobian_file = traits.Either(traits.Bool, File, genfile=True,
                                  argstr='--jout=%s',
                                  desc='name of file for writing out the Jacobian'\
                                  'of the field (for diagnostic or VBM purposes)')
    modulatedref_file = traits.Either(traits.Bool, File, genfile=True,
                                      argstr='--refout=%s',
                                      desc='name of file for writing out intensity modulated'\
                                      '--ref (for diagnostic purposes)')
    out_intensitymap_file = traits.Either(traits.Bool, File, genfile=True,
                                      argstr='--intout=%s',
                                      desc='name of files for writing information pertaining '\
                                          'to intensity mapping')
    log_file = traits.Either(traits.Bool, File, genfile=True,
                             argstr='--logout=%s',
                             desc='Name of log-file')
    config_file = File(exists=True, argstr='--config=%s',
                       desc='Name of config file specifying command line arguments')
    refmask_file = File(exists=True, argstr='--refmask=%s',
                        desc='name of file with mask in reference space')
    inmask_file = File(exists=True, argstr='--inmask=%s',
                       desc='name of file with mask in input image space')
    skip_ref_mask = traits.Bool(argstr='--applyrefmask 0',
                              desc='Skip specified refmask if set, default false')
    skip_inmask = traits.Bool(argstr='--applyinmask 0',
                             desc='skip specified inmask if set, default false')
    skip_implicit_ref_masking = traits.Bool(argstr='--imprefm 0',
                                      desc='skip implicit masking  based on value'\
                                            'in --ref image. Default = 0')
    skip_implicit_in_masking = traits.Bool(argstr='--impinm 0',
                                      desc='skip implicit masking  based on value'\
                                           'in --in image. Default = 0')
    refmask_val = traits.Float(argstr='--imprefval=%f',
                              desc='Value to mask out in --ref image. Default =0.0')
    inmask_val = traits.Float(argstr='--impinval=%f',
                              desc='Value to mask out in --in image. Default =0.0')
    max_nonlin_iter = traits.Tuple(traits.Int,traits.Int,traits.Int,traits.Int,
                                   argstr='--miter=%d,%d,%d,%d',
                                   desc='Max # of non-linear iterations tuple, default (5,5,5,5)')
    subsampling_scheme = traits.Tuple((traits.Int,traits.Int,traits.Int,traits.Int),
                                   argstr='--subsamp=%d,%d,%d,%d',
                                   desc='sub-sampling scheme, tuple, default (4,2,1,1)')
    warp_resolution = traits.Tuple(traits.Int, traits.Int, traits.Int,
                                   argstr='--warpres=%d,%d,%d',
                                   desc='(approximate) resolution (in mm) of warp basis '\
                                   'in x-, y- and z-direction, default 10,10,10')
    spline_order = traits.Int(argstr='--splineorder=%d',
                              desc='Order of spline, 2->Qadratic spline, 3->Cubic spline. Default=3')
    in_fwhm = traits.Tuple(traits.Int,traits.Int,traits.Int,traits.Int,
                           argstr='--infwhm=%d,%d,%d,%d',
                           desc='FWHM (in mm) of gaussian smoothing kernel for input volume, default 6,4,2,2')
    ref_fwhm = traits.Tuple(traits.Int,traits.Int,traits.Int,traits.Int,
                           argstr='--reffwhm=%d,%d,%d,%d',
                           desc='FWHM (in mm) of gaussian smoothing kernel for ref volume, default 4,2,0,0')
    regularization_model = traits.Enum('membrane_energy', 'bending_energy',
                                       argstr='--regmod=%s',
        desc='Model for regularisation of warp-field [membrane_energy bending_energy], default bending_energy')
    regularization_lambda = traits.Float(argstr='--lambda=%f',
        desc='Weight of regularisation, default depending on --ssqlambda and --regmod '\
                                         'switches. See user documetation.')
    skip_lambda_ssq = traits.Bool(argstr='--ssqlambda 0',
                                  desc='If true, lambda is not weighted by current ssq, default false')
    jacobian_range = traits.Tuple(traits.Float, traits.Float,
                                  argstr='--jacrange=%f,%f',
                                  desc='Allowed range of Jacobian determinants, default 0.01,100.0')
    derive_from_ref = traits.Bool(argstr='--refderiv',
                                  desc='If true, ref image is used to calculate derivatives. Default false')
    intensity_mapping_model = traits.Enum('none', 'global_linear', 'global_non_linear'
                                          'local_linear', 'global_non_linear_with_bias',
                                          'local_non_linear', argstr='--intmod=%s',
                                          desc='Model for intensity-mapping')
    intensity_mapping_order = traits.Int(argstr='--intorder=%d',
                                         desc='Order of poynomial for mapping intensities, default 5')
    biasfield_resolution = traits.Tuple(traits.Int, traits.Int, traits.Int,
                                        argstr='--biasres=%d,%d,%d',
                                        desc='Resolution (in mm) of bias-field modelling '\
                                        'local intensities, default 50,50,50')
    bias_regularization_lambda = traits.Float(argstr='--biaslambda=%f',
                                              desc='Weight of regularisation for bias-field, default 10000')
    skip_intensity_mapping = traits.Bool(argstr='--estint 0',
                                         desc='Skip estimate intensity-mapping default false')
    hessian_precision = traits.Enum('double', 'float', argstr='--numprec=%s',
                                    desc='Precision for representing Hessian, double or float. Default double')

class FNIRTOutputSpec(TraitedSpec):
    fieldcoeff_file = File(exists=True,desc='file with field coefficients')
    warped_file = File(exists=True, desc='warped image')
    field_file = File(desc='file with warp field')
    jacobian_file = File(desc='file containing Jacobian of the field')
    modulatedref_file = File(desc='file containing intensity modulated --ref')
    out_intensitymap_file = File(\
                        desc='file containing info pertaining to intensity mapping')
    log_file = File(desc='Name of log-file')

class FNIRT(FSLCommand):
    """Use FSL FNIRT for non-linear registration.

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> fnt = fsl.FNIRT(affine_file=example_data('trans.mat'))
    >>> res = fnt.run(ref_file=example_data('mni.nii', in_file=example_data('structural.nii')) #doctest: +SKIP

    T1 -> Mni153

    >>> from nipype.interfaces import fsl
    >>> fnirt_mprage = fsl.FNIRT()
    >>> fnirt_mprage.inputs.in_fwhm = (8, 4, 2, 2)
    >>> fnirt_mprage.inputs.subsampling_scheme = (4, 2, 1, 1)

    Specify the resolution of the warps

    >>> fnirt_mprage.inputs.warp_resolution = (6, 6, 6)
    >>> res = fnirt_mprage.run(in_file='structural.nii', ref_file='mni.nii', warped_file='warped.nii', fieldcoeff_file='fieldcoeff.nii')#doctest: +SKIP

    We can check the command line and confirm that it's what we expect.

    >>> fnirt_mprage.cmdline  #doctest: +SKIP
    'fnirt --cout=fieldcoeff.nii --in=structural.nii --infwhm=8,4,2,2 --ref=mni.nii --subsamp=4,2,1,1 --warpres=6,6,6 --iout=warped.nii'

    """

    _cmd = 'fnirt'
    input_spec = FNIRTInputSpec
    output_spec = FNIRTOutputSpec

    out_map = dict(warped_file='_warped',
                   field_file='_field',
                   jacobian_file='_field_jacobian',
                   modulatedref_file='_modulated',
                   out_intensitymap_file='_intmap',
                   log_file='_log',
                   fieldcoeff_file = '_fieldwarp')

    def _format_arg(self, name, spec, value):
        if name in self.out_map.keys():
            if isinstance(value, bool):
                if value:
                    fname = self._list_outputs()[name]
                else:
                    return ''
            else:
                fname = value
            return spec.argstr % fname
        return super(FNIRT, self)._format_arg(name, spec, value)

    def _parse_inputs(self, skip=None):
        """Parse all inputs using the ``argstr`` format string in the Trait.

        Any inputs that are assigned (not the default_value) are formatted
        to be added to the command line.

        Returns
        -------
        all_args : list
            A list of all inputs formatted for the command line.

        """
        all_args = []
        initial_args = {}
        final_args = {}
        metadata = dict(argstr=lambda t : t is not None)
        for name, spec in sorted(self.inputs.traits(**metadata).items()):

            value = getattr(self.inputs, name)
            if not isdefined(value):
                if spec.default_value() == (0, None):
                    continue
                if spec.genfile:
                    value = self._gen_filename(name)
                else:
                    continue
            arg = self._format_arg(name, spec, value)
            pos = spec.position
            if pos is not None:
                if pos >= 0:
                    initial_args[pos] = arg
                else:
                    final_args[pos] = arg
            else:
                all_args.append(arg)
        first_args = [arg for pos, arg in sorted(initial_args.items())]
        last_args = [arg for pos, arg in sorted(final_args.items())]
        return first_args + all_args + last_args


    def _set_output(self, field, src, suffix, change_ext=True):
        val = getattr(self.inputs, field)
        if isdefined(val):
            if isinstance(val, bool):
                val = self._gen_fname(src, suffix=suffix,
                                      change_ext=change_ext)
        else:
            val = None
        return val

    def _list_outputs(self):
        outputs = self._outputs().get()
        """
        outputs['fieldcoeff_file']=self.inputs.fieldcoeff_file
        if not isdefined(self.inputs.fieldcoeff_file):
            outputs['fieldcoeff_file'] = self._gen_fname(self.inputs.in_file,
                                                         suffix='_warpcoef')
        """

        if not isdefined(self.inputs.warped_file):
            outputs['warped_file'] = self._gen_fname(self.inputs.in_file,
                                                     suffix = '_warped')

        for name, suffix in self.out_map.items():
            if name == 'modulatedref_file':
                src = self.inputs.ref_file
            else:
                src = self.inputs.in_file
            if not isdefined(name):
                val = None
            elif name == 'log_file':
                val = self._gen_fname(src, suffix=suffix,
                                      change_ext=True, ext='.log')
            else:
                val = self._gen_fname(src, suffix=suffix)

            outputs[name] = val

        return outputs

    def _gen_filename(self, name):
        if name in self.out_map.keys():
            return self._list_outputs()[name]
        return None

    def write_config(self, configfile):
        """Writes out currently set options to specified config file

        XX TODO : need to figure out how the config file is written

        Parameters
        ----------
        configfile : /path/to/configfile
        """
        try:
            fid = open(configfile, 'w+')
        except IOError:
            print ('unable to create config_file %s' % (configfile))

        for item in self.inputs.get().items():
            fid.write('%s\n' % (item))
        fid.close()

class ApplyWarpInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr='--in=%s',
                  mandatory=True,
                  desc='image to be warped')
    out_file = File(argstr='--out=%s', genfile=True,
                   desc='output filename')
    ref_file = File(exists=True, argstr='--ref=%s',
                     mandatory=True,
                     desc='reference image')
    field_file = File(exists=True, argstr='--warp=%s',
                     mandatory=True,
                     desc='file containing warp field')
    abswarp = traits.Bool(argstr='--abs', xor=['relwarp'],
                          desc="treat warp field as absolute: x' = w(x)")
    relwarp = traits.Bool(argstr='--rel', xor=['abswarp'],
                          desc="treat warp field as relative: x' = x + w(x)")
    datatype = traits.Enum('char', 'short', 'int', 'float', 'double',
                           argstr='--datatype=%s',
                           desc='Force output data type [char short int float double].')
    supersample = traits.Bool(argstr='--super',
                              desc='intermediary supersampling of output, default is off')
    superlevel = traits.Either(traits.Enum('a'), traits.Int,
                               argstr='--superlevel=%s',
                desc="level of intermediary supersampling, a for 'automatic' or integer level. Default = 2")
    premat = File(exists=True, argstr='--premat=%s',
                  desc='filename for pre-transform (affine matrix)')
    postmat = File(exists=True, argstr='--postmat=%s',
                  desc='filename for post-transform (affine matrix)')
    mask_file = File(exists=True, argstr='--mask=%s',
                    desc='filename for mask image (in reference space)')
    interp = traits.Enum('nn', 'trilinear', 'sinc', argstr='--interp=%s',
                         desc='interpolation method {nn,trilinear,sinc}')

class ApplyWarpOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Warped output file')

class ApplyWarp(FSLCommand):
    """Use FSL's applywarp to apply the results of a FNIRT registration

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> aw = fsl.ApplyWarp()
    >>> aw.inputs.in_file = example_data('structural.nii')
    >>> aw.inputs.ref_file = example_data('mni.nii')
    >>> aw.inputs.field_file = 'my_coefficients_filed.nii' #doctest: +SKIP
    >>> res = aw.run() #doctest: +SKIP


    """

    _cmd = 'applywarp'
    input_spec = ApplyWarpInputSpec
    output_spec = ApplyWarpOutputSpec

    def _format_arg(self, name, spec, value):
        if name == 'superlevel':
            return spec.argstr%str(value)
        return super(ApplyWarp, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()

        outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                             suffix='_warp')
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

class SliceTimerInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr='--in=%s',
                  mandatory=True, position=0,
                  desc='filename of input timeseries')
    out_file = File(argstr='--out=%s', genfile=True,
                   desc='filename of output timeseries')
    index_dir = traits.Bool(argstr='--down',
              desc='slice indexing from top to bottom')
    time_repetition = traits.Float(argstr='--repeat=%f',
                                   desc='Specify TR of data - default is 3s')
    slice_direction = traits.Enum(1,2,3, argstr='--direction=%d',
                                  desc='direction of slice acquisition (x=1,y=2,z=3) - default is z')
    interleaved = traits.Bool(argstr='--odd',
                              desc='use interleaved acquisition')
    custom_timings = File(exists=True, argstr='--tcustom=%s',
                          desc='slice timings, in fractions of TR, range 0:1 (default is 0.5 = no shift)')
    global_shift = traits.Float(argstr='--tglobal',
                                desc='shift in fraction of TR, range 0:1 (default is 0.5 = no shift)')
    custom_order = File(exists=True, argstr='--ocustom=%s',
                        desc='filename of single-column custom interleave order file (first slice is referred to as 1 not 0)')

class SliceTimerOutputSpec(TraitedSpec):
    slice_time_corrected_file = File(exists=True, desc='slice time corrected file')

class SliceTimer(FSLCommand):
    """ use FSL slicetimer to perform slice timing correction.

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> st = fsl.SliceTimer()
    >>> st.inputs.in_file = example_data('functional.nii')
    >>> st.inputs.interleaved = True
    >>> result = st.run() #doctest: +SKIP

    """

    _cmd = 'slicetimer'
    input_spec = SliceTimerInputSpec
    output_spec = SliceTimerOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_file = self.inputs.out_file
        if not isdefined(out_file):
            out_file = self._gen_fname(self.inputs.in_file,
                                      suffix='_st')
        outputs['slice_time_corrected_file'] = out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['slice_time_corrected_file']
        return None

class SUSANInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, argstr='%s',
                   mandatory=True, position=1,
                   desc='filename of input timeseries')
    brightness_threshold = traits.Float(argstr='%.10f',
                                        position=2, mandatory=True,
                   desc='brightness threshold and should be greater than' \
                        'noise level and less than contrast of edges to' \
                        'be preserved.')
    fwhm = traits.Float(argstr='%.10f',
                        position=3, mandatory=True,
                        desc='fwhm of smoothing, in mm, gets converted using sqrt(8*log(2))')
    dimension = traits.Enum(3,2, argstr='%d', position=4, usedefault=True,
                            desc='within-plane (2) or fully 3D (3)')
    use_median = traits.Enum(1,0, argstr='%d', position=5, usedefault=True,
                        desc='whether to use a local median filter in the cases where single-point noise is detected')
    usans = traits.List(traits.Tuple(File(exists=True),traits.Float), maxlen=2,
                        argstr='', position=6,
             desc='determines whether the smoothing area (USAN) is to be' \
                  'found from secondary images (0, 1 or 2). A negative' \
                  'value for any brightness threshold will auto-set the' \
                  'threshold at 10% of the robust range')
    out_file = File(argstr='%s', position=-1, genfile=True,
                    desc='output file name')

class SUSANOutputSpec(TraitedSpec):
    smoothed_file = File(exists=True, desc='smoothed output file')

class SUSAN(FSLCommand):
    """ use FSL SUSAN to perform smoothing

    Examples
    --------
    
    >>> from nipype.interfaces import fsl
    >>> from nipype.testing import example_data
    >>> print anatfile #doctest: +SKIP
    anatomical.nii #doctest: +SKIP
    >>> sus = fsl.SUSAN()
    >>> sus.inputs.in_file = example_data('structural.nii')
    >>> sus.inputs.brightness_threshold = 2000.0
    >>> sus.inputs.fwhm = 8.0
    >>> result = sus.run() #doctest: +SKIP
    """

    _cmd = 'susan'
    input_spec = SUSANInputSpec
    output_spec = SUSANOutputSpec

    def _format_arg(self, name, spec, value):
        if name == 'fwhm':
            return spec.argstr%(float(value)/np.sqrt(8 * np.log(2)))
        if name == 'usans':
            if not isdefined(value):
                return '0'
            arglist = [str(len(value))]
            for filename, thresh in value:
                arglist.extend([filename, '%.10f'%thresh])
            return ' '.join(arglist)
        return super(SUSAN, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self._outputs().get()
        out_file = self.inputs.out_file
        if not isdefined(out_file):
            out_file = self._gen_fname(self.inputs.in_file,
                                      suffix='_smooth')
        outputs['smoothed_file'] = out_file
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()['smoothed_file']
        return None
