# -*- coding: utf-8 -*-
"""The ants module provides basic functions for interfacing with ants functions.
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import range, str

import os
from ...external.due import BibTeX
from ...utils.filemanip import split_filename, copyfile, which
from ..base import TraitedSpec, File, traits, InputMultiPath, OutputMultiPath, isdefined
from .base import ANTSCommand, ANTSCommandInputSpec


class AtroposInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        4,
        argstr='--image-dimensionality %d',
        usedefault=True,
        desc='image dimension (2, 3, or 4)')
    intensity_images = InputMultiPath(
        File(exists=True), argstr="--intensity-image %s...", mandatory=True)
    mask_image = File(exists=True, argstr='--mask-image %s', mandatory=True)
    initialization = traits.Enum(
        'Random',
        'Otsu',
        'KMeans',
        'PriorProbabilityImages',
        'PriorLabelImage',
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
    maximum_number_of_icm_terations = traits.Int(
        requires=['icm_use_synchronous_update'])
    n_iterations = traits.Int(argstr="%s")
    convergence_threshold = traits.Float(requires=['n_iterations'])
    posterior_formulation = traits.Str(argstr="%s")
    use_random_seed = traits.Bool(
        True,
        argstr='--use-random-seed %d',
        desc='use random seed value over constant',
        usedefault=True)
    use_mixture_model_proportions = traits.Bool(
        requires=['posterior_formulation'])
    out_classified_image_name = File(
        argstr="%s", genfile=True, hash_files=False)
    save_posteriors = traits.Bool()
    output_posteriors_name_template = traits.Str(
        'POSTERIOR_%02d.nii.gz', usedefault=True)


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
    'Atropos --image-dimensionality 3 --icm [1,1] \
--initialization PriorProbabilityImages[2,priors/priorProbImages%02d.nii,0.8,1e-07] --intensity-image structural.nii \
--likelihood-model Gaussian --mask-image mask.nii --mrf [0.2,1x1x1] --convergence [5,1e-06] \
--output [structural_labeled.nii,POSTERIOR_%02d.nii.gz] --posterior-formulation Socrates[1] --use-random-seed 1'

    """
    input_spec = AtroposInputSpec
    output_spec = AtroposOutputSpec
    _cmd = 'Atropos'

    def _format_arg(self, opt, spec, val):
        if opt == 'initialization':
            retval = "--initialization %s[%d" % (
                val, self.inputs.number_of_tissue_classes)
            if val == "PriorProbabilityImages":
                _, _, ext = split_filename(
                    self.inputs.prior_probability_images[0])
                retval += ",priors/priorProbImages%02d" + \
                    ext + ",%g" % self.inputs.prior_weighting
                if isdefined(self.inputs.prior_probability_threshold):
                    retval += ",%g" % self.inputs.prior_probability_threshold
            return retval + "]"
        if opt == 'mrf_smoothing_factor':
            retval = "--mrf [%g" % val
            if isdefined(self.inputs.mrf_radius):
                retval += ",%s" % self._format_xarray(
                    [str(s) for s in self.inputs.mrf_radius])
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
        return super(Atropos, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime, correct_return_codes=[0]):
        if self.inputs.initialization == "PriorProbabilityImages":
            priors_directory = os.path.join(os.getcwd(), "priors")
            if not os.path.exists(priors_directory):
                os.makedirs(priors_directory)
            _, _, ext = split_filename(self.inputs.prior_probability_images[0])
            for i, f in enumerate(self.inputs.prior_probability_images):
                target = os.path.join(priors_directory,
                                      'priorProbImages%02d' % (i + 1) + ext)
                if not (os.path.exists(target)
                        and os.path.realpath(target) == os.path.abspath(f)):
                    copyfile(
                        os.path.abspath(f),
                        os.path.join(priors_directory,
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
        outputs['classified_image'] = os.path.abspath(
            self._gen_filename('out_classified_image_name'))
        if isdefined(
                self.inputs.save_posteriors) and self.inputs.save_posteriors:
            outputs['posteriors'] = []
            for i in range(self.inputs.number_of_tissue_classes):
                outputs['posteriors'].append(
                    os.path.abspath(
                        self.inputs.output_posteriors_name_template % (i + 1)))
        return outputs


class LaplacianThicknessInputSpec(ANTSCommandInputSpec):
    input_wm = File(
        argstr='%s',
        mandatory=True,
        copyfile=True,
        desc='white matter segmentation image',
        position=1)
    input_gm = File(
        argstr='%s',
        mandatory=True,
        copyfile=True,
        desc='gray matter segmentation image',
        position=2)
    output_image = File(
        desc='name of output file',
        argstr='%s',
        position=3,
        genfile=True,
        hash_files=False)
    smooth_param = traits.Float(argstr='smoothparam=%d', desc='', position=4)
    prior_thickness = traits.Float(
        argstr='priorthickval=%d', desc='', position=5)
    dT = traits.Float(argstr='dT=%d', desc='', position=6)
    sulcus_prior = traits.Bool(argstr='use-sulcus-prior', desc='', position=7)
    opt_tolerance = traits.Float(
        argstr='optional-laplacian-tolerance=%d', desc='', position=8)


class LaplacianThicknessOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='Cortical thickness')


class LaplacianThickness(ANTSCommand):
    """Calculates the cortical thickness from an anatomical image

    Examples
    --------

    >>> from nipype.interfaces.ants import LaplacianThickness
    >>> cort_thick = LaplacianThickness()
    >>> cort_thick.inputs.input_wm = 'white_matter.nii.gz'
    >>> cort_thick.inputs.input_gm = 'gray_matter.nii.gz'
    >>> cort_thick.inputs.output_image = 'output_thickness.nii.gz'
    >>> cort_thick.cmdline
    'LaplacianThickness white_matter.nii.gz gray_matter.nii.gz output_thickness.nii.gz'

    """

    _cmd = 'LaplacianThickness'
    input_spec = LaplacianThicknessInputSpec
    output_spec = LaplacianThicknessOutputSpec

    def _gen_filename(self, name):
        if name == 'output_image':
            output = self.inputs.output_image
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.input_wm)
                output = name + '_thickness' + ext
            return output
        return None

    def _list_outputs(self):
        outputs = self._outputs().get()
        _, name, ext = split_filename(os.path.abspath(self.inputs.input_wm))
        outputs['output_image'] = os.path.join(os.getcwd(), ''.join(
            (name, self.inputs.output_image, ext)))
        return outputs


class N4BiasFieldCorrectionInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        4,
        argstr='-d %d',
        usedefault=True,
        desc='image dimension (2, 3 or 4)')
    input_image = File(
        argstr='--input-image %s',
        mandatory=True,
        desc=('input for bias correction. Negative values or values close to '
            'zero should be processed prior to correction'))
    mask_image = File(
        argstr='--mask-image %s',
        desc=('image to specify region to perform final bias correction in'))
    weight_image = File(
        argstr='--weight-image %s',
        desc=('image for relative weighting (e.g. probability map of the white '
            'matter) of voxels during the B-spline fitting. '))
    output_image = traits.Str(
        argstr='--output %s',
        desc='output file name',
        genfile=True,
        hash_files=False)
    bspline_fitting_distance = traits.Float(argstr="--bspline-fitting %s")
    bspline_order = traits.Int(requires=['bspline_fitting_distance'])
    shrink_factor = traits.Int(argstr="--shrink-factor %d")
    n_iterations = traits.List(traits.Int(), argstr="--convergence %s")
    convergence_threshold = traits.Float(requires=['n_iterations'])
    save_bias = traits.Bool(
        False,
        mandatory=True,
        usedefault=True,
        desc=('True if the estimated bias should be saved to file.'),
        xor=['bias_image'])
    bias_image = File(
        desc='Filename for the estimated bias.', hash_files=False)
    copy_header = traits.Bool(
        False,
        mandatory=True,
        usedefault=True,
        desc='copy headers of the original image into the '
        'output (corrected) file')


