"""The ants module provides basic functions for interfacing with ants functions.

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""

from ..base import (TraitedSpec, File, traits, InputMultiPath, OutputMultiPath,
                    isdefined)
from ...utils.filemanip import split_filename
from .base import ANTSCommand, ANTSCommandInputSpec
import os
from nipype.utils.filemanip import copyfile


class AtroposInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, 4, argstr='--image-dimensionality %d', usedefault=True,
                            desc='image dimension (2, 3, or 4)')
    intensity_images = InputMultiPath(File(exists=True), argstr="--intensity-image %s...", madatory=True)
    mask_image = File(exists=True, argstr='--mask-image %s', mandatory=True)
    initialization = traits.Enum('Random', 'Otsu', 'KMeans',
                                 'PriorProbabilityImages', 'PriorLabelImage',
                                 argstr="%s",
                                 requires=['number_of_tissue_classes'],
                                 mandatory=True)
    prior_probability_images = InputMultiPath(File(exists=True))
    number_of_tissue_classes = traits.Int(mandatory=True)
    prior_weighting = traits.Float()
    prior_probability_threshold = traits.Float(requires=['prior_weighting'])
    likelihood_model = traits.Str(argstr="--likelihood-model %s")
    mrf_smoothing_factor = traits.Float(argstr="%s")
    mrf_radius = traits.List(traits.Int(), requires=['mrf_smoothing_factor'])
    icm_use_synchronous_update = traits.Bool(argstr="%s")
    maximum_number_of_icm_terations = traits.Int(requires=['icm_use_synchronous_update'])
    n_iterations = traits.Int(argstr="%s")
    convergence_threshold = traits.Float(requires=['n_iterations'])
    posterior_formulation = traits.Str(argstr="%s")
    use_mixture_model_proportions = traits.Bool(requires=['posterior_formulation'])
    out_classified_image_name = File(argstr="%s", genfile=True,
                                     hash_file=False)
    save_posteriors = traits.Bool()
    output_posteriors_name_template = traits.Str('POSTERIOR_%02d.nii.gz', usedefault=True)


class AtroposOutputSpec(TraitedSpec):
    classified_image = File(exists=True)
    posteriors = OutputMultiPath(File(exist=True))


class Atropos(ANTSCommand):
    """A finite mixture modeling (FMM) segmentation approach with possibilities for
    specifying prior constraints. These prior constraints include the specification
    of a prior label image, prior probability images (one for each class), and/or an
    MRF prior to enforce spatial smoothing of the labels. Similar algorithms include
    FAST and SPM.

    Examples
    --------

    >>> from nipype.interfaces.ants import Atropos
    >>> at = Atropos()
    >>> at.inputs.dimension = 3
    >>> at.inputs.intensity_images = 'structural.nii'
    >>> at.inputs.mask_image = 'mask.nii'
    >>> at.inputs.initialization = 'PriorProbabilityImages'
    >>> at.inputs.prior_probability_images = ['rc1s1.nii', 'rc1s2.nii']
    >>> at.inputs.number_of_tissue_classes = 2
    >>> at.inputs.prior_weighting = 0.8
    >>> at.inputs.prior_probability_threshold = 0.0000001
    >>> at.inputs.likelihood_model = 'Gaussian'
    >>> at.inputs.mrf_smoothing_factor = 0.2
    >>> at.inputs.mrf_radius = [1, 1, 1]
    >>> at.inputs.icm_use_synchronous_update = True
    >>> at.inputs.maximum_number_of_icm_terations = 1
    >>> at.inputs.n_iterations = 5
    >>> at.inputs.convergence_threshold = 0.000001
    >>> at.inputs.posterior_formulation = 'Socrates'
    >>> at.inputs.use_mixture_model_proportions = True
    >>> at.inputs.save_posteriors = True
    >>> at.cmdline
    'Atropos --image-dimensionality 3 --icm [1,1] --initialization PriorProbabilityImages[2,priors/priorProbImages%02d.nii,0.8,1e-07] --intensity-image structural.nii --likelihood-model Gaussian --mask-image mask.nii --mrf [0.2,1x1x1] --convergence [5,1e-06] --output [structural_labeled.nii,POSTERIOR_%02d.nii.gz] --posterior-formulation Socrates[1]'
    """
    input_spec = AtroposInputSpec
    output_spec = AtroposOutputSpec
    _cmd = 'Atropos'

    def _format_arg(self, opt, spec, val):
        if opt == 'initialization':
            retval = "--initialization %s[%d" % (val, self.inputs.number_of_tissue_classes)
            if val == "PriorProbabilityImages":
                _, _, ext = split_filename(self.inputs.prior_probability_images[0])
                retval += ",priors/priorProbImages%02d" + ext + ",%g" % self.inputs.prior_weighting
                if isdefined(self.inputs.prior_probability_threshold):
                    retval += ",%g" % self.inputs.prior_probability_threshold
            return retval + "]"
        if opt == 'mrf_smoothing_factor':
            retval = "--mrf [%g" % val
            if isdefined(self.inputs.mrf_radius):
                retval += ",%s" % 'x'.join([str(s) for s in self.inputs.mrf_radius])
            return retval + "]"
        if opt == "icm_use_synchronous_update":
            retval = "--icm [%d" % val
            if isdefined(self.inputs.maximum_number_of_icm_terations):
                retval += ",%g" % self.inputs.maximum_number_of_icm_terations
            return retval + "]"
        if opt == "n_iterations":
            retval = "--convergence [%d" % val
            if isdefined(self.inputs.convergence_threshold):
                retval += ",%g" % self.inputs.convergence_threshold
            return retval + "]"
        if opt == "posterior_formulation":
            retval = "--posterior-formulation %s" % val
            if isdefined(self.inputs.use_mixture_model_proportions):
                retval += "[%d]" % self.inputs.use_mixture_model_proportions
            return retval
        if opt == "out_classified_image_name":
            retval = "--output [%s" % val
            if isdefined(self.inputs.save_posteriors):
                retval += ",%s" % self.inputs.output_posteriors_name_template
            return retval + "]"
        return super(ANTSCommand, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime):
        if self.inputs.initialization == "PriorProbabilityImages":
            priors_directory = os.path.join(os.getcwd(), "priors")
            if not os.path.exists(priors_directory):
                os.makedirs(priors_directory)
            _, _, ext = split_filename(self.inputs.prior_probability_images[0])
            for i, f in enumerate(self.inputs.prior_probability_images):
                target = os.path.join(priors_directory,
                                         'priorProbImages%02d' % (i + 1) + ext)
                if not (os.path.exists(target) and os.path.realpath(target) == os.path.abspath(f)):
                    copyfile(os.path.abspath(f), os.path.join(priors_directory,
                                         'priorProbImages%02d' % (i + 1) + ext))
        runtime = super(Atropos, self)._run_interface(runtime)
        return runtime

    def _gen_filename(self, name):
        if name == 'out_classified_image_name':
            output = self.inputs.out_classified_image_name
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.intensity_images[0])
                output = name + '_labeled' + ext
            return output
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['classified_image'] = os.path.abspath(self._gen_filename('out_classified_image_name'))
        if isdefined(self.inputs.save_posteriors) and self.inputs.save_posteriors:
            outputs['posteriors'] = []
            for i in range(self.inputs.number_of_tissue_classes):
                outputs['posteriors'].append(os.path.abspath(self.inputs.output_posteriors_name_template % (i + 1)))
        return outputs
