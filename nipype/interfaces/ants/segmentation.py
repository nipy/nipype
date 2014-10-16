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
from ...utils.filemanip import copyfile


class AtroposInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, 4, argstr='--image-dimensionality %d',
                            usedefault=True,
                            desc='image dimension (2, 3, or 4)')
    intensity_images = InputMultiPath(File(exists=True),
                                      argstr="--intensity-image %s...",
                                      mandatory=True)
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
                                     hash_files=False)
    save_posteriors = traits.Bool()
    output_posteriors_name_template = traits.Str('POSTERIOR_%02d.nii.gz',
                                                 usedefault=True)


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

class LaplacianThicknessInputSpec(ANTSCommandInputSpec):
    input_wm = File(argstr='%s', mandatory=True, copyfile=True,
                       desc=('white matter segmentation image'),
                       position=1)
    input_gm = File(argstr='%s', mandatory=True, copyfile=True,
                       desc=('gray matter segmentation image'),
                       position=2)
    output_image = File(desc='name of output file', argstr='%s', position=3,
                        genfile=True, hash_files=False)
    smooth_param = traits.Float(argstr='smoothparam=%d', desc='', position=4)
    prior_thickness = traits.Float(argstr='priorthickval=%d', desc='',
                                   position=5)
    dT = traits.Float(argstr='dT=%d', desc='', position=6)
    sulcus_prior = traits.Bool(argstr='use-sulcus-prior', desc='', position=7)
    opt_tolerance = traits.Float(argstr='optional-laplacian-tolerance=%d',
                                 desc='', position=8)


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
        outputs['output_image'] = os.path.join(os.getcwd(),
                                               ''.join((name,
                                                        self.inputs.output_image,
                                                        ext)))
        return outputs


class N4BiasFieldCorrectionInputSpec(ANTSCommandInputSpec):
    dimension = traits.Enum(3, 2, argstr='--image-dimension %d',
                            usedefault=True,
                            desc='image dimension (2 or 3)')
    input_image = File(argstr='--input-image %s', mandatory=True,
                       desc=('image to apply transformation to (generally a '
                             'coregistered functional)'))
    mask_image = File(argstr='--mask-image %s')
    output_image = traits.Str(argstr='--output %s',
                              desc=('output file name'), genfile=True,
                              hash_files=False)
    bspline_fitting_distance = traits.Float(argstr="--bsline-fitting [%g]")
    shrink_factor = traits.Int(argstr="--shrink-factor %d")
    n_iterations = traits.List(traits.Int(), argstr="--convergence [ %s",
                               sep="x", requires=['convergence_threshold'],
                               position=1)
    convergence_threshold = traits.Float(argstr=",%g]",
                                         requires=['n_iterations'],
                                         position=2)
    save_bias = traits.Bool(False, mandatory=True, usedefault=True,
                            desc=('True if the estimated bias should be saved'
                                  ' to file.'), xor=['bias_image'])
    bias_image = File(desc=('Filename for the estimated bias.'),
                      hash_files=False)


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

    >>> from nipype.interfaces.ants import N4BiasFieldCorrection
    >>> n4 = N4BiasFieldCorrection()
    >>> n4.inputs.dimension = 3
    >>> n4.inputs.input_image = 'structural.nii'
    >>> n4.inputs.bspline_fitting_distance = 300
    >>> n4.inputs.shrink_factor = 3
    >>> n4.inputs.n_iterations = [50,50,30,20]
    >>> n4.inputs.convergence_threshold = 1e-6
    >>> n4.cmdline
    'N4BiasFieldCorrection --convergence [ 50x50x30x20 ,1e-06] \
--bsline-fitting [300] --image-dimension 3 --input-image structural.nii \
--output structural_corrected.nii --shrink-factor 3'

    >>> n4_2 = N4BiasFieldCorrection()
    >>> n4_2.inputs.input_image = 'structural.nii'
    >>> n4_2.inputs.save_bias = True
    >>> n4_2.cmdline
    'N4BiasFieldCorrection --image-dimension 3 --input-image structural.nii \
--output [structural_corrected.nii,structural_bias.nii]'
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
            newval = '[%s,%s]' % (output, bias_image)
            return trait_spec.argstr % newval

        return super(N4BiasFieldCorrection,
                     self)._format_arg(name, trait_spec, value)

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []
        skip += ['save_bias', 'bias_image']
        return super(N4BiasFieldCorrection, self)._parse_inputs(skip=skip)

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['output_image'] = os.path.abspath(self._gen_filename('output_image'))

        if self.inputs.save_bias or isdefined(self.inputs.bias_image):
            outputs['bias_image'] = os.path.abspath(self._gen_filename('bias_image'))
        return outputs

