# Local imports
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
    mask_image = File(exists=True, argstr='--mask-image %s')
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