class N4BiasFieldCorrectionOutputSpec(TraitedSpec):
    output_image = File(exists=True, desc='Warped image')
    bias_image = File(exists=True, desc='Estimated bias')


class N4BiasFieldCorrection(ANTSCommand):
    """N4 is a variant of the popular N3 (nonparameteric nonuniform normalization)
    retrospective bias correction algorithm. Based on the assumption that the
    corruption of the low frequency bias field can be modeled as a convolution of
    the intensity histogram by a Gaussian, the basic algorithmic protocol is to
    iterate between deconvolving the intensity histogram by a Gaussian, remapping
    the intensities, and then spatially smoothing this result by a B-spline modeling
    of the bias field itself. The modifications from and improvements obtained over
    the original N3 algorithm are described in [Tustison2010]_.

    .. [Tustison2010] N. Tustison et al.,
      N4ITK: Improved N3 Bias Correction, IEEE Transactions on Medical Imaging,
      29(6):1310-1320, June 2010.

    Examples
    --------

    >>> import copy
    >>> from nipype.interfaces.ants import N4BiasFieldCorrection
    >>> n4 = N4BiasFieldCorrection()
    >>> n4.inputs.dimension = 3
    >>> n4.inputs.input_image = 'structural.nii'
    >>> n4.inputs.bspline_fitting_distance = 300
    >>> n4.inputs.shrink_factor = 3
    >>> n4.inputs.n_iterations = [50,50,30,20]
    >>> n4.cmdline
    'N4BiasFieldCorrection --bspline-fitting [ 300 ] \
-d 3 --input-image structural.nii \
--convergence [ 50x50x30x20 ] --output structural_corrected.nii \
--shrink-factor 3'

    >>> n4_2 = copy.deepcopy(n4)
    >>> n4_2.inputs.convergence_threshold = 1e-6
    >>> n4_2.cmdline
    'N4BiasFieldCorrection --bspline-fitting [ 300 ] \
-d 3 --input-image structural.nii \
--convergence [ 50x50x30x20, 1e-06 ] --output structural_corrected.nii \
--shrink-factor 3'

    >>> n4_3 = copy.deepcopy(n4_2)
    >>> n4_3.inputs.bspline_order = 5
    >>> n4_3.cmdline
    'N4BiasFieldCorrection --bspline-fitting [ 300, 5 ] \
-d 3 --input-image structural.nii \
--convergence [ 50x50x30x20, 1e-06 ] --output structural_corrected.nii \
--shrink-factor 3'

    >>> n4_4 = N4BiasFieldCorrection()
    >>> n4_4.inputs.input_image = 'structural.nii'
    >>> n4_4.inputs.save_bias = True
    >>> n4_4.inputs.dimension = 3
    >>> n4_4.cmdline
    'N4BiasFieldCorrection -d 3 --input-image structural.nii \
--output [ structural_corrected.nii, structural_bias.nii ]'
    """

    _cmd = 'N4BiasFieldCorrection'
    input_spec = N4BiasFieldCorrectionInputSpec
    output_spec = N4BiasFieldCorrectionOutputSpec

    def _gen_filename(self, name):
        if name == 'output_image':
            output = self.inputs.output_image
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.input_image)
                output = name + '_corrected' + ext
            return output

        if name == 'bias_image':
            output = self.inputs.bias_image
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.input_image)
                output = name + '_bias' + ext
            return output
        return None

    def _format_arg(self, name, trait_spec, value):
        if ((name == 'output_image') and
            (self.inputs.save_bias or isdefined(self.inputs.bias_image))):
            bias_image = self._gen_filename('bias_image')
            output = self._gen_filename('output_image')
            newval = '[ %s, %s ]' % (output, bias_image)
            return trait_spec.argstr % newval

        if name == 'bspline_fitting_distance':
            if isdefined(self.inputs.bspline_order):
                newval = '[ %g, %d ]' % (value, self.inputs.bspline_order)
            else:
                newval = '[ %g ]' % value
            return trait_spec.argstr % newval

        if name == 'n_iterations':
            if isdefined(self.inputs.convergence_threshold):
                newval = '[ %s, %g ]' % (
                    self._format_xarray([str(elt) for elt in value]),
                    self.inputs.convergence_threshold)
            else:
                newval = '[ %s ]' % self._format_xarray(
                    [str(elt) for elt in value])
            return trait_spec.argstr % newval

        return super(N4BiasFieldCorrection, self)._format_arg(
            name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []
        skip += ['save_bias', 'bias_image']
        return super(N4BiasFieldCorrection, self)._parse_inputs(skip=skip)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_image'] = os.path.abspath(
            self._gen_filename('output_image'))

        if self.inputs.save_bias or isdefined(self.inputs.bias_image):
            outputs['bias_image'] = os.path.abspath(
                self._gen_filename('bias_image'))
        return outputs

    def _run_interface(self, runtime, correct_return_codes=(0, )):
        runtime = super(N4BiasFieldCorrection, self)._run_interface(
            runtime, correct_return_codes)

        if self.inputs.copy_header and runtime.returncode in correct_return_codes:
            self._copy_header(self._gen_filename('output_image'))
            if self.inputs.save_bias or isdefined(self.inputs.bias_image):
                self._copy_header(self._gen_filename('bias_image'))

        return runtime

    def _copy_header(self, fname):
        """Copy header from input image to an output image"""
        import nibabel as nb
        in_img = nb.load(self.inputs.input_image)
        out_img = nb.load(fname, mmap=False)
        new_img = out_img.__class__(out_img.get_data(), in_img.affine,
                                    in_img.header)
        new_img.set_data_dtype(out_img.get_data_dtype())
        new_img.to_filename(fname)


class CorticalThicknessInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, argstr='-d %d', usedefault=True, desc='image dimension (2 or 3)')
    anatomical_image = File(
        exists=True,
        argstr='-a %s',
        desc=('Structural *intensity* image, typically T1.'
              ' If more than one anatomical image is specified,'
              ' subsequently specified images are used during the'
              ' segmentation process. However, only the first'
              ' image is used in the registration of priors.'
              ' Our suggestion would be to specify the T1'
              ' as the first image.'),
        mandatory=True)
    brain_template = File(
        exists=True,
        argstr='-e %s',
        desc=('Anatomical *intensity* template (possibly created using a'
              ' population data set with buildtemplateparallel.sh in ANTs).'
              ' This template is  *not* skull-stripped.'),
        mandatory=True)
    brain_probability_mask = File(
        exists=True,
        argstr='-m %s',
        desc='brain probability mask in template space',
        copyfile=False,
        mandatory=True)
    segmentation_priors = InputMultiPath(
        File(exists=True), argstr='-p %s', mandatory=True)
    out_prefix = traits.Str(
        'antsCT_',
        argstr='-o %s',
        usedefault=True,
        desc=('Prefix that is prepended to all output'
              ' files (default = antsCT_)'))
    image_suffix = traits.Str(
        'nii.gz',
        desc=('any of standard ITK formats,'
              ' nii.gz is default'),
        argstr='-s %s',
        usedefault=True)
    t1_registration_template = File(
        exists=True,
        desc=('Anatomical *intensity* template'
              ' (assumed to be skull-stripped). A common'
              ' case would be where this would be the same'
              ' template as specified in the -e option which'
              ' is not skull stripped.'),
        argstr='-t %s',
        mandatory=True)
    extraction_registration_mask = File(
        exists=True,
        argstr='-f %s',
        desc=('Mask (defined in the template space) used during'
              ' registration for brain extraction.'))
    keep_temporary_files = traits.Int(
        argstr='-k %d',
        desc='Keep brain extraction/segmentation warps, etc (default = 0).')
    max_iterations = traits.Int(
        argstr='-i %d',
        desc=('ANTS registration max iterations (default = 100x100x70x20)'))
    prior_segmentation_weight = traits.Float(
        argstr='-w %f',
        desc=('Atropos spatial prior *probability* weight for'
              ' the segmentation'))
    segmentation_iterations = traits.Int(
        argstr='-n %d',
        desc=('N4 -> Atropos -> N4 iterations during segmentation'
              ' (default = 3)'))
    posterior_formulation = traits.Str(
        argstr='-b %s',
        desc=('Atropos posterior formulation and whether or not'
              ' to use mixture model proportions.'
              ''' e.g 'Socrates[1]' (default) or 'Aristotle[1]'.'''
              ' Choose the latter if you'
              ' want use the distance priors (see also the -l option'
              ' for label propagation control).'))
    use_floatingpoint_precision = traits.Enum(
        0,
        1,
        argstr='-j %d',
        desc=('Use floating point precision in registrations (default = 0)'))
    use_random_seeding = traits.Enum(
        0,
        1,
        argstr='-u %d',
        desc=('Use random number generated from system clock in Atropos'
              ' (default = 1)'))
    b_spline_smoothing = traits.Bool(
        argstr='-v',
        desc=('Use B-spline SyN for registrations and B-spline'
              ' exponential mapping in DiReCT.'))
    cortical_label_image = File(
        exists=True, desc='Cortical ROI labels to use as a prior for ATITH.')
    label_propagation = traits.Str(
        argstr='-l %s',
        desc=
        ('Incorporate a distance prior one the posterior formulation.  Should be'
         ''' of the form 'label[lambda,boundaryProbability]' where label'''
         ' is a value of 1,2,3,... denoting label ID.  The label'
         ' probability for anything outside the current label'
         ' = boundaryProbability * exp( -lambda * distanceFromBoundary )'
         ' Intuitively, smaller lambda values will increase the spatial capture'
         ' range of the distance prior.  To apply to all label values, simply omit'
         ' specifying the label, i.e. -l [lambda,boundaryProbability].'))
    quick_registration = traits.Bool(
        argstr='-q 1',
        desc=
        ('If = 1, use antsRegistrationSyNQuick.sh as the basis for registration'
         ' during brain extraction, brain segmentation, and'
         ' (optional) normalization to a template.'
         ' Otherwise use antsRegistrationSyN.sh (default = 0).'))
    debug = traits.Bool(
        argstr='-z 1',
        desc=(
            'If > 0, runs a faster version of the script.'
            ' Only for testing. Implies -u 0.'
            ' Requires single thread computation for complete reproducibility.'
        ))


class CorticalThicknessOutputSpec(TraitedSpec):
    BrainExtractionMask = File(exists=True, desc='brain extraction mask')
    BrainSegmentation = File(exists=True, desc='brain segmentaion image')
    BrainSegmentationN4 = File(exists=True, desc='N4 corrected image')
    BrainSegmentationPosteriors = OutputMultiPath(
        File(exists=True), desc='Posterior probability images')
    CorticalThickness = File(exists=True, desc='cortical thickness file')
    TemplateToSubject1GenericAffine = File(
        exists=True, desc='Template to subject affine')
    TemplateToSubject0Warp = File(exists=True, desc='Template to subject warp')
    SubjectToTemplate1Warp = File(
        exists=True, desc='Template to subject inverse warp')
    SubjectToTemplate0GenericAffine = File(
        exists=True, desc='Template to subject inverse affine')
    SubjectToTemplateLogJacobian = File(
        exists=True, desc='Template to subject log jacobian')
    CorticalThicknessNormedToTemplate = File(
        exists=True, desc='Normalized cortical thickness')
    BrainVolumes = File(exists=True, desc='Brain volumes as text')


