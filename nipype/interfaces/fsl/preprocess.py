"""The fsl module provides classes for interfacing with the `FSL
<http://www.fmrib.ox.ac.uk/fsl/index.html>`_ command line tools.  This
was written to work with FSL version 4.1.4.

Examples
--------
See the docstrings of the individual classes for examples.

"""

import os
from glob import glob
import warnings

from nipype.interfaces.fsl.base import FSLCommand, FSLInfo
from nipype.interfaces.fsl.base import NEW_FSLCommand, FSLTraitedSpec
from nipype.interfaces.base import Bunch, TraitedSpec, File,\
    InputMultiPath
from nipype.utils.filemanip import fname_presuffix, list_to_filename,\
    split_filename
from nipype.utils.docparse import get_doc
from nipype.utils.misc import container_to_string, is_container, isdefined

import enthought.traits.api as traits

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class BetInputSpec(FSLTraitedSpec):
    '''Note: Currently we don't support -R, -S, -Z,-A or -A2'''
    # We use position args here as list indices - so a negative number
    # will put something on the end
    infile = File(exists=True,
                  desc = 'input file to skull strip',
                  argstr='%s', position=0, mandatory=True)
    outfile = File(desc = 'name of output skull stripped image',
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

class BetOutputSpec(TraitedSpec):
    outfile = File(exists=True,
                   desc="path/name of skullstripped file")
    maskfile = File(
        desc="path/name of binary brain mask (if generated)")
    outlinefile = File(
        desc="path/name of outline file (if generated)")
    meshfile = File(
        desc="path/name of vtk mesh file (if generated)")

class Bet(NEW_FSLCommand):
    """Use FSL BET command for skull stripping.

    For complete details, see the `BET Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/bet2/index.html>`_

    To print out the command line help, use:
        fsl.Bet().inputs_help()

    Examples
    --------
    Initialize Bet with no options, assigning them when calling run:

    >>> from nipype.interfaces import fsl
    >>> btr = fsl.Bet()
    >>> res = btr.run('infile', 'outfile', frac=0.5) # doctest: +SKIP

    Assign options through the ``inputs`` attribute:

    >>> btr = fsl.Bet()
    >>> btr.inputs.infile = 'foo.nii'
    >>> btr.inputs.outfile = 'bar.nii'
    >>> btr.inputs.frac = 0.7
    >>> res = btr.run() # doctest: +SKIP

    Specify options when creating a Bet instance:

    >>> btr = fsl.Bet(infile='infile', outfile='outfile', frac=0.5)
    >>> res = btr.run() # doctest: +SKIP

    Loop over many inputs (Note: the snippet below would overwrite the
    outfile each time):

    >>> btr = fsl.Bet(infile='infile', outfile='outfile')
    >>> fracvals = [0.3, 0.4, 0.5]
    >>> for val in fracvals:
    ...     res = btr.run(frac=val) # doctest: +SKIP

    """

    _cmd = 'bet'
    input_spec = BetInputSpec
    output_spec = BetOutputSpec

    def _run_interface(self, runtime):
        # The returncode is meaningless in Bet.  So check the output
        # in stderr and if it's set, then update the returncode
        # accordingly.
        runtime = super(Bet, self)._run_interface(runtime)
        if runtime.stderr:
            runtime.returncode = 1
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['outfile'] = self.inputs.outfile
        if not isdefined(outputs['outfile']) and isdefined(self.inputs.infile):
            outputs['outfile'] = self._gen_fname(self.inputs.infile,
                                              suffix = '_brain')
        if isdefined(self.inputs.mesh) and self.inputs.mesh:
            outputs['meshfile'] = self._gen_fname(outputs['outfile'],
                                               suffix = '_mesh.vtk',
                                               change_ext = False)
        if (isdefined(self.inputs.mask) and self.inputs.mask) or \
                (isdefined(self.inputs.reduce_bias) and \
                     self.inputs.reduce_bias):
            outputs['maskfile'] = self._gen_fname(outputs['outfile'],
                                               suffix = '_mask')
        return outputs

    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None


class FastInputSpec(FSLTraitedSpec):
    """ Defines inputs (trait classes) for Fast """
    infiles = InputMultiPath(File(exists=True),
                          desc = 'image, or multi-channel set of images, ' \
                              'to be segmented',
                          argstr='%s', position=-1, mandatory=True)
    out_basename = File(desc = 'base name of output files',
                        argstr='-o %s', genfile=True) # maybe not genfile
    number_classes = traits.Range(low=1, high=10, argstr = '-n %d',
                                  desc = 'number of tissue-type classes')
    output_biasfield = traits.Bool(desc = 'output estimated bias field',
                                   argstr = '-b', genfile=True)
    output_biascorrected = traits.Bool(desc = 'output restored image ' \
                                           '(bias-corrected image)',
                                       argstr = '-B', genfile = True)
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
                           argstr = '-g', genfile=True)
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
                                   argstr = '-p', genfile = True)
    