class antsCorticalThicknessInputSpec(ANTSCommandInputSpec):
    dimension=traits.Enum(3, 2, argstr= '-d %d', usedefault=True,
                           desc='image dimension (2 or 3)')
    anatomical_image=File(exists=True,
                           argstr='-a %s',
                           desc=('Structural *intensity* image, typically T1.'
                           'If more than one anatomical image is specified,'
                           'subsequently specified images are used during the'
                           'segmentation process. However, only the first'
                           'image is used in the registration of priors.'
                           'Our suggestion would be to specify the T1'
                           'as the first image.'),
                           mandatory=True)
    brain_template=File(exists=True,
            argstr='-e %s',
            desc=('Anatomical *intensity* template (possibly created using a'
            'population data set with buildtemplateparallel.sh in ANTs).'
            'This template is  *not* skull-stripped.'),
            mandatory=True)
    brain_probability_mask=File(exists=True,
            argstr='-m %s', desc='brain probability mask in template space',
            copyfile=False, mandatory=True)
    segmentation_priors = InputMultiPath(File(exists=True),
            argstr='-p %s', mandatory=True)
    out_prefix = traits.Str('antsCT_', argstr='-o %s', usedefault=True,
                             desc=('Prefix that is prepended to all output'
                                   ' files (default = antsCT_)'))
    image_suffix=traits.Str('nii.gz', desc=('any of standard ITK formats,'
        ' nii.gz is default'),  argstr='-s %s', usedefault=True)
    t1_registration_template = File(exists=True,
            desc = ('Anatomical *intensity* template'
           '(assumed to be skull-stripped). A common'
           'case would be where this would be the same'
           'template as specified in the -e option which'
           'is not skull stripped.'),
           argstr='-t %s',
           mandatory=True)
    extraction_registration_mask=File(exists=True, argstr='-f %s',
                        desc=('Mask (defined in the template space) used during'
                              ' registration for brain extraction.'))
    keep_temporary_files=traits.Int(argstr='-k %d',
            desc='Keep brain extraction/segmentation warps, etc (default = 0).')
    max_iterations=traits.Int(argstr='-i %d',
            desc=('ANTS registration max iterations'
            '(default = 100x100x70x20)'))
    prior_segmentation_weight=traits.Float(argstr='-w %f',
            desc=('Atropos spatial prior *probability* weight for'
            'the segmentation'))
    segmentation_iterations=traits.Int(argstr='-n %d',
            desc=('N4 -> Atropos -> N4 iterations during segmentation'
            '(default = 3)'))
    posterior_formulation=traits.Str(argstr='-b %s',
            desc=('Atropos posterior formulation and whether or not'
                'to use mixture model proportions.'
                   '''e.g 'Socrates[1]' (default) or 'Aristotle[1]'.'''
                   'Choose the latter if you'
                   'want use the distance priors (see also the -l option'
                   'for label propagation control).'))
    use_floatingpoint_precision=traits.Enum(0, 1, argstr='-j %d',
            desc='Use floating point precision in registrations (default = 0)')
    use_random_seeding=traits.Enum(0, 1, argstr='-u %d',
            desc=('Use random number generated from system clock in Atropos'
            '(default = 1)'))
    b_spline_smoothing=traits.Bool(argstr='-v',
            desc=('Use B-spline SyN for registrations and B-spline'
            'exponential mapping in DiReCT.'))
    cortical_label_image=File(exists=True,
            desc='Cortical ROI labels to use as a prior for ATITH.')
    label_propagation=traits.Str(argstr='-l %s',
            desc=('Incorporate a distance prior one the posterior formulation.  Should be'
              '''of the form 'label[lambda,boundaryProbability]' where label'''
              'is a value of 1,2,3,... denoting label ID.  The label'
              'probability for anything outside the current label'
              '  = boundaryProbability * exp( -lambda * distanceFromBoundary )'
              'Intuitively, smaller lambda values will increase the spatial capture'
              'range of the distance prior.  To apply to all label values, simply omit'
              'specifying the label, i.e. -l [lambda,boundaryProbability].'))
    quick_registration=traits.Bool(argstr='-q 1',
            desc=('If = 1, use antsRegistrationSyNQuick.sh as the basis for registration'
                  'during brain extraction, brain segmentation, and'
                  '(optional) normalization to a template.'
                  'Otherwise use antsRegistrationSyN.sh (default = 0).'))
    debug=traits.Bool(argstr='-z 1',
            desc=('If > 0, runs a faster version of the script.'
            'Only for testing. Implies -u 0.'
            'Requires single thread computation for complete reproducibility.'))

