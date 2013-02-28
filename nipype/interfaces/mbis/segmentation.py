# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" MBIS nipype interface definition
    Based on FAST interface definition

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)
"""

import os, os.path as op
import warnings
import numpy as np
import nibabel as nib
from nipype.interfaces.base import (TraitedSpec, File, InputMultiPath,
                                    OutputMultiPath, Undefined, traits,
                                    isdefined, OutputMultiPath, 
                                    CommandLineInputSpec, CommandLine,
                                    BaseInterface, BaseInterfaceInputSpec,
                                    traits )
from nipype.utils.filemanip import split_filename,fname_presuffix
import postproc as pp
#import csv

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)



class MBISInputSpec( CommandLineInputSpec ):
    in_files = InputMultiPath( File(exists=True), copyfile=False,
                            desc='image, or multi-channel set of images, ' \
                                'to be segmented',
                            argstr='-C %s', position=-1, mandatory=True )

    mask = File(exists=True, desc='binary mask file', argstr='-x %s' )

    mask_auto = traits.Bool( desc='channels are implicitly masked', argstr='-M' )

    out_prefix = File('outpath', desc='base name of output files',
                        argstr='-o %s', genfile=True)  # uses in_file name as basename if none given

    initialization = traits.Enum( 'none','em','km','km+em', argstr='-I %s',desc='Initialization mode' )

    number_classes = traits.Range(low=2, high=10, argstr='-n %d',
                                  desc='number of tissue-type classes', value=3)

    output_steps = traits.Bool(desc='output intermediate steps',
                                   argstr='--output-steps')


    output_biasfield = traits.Bool(desc='output estimated bias field',
                                   argstr='--bias-output')

    output_biascorrected = traits.Bool(desc='output restored image ' \
                                           '(bias-corrected image)',
                                       argstr='--bias-corrected-output')

    output_stats = File( 'outcsvfile', desc='output file containing mixture parameters', argstr='--output-stats %s' )

    probability_maps = traits.Bool(desc='outputs a separate binary image for each ' \
                               'tissue type',
                           argstr='-g' )

    priors = InputMultiPath(File(exist=True), desc='initialize with prior images',
                               argstr='-P %s', minlen=3, maxlen=10)

    no_bias = traits.Bool(desc='do not remove bias field',
                         argstr='--bias-skip' )

    no_normalize = traits.Bool( desc='do not normalize input channels', argstr='-N',
                         value=False )

    em_iters = traits.Range(low=1, high=50, value=3,
                                 desc='number of EM iterations',
                                 argstr='--em-iterations %d')
    mrf_iters = traits.Range(low=1, high=10,
                                 desc='number of MRF iterations',
                                 argstr='--mrf-iterations %d')

    mrf_lambda = traits.Range(low=0.01, high=3.0,
                         desc='MRF lambda parameter (segmentation spatial smoothness)',
                         argstr='-l %.3f')

    manual_init = File(exists=True, desc='Filename containing intensities',
                     argstr='-f %s')
    manual_init_means = File(exists=True, desc='Filename containing intensities',
                     argstr='--init-means %s')

#    no_pve = traits.Bool(desc='turn off PVE (partial volume estimation)',
#                        argstr='--nopve')
 
#    use_priors = traits.Bool(desc='use priors throughout',
#                             argstr='-P')   # must also set -a!,
#                                              # mutually inclusive??
#                                              # No, conditional
#                                              # mandatory... need to
#                                              # figure out how to
#                                              # handle with traits.
#   verbose = traits.Bool(desc='switch on diagnostic messages',
#                         argstr='-v')



class MBISOutputSpec( TraitedSpec ):
    out_classified = File(desc='path/name of binary segmented volume file' \
                            ' one val for each class  _mrf')
    out_parameters = traits.File(desc='csv file with tissue purameters') 
    bias_field = OutputMultiPath(File(desc='Estimated bias field _bias'))
    probability_maps = OutputMultiPath(File(desc='filenames, one for each class, for each ' \
                                'input, mrf_x'))
    restored_image = OutputMultiPath(File(desc='restored images (one for each input image) ' \
                              'named according to the input images _corrected_chXX'))

    normalized_inputs = OutputMultiPath( File( desc='normalized input channels' ) )


class MBIS(CommandLine):
    """ Use MBIS for segmentation and bias correction.

    Examples
    --------
    >>> from nipype.interfaces import mbis
    >>> from nipype.testing import example_data

    Assign options through the ``inputs`` attribute:

    >>> mbisr = mbis.MBIS()
    >>> mbisr.inputs.in_files = example_data('structural.nii')
    >>> out = mbisr.run() #doctest: +SKIP

    """
    _cmd = 'brain_seg'
    input_spec = MBISInputSpec
    output_spec = MBISOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if not isdefined(self.inputs.number_classes):
            nclasses = 3
        else:
            nclasses = self.inputs.number_classes

        outprefix = self._getdefaultprefix() 

        outputs['out_classified'] = '%s_mrf.nii.gz' % outprefix

        if self.inputs.probability_maps:
            outputs['probability_maps'] = []
            for  i in range(1,nclasses+1):
                outputs['probability_maps'].append('%s_mrf_seg%02d.nii.gz' % (outprefix,i) )

        if (not (isdefined(self.inputs.no_bias))) and self.inputs.output_biascorrected:
            outputs['restored_image'] = []
            for val, f in enumerate(self.inputs.in_files):
                 # image numbering is 1-based
                 outputs['restored_image'].append('%s_corrected_ch%02d.nii.gz' % (outprefix,val+1) )

        if (not (isdefined(self.inputs.no_bias))) and self.inputs.output_biasfield:
            outputs['bias_field'] = []
            for val, f in enumerate(self.inputs.in_files):
                # image numbering is 1-based
                outputs['bias_field'].append('%s_bias_ch%02d.nii.gz' % (outprefix,val) )

        if ((not self.inputs.no_normalize) and self.inputs.output_steps ):
            outputs['normalized_inputs' ] = []
            for val, f in enumerate(self.inputs.in_files):
                outputs['normalized_inputs'].append('%s_normin_%0d.nii.gz' % (outprefix,val) )

        if isdefined(self.inputs.output_stats):
            fname= outprefix + '_stats_final' + self.inputs.output_stats
            outputs['out_parameters'] = fname
#            outputs['out_parameters'] = np.loadtxt( fname, delimiter='[],' )
#            with open( self.inputs.output_stats ) as csvfile:
#                dataReader = csv.reader( csvfile )
#                outputs['out_parameters'] = np.array( [ [ row ] for row in dataReader ] )
#		csvfile.close()

        return outputs

    def _getdefaultprefix( self, name='mbis' ):
       if not isdefined(self.inputs.out_prefix):
           return os.path.abspath( os.path.join( os.getcwd(), name ) )
       else:
           return self.inputs.out_prefix

    def _gen_filename(self,name):
        if name == 'out_prefix':
            return self._getdefaultprefix()
        return None
		

    def _gen_fname(self, prefix, suffix=None, ext='.nii.gz', cwd=None):
        """Generate a filename based on the given parameters.

        The filename will take the form: preffix<suffix><ext>.

        Parameters
        ----------
        prefix : str
            Filename to base the new filename on.

        suffix : str
            Suffix to add to the `basename`.  (defaults is '' )

        ext : str
            Desired extension (default is nii.gz)

        Returns
        -------
        fname : str
            New filename based on given parameters.

        """
        if ((prefix == '') or (prefix is None) ):
            prefix = './'
        if suffix is None:
            suffix = ''
        if cwd is None:
            cwd = os.getcwd()

        suffix = ''.join((suffix,ext))
        fname = fname_presuffix(prefix, suffix=suffix, use_ext=False, newpath=cwd )
        return fname


class PVMergeInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiPath( File(exists=True), copyfile=False, desc='image, or multi-channel set of images,' \
                                                                       'used for segmentation', mandatory=True )
    in_maps  = InputMultiPath( File(exists=True), copyfile=False, desc='Resulting tissue probability maps', mandatory=True )
    in_labelling = File( exists=True, desc='Hard labelling resulting from segmentation', mandatory=True)
    parameters = File( exists=True, desc='CSV file containing parameters for all the classes', mandatory=True)
    pure_tissues = traits.Tuple( value=( (0,), (1,), (2,) ), minlen=1, desc='Identifiers of the pure tissue classes' )
    dist = traits.String( value="euclidean", desc="Distance definition to be used" )
    reorder = traits.Bool( value=True, desc='Reorder classes if the classification is not ordered by first contrast means' )

class PVMergeOutputSpec(TraitedSpec):
    out_files = OutputMultiPath( File( desc='filenames, one for each pure tissue according to prefix_msegXX.nii.gz' ) )

class PVMerge(BaseInterface):
    input_spec = PVMergeInputSpec
    output_spec = PVMergeOutputSpec
    _ppmnames = []

    def _run_interface(self, runtime):
        params = pp.loadParameters(self.inputs.parameters)
        path, base, _ = split_filename( self.inputs.in_maps[0] )

        self._ppmnames = pp.fusePV2( self.inputs.in_files,
                               self.inputs.in_maps,
                               params,
                               self.inputs.pure_tissues,
                               self.inputs.dist,
                               self.inputs.reorder,
                               os.path.abspath( os.path.join( os.getcwd(), base ) ) )

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["out_files"] = self._ppmnames
        return outputs

class MAPInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiPath( File(exists=True), copyfile=False, desc='Input tissue probability maps', mandatory=True )
    normalize = traits.Bool( desc='apply normalization to input tpms', value=True )
    prefix = traits.String( desc='prefix path and basename for output', value='' )

class MAPOutputSpec(TraitedSpec):
    out_tpms = OutputMultiPath( File( desc='Normalized tpms' ) )
    out_file  = File( desc='output labelling after MAP' )

class MAP(BaseInterface):
    input_spec = MAPInputSpec
    output_spec = MAPOutputSpec

    def _run_interface(self, runtime):
 	import nibabel as nib
        import numpy as np
        path, base, _ = split_filename( self.inputs.in_files[0] )
        prefix=self.inputs.prefix
        if not isdefined(self.inputs.prefix):
            prefix = os.getcwd() + "/"+ base
        self._out_fname = '%s_map.nii.gz' % prefix
        assert( len(self.inputs.in_files) > 1 )
        tpm_data = np.array( [ nib.load(tpm).get_data() for tpm in self.inputs.in_files ] )
        (seg_file,tpms_norm) = pp.computeMAP( tpm_data, self.inputs.normalize )
        ref = nib.load(self.inputs.in_files[0] )
        nib.save( nib.Nifti1Image( seg_file, ref.get_affine(), ref.get_header() ), self._out_fname )
        if self.inputs.normalize:
            self._tpmnames = [ '%s_tpm%02d.nii.gz' % (prefix,i) for i in range(1,len(self.inputs.in_files)+1) ]
            for tpm,name in zip(tpms_norm,self._tpmnames):
                nib.save( nib.Nifti1Image( tpm, ref.get_affine(), ref.get_header() ), name )
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        if self.inputs.normalize:
	    outputs["out_tpms"] = self._tpmnames
        outputs["out_file"] = self._out_fname
        return outputs