class FastOutputSpec(TraitedSpec):
    """Specify possible outputs from Fast"""
    tissue_class_map = File(exists=True,
                            desc = 'path/name of binary segmented volume file' \
                                ' one val for each class  _seg')
    tissue_class_files = File(desc = 'path/name of binary segmented volumes ' \
                                  'one file for each class  _seg_x')
    restored_image = File(desc = 'restored images (one for each input image) ' \
                              'named according to the input images _restore')

    mixeltype  = File(desc = "path/name of mixeltype volume file _mixeltype")

    partial_volume_map = File(desc = "path/name of partial volume file _pveseg")
    partial_volume_files  = File(desc = 'path/name of partial volumes files ' \
                                     'one for each class, _pve_x')
    
    bias_field = File(desc = 'Estimated bias field _bias')
    probability_maps = File(desc= 'filenames, one for each class, for each ' \
                                'input, prob_x')


class NEW_Fast(NEW_FSLCommand):
    """ Use FSL FAST for segmenting and bias correction.

    For complete details, see the `FAST Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/fast4/index.html>`_
    """
    _cmd = 'fast'
    input_spec = FastInputSpec
    output_spec = FastOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        orignames = self.inputs.infiles
        if isdefined(self.inputs.out_basename):
            basepth, basename = os.path.split(self.inputs.out_basename)
        
        for item in self.inputs.infiles:
            print item
        outputs['tissue_class_map'] = 'FIX'
        if not isdefined(outputs['outfile']) and isdefined(self.inputs.infile):
            outputs['outfile'] = self._gen_fname(self.inputs.infile,
                                              suffix = '_brain')
        if isdefined(self.inputs.mesh) and self.inputs.mesh:
            outputs['meshfile'] = self._gen_fname(outputs['outfile'],
                                               suffix = '_mesh.vtk',
                                               change_ext = False)
        if (isdefined(self.inputs.mask) and self.inputs.mask) or \
                (isdefined(self.inputs.reduce_bias) and self.inputs.reduce_bias):
            outputs['maskfile'] = self._gen_fname(outputs['outfile'],
                                               suffix = '_mask')
        return outputs 


   