class antsCorticalThicknessoutputSpec(TraitedSpec):
    BrainExtractionMask=File(exists=True,
            desc= 'brain extraction mask')
    BrainSegmentation=File(exists=True,
            desc='brain segmentaion image')
    BrainSegmentationN4=File(exists=True,
            desc='N4 corrected image')
    BrainSegmentationPosteriorsCSF=File(exists=True,
            desc='CSF posterior probability image')
    BrainSegmentationPosteriorsGM=File(exists=True,
            desc='GM posterior probability image')
    BrainSegmentationPosteriorsWM=File(exists=True,
            desc='WM posterior probability image')
    BrainSegmentationPosteriorsDGM=File(exists=True,
            desc='DGM posterior probability image')
    CorticalThickness=File(exists=True,
            desc='cortical thickness file')
    TemplateToSubject1GenericAffine=File(exists=True,
            desc='Template to subject affine')
    TemplateToSubject0Warp=File(exists=True,
            desc='Template to subject warp')
    SubjectToTemplate1Warp=File(exists=True,
            desc='Template to subject inverse warp')
    SubjectToTemplate0GenericAffine=File(exists=True,
            desc='Template to subject inverse affine')
    TemplateToSubjectLogJacobian=File(exists=True,
            desc='Template to subject log jacobian')