class CorticalThickness(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants.segmentation import CorticalThickness
    >>> corticalthickness = CorticalThickness()
    >>> corticalthickness.inputs.dimension = 3
    >>> corticalthickness.inputs.anatomical_image ='T1.nii.gz'
    >>> corticalthickness.inputs.brain_template = 'study_template.nii.gz'
    >>> corticalthickness.inputs.brain_probability_mask ='ProbabilityMaskOfStudyTemplate.nii.gz'
    >>> corticalthickness.inputs.segmentation_priors = ['BrainSegmentationPrior01.nii.gz',
    ...                                                 'BrainSegmentationPrior02.nii.gz',
    ...                                                 'BrainSegmentationPrior03.nii.gz',
    ...                                                 'BrainSegmentationPrior04.nii.gz']
    >>> corticalthickness.inputs.t1_registration_template = 'brain_study_template.nii.gz'
    >>> corticalthickness.cmdline
    'antsCorticalThickness.sh -a T1.nii.gz -m ProbabilityMaskOfStudyTemplate.nii.gz -e study_template.nii.gz -d 3 \
-s nii.gz -o antsCT_ -p nipype_priors/BrainSegmentationPrior%02d.nii.gz -t brain_study_template.nii.gz'

    """

    input_spec = CorticalThicknessInputSpec
    output_spec = CorticalThicknessOutputSpec
    _cmd = 'antsCorticalThickness.sh'

    def _format_arg(self, opt, spec, val):
        if opt == 'anatomical_image':
            retval = '-a %s' % val
            return retval
        if opt == 'brain_template':
            retval = '-e %s' % val
            return retval
        if opt == 'brain_probability_mask':
            retval = '-m %s' % val
            return retval
        if opt == 'out_prefix':
            retval = '-o %s' % val
            return retval
        if opt == 't1_registration_template':
            retval = '-t %s' % val
            return retval
        if opt == 'segmentation_priors':
            _, _, ext = split_filename(self.inputs.segmentation_priors[0])
            retval = "-p nipype_priors/BrainSegmentationPrior%02d" + ext
            return retval
        return super(CorticalThickness, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime, correct_return_codes=[0]):
        priors_directory = os.path.join(os.getcwd(), "nipype_priors")
        if not os.path.exists(priors_directory):
            os.makedirs(priors_directory)
        _, _, ext = split_filename(self.inputs.segmentation_priors[0])
        for i, f in enumerate(self.inputs.segmentation_priors):
            target = os.path.join(priors_directory,
                                  'BrainSegmentationPrior%02d' % (i + 1) + ext)
            if not (os.path.exists(target)
                    and os.path.realpath(target) == os.path.abspath(f)):
                copyfile(os.path.abspath(f), target)
        runtime = super(CorticalThickness, self)._run_interface(runtime)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['BrainExtractionMask'] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + 'BrainExtractionMask.' +
            self.inputs.image_suffix)
        outputs['BrainSegmentation'] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + 'BrainSegmentation.' +
            self.inputs.image_suffix)
        outputs['BrainSegmentationN4'] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + 'BrainSegmentation0N4.' +
            self.inputs.image_suffix)
        posteriors = []
        for i in range(len(self.inputs.segmentation_priors)):
            posteriors.append(
                os.path.join(os.getcwd(), self.inputs.out_prefix +
                             'BrainSegmentationPosteriors%02d.' %
                             (i + 1) + self.inputs.image_suffix))
        outputs['BrainSegmentationPosteriors'] = posteriors
        outputs['CorticalThickness'] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + 'CorticalThickness.' +
            self.inputs.image_suffix)
        outputs['TemplateToSubject1GenericAffine'] = os.path.join(
            os.getcwd(),
            self.inputs.out_prefix + 'TemplateToSubject1GenericAffine.mat')
        outputs['TemplateToSubject0Warp'] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + 'TemplateToSubject0Warp.' +
            self.inputs.image_suffix)
        outputs['SubjectToTemplate1Warp'] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + 'SubjectToTemplate1Warp.' +
            self.inputs.image_suffix)
        outputs['SubjectToTemplate0GenericAffine'] = os.path.join(
            os.getcwd(),
            self.inputs.out_prefix + 'SubjectToTemplate0GenericAffine.mat')
        outputs['SubjectToTemplateLogJacobian'] = os.path.join(
            os.getcwd(), self.inputs.out_prefix +
            'SubjectToTemplateLogJacobian.' + self.inputs.image_suffix)
        outputs['CorticalThicknessNormedToTemplate'] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + 'CorticalThickness.' +
            self.inputs.image_suffix)
        outputs['BrainVolumes'] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + 'brainvols.csv')
        return outputs


class BrainExtractionInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3, 2, argstr='-d %d', usedefault=True, desc='image dimension (2 or 3)')
    anatomical_image = File(
        exists=True,
        argstr='-a %s',
        desc=('Structural image, typically T1.  If more than one'
              ' anatomical image is specified, subsequently specified'
              ' images are used during the segmentation process.  However,'
              ' only the first image is used in the registration of priors.'
              ' Our suggestion would be to specify the T1 as the first image.'
              ' Anatomical template created using e.g. LPBA40 data set with'
              ' buildtemplateparallel.sh in ANTs.'),
        mandatory=True)
    brain_template = File(
        exists=True,
        argstr='-e %s',
        desc=('Anatomical template created using e.g. LPBA40 data set with'
              ' buildtemplateparallel.sh in ANTs.'),
        mandatory=True)
    brain_probability_mask = File(
        exists=True,
        argstr='-m %s',
        desc=('Brain probability mask created using e.g. LPBA40 data set which'
              ' have brain masks defined, and warped to anatomical template and'
              ' averaged resulting in a probability image.'),
        copyfile=False,
        mandatory=True)
    out_prefix = traits.Str(
        'highres001_',
        argstr='-o %s',
        usedefault=True,
        desc=('Prefix that is prepended to all output'
              ' files (default = highress001_)'))

    extraction_registration_mask = File(
        exists=True,
        argstr='-f %s',
        desc=('Mask (defined in the template space) used during'
              ' registration for brain extraction.'
              ' To limit the metric computation to a specific region.'))
    image_suffix = traits.Str(
        'nii.gz',
        desc=('any of standard ITK formats,'
              ' nii.gz is default'),
        argstr='-s %s',
        usedefault=True)
    use_random_seeding = traits.Enum(
        0,
        1,
        argstr='-u %d',
        desc=('Use random number generated from system clock in Atropos'
              ' (default = 1)'))
    keep_temporary_files = traits.Int(
        argstr='-k %d',
        desc='Keep brain extraction/segmentation warps, etc (default = 0).')
    use_floatingpoint_precision = traits.Enum(
        0,
        1,
        argstr='-q %d',
        desc=('Use floating point precision in registrations (default = 0)'))
    debug = traits.Bool(
        argstr='-z 1',
        desc=(
            'If > 0, runs a faster version of the script.'
            ' Only for testing. Implies -u 0.'
            ' Requires single thread computation for complete reproducibility.'
        ))


class BrainExtractionOutputSpec(TraitedSpec):
    BrainExtractionMask = File(exists=True, desc='brain extraction mask')
    BrainExtractionBrain = File(exists=True, desc='brain extraction image')
    BrainExtractionCSF = File(
        exists=True, desc='segmentation mask with only CSF')
    BrainExtractionGM = File(
        exists=True, desc='segmentation mask with only grey matter')
    BrainExtractionInitialAffine = File(exists=True, desc='')
    BrainExtractionInitialAffineFixed = File(exists=True, desc='')
    BrainExtractionInitialAffineMoving = File(exists=True, desc='')
    BrainExtractionLaplacian = File(exists=True, desc='')
    BrainExtractionPrior0GenericAffine = File(exists=True, desc='')
    BrainExtractionPrior1InverseWarp = File(exists=True, desc='')
    BrainExtractionPrior1Warp = File(exists=True, desc='')
    BrainExtractionPriorWarped = File(exists=True, desc='')
    BrainExtractionSegmentation = File(
        exists=True, desc='segmentation mask with CSF, GM, and WM')
    BrainExtractionTemplateLaplacian = File(exists=True, desc='')
    BrainExtractionTmp = File(exists=True, desc='')
    BrainExtractionWM = File(
        exists=True, desc='segmenration mask with only white matter')
    N4Corrected0 = File(exists=True, desc='N4 bias field corrected image')
    N4Truncated0 = File(exists=True, desc='')


class BrainExtraction(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants.segmentation import BrainExtraction
    >>> brainextraction = BrainExtraction()
    >>> brainextraction.inputs.dimension = 3
    >>> brainextraction.inputs.anatomical_image ='T1.nii.gz'
    >>> brainextraction.inputs.brain_template = 'study_template.nii.gz'
    >>> brainextraction.inputs.brain_probability_mask ='ProbabilityMaskOfStudyTemplate.nii.gz'
    >>> brainextraction.cmdline
    'antsBrainExtraction.sh -a T1.nii.gz -m ProbabilityMaskOfStudyTemplate.nii.gz -e study_template.nii.gz -d 3 \
-s nii.gz -o highres001_'
    """
    input_spec = BrainExtractionInputSpec
    output_spec = BrainExtractionOutputSpec
    _cmd = 'antsBrainExtraction.sh'

    def _run_interface(self, runtime, correct_return_codes=(0, )):
        # antsBrainExtraction.sh requires ANTSPATH to be defined
        out_environ = self._get_environ()
        ants_path = out_environ.get('ANTSPATH', None) or os.getenv(
            'ANTSPATH', None)
        if ants_path is None:
            # Check for antsRegistration, which is under bin/ (the $ANTSPATH) instead of
            # checking for antsBrainExtraction.sh which is under script/
            cmd_path = which('antsRegistration', env=runtime.environ)
            if not cmd_path:
                raise RuntimeError(
                    'The environment variable $ANTSPATH is not defined in host "%s", '
                    'and Nipype could not determine it automatically.' %
                    runtime.hostname)
            ants_path = os.path.dirname(cmd_path)

        self.inputs.environ.update({'ANTSPATH': ants_path})
        runtime.environ.update({'ANTSPATH': ants_path})
        runtime = super(BrainExtraction, self)._run_interface(runtime)

        # Still, double-check if it didn't found N4
        if 'we cant find' in runtime.stdout:
            for line in runtime.stdout.split('\n'):
                if line.strip().startswith('we cant find'):
                    tool = line.strip().replace('we cant find the',
                                                '').split(' ')[0]
                    break

            errmsg = (
                'antsBrainExtraction.sh requires "%s" to be found in $ANTSPATH '
                '($ANTSPATH="%s").') % (tool, ants_path)
            if runtime.stderr is None:
                runtime.stderr = errmsg
            else:
                runtime.stderr += '\n' + errmsg
            runtime.returncode = 1
            self.raise_exception(runtime)

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['BrainExtractionMask'] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + 'BrainExtractionMask.' +
            self.inputs.image_suffix)
        outputs['BrainExtractionBrain'] = os.path.join(
            os.getcwd(), self.inputs.out_prefix + 'BrainExtractionBrain.' +
            self.inputs.image_suffix)
        if isdefined(self.inputs.keep_temporary_files
                     ) and self.inputs.keep_temporary_files != 0:
            outputs['BrainExtractionCSF'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix + 'BrainExtractionCSF.' +
                self.inputs.image_suffix)
            outputs['BrainExtractionGM'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix + 'BrainExtractionGM.' +
                self.inputs.image_suffix)
            outputs['BrainExtractionInitialAffine'] = os.path.join(
                os.getcwd(),
                self.inputs.out_prefix + 'BrainExtractionInitialAffine.mat')
            outputs['BrainExtractionInitialAffineFixed'] = os.path.join(
                os.getcwd(),
                self.inputs.out_prefix + 'BrainExtractionInitialAffineFixed.' +
                self.inputs.image_suffix)
            outputs['BrainExtractionInitialAffineMoving'] = os.path.join(
                os.getcwd(),
                self.inputs.out_prefix + 'BrainExtractionInitialAffineMoving.'
                + self.inputs.image_suffix)
            outputs['BrainExtractionLaplacian'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix +
                'BrainExtractionLaplacian.' + self.inputs.image_suffix)
            outputs['BrainExtractionPrior0GenericAffine'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix +
                'BrainExtractionPrior0GenericAffine.mat')
            outputs['BrainExtractionPrior1InverseWarp'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix +
                'BrainExtractionPrior1InverseWarp.' + self.inputs.image_suffix)
            outputs['BrainExtractionPrior1Warp'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix +
                'BrainExtractionPrior1Warp.' + self.inputs.image_suffix)
            outputs['BrainExtractionPriorWarped'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix +
                'BrainExtractionPriorWarped.' + self.inputs.image_suffix)
            outputs['BrainExtractionSegmentation'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix +
                'BrainExtractionSegmentation.' + self.inputs.image_suffix)
            outputs['BrainExtractionTemplateLaplacian'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix +
                'BrainExtractionTemplateLaplacian.' + self.inputs.image_suffix)
            outputs['BrainExtractionTmp'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix + 'BrainExtractionTmp.' +
                self.inputs.image_suffix)
            outputs['BrainExtractionWM'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix + 'BrainExtractionWM.' +
                self.inputs.image_suffix)
            outputs['N4Corrected0'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix + 'N4Corrected0.' +
                self.inputs.image_suffix)
            outputs['N4Truncated0'] = os.path.join(
                os.getcwd(), self.inputs.out_prefix + 'N4Truncated0.' +
                self.inputs.image_suffix)

        return outputs


class JointFusionInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        4,
        argstr='%d',
        position=0,
        usedefault=True,
        mandatory=True,
        desc='image dimension (2, 3, or 4)')
    modalities = traits.Int(
        argstr='%d',
        position=1,
        mandatory=True,
        desc='Number of modalities or features')
    warped_intensity_images = InputMultiPath(
        File(exists=True),
        argstr="-g %s...",
        mandatory=True,
        desc='Warped atlas images')
    target_image = InputMultiPath(
        File(exists=True),
        argstr='-tg %s...',
        mandatory=True,
        desc='Target image(s)')
    warped_label_images = InputMultiPath(
        File(exists=True),
        argstr="-l %s...",
        mandatory=True,
        desc='Warped atlas segmentations')
    method = traits.Str(
        default='Joint',
        argstr='-m %s',
        usedefault=True,
        desc=('Select voting method. Options: Joint (Joint'
              ' Label Fusion). May be followed by optional'
              ' parameters in brackets, e.g., -m Joint[0.1,2]'))
    alpha = traits.Float(
        default=0.1,
        usedefault=True,
        requires=['method'],
        desc=('Regularization term added to matrix Mx for inverse'))
    beta = traits.Int(
        default=2,
        usedefault=True,
        requires=['method'],
        desc=('Exponent for mapping intensity difference to joint error'))
    output_label_image = File(
        argstr='%s',
        mandatory=True,
        position=-1,
        name_template='%s',
        output_name='output_label_image',
        desc='Output fusion label map image')
    patch_radius = traits.ListInt(
        minlen=3,
        maxlen=3,
        argstr='-rp %s',
        desc=('Patch radius for similarity measures, '
              'scalar or vector. Default: 2x2x2'))
    search_radius = traits.ListInt(
        minlen=3,
        maxlen=3,
        argstr='-rs %s',
        desc='Local search radius. Default: 3x3x3')
    exclusion_region = File(
        exists=True,
        argstr='-x %s',
        desc=('Specify an exclusion region for the given label.'))
    atlas_group_id = traits.ListInt(
        argstr='-gp %d...', desc='Assign a group ID for each atlas')
    atlas_group_weights = traits.ListInt(
        argstr='-gpw %d...',
        desc=('Assign the voting weights to each atlas group'))


class JointFusionOutputSpec(TraitedSpec):
    output_label_image = File(exists=True)
    # TODO: optional outputs - output_posteriors, output_voting_weights


class JointFusion(ANTSCommand):
    """
    Examples
    --------

    >>> from nipype.interfaces.ants import JointFusion
    >>> at = JointFusion()
    >>> at.inputs.dimension = 3
    >>> at.inputs.modalities = 1
    >>> at.inputs.method = 'Joint[0.1,2]'
    >>> at.inputs.output_label_image ='fusion_labelimage_output.nii'
    >>> at.inputs.warped_intensity_images = ['im1.nii',
    ...                                      'im2.nii',
    ...                                      'im3.nii']
    >>> at.inputs.warped_label_images = ['segmentation0.nii.gz',
    ...                                  'segmentation1.nii.gz',
    ...                                  'segmentation1.nii.gz']
    >>> at.inputs.target_image = 'T1.nii'
    >>> at.cmdline
    'jointfusion 3 1 -m Joint[0.1,2] -tg T1.nii -g im1.nii -g im2.nii -g im3.nii -l segmentation0.nii.gz \
-l segmentation1.nii.gz -l segmentation1.nii.gz fusion_labelimage_output.nii'

    >>> at.inputs.method = 'Joint'
    >>> at.inputs.alpha = 0.5
    >>> at.inputs.beta = 1
    >>> at.inputs.patch_radius = [3,2,1]
    >>> at.inputs.search_radius = [1,2,3]
    >>> at.cmdline
    'jointfusion 3 1 -m Joint[0.5,1] -rp 3x2x1 -rs 1x2x3 -tg T1.nii -g im1.nii -g im2.nii -g im3.nii \
-l segmentation0.nii.gz -l segmentation1.nii.gz -l segmentation1.nii.gz fusion_labelimage_output.nii'
    """
    input_spec = JointFusionInputSpec
    output_spec = JointFusionOutputSpec
    _cmd = 'jointfusion'

    def _format_arg(self, opt, spec, val):
        if opt == 'method':
            if '[' in val:
                retval = '-m {0}'.format(val)
            else:
                retval = '-m {0}[{1},{2}]'.format(
                    self.inputs.method, self.inputs.alpha, self.inputs.beta)
        elif opt == 'patch_radius':
            retval = '-rp {0}'.format(self._format_xarray(val))
        elif opt == 'search_radius':
            retval = '-rs {0}'.format(self._format_xarray(val))
        else:
            if opt == 'warped_intensity_images':
                assert len(val) == self.inputs.modalities * len(self.inputs.warped_label_images), \
                    "Number of intensity images and label maps must be the same {0}!={1}".format(
                    len(val), len(self.inputs.warped_label_images))
            return super(JointFusion, self)._format_arg(opt, spec, val)
        return retval

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_label_image'] = os.path.abspath(
            self.inputs.output_label_image)
        return outputs


class DenoiseImageInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        2,
        3,
        4,
        argstr='-d %d',
        desc='This option forces the image to be treated '
        'as a specified-dimensional image. If not '
        'specified, the program tries to infer the '
        'dimensionality from the input image.')
    input_image = File(
        exists=True,
        argstr="-i %s",
        mandatory=True,
        desc='A scalar image is expected as input for noise correction.')
    noise_model = traits.Enum(
        'Gaussian',
        'Rician',
        argstr='-n %s',
        usedefault=True,
        desc=('Employ a Rician or Gaussian noise model.'))
    shrink_factor = traits.Int(
        default_value=1,
        usedefault=True,
        argstr='-s %s',
        desc=('Running noise correction on large images can'
              ' be time consuming. To lessen computation time,'
              ' the input image can be resampled. The shrink'
              ' factor, specified as a single integer, describes'
              ' this resampling. Shrink factor = 1 is the default.'))
    output_image = File(
        argstr="-o %s",
        name_source=['input_image'],
        hash_files=False,
        keep_extension=True,
        name_template='%s_noise_corrected',
        desc='The output consists of the noise corrected'
             ' version of the input image.')
    save_noise = traits.Bool(
        False,
        mandatory=True,
        usedefault=True,
        desc=('True if the estimated noise should be saved to file.'),
        xor=['noise_image'])
    noise_image = File(
        name_source=['input_image'],
        hash_files=False,
        keep_extension=True,
        name_template='%s_noise',
        desc='Filename for the estimated noise.')
    verbose = traits.Bool(False, argstr="-v", desc=('Verbose output.'))


class DenoiseImageOutputSpec(TraitedSpec):
    output_image = File(exists=True)
    noise_image = File()


class DenoiseImage(ANTSCommand):
    """
    Examples
    --------
    >>> import copy
    >>> from nipype.interfaces.ants import DenoiseImage
    >>> denoise = DenoiseImage()
    >>> denoise.inputs.dimension = 3
    >>> denoise.inputs.input_image = 'im1.nii'
    >>> denoise.cmdline
    'DenoiseImage -d 3 -i im1.nii -n Gaussian -o im1_noise_corrected.nii -s 1'

    >>> denoise_2 = copy.deepcopy(denoise)
    >>> denoise_2.inputs.output_image = 'output_corrected_image.nii.gz'
    >>> denoise_2.inputs.noise_model = 'Rician'
    >>> denoise_2.inputs.shrink_factor = 2
    >>> denoise_2.cmdline
    'DenoiseImage -d 3 -i im1.nii -n Rician -o output_corrected_image.nii.gz -s 2'

    >>> denoise_3 = DenoiseImage()
    >>> denoise_3.inputs.input_image = 'im1.nii'
    >>> denoise_3.inputs.save_noise = True
    >>> denoise_3.cmdline
    'DenoiseImage -i im1.nii -n Gaussian -o [ im1_noise_corrected.nii, im1_noise.nii ] -s 1'
    """
    input_spec = DenoiseImageInputSpec
    output_spec = DenoiseImageOutputSpec
    _cmd = 'DenoiseImage'

    def _format_arg(self, name, trait_spec, value):
        if ((name == 'output_image') and
            (self.inputs.save_noise or isdefined(self.inputs.noise_image))):
            newval = '[ %s, %s ]' % (
                self._filename_from_source('output_image'),
                self._filename_from_source('noise_image'))
            return trait_spec.argstr % newval

        return super(DenoiseImage, self)._format_arg(name, trait_spec, value)


class AntsJointFusionInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        4,
        argstr='-d %d',
        desc='This option forces the image to be treated '
        'as a specified-dimensional image. If not '
        'specified, the program tries to infer the '
        'dimensionality from the input image.')
    target_image = traits.List(
        InputMultiPath(File(exists=True)),
        argstr='-t %s',
        mandatory=True,
        desc='The target image (or '
        'multimodal target images) assumed to be '
        'aligned to a common image domain.')
    atlas_image = traits.List(
        InputMultiPath(File(exists=True)),
        argstr="-g %s...",
        mandatory=True,
        desc='The atlas image (or '
        'multimodal atlas images) assumed to be '
        'aligned to a common image domain.')
    atlas_segmentation_image = InputMultiPath(
        File(exists=True),
        argstr="-l %s...",
        mandatory=True,
        desc='The atlas segmentation '
        'images. For performing label fusion the number '
        'of specified segmentations should be identical '
        'to the number of atlas image sets.')
    alpha = traits.Float(
        default_value=0.1,
        usedefault=True,
        argstr='-a %s',
        desc=(
            'Regularization '
            'term added to matrix Mx for calculating the inverse. Default = 0.1'
        ))
    beta = traits.Float(
        default_value=2.0,
        usedefault=True,
        argstr='-b %s',
        desc=('Exponent for mapping '
              'intensity difference to the joint error. Default = 2.0'))
    retain_label_posterior_images = traits.Bool(
        False,
        argstr='-r',
        usedefault=True,
        requires=['atlas_segmentation_image'],
        desc=('Retain label posterior probability images. Requires '
              'atlas segmentations to be specified. Default = false'))
    retain_atlas_voting_images = traits.Bool(
        False,
        argstr='-f',
        usedefault=True,
        desc=('Retain atlas voting images. Default = false'))
    constrain_nonnegative = traits.Bool(
        False,
        argstr='-c',
        usedefault=True,
        desc=('Constrain solution to non-negative weights.'))
    patch_radius = traits.ListInt(
        minlen=3,
        maxlen=3,
        argstr='-p %s',
        desc=('Patch radius for similarity measures.'
              'Default: 2x2x2'))
    patch_metric = traits.Enum(
        'PC',
        'MSQ',
        argstr='-m %s',
        desc=('Metric to be used in determining the most similar '
              'neighborhood patch. Options include Pearson\'s '
              'correlation (PC) and mean squares (MSQ). Default = '
              'PC (Pearson correlation).'))
    search_radius = traits.List(
        [3, 3, 3],
        minlen=1,
        maxlen=3,
        argstr='-s %s',
        usedefault=True,
        desc=('Search radius for similarity measures. Default = 3x3x3. '
              'One can also specify an image where the value at the '
              'voxel specifies the isotropic search radius at that voxel.'))
    exclusion_image_label = traits.List(
        traits.Str(),
        argstr='-e %s',
        requires=['exclusion_image'],
        desc=('Specify a label for the exclusion region.'))
    exclusion_image = traits.List(
        File(exists=True),
        desc=('Specify an exclusion region for the given label.'))
    mask_image = File(
        argstr='-x %s',
        exists=True,
        desc='If a mask image '
        'is specified, fusion is only performed in the mask region.')
    out_label_fusion = File(
        argstr="%s", hash_files=False, desc='The output label fusion image.')
    out_intensity_fusion_name_format = traits.Str(
        argstr="",
        desc='Optional intensity fusion '
        'image file name format. '
        '(e.g. "antsJointFusionIntensity_%d.nii.gz")')
    out_label_post_prob_name_format = traits.Str(
        'antsJointFusionPosterior_%d.nii.gz',
        requires=['out_label_fusion', 'out_intensity_fusion_name_format'],
        desc='Optional label posterior probability '
        'image file name format.')
    out_atlas_voting_weight_name_format = traits.Str(
        'antsJointFusionVotingWeight_%d.nii.gz',
        requires=[
            'out_label_fusion', 'out_intensity_fusion_name_format',
            'out_label_post_prob_name_format'
        ],
        desc='Optional atlas voting weight image '
        'file name format.')
    verbose = traits.Bool(False, argstr="-v", desc=('Verbose output.'))


class AntsJointFusionOutputSpec(TraitedSpec):
    out_label_fusion = File(exists=True)
    out_intensity_fusion_name_format = traits.Str()
    out_label_post_prob_name_format = traits.Str()
    out_atlas_voting_weight_name_format = traits.Str()