class Fast(FSLCommand):
    """Use FSL FAST for segmenting and bias correction.

    For complete details, see the `FAST Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/fast4/index.html>`_

    To print out the command line help, use:
        fsl.Fast().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> faster = fsl.Fast(out_basename = 'myfasted')
    >>> fasted = faster.run(['file1', 'file2'])

    >>> faster = fsl.Fast(infiles=['filea', 'fileb'], out_basename='myfasted')
    >>> fasted = faster.run()

    """

    @property
    def cmd(self):
        """sets base command, not editable"""
        return 'fast'

    opt_map = {'number_classes':       '-n %d',
            'bias_iters':           '-I %d',
            'bias_lowpass':         '-l %d',  # in mm
            'img_type':             '-t %d',
            'init_seg_smooth':      '-f %.3f',
            'segments':             '-g',
            'init_transform':       '-a %s',
            # This option is not really documented on the Fast web page:
            # http://www.fmrib.ox.ac.uk/fsl/fast4/index.html#fastcomm
            # I'm not sure if there are supposed to be exactly 3 args or what
            'other_priors':         '-A %s %s %s',
            'nopve':                '--nopve',
            'output_biasfield':     '-b',
            'output_biascorrected': '-B',
            'nobias':               '-N',
            'n_inputimages':        '-S %d',
            'out_basename':         '-o %s',
            'use_priors':           '-P',  # must also set -a!
            'segment_iters':        '-W %d',
            'mixel_smooth':         '-R %.2f',
            'iters_afterbias':      '-O %d',
            'hyper':                '-H %.2f',
            'verbose':              '-v',
            'manualseg':            '-s %s',
            'probability_maps':     '-p',
            'infiles':               None,
            }

    def inputs_help(self):
        """Print command line documentation for FAST."""
        print get_doc(self.cmd, self.opt_map, trap_error=False)

    def run(self, infiles=None, **inputs):
        """Execute the FSL fast command.

        Parameters
        ----------
        infiles : string or list of strings
            File(s) to be segmented or bias corrected
        inputs : dict, optional
            Additional ``inputs`` assignments can be passed in.

        Returns
        -------
        results : InterfaceResult
            An :class:`nipype.interfaces.base.InterfaceResult` object
            with a copy of self in `interface`

        """

        if infiles:
            self.inputs.infiles = infiles
        if not self.inputs.infiles:
            raise AttributeError('Fast requires input file(s)')
        self.inputs.update(**inputs)
        return super(Fast, self).run()

    def _parse_inputs(self):
        '''Call our super-method, then add our input files'''
        # Could do other checking above and beyond regular _parse_inputs here
        allargs = super(Fast, self)._parse_inputs(skip=('infiles'))
        if self.inputs.infiles:
            allargs.append(container_to_string(self.inputs.infiles))
        return allargs

    def outputs(self):
        """Returns a :class:`nipype.interfaces.base.Bunch` with outputs

        Parameters
        ----------
        Each attribute in ``outputs`` is a list.  There will be
        one set of ``outputs`` for each file specified in
        ``infiles``.  ``outputs`` will contain the following
        files:

        mixeltype : list
            filename(s)
        partial_volume_map : list
            filenames, one for each input
        partial_volume_files : list
            filenames, one for each class, for each input
        tissue_class_map : list
            filename(s), each tissue has unique int value
        tissue_class_files : list
            filenames, one for each class, for each input
        restored_image : list
            filename(s) bias corrected image(s)
        bias_field : list
            filename(s)
        probability_maps : list
            filenames, one for each class, for each input

        """

        outputs = Bunch(mixeltype=[],
                seg=[],
                partial_volume_map=[],
                partial_volume_files=[],
                tissue_class_map=[],
                tissue_class_files=[],
                bias_corrected=[],
                bias_field=[],
                prob_maps=[])
        return outputs

    def aggregate_outputs(self):
        """Create a Bunch which contains all possible files generated
        by running the interface.  Some files are always generated, others
        depending on which ``inputs`` options are set.

        Returns
        -------
        outputs : Bunch object

        Notes
        -----
        For each item in Bunch:
        If [] empty list, optional file was not generated
        Else, list contains path,filename of generated outputfile(s)

        Raises
        ------
        IOError
            If any expected output file is not found.

        """
        _, envext = FSLInfo.outputtype()
        outputs = self.outputs()

        if not is_container(self.inputs.infiles):
            infiles = [self.inputs.infiles]
        else:
            infiles = self.inputs.infiles
        for item in infiles:
            # get basename (correct fsloutpputytpe extension)
            if self.inputs.out_basename:
                pth, nme = os.path.split(item)
                _, _ = os.path.splitext(nme)
                item = pth + self.inputs.out_basename + envext
            else:
                nme, _ = os.path.splitext(item)
                item = nme + envext
            # get number of tissue classes
            if not self.inputs.number_classes:
                nclasses = 3
            else:
                nclasses = self.inputs.number_classes

            # always seg, (plus mutiple?)
            outputs.seg.append(fname_presuffix(item, suffix='_seg'))
            if self.inputs.segments:
                for i in range(nclasses):
                    outputs.seg.append(fname_presuffix(item,
                        suffix='_seg_%d' % (i)))
                    # always pve,mixeltype unless nopve = True
            if not self.inputs.nopve:
                fname = fname_presuffix(item, suffix='_pveseg')
                outputs.partial_volume_map.append(fname)
                fname = fname_presuffix(item, suffix='_mixeltype')
                outputs.mixeltype.append(fname)

                for i in range(nclasses):
                    fname = fname_presuffix(item, suffix='_pve_%d' % (i))
                    outputs.partial_volume_files.append(fname)

            # biasfield ?
            if self.inputs.output_biasfield:
                outputs.bias_field.append(fname_presuffix(item, suffix='_bias'))

            # restored image (bias corrected)?
            if self.inputs.output_biascorrected:
                fname = fname_presuffix(item, suffix='_restore')
                outputs.biascorrected.append(fname)

            # probability maps ?
            if self.inputs.probability_maps:
                for i in range(nclasses):
                    fname = fname_presuffix(item, suffix='_prob_%d' % (i))
                    outputs.prob_maps.append(fname)

        # For each output file-type (key), check that any expected
        # files in the output list exist.
        for outtype, outlist in outputs.items():
            if len(outlist) > 0:
                for outfile in outlist:
                    if not len(glob(outfile)) == 1:
                        msg = "Output file '%s' of type '%s' was not generated"\
                                % (outfile, outtype)
                        raise IOError(msg)

        return outputs