class antsCorticalThickness(ANTSCommand):
    """
    Examples
    --------
    >>> from nipype.interfaces.ants.segmentation import antsCorticalThickness
    >>> corticalthickness = antsCorticalThickness()
    >>> corticalthickness.inputs.dimension = 3
    >>> corticalthickness.inputs.anatomical_image ='T1.nii.gz'
    >>> corticalthickness.inputs.brain_template = 'study_template.nii.gz'
    >>> corticalthickness.inputs.brain_probability_mask ='ProbabilityMaskOfStudyTemplate.nii.gz'
    >>> corticalthickness.inputs.segmentation_priors = ['BrainSegmentationPrior01.nii.gz', 'BrainSegmentationPrior02.nii.gz', 'BrainSegmentationPrior03.nii.gz', 'BrainSegmentationPrior04.nii.gz']
    >>> corticalthickness.inputs.t1_registration_template = 'brain_study_template.nii.gz'
    >>> corticalthickness.cmdline
    'antsCorticalThickness.sh -a T1.nii.gz -m ProbabilityMaskOfStudyTemplate.nii.gz -e study_template.nii.gz -d 3 -s nii.gz -o antsCT_ -p BrainSegmentationPrior%02d.nii.gz -t brain_study_template.nii.gz'
    """

    input_spec = antsCorticalThicknessInputSpec
    output_spec = antsCorticalThicknessoutputSpec
    _cmd = 'antsCorticalThickness.sh'
    def _format_arg(self, opt, spec, val):
        if opt == 'anatomical_image':
            retval = '-a %s' %(val)
            return retval
        if opt == 'brain_template':
            retval = '-e %s' %(val)
            return retval
        if opt == 'brain_probability_mask':
            retval = '-m %s' %(val)
            return retval
        if opt == 'out_prefix':
            retval = '-o %s' %(val)
            return retval
        if opt == 't1_registration_template':
            retval = '-t %s' %(val)
            return retval
        if opt == 'segmentation_priors':
            priors_directory, _, ext = split_filename(self.inputs.segmentation_priors[0])
            if priors_directory is not '':
                retval = "-p %s/BrainSegmentationPrior%%02d" %(priors_directory)
            else:
                retval = "-p BrainSegmentationPrior%02d" 
            retval += ext
            return retval
        return super(ANTSCommand, self)._format_arg(opt, spec, val)

    def _run_interface(self, runtime):
        priors_directory = os.path.join(os.getcwd(), "priors")
        if not os.path.exists(priors_directory):
            os.makedirs(priors_directory)
        _, _, ext = split_filename(self.inputs.segmentation_priors[0])
        for i, f in enumerate(self.inputs.segmentation_priors):
            target = os.path.join(priors_directory,
                    'BrainSegmentationPrior%02d' % (i + 1) + ext)
            if not (os.path.exists(target) and os.path.realpath(target) == os.path.abspath(f)):
                copyfile(os.path.abspath(f), os.path.join(priors_directory,
                    'BrainSegmentationPrior%02d' % (i + 1) + ext))
        runtime = super(antsCorticalThickness, self)._run_interface(runtime)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['BrainExtractionMask'] = os.path.join(os.getcwd(),
                                                        self.inputs.out_prefix +
                                                        'BrainExtractionMask.'+
                                                        self.inputs.image_suffix)
        outputs['BrainSegmentation'] = os.path.join(os.getcwd(),
                                             self.inputs.out_prefix +
                                             'BrainSegmentation.' +
                                             self.inputs.image_suffix)
        outputs['BrainSegmentationN4'] = os.path.join(os.getcwd(),
                                                     self.inputs.out_prefix +
                                                     'BrainSegmentation0N4.' +
                                                     self.inputs.image_suffix)
        outputs['BrainSegmentationPosteriorsCSF'] = os.path.join(os.getcwd(),
                                                  self.inputs.out_prefix +
                                                  'BrainSegmentationPosteriors01.' +
                                                  self.inputs.image_suffix)
        outputs['BrainSegmentationPosteriorsGM'] = os.path.join(os.getcwd(),
                                                  self.inputs.out_prefix +
                                                  'BrainSegmentationPosteriors02.' +
                                                  self.inputs.image_suffix)
        outputs['BrainSegmentationPosteriorsWM'] = os.path.join(os.getcwd(),
                                                  self.inputs.out_prefix +
                                                  'BrainSegmentationPosteriors03.' +
                                                   self.inputs.image_suffix)
        outputs['BrainSegmentationPosteriorsDGM'] = os.path.join(os.getcwd(),
                                                  self.inputs.out_prefix +
                                                  'BrainSegmentationPosteriors04.' +
                                                   self.inputs.image_suffix)
        outputs['CorticalThickness'] = os.path.join(os.getcwd(),
               self.inputs.out_prefix + 'CorticalThickness.' +
               self.inputs.image_suffix)
        outputs['TemplateToSubject1GenericAffine'] = os.path.join(
                os.getcwd(),
                'TemplateToSubject1GenericAffine.mat')
        outputs['TemplateToSubject0Warp'] = os.path.join(os.getcwd(),
               self.inputs.out_prefix + 'TemplateToSubject0Warp.'+
               self.inputs.image_suffix)
        outputs['SubjectToTemplate1Warp'] = os.path.join(os.getcwd(),
               self.inputs.out_prefix + 'SubjectToTemplate1Warp' +
               self.inputs.image_suffix)
        outputs['SubjectToTemplate0GenericAffine'] = os.path.join(os.getcwd(),
                self.inputs.out_prefix + 'SubjectToTemplate0GenericAffine.mat')
        outputs['TemplateToSubjectLogJacobian'] = os.path.join(os.getcwd(),
               self.inputs.out_prefix + 'subjectToTemplateLogJacobian.'+
               self.inputs.image_suffix)
        return outputs