class AntsJointFusion(ANTSCommand):
    """
    Examples
    --------

    >>> from nipype.interfaces.ants import AntsJointFusion
    >>> antsjointfusion = AntsJointFusion()
    >>> antsjointfusion.inputs.out_label_fusion = 'ants_fusion_label_output.nii'
    >>> antsjointfusion.inputs.atlas_image = [ ['rc1s1.nii','rc1s2.nii'] ]
    >>> antsjointfusion.inputs.atlas_segmentation_image = ['segmentation0.nii.gz']
    >>> antsjointfusion.inputs.target_image = ['im1.nii']
    >>> antsjointfusion.cmdline
    "antsJointFusion -a 0.1 -g ['rc1s1.nii', 'rc1s2.nii'] -l segmentation0.nii.gz \
-b 2.0 -o ants_fusion_label_output.nii -s 3x3x3 -t ['im1.nii']"

    >>> antsjointfusion.inputs.target_image = [ ['im1.nii', 'im2.nii'] ]
    >>> antsjointfusion.cmdline
    "antsJointFusion -a 0.1 -g ['rc1s1.nii', 'rc1s2.nii'] -l segmentation0.nii.gz \
-b 2.0 -o ants_fusion_label_output.nii -s 3x3x3 -t ['im1.nii', 'im2.nii']"

    >>> antsjointfusion.inputs.atlas_image = [ ['rc1s1.nii','rc1s2.nii'],
    ...                                        ['rc2s1.nii','rc2s2.nii'] ]
    >>> antsjointfusion.inputs.atlas_segmentation_image = ['segmentation0.nii.gz',
    ...                                                    'segmentation1.nii.gz']
    >>> antsjointfusion.cmdline
    "antsJointFusion -a 0.1 -g ['rc1s1.nii', 'rc1s2.nii'] -g ['rc2s1.nii', 'rc2s2.nii'] \
-l segmentation0.nii.gz -l segmentation1.nii.gz -b 2.0 -o ants_fusion_label_output.nii \
-s 3x3x3 -t ['im1.nii', 'im2.nii']"

    >>> antsjointfusion.inputs.dimension = 3
    >>> antsjointfusion.inputs.alpha = 0.5
    >>> antsjointfusion.inputs.beta = 1.0
    >>> antsjointfusion.inputs.patch_radius = [3,2,1]
    >>> antsjointfusion.inputs.search_radius = [3]
    >>> antsjointfusion.cmdline
    "antsJointFusion -a 0.5 -g ['rc1s1.nii', 'rc1s2.nii'] -g ['rc2s1.nii', 'rc2s2.nii'] \
-l segmentation0.nii.gz -l segmentation1.nii.gz -b 1.0 -d 3 -o ants_fusion_label_output.nii \
-p 3x2x1 -s 3 -t ['im1.nii', 'im2.nii']"

    >>> antsjointfusion.inputs.search_radius = ['mask.nii']
    >>> antsjointfusion.inputs.verbose = True
    >>> antsjointfusion.inputs.exclusion_image = ['roi01.nii', 'roi02.nii']
    >>> antsjointfusion.inputs.exclusion_image_label = ['1','2']
    >>> antsjointfusion.cmdline
    "antsJointFusion -a 0.5 -g ['rc1s1.nii', 'rc1s2.nii'] -g ['rc2s1.nii', 'rc2s2.nii'] \
-l segmentation0.nii.gz -l segmentation1.nii.gz -b 1.0 -d 3 -e 1[roi01.nii] -e 2[roi02.nii] \
-o ants_fusion_label_output.nii -p 3x2x1 -s mask.nii -t ['im1.nii', 'im2.nii'] -v"

    >>> antsjointfusion.inputs.out_label_fusion = 'ants_fusion_label_output.nii'
    >>> antsjointfusion.inputs.out_intensity_fusion_name_format = 'ants_joint_fusion_intensity_%d.nii.gz'
    >>> antsjointfusion.inputs.out_label_post_prob_name_format = 'ants_joint_fusion_posterior_%d.nii.gz'
    >>> antsjointfusion.inputs.out_atlas_voting_weight_name_format = 'ants_joint_fusion_voting_weight_%d.nii.gz'
    >>> antsjointfusion.cmdline
    "antsJointFusion -a 0.5 -g ['rc1s1.nii', 'rc1s2.nii'] -g ['rc2s1.nii', 'rc2s2.nii'] \
-l segmentation0.nii.gz -l segmentation1.nii.gz -b 1.0 -d 3 -e 1[roi01.nii] -e 2[roi02.nii]  \
-o [ants_fusion_label_output.nii, ants_joint_fusion_intensity_%d.nii.gz, \
ants_joint_fusion_posterior_%d.nii.gz, ants_joint_fusion_voting_weight_%d.nii.gz] \
-p 3x2x1 -s mask.nii -t ['im1.nii', 'im2.nii'] -v"

    """
    input_spec = AntsJointFusionInputSpec
    output_spec = AntsJointFusionOutputSpec
    _cmd = 'antsJointFusion'

    def _format_arg(self, opt, spec, val):
        if opt == 'exclusion_image_label':
            retval = []
            for ii in range(len(self.inputs.exclusion_image_label)):
                retval.append(
                    '-e {0}[{1}]'.format(self.inputs.exclusion_image_label[ii],
                                         self.inputs.exclusion_image[ii]))
            retval = ' '.join(retval)
        elif opt == 'patch_radius':
            retval = '-p {0}'.format(self._format_xarray(val))
        elif opt == 'search_radius':
            retval = '-s {0}'.format(self._format_xarray(val))
        elif opt == 'out_label_fusion':
            if isdefined(self.inputs.out_intensity_fusion_name_format):
                if isdefined(self.inputs.out_label_post_prob_name_format):
                    if isdefined(
                            self.inputs.out_atlas_voting_weight_name_format):
                        retval = '-o [{0}, {1}, {2}, {3}]'.format(
                            self.inputs.out_label_fusion,
                            self.inputs.out_intensity_fusion_name_format,
                            self.inputs.out_label_post_prob_name_format,
                            self.inputs.out_atlas_voting_weight_name_format)
                    else:
                        retval = '-o [{0}, {1}, {2}]'.format(
                            self.inputs.out_label_fusion,
                            self.inputs.out_intensity_fusion_name_format,
                            self.inputs.out_label_post_prob_name_format)
                else:
                    retval = '-o [{0}, {1}]'.format(
                        self.inputs.out_label_fusion,
                        self.inputs.out_intensity_fusion_name_format)
            else:
                retval = '-o {0}'.format(self.inputs.out_label_fusion)
        elif opt == 'out_intensity_fusion_name_format':
            retval = ''
            if not isdefined(self.inputs.out_label_fusion):
                retval = '-o {0}'.format(
                    self.inputs.out_intensity_fusion_name_format)
        elif opt == 'atlas_image':
            atlas_image_cmd = " ".join([
                '-g [{0}]'.format(", ".join("'%s'" % fn for fn in ai))
                for ai in self.inputs.atlas_image
            ])
            retval = atlas_image_cmd
        elif opt == 'target_image':
            target_image_cmd = " ".join([
                '-t [{0}]'.format(", ".join("'%s'" % fn for fn in ai))
                for ai in self.inputs.target_image
            ])
            retval = target_image_cmd
        elif opt == 'atlas_segmentation_image':
            assert len(val) == len(self.inputs.atlas_image), "Number of specified " \
                "segmentations should be identical to the number of atlas image " \
                "sets {0}!={1}".format(len(val), len(self.inputs.atlas_image))

            atlas_segmentation_image_cmd = " ".join([
                '-l {0}'.format(fn)
                for fn in self.inputs.atlas_segmentation_image
            ])
            retval = atlas_segmentation_image_cmd
        else:

            return super(AntsJointFusion, self)._format_arg(opt, spec, val)
        return retval

    def _list_outputs(self):
        outputs = self._outputs().get()
        if isdefined(self.inputs.out_label_fusion):
            outputs['out_label_fusion'] = os.path.abspath(
                self.inputs.out_label_fusion)
        if isdefined(self.inputs.out_intensity_fusion_name_format):
            outputs['out_intensity_fusion_name_format'] = os.path.abspath(
                self.inputs.out_intensity_fusion_name_format)
        if isdefined(self.inputs.out_label_post_prob_name_format):
            outputs['out_label_post_prob_name_format'] = os.path.abspath(
                self.inputs.out_label_post_prob_name_format)
        if isdefined(self.inputs.out_atlas_voting_weight_name_format):
            outputs['out_atlas_voting_weight_name_format'] = os.path.abspath(
                self.inputs.out_atlas_voting_weight_name_format)

        return outputs


class KellyKapowskiInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(
        3,
        2,
        argstr='--image-dimensionality %d',
        usedefault=True,
        desc='image dimension (2 or 3)')

    segmentation_image = File(
        exists=True,
        argstr='--segmentation-image "%s"',
        mandatory=True,
        desc=
        "A segmentation image must be supplied labeling the gray and white matters."
        " Default values = 2 and 3, respectively.",
    )

    gray_matter_label = traits.Int(
        2,
        usedefault=True,
        desc=
        "The label value for the gray matter label in the segmentation_image.")

    white_matter_label = traits.Int(
        3,
        usedefault=True,
        desc=
        "The label value for the white matter label in the segmentation_image."
    )

    gray_matter_prob_image = File(
        exists=True,
        argstr='--gray-matter-probability-image "%s"',
        desc=
        "In addition to the segmentation image, a gray matter probability image can be"
        " used. If no such image is supplied, one is created using the segmentation image"
        " and a variance of 1.0 mm.")

    white_matter_prob_image = File(
        exists=True,
        argstr='--white-matter-probability-image "%s"',
        desc=
        "In addition to the segmentation image, a white matter probability image can be"
        " used. If no such image is supplied, one is created using the segmentation image"
        " and a variance of 1.0 mm.")

    convergence = traits.Str(
        default="[50,0.001,10]",
        argstr='--convergence "%s"',
        usedefault=True,
        desc=
        "Convergence is determined by fitting a line to the normalized energy profile of"
        " the last N iterations (where N is specified by the window size) and determining"
        " the slope which is then compared with the convergence threshold.",
    )

    thickness_prior_estimate = traits.Float(
        10,
        usedefault=True,
        argstr="--thickness-prior-estimate %f",
        desc=
        "Provides a prior constraint on the final thickness measurement in mm."
    )

    thickness_prior_image = File(
        exists=True,
        argstr='--thickness-prior-image "%s"',
        desc="An image containing spatially varying prior thickness values.")

    gradient_step = traits.Float(
        0.025,
        usedefault=True,
        argstr="--gradient-step %f",
        desc="Gradient step size for the optimization.")

    smoothing_variance = traits.Float(
        1.0, usedefault=True,
        argstr="--smoothing-variance %f",
        desc="Defines the Gaussian smoothing of the hit and total images.")

    smoothing_velocity_field = traits.Float(
        1.5, usedefault=True,
        argstr="--smoothing-velocity-field-parameter %f",
        desc=
        "Defines the Gaussian smoothing of the velocity field (default = 1.5)."
        " If the b-spline smoothing option is chosen, then this defines the"
        " isotropic mesh spacing for the smoothing spline (default = 15).")

    use_bspline_smoothing = traits.Bool(
        argstr="--use-bspline-smoothing 1",
        desc="Sets the option for B-spline smoothing of the velocity field.")

    number_integration_points = traits.Int(
        10, usedefault=True,
        argstr="--number-of-integration-points %d",
        desc="Number of compositions of the diffeomorphism per iteration.")

    max_invert_displacement_field_iters = traits.Int(
        20, usedefault=True,
        argstr="--maximum-number-of-invert-displacement-field-iterations %d",
        desc="Maximum number of iterations for estimating the invert"
        "displacement field.")

    cortical_thickness = File(
        argstr='--output "%s"',
        keep_extension=True,
        name_source=["segmentation_image"],
        name_template='%s_cortical_thickness',
        desc='Filename for the cortical thickness.',
        hash_files=False)

    warped_white_matter = File(
        name_source=["segmentation_image"],
        keep_extension=True,
        name_template='%s_warped_white_matter',
        desc='Filename for the warped white matter file.',
        hash_files=False)


class KellyKapowskiOutputSpec(TraitedSpec):
    cortical_thickness = File(
        desc="A thickness map defined in the segmented gray matter.")
    warped_white_matter = File(desc="A warped white matter image.")


class KellyKapowski(ANTSCommand):
    """ Nipype Interface to ANTs' KellyKapowski, also known as DiReCT.

    DiReCT is a registration based estimate of cortical thickness. It was published
    in S. R. Das, B. B. Avants, M. Grossman, and J. C. Gee, Registration based
    cortical thickness measurement, Neuroimage 2009, 45:867--879.

    Examples
    --------
    >>> from nipype.interfaces.ants.segmentation import KellyKapowski
    >>> kk = KellyKapowski()
    >>> kk.inputs.dimension = 3
    >>> kk.inputs.segmentation_image = "segmentation0.nii.gz"
    >>> kk.inputs.convergence = "[45,0.0,10]"
    >>> kk.inputs.thickness_prior_estimate = 10
    >>> kk.cmdline
    'KellyKapowski --convergence "[45,0.0,10]" \
--output "[segmentation0_cortical_thickness.nii.gz,segmentation0_warped_white_matter.nii.gz]" \
--image-dimensionality 3 --gradient-step 0.025000 \
--maximum-number-of-invert-displacement-field-iterations 20 --number-of-integration-points 10 \
--segmentation-image "[segmentation0.nii.gz,2,3]" --smoothing-variance 1.000000 \
--smoothing-velocity-field-parameter 1.500000 --thickness-prior-estimate 10.000000'

    """
    _cmd = "KellyKapowski"
    input_spec = KellyKapowskiInputSpec
    output_spec = KellyKapowskiOutputSpec

    references_ = [{
        'entry':
        BibTeX(
            "@book{Das2009867,"
            "author={Sandhitsu R. Das and Brian B. Avants and Murray Grossman and James C. Gee},"
            "title={Registration based cortical thickness measurement.},"
            "journal={NeuroImage},"
            "volume={45},"
            "number={37},"
            "pages={867--879},"
            "year={2009},"
            "issn={1053-8119},"
            "url={http://www.sciencedirect.com/science/article/pii/S1053811908012780},"
            "doi={http://dx.doi.org/10.1016/j.neuroimage.2008.12.016}"
            "}"),
        'description':
        'The details on the implementation of DiReCT.',
        'tags': ['implementation'],
    }]

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []
        skip += [
            'warped_white_matter', 'gray_matter_label', 'white_matter_label'
        ]
        return super(KellyKapowski, self)._parse_inputs(skip=skip)

    def _gen_filename(self, name):
        if name == 'cortical_thickness':
            output = self.inputs.cortical_thickness
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.segmentation_image)
                output = name + '_cortical_thickness' + ext
            return output

        if name == 'warped_white_matter':
            output = self.inputs.warped_white_matter
            if not isdefined(output):
                _, name, ext = split_filename(self.inputs.segmentation_image)
                output = name + '_warped_white_matter' + ext
            return output

        return None

    def _format_arg(self, opt, spec, val):
        if opt == "segmentation_image":
            newval = '[{0},{1},{2}]'.format(self.inputs.segmentation_image,
                                            self.inputs.gray_matter_label,
                                            self.inputs.white_matter_label)
            return spec.argstr % newval

        if opt == "cortical_thickness":
            ct = self._gen_filename("cortical_thickness")
            wm = self._gen_filename("warped_white_matter")
            newval = '[{},{}]'.format(ct, wm)
            return spec.argstr % newval

        return super(KellyKapowski, self)._format_arg(opt, spec, val)
