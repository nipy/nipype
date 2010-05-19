"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os
import warnings

from nipype.interfaces.fsl.base import FSLCommand, FSLCommandInputSpec
from nipype.interfaces.base import TraitedSpec, File,\
    InputMultiPath, OutputMultiPath
from nipype.utils.filemanip import split_filename
from nipype.utils.misc import isdefined

import enthought.traits.api as traits

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
    nooutput = traits.Bool(argstr='-n',
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
    out_file = File(exists=True,
                   desc="path/name of skullstripped file")
    mask_file = File(
        desc="path/name of binary brain mask (if generated)")
    outlinefile = File(
        desc="path/name of outline file (if generated)")
    meshfile = File(
        desc="path/name of vtk mesh file (if generated)")

class BET(FSLCommand):
    """Use FSL BET command for skull stripping.

    For complete details, see the `BET Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/bet2/index.html>`_

    To print out the command line help, use:
        fsl.BET().inputs_help()

    Examples
    --------
    Initialize BET with no options, assigning them when calling run:

    >>> from nipype.interfaces import fsl
    >>> btr = fsl.BET()
    >>> res = btr.run('in_file', 'out_file', frac=0.5) # doctest: +SKIP

    Assign options through the ``inputs`` attribute:

    >>> btr = fsl.BET()
    >>> btr.inputs.in_file = 'foo.nii'
    >>> btr.inputs.out_file = 'bar.nii'
    >>> btr.inputs.frac = 0.7
    >>> res = btr.run() # doctest: +SKIP

    Specify options when creating a BET instance:

    >>> btr = fsl.BET(in_file='in_file', out_file='out_file', frac=0.5)
    >>> res = btr.run() # doctest: +SKIP

    Loop over many inputs (Note: the snippet below would overwrite the
    out_file each time):

    >>> btr = fsl.BET(in_file='in_file', out_file='out_file')
    >>> fracvals = [0.3, 0.4, 0.5]
    >>> for val in fracvals:
    ...     res = btr.run(frac=val) # doctest: +SKIP

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

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']) and isdefined(self.inputs.in_file):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                              suffix = '_brain')
        if isdefined(self.inputs.mesh) and self.inputs.mesh:
            outputs['meshfile'] = self._gen_fname(outputs['out_file'],
                                               suffix = '_mesh.vtk',
                                               change_ext = False)
        if (isdefined(self.inputs.mask) and self.inputs.mask) or \
                (isdefined(self.inputs.reduce_bias) and \
                     self.inputs.reduce_bias):
            outputs['mask_file'] = self._gen_fname(outputs['out_file'],
                                               suffix = '_mask')
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None


class FASTInputSpec(FSLCommandInputSpec):
    """ Defines inputs (trait classes) for FAST """
    in_files = InputMultiPath(File(exists=True),
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
    nopve = traits.Bool(desc = 'turn off PVE (partial volume estimation)',
                        argstr = '--nopve')
    nobias = traits.Bool(desc = 'do not remove bias field',
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
    manualseg = File(exists=True, desc = 'Filename containing intensities',
                     argstr = '-s %s')
    probability_maps = traits.Bool(desc = 'outputs individual probability maps',
                                   argstr = '-p')
    

class FASTOutputSpec(TraitedSpec):
    """Specify possible outputs from FAST"""
    tissue_class_map = File(exists=True,
                            desc = 'path/name of binary segmented volume file' \
                            ' one val for each class  _seg')
    tissue_class_files =OutputMultiPath( File(desc = 'path/name of binary segmented volumes ' \
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
        for  i in range(nclasses):
            outputs['tissue_class_files'].append(self._gen_fname(basefile,
                                                                 suffix = '_seg_%d'%(i)))
        if isdefined(self.inputs.output_biascorrected):
            for val,f in enumerate(self.inputs.in_files):
                outputs['restored_image'].append(self._gen_fname(f,
                                                                 suffix = '_restore_%d'%(val)))
        outputs['mixeltype'] = self._gen_fname(basefile, suffix = '_mixeltype')
        if not self.inputs.nopve:
            outputs['partial_volume_map'] = self._gen_fname(basefile, suffix = '_pveseg')
            for i in range(nclasses):
                outputs['partial_volume_files'].append(self._gen_fname(basefile,
                                                                       suffix='_pve_%d'%(i)))
        if self.inputs.output_biasfield:
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
    outmatrix = File(argstr = '-omat %s',
                     desc = 'output affine matrix in 4x4 asciii format',
                     genfile = True, position = 3)
    inmatrix = File(argstr = '-init %s', desc = 'input 4x4 affine matrix')

    datatype = traits.Enum('char', 'short', 'int', 'float', 'double',
                           argstr = '-datatype %s',
                           desc = 'force output data type')
    cost = traits.Enum('mutualinfo', 'corratio', 'normcorr', 'normmi',
                       'leastsq', 'labeldiff',
                       argstr = '-cost %s',
                       desc = 'cost function')
    # XXX What is the difference between 'cost' and 'searchcost'?  Are
    # these both necessary or do they map to the same variable.
    searchcost = traits.Enum('mutualinfo', 'corratio', 'normcorr', 'normmi',
                             'leastsq', 'labeldiff',
                             argstr = '-searchcost %s',
                             desc = 'cost function')
    usesqform = traits.Bool(argstr = '-usesqform',
                            desc = 'initialize using sform or qform')
    displayinit = traits.Bool(argstr = '-displayinit',
                              desc = 'display initial matrix')
    anglerep = traits.Enum('quaternion', 'euler',
                           argstr = '-anglerep %s',
                           desc = 'representation of rotation angles')
    interp = traits.Enum('trilinear', 'nearestneighbour', 'sinc',
                         argstr = '-interp %s',
                         desc = 'final interpolation method used in reslicing')
    sincwidth = traits.Int(argstr = '-sincwidth %d', units = 'voxels',
                           desc = 'full-width in voxels')
    sincwindow = traits.Enum('rectangular', 'hanning', 'blackman',
                             argstr = '-sincwindow %s',
                             desc = 'sinc window') # XXX better doc
    bins = traits.Int(argstr = '-bins %d', desc = 'number of histogram bins')
    dof = traits.Int(argstr = '-dof %d',
                     desc = 'number of transform degrees of freedom')
    noresample = traits.Bool(argstr = '-noresample',
                             desc = 'do not change input sampling')
    forcescaling = traits.Bool(argstr = '-forcescaling',
                               desc = 'force rescaling even for low-res images')
    minsampling = traits.Float(argstr = '-minsampling %f', units = 'mm',
                               desc ='set minimum voxel dimension for sampling')
    paddingsize = traits.Int(argstr = '-paddingsize %d', units = 'voxels',
                             desc = 'for applyxfm: interpolates outside image '\
                                 'by size')
    searchrx = traits.List(traits.Int, minlen = 2, maxlen = 2, units ='degrees',
                           argstr = '-searchrx %s',
                           desc = 'search angles along x-axis, in degrees')
    searchry = traits.List(traits.Int, minlen = 2, maxlen = 2, units ='degrees',
                           argstr = '-searchry %s',
                           desc = 'search angles along y-axis, in degrees')
    searchrz = traits.List(traits.Int, minlen = 2, maxlen = 2, units ='degrees',
                           argstr = '-searchrz %s',
                           desc = 'search angles along z-axis, in degrees')
    nosearch = traits.Bool(argstr = '-nosearch',
                           desc = 'set all angular searches to ranges 0 to 0')
    coarsesearch = traits.Int(argstr = '-coarsesearch %d', units = 'degrees',
                              desc = 'coarse search delta angle')
    finesearch = traits.Int(argstr = '-finesearch %d', units = 'degrees',
                            desc = 'fine search delta angle')
    schedule = File(exists = True, argstr = '-schedule %s',
                    desc = 'replaces default schedule')
    refweight = File(exists = True, argstr = '-refweight %s',
                     desc = 'File for reference weighting volume')
    inweight = File(exists = True, argstr = '-inweight %s',
                    desc = 'File for input weighting volume')
    noclamp = traits.Bool(argstr = '-noclamp',
                          desc = 'do not use intensity clamping')
    noresampblur = traits.Bool(argstr = '-noresampblur',
                               desc = 'do not use blurring on downsampling')
    rigid2D = traits.Bool(argstr = '-2D',
                          desc = 'use 2D rigid body mode - ignores dof')
    verbose = traits.Int(argstr = '-verbose %d',
                         desc = 'verbose mode, 0 is least')

class FLIRTOutputSpec(TraitedSpec):
    out_file = File(exists = True,
                   desc = 'path/name of registered file (if generated)')
    outmatrix = File(exists = True,
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
    >>> flt = fsl.FLIRT(bins=640, searchcost='mutualinfo')
    >>> flt.inputs.in_file = 'subject.nii'
    >>> flt.inputs.reference = 'template.nii'
    >>> flt.inputs.out_file = 'moved_subject.nii'
    >>> flt.inputs.outmatrix = 'subject_to_template.mat'
    >>> res = flt.run()

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
        outputs['outmatrix'] = self.inputs.outmatrix
        # Generate an outmatrix file if one is not provided
        if not isdefined(outputs['outmatrix']) and \
                isdefined(self.inputs.in_file):
            outputs['outmatrix'] = self._gen_fname(self.inputs.in_file,
                                                   suffix = '_flirt.mat',
                                                   change_ext = False)
        return outputs

    def _gen_filename(self, name):
        if name in ('out_file', 'outmatrix'):
            return self._list_outputs()[name]
        else:
            return None

    
class ApplyXfm(FLIRT):
    pass


class MCFLIRTInputSpec(FSLCommandInputSpec):
    in_file = File(exists=True, position= 0, argstr="-in %s", mandatory=True)
    out_file = File(exists=True, argstr='-out %s', genfile=True)
    cost = traits.Enum('mutualinfo','woods','corratio','normcorr','normmi','leastsquares', argstr='-cost %s')
    bins = traits.Int(argstr='-bins %d')
    dof = traits.Int(argstr='-dof %d')
    refvol = traits.Int(argstr='-refvol %d')
    scaling = traits.Float(argstr='-scaling %.2f')
    smooth = traits.Float(argstr='-smooth %.2f')
    rotation = traits.Int(argstr='-rotation %d')
    stages = traits.Int(argstr='-stages %d')
    init = File(exists=True, argstr='-init %s')
    usegradient = traits.Bool(argstr='-gdt')
    usecontour = traits.Bool(argstr='-edge')
    meanvol = traits.Bool(argstr='-meanvol')
    statsimgs = traits.Bool(argstr='-stats')
    savemats = traits.Bool(argstr='-mats')
    saveplots = traits.Bool(argstr='-plots')
    ref_file = File(exists=True, argstr='-reffile %s')
    
class MCFLIRTOutputSpec(TraitedSpec):
    out_file = File(exists=True)
    varianceimg = File(exists=True)
    stdimg = File(exists=True)
    meanimg = File(exists=True)
    parfile = File(exists=True)
    outmatfile = File(exists=True)

class MCFLIRT(FSLCommand):
    """Use FSL MCFLIRT to do within-modality motion correction.

    For complete details, see the `MCFLIRT Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/mcflirt/index.html>`_

    To print out the command line help, use:
        MCFLIRT().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> mcflt = fsl.MCFLIRT(in_file='timeseries.nii', cost='mututalinfo')
    >>> res = mcflt.run()

    """
    _cmd = 'mcflirt'
    input_spec = MCFLIRTInputSpec
    output_spec = MCFLIRTOutputSpec

    def _list_outputs(self):
        cwd = os.getcwd()
        outputs = self._outputs().get()
        
        outputs['out_file'] = self.inputs.out_file
        if not isdefined(outputs['out_file']):
            outputs['out_file'] = self._gen_fname(self.inputs.in_file,
                                              suffix = '_mcf')
        
        # XXX Need to change 'item' below to something that exists
        # out_file? in_file?
        # These could be handled similarly to default values for inputs
        if isdefined(self.inputs.statsimgs):
            outputs['varianceimg'] = self._gen_fname(self.inputs.in_file, cwd=cwd, suffix='_variance')
            outputs['stdimg'] = self._gen_fname(self.inputs.in_file, cwd=cwd, suffix='_sigma')
            outputs['meanimg'] = self._gen_fname(self.inputs.in_file, cwd=cwd, suffix='_meanvol')
        if isdefined(self.inputs.savemats):
            pth, basename, _ = split_filename(self.inputs.in_file)
            matname = os.path.join(pth, basename + '.mat')
            outputs['outmatfile'] = matname
        if isdefined(self.inputs.saveplots):
            # Note - if e.g. out_file has .nii.gz, you get .nii.gz.par, which is
            # what mcflirt does!
            outputs['parfile'] = outputs['out_file'] + '.par'
        return outputs
    
    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None

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
                             desc='name of file/files containing initial intensity maping')
    fieldcoeff_file = File(genfile=True, argstr='--cout=%s',
                           desc='name of output file with field coefficients or true')
    out_file = traits.Either(traits.Bool, File, genfile=True,
                            argstr='--iout=%s',
                            desc='name of output image or true')
    field_file = traits.Either(traits.Bool, File, genfile=True,
                               argstr='--fout=%s',
                               desc='name of output file with field or true')
    jacobian_file = traits.Either(traits.Bool, File, genfile=True,
                                  argstr='--jout=%s',
                                  desc='name of file for writing out the Jacobian of the field (for diagnostic or VBM purposes)')
    modulatedref_file = traits.Either(traits.Bool, File, genfile=True,
                                      argstr='--refout=%s',
                                      desc='name of file for writing out intensity modulated --ref (for diagnostic purposes)')
    out_intensitymap_file = traits.Either(traits.Bool, File, genfile=True,
                                      argstr='--intout=%s',
                                      desc='name of files for writing information pertaining to intensity mapping')
    log_file = traits.Either(traits.Bool, File, genfile=True,
                             argstr='--logout=%s',
                             desc='Name of log-file')
    config_file = File(exists=True, argstr='--config=%s',
                       desc='Name of config file specifying command line arguments')
    refmask_file = File(exists=True, argstr='--refmask=%s',
                        desc='name of file with mask in reference space')
    inmask_file = File(exists=True, argstr='--inmask=%s',
                       desc='name of file with mask in input image space')
    skiprefmask = traits.Bool(argstr='--applyrefmask 0',
                              requires=['refmask_file'],
                              desc='Skip specified refmask if set, default false')
    skipinmask = traits.Bool(argstr='--applyinmask 0',
                             requires=['inmask_file'],
                             desc='skip specified inmask if set, default false')
    skipimplicitrefmasking = traits.Bool(argstr='--imprefm 0',
                                      desc='skip implicit masking  based on value in --ref image. Default = 0')
    skipimplicitinmasking = traits.Bool(argstr='--impinm 0',
                                      desc='skip implicit masking  based on value in --in image. Default = 0')
    refmask_val = traits.Float(argstr='--imprefval=%f',
                              desc='Value to mask out in --ref image. Default =0.0')
    inmask_val = traits.Float(argstr='--impinval=%f',
                              desc='Value to mask out in --in image. Default =0.0')
    max_nonlin_iter = traits.Tuple(traits.Int,traits.Int,traits.Int,traits.Int,
                                   argstr='--miter=%d,%d,%d,%d',
                                   desc='Max # of non-linear iterations, default 5,5,5,5')
    subsampling_scheme = traits.Tuple(traits.Int,traits.Int,traits.Int,traits.Int,
                                   argstr='--subsamp=%d,%d,%d,%d',
                                   desc='sub-sampling scheme, default 4,2,1,1')
    warp_resolution = traits.Tuple(traits.Int, traits.Int, traits.Int,
                                   argstr='--warpres=%d,%d,%d',
                                   desc='(approximate) resolution (in mm) of warp basis in x-, y- and z-direction, default 10,10,10')
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
        desc='Weight of regularisation, default depending on --ssqlambda and --regmod switches. See user documetation.')
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
                                        desc='Resolution (in mm) of bias-field modelling local intensities, default 50,50,50')
    bias_regularization_lambda = traits.Float(argstr='--biaslambda=%f',
                                              desc='Weight of regularisation for bias-field, default 10000')
    skip_intensity_mapping = traits.Bool(argstr='--estint 0',
                                         desc='Skip estimate intensity-mapping deafult false')
    hessian_precision = traits.Enum('double', 'float', argstr='--numprec=%s',
                                    desc='Precision for representing Hessian, double or float. Default double')

class FNIRTOutputSpec(TraitedSpec):
    fieldcoeff_file = File(exists=True, desc='file with field coefficients')
    out_file = File(exists=True, desc='warped image')
    field_file = File(exists=True, desc='file with warp field')
    jacobian_file = File(exists=True, desc='file containing Jacobian of the field')
    modulatedref_file = File(exists=True, desc='file containing intensity modulated --ref')
    out_intensitymap_file = File(exists=True,
                        desc='file containing info pertaining to intensity mapping')
    log_file = File(exists=True, desc='Name of log-file')

class FNIRT(FSLCommand):
    """Use FSL FNIRT for non-linear registration.

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> fnt = fsl.FNIRT(affine='affine.mat')
    >>> res = fnt.run(reference='ref.nii', in_file='anat.nii') # doctests: +SKIP

    T1 -> Mni153
    
    >>> from nipype.interfaces import fsl
    >>> fnirt_mprage = fsl.FNIRT()
    >>> fnirt_mprage.inputs.imgfwhm = [8, 4, 2]
    >>> fnirt_mprage.inputs.sub_sampling = [4, 2, 1]

    Specify the resolution of the warps, currently not part of the
    ``fnirt_mprage.inputs``:
    
    >>> fnirt_mprage.inputs.flags = '--warpres 6, 6, 6'
    >>> res = fnirt_mprage.run(in_file='subj.nii', reference='mni.nii')
    
    We can check the command line and confirm that it's what we expect.
    
    >>> fnirt_mprage.cmdline  #doctest: +NORMALIZE_WHITESPACE
    'fnirt --warpres 6, 6, 6 --infwhm=8,4,2 --in=subj.nii --ref=mni.nii --subsamp=4,2,1'

    """
    
    _cmd = 'fnirt'
    input_spec = FNIRTInputSpec
    output_spec = FNIRTOutputSpec

    out_map = dict(out_file='_warp', field_file='_field',
                   jacobian_file='_field_jacobian',
                   modulatedref_file='_modulated',
                   out_intensitymap_file='_intmap',
                   log_file='.log')
    
    def _format_arg(self, name, spec, value):
        if name in self.out_map.keys():
            if isinstance(value, bool):
                fname = self._list_outputs()[name]
            else:
                fname = value
            return spec.argstr % fname
        return super(FNIRT, self)._format_arg(name, spec, value)

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
        outputs['fieldcoeff_file']=self.inputs.fieldcoeff_file
        if not isdefined(self.inputs.fieldcoeff_file):
            outputs['fieldcoeff_file'] = self._gen_fname(self.inputs.file,
                                                         suffix='_warpcoef')
        for name, suffix in self.out_map.items():
            src = self.inputs.in_file
            if name == 'modulatedref_file':
                src = self.inputs.ref_file
            if name == 'log_file':
                val = self._set_output(name, src, suffix, change_ext=False)
            else:
                val = self._set_output(name, src, suffix)
            if val:
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
    fieldfile = File(exists=True, argstr='--warp=%s',
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
    maskfile = File(exists=True, argstr='--mask=%s',
                    desc='filename for mask image (in reference space)')
    interp = traits.Enum('nn', 'trilinear', 'sinc', argstr='--interp=%s',
                         desc='interpolation method {nn,trilinear,sinc}')

class ApplyWarpOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Warped output file')

class ApplyWarp(FSLCommand):
    """Use FSL's applywarp to apply the results of a FNIRT registration

    Examples
    --------
    
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
    out_file = File(exists=True, desc='slice time corrected file')

class SliceTimer(FSLCommand):
    """ use FSL slicetimer to perform slice timing correction.

    Examples
    --------
    
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
        outputs['out_file'] = out_file
        return outputs
    
    def _gen_filename(self, name):
        if name == 'out_file':
            return self._list_outputs()[name]
        return None