class FlirtInputSpec(FSLTraitedSpec):
    infile = File(exists = True, argstr = '-in %s', mandatory = True,
                  position = 0, desc = 'input file')
    # XXX Not clear if position is required for mandatory flirt inputs
    # since they are prefixed with argstrs.  But doing it to follow
    # our previous convention and so we can test the generated command
    # line.
    reference = File(exists = True, argstr = '-ref %s', mandatory = True,
                     position = 1, desc = 'reference file')
    outfile = File(argstr = '-out %s', desc = 'registered output file',
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

class FlirtOutputSpec(TraitedSpec):
    outfile = File(exists = True,
                   desc = 'path/name of registered file (if generated)')
    outmatrix = File(exists = True,
                     desc = 'path/name of calculated affine transform ' \
                         '(if generated)')

class Flirt(NEW_FSLCommand):
    """Use FSL FLIRT for coregistration.

    For complete details, see the `FLIRT Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/flirt/index.html>`_

    To print out the command line help, use:
        fsl.Flirt().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> flt = fsl.Flirt(bins=640, searchcost='mutualinfo')
    >>> flt.inputs.infile = 'subject.nii'
    >>> flt.inputs.reference = 'template.nii'
    >>> flt.inputs.outfile = 'moved_subject.nii'
    >>> flt.inputs.outmatrix = 'subject_to_template.mat'
    >>> res = flt.run()

    """
    _cmd = 'flirt'
    input_spec = FlirtInputSpec
    output_spec = FlirtOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['outfile'] = self.inputs.outfile
        # Generate an outfile if one is not provided
        if not isdefined(outputs['outfile']) and isdefined(self.inputs.infile):
            outputs['outfile'] = self._gen_fname(self.inputs.infile,
                                                 suffix = '_flirt')
        outputs['outmatrix'] = self.inputs.outmatrix
        # Generate an outmatrix file if one is not provided
        if not isdefined(outputs['outmatrix']) and \
                isdefined(self.inputs.infile):
            outputs['outmatrix'] = self._gen_fname(self.inputs.infile,
                                                   suffix = '_flirt.mat',
                                                   change_ext = False)
        return outputs

    def _gen_filename(self, name):
        if name in ('outfile', 'outmatrix'):
            return self._list_outputs()[name]
        else:
            return None


class ApplyXfm(Flirt):
    pass


class McFlirtInputSpec(FSLTraitedSpec):
    infile = File(exists=True, position= 0, argstr="-in %s", mandatory=True)
    outfile = File(exists=True, argstr='-out %s', genfile=True)
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
    reffile = File(exists=True, argstr='-reffile %s')
    
class McFlirtOutputSpec(TraitedSpec):
    outfile = File(exists=True)
    varianceimg = File(exists=True)
    stdimg = File(exists=True)
    meanimg = File(exists=True)
    parfile = File(exists=True)
    outmatfile = File(exists=True)

class McFlirt(NEW_FSLCommand):
    """Use FSL MCFLIRT to do within-modality motion correction.

    For complete details, see the `MCFLIRT Documentation.
    <http://www.fmrib.ox.ac.uk/fsl/mcflirt/index.html>`_

    To print out the command line help, use:
        McFlirt().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> mcflt = fsl.McFlirt(infile='timeseries.nii', cost='mututalinfo')
    >>> res = mcflt.run()

    """
    _cmd = 'mcflirt'
    input_spec = McFlirtInputSpec
    output_spec = McFlirtOutputSpec

    def _list_outputs(self):
        cwd = os.getcwd()
        outputs = self._outputs().get()
        
        outputs['outfile'] = self.inputs.outfile
        if not isdefined(outputs['outfile']):
            outputs['outfile'] = self._gen_fname(self.inputs.infile,
                                              suffix = '_mcf')
        
        # XXX Need to change 'item' below to something that exists
        # outfile? infile?
        # These could be handled similarly to default values for inputs
        if isdefined(self.inputs.statsimgs):
            outputs['varianceimg'] = self._gen_fname(self.inputs.infile, cwd=cwd, suffix='_variance')
            outputs['stdimg'] = self._gen_fname(self.inputs.infile, cwd=cwd, suffix='_sigma')
            outputs['meanimg'] = self._gen_fname(self.inputs.infile, cwd=cwd, suffix='_meanvol')
        if isdefined(self.inputs.savemats):
            pth, basename, _ = split_filename(self.inputs.infile)
            matname = os.path.join(pth, basename + '.mat')
            outputs['outmatfile'] = matname
        if isdefined(self.inputs.saveplots):
            # Note - if e.g. outfile has .nii.gz, you get .nii.gz.par, which is
            # what mcflirt does!
            outputs['parfile'] = outputs['outfile'] + '.par'
        return outputs
    
    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None

class FnirtInputSpec(FSLTraitedSpec):
    ref_file = File(exists=True, argstr='--ref=%s', mandatory=True,
                    desc='name of reference image')
    infile = File(exists=True, argstr='--in=%s', mandatory=True,
                  desc='name of input image')
    affine_file = File(exists=True, argstr='--aff=%s',
                       desc='name of file containing affine transform')
    inwarp_file = File(exists=True, argstr='--inwarp=%s',
                       desc='name of file containing initial non-linear warps')
    in_intensitymap_file = File(exists=True, argstr='--intin=%s',
                             desc='name of file/files containing initial intensity maping')
    fieldcoeff_file = File(genfile=True, argstr='--cout=%s',
                           desc='name of output file with field coefficients or true')
    outfile = traits.Either(traits.Bool, File, genfile=True,
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

class FnirtOutputSpec(TraitedSpec):
    fieldcoeff_file = File(exists=True, desc='file with field coefficients')
    outfile = File(exists=True, desc='warped image')
    field_file = File(exists=True, desc='file with warp field')
    jacobian_file = File(exists=True, desc='file containing Jacobian of the field')
    modulatedref_file = File(exists=True, desc='file containing intensity modulated --ref')
    out_intensitymap_file = File(exists=True,
                        desc='file containing info pertaining to intensity mapping')
    log_file = File(exists=True, desc='Name of log-file')

class Fnirt(NEW_FSLCommand):
    """Use FSL FNIRT for non-linear registration.

    Examples
    --------
    >>> from nipype.interfaces import fsl
    >>> fnt = fsl.Fnirt(affine='affine.mat')
    >>> res = fnt.run(reference='ref.nii', infile='anat.nii') # doctests: +SKIP

    T1 -> Mni153
    
    >>> from nipype.interfaces import fsl
    >>> fnirt_mprage = fsl.Fnirt()
    >>> fnirt_mprage.inputs.imgfwhm = [8, 4, 2]
    >>> fnirt_mprage.inputs.sub_sampling = [4, 2, 1]

    Specify the resolution of the warps, currently not part of the
    ``fnirt_mprage.inputs``:
    
    >>> fnirt_mprage.inputs.flags = '--warpres 6, 6, 6'
    >>> res = fnirt_mprage.run(infile='subj.nii', reference='mni.nii')
    
    We can check the command line and confirm that it's what we expect.
    
    >>> fnirt_mprage.cmdline  #doctest: +NORMALIZE_WHITESPACE
    'fnirt --warpres 6, 6, 6 --infwhm=8,4,2 --in=subj.nii --ref=mni.nii --subsamp=4,2,1'

    """
    
    _cmd = 'fnirt'
    input_spec = FnirtInputSpec
    output_spec = FnirtOutputSpec

    out_map = dict(outfile='_warp', field_file='_field',
                   jacobian_file='_field_jacobian',
                   modulatedref_file='_modulated',
                   out_intensitymap_file='_intmap',
                   log_file='.log')
    def _format_arg(self, name, spec, value):
        if name in out_map.keys():
            if isinstance(value, bool):
                fname = self._list_outputs()[name]
            else:
                fname = value
            return spec.argstr % fname
        return super(Fnirt, self)._format_arg(name, spec, value)

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
        for name, suffix in out_map.items():
            src = self.inputs.infile
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
        if name in out_map.keys():
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

class ApplyWarpInputSpec(FSLTraitedSpec):
    infile = File(exists=True, argstr='--in=%s',
                  mandatory=True,
                  desc='image to be warped')
    outfile = File(argstr='--out=%s', genfile=True,
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
    outfile = File(exists=True, desc='Warped output file')

class ApplyWarp(NEW_FSLCommand):
    """Use FSL's applywarp to apply the results of a Fnirt registration

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
                             
        outputs['outfile'] = self._gen_fname(self.inputs.infile,
                                             suffix='_warp')
        return outputs
    
    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None

class SliceTimerInputSpec(FSLTraitedSpec):
    infile = File(exists=True, argstr='--in=%s',
                  mandatory=True, position=0,
                  desc='filename of input timeseries')
    outfile = File(argstr='--out=%s', genfile=True,
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
    outfile = File(exists=True, desc='slice time corrected file')

class SliceTimer(NEW_FSLCommand):
    """ use FSL slicetimer to perform slice timing correction.

    Examples
    --------
    
    """

    _cmd = 'slicetimer'
    input_spec = SliceTimerInputSpec
    output_spec = SliceTimerOutputSpec

    def _list_outputs(self):
        outputs = self._outputs().get()
        outfile = self.inputs.outfile
        if not isdefined(outfile):
            outfile = self._gen_fname(self.inputs.infile,
                                      suffix='_st')
        outputs['outfile'] = outfile
        return outputs
    
    def _gen_filename(self, name):
        if name == 'outfile':
            return self._list_outputs()[name]
        return None
