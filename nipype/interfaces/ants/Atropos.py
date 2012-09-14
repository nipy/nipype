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

## Atropos main documentation
"""
COMMAND:
     Atropos
          A finite mixture modeling (FMM) segmentation approach with possibilities for
          specifying prior constraints. These prior constraints include the specification
          of a prior label image, prior probability images (one for each class), and/or an
          MRF prior to enforce spatial smoothing of the labels. Similar algorithms include
          FAST and SPM.

OPTIONS:
     -d, --image-dimensionality 2/3/4
          This option forces the image to be treated as a specified-dimensional image. If
          not specified, Atropos tries to infer the dimensionality from the first input
          image.

     -a, --intensity-image [intensityImage,<adaptiveSmoothingWeight>]
          One or more scalar images is specified for segmentation using the
          -a/--intensity-image option. For segmentation scenarios with no prior
          information, the first scalar image encountered on the command line is used to
          order labelings such that the class with the smallest intensity signature is
          class '1' through class 'N' which represents the voxels with the largest
          intensity values. The optional adaptive smoothing weight parameter is applicable
          only when using prior label or probability images. This scalar parameter is to
          be specified between [0,1] which smooths each labeled region separately and
          modulates the intensity measurement at each voxel in each intensity image
          between the original intensity and its smoothed counterpart. The smoothness
          parameters are governed by the -b/--bspline option.

     -b, --bspline [<numberOfLevels=6>,<initialMeshResolution=1x1x...>,<splineOrder=3>]
          If the adaptive smoothing weights are > 0, the intensity images are smoothed in
          calculating the likelihood values. This is to account for subtle intensity
          differences across the same tissue regions.

     -i, --initialization Random[numberOfClasses]
                          Otsu[numberOfTissueClasses]
                          KMeans[numberOfTissueClasses,<clusterCenters(in ascending order and for first intensity image only)>]
                          PriorProbabilityImages[numberOfTissueClasses,fileSeriesFormat(index=1 to numberOfClasses) or vectorImage,priorWeighting,<priorProbabilityThreshold>]
                          PriorLabelImage[numberOfTissueClasses,labelImage,priorWeighting]
          To initialize the FMM parameters, one of the following options must be
          specified. If one does not have prior label or probability images we recommend
          using kmeans as it is typically faster than otsu and can be used with
          multivariate initialization. However, since a Euclidean distance on the inter
          cluster distances is used, one might have to appropriately scale the additional
          input images. Random initialization is meant purely for intellectual curiosity.
          The prior weighting (specified in the range [0,1]) is used to modulate the
          calculation of the posterior probabilities between the likelihood*mrfprior and
          the likelihood*mrfprior*prior. For specifying many prior probability images for
          a multi-label segmentation, we offer a minimize usage option (see -m). With that
          option one can specify a prior probability threshold in which only those pixels
          exceeding that threshold are stored in memory.

     -s, --partial-volume-label-set label1xlabel2xlabel3
          The partial volume estimation option allows one to modelmixtures of classes
          within single voxels. Atropos currently allows the user to model two class
          mixtures per partial volume class. The user specifies a set of class labels per
          partial volume class requested. For example, suppose the user was performing a
          classic 3-tissue segmentation (csf, gm, wm) using kmeans initialization. Suppose
          the user also wanted to model the partial voluming effects between csf/gm and
          gm/wm. The user would specify it using -i kmeans[3] and -t 1x2 -t 2x3. So, for
          this example, there would be 3 tissue classes and 2 partial volume classes.
          Optionally,the user can limit partial volume handling to mrf considerations only
          whereby the output would only be the three tissues.

     --use-partial-volume-likelihoods 1/(0)
                                      true/(false)
          The user can specify whether or not to use the partial volume likelihoods, in
          which case the partial volume class is considered separate from the tissue
          classes. Alternatively, one can use the MRF only to handle partial volume in
          which case, partial volume voxels are not considered as separate classes.

     -p, --posterior-formulation Socrates[<useMixtureModelProportions=1>,<initialAnnealingTemperature=1>,<annealingRate=1>,<minimumTemperature=0.1>]
                                 Plato[<useMixtureModelProportions=1>,<initialAnnealingTemperature=1>,<annealingRate=1>,<minimumTemperature=0.1>]
                                 Aristotle[<useMixtureModelProportions=1>,<initialAnnealingTemperature=1>,<annealingRate=1>,<minimumTemperature=0.1>]
          Different posterior probability formulations are possible as are different
          update options. To guarantee theoretical convergence properties, a proper
          formulation of the well-known iterated conditional modes (ICM) uses an
          asynchronous update step modulated by a specified annealing temperature. If one
          sets the AnnealingTemperature > 1 in the posterior formulation a traditional
          code set for a proper ICM update will be created. Otherwise, a synchronous
          update step will take place at each iteration. The annealing temperature, T,
          converts the posteriorProbability to posteriorProbability^(1/T) over the course
          of optimization.

     -x, --mask-image maskImageFilename
          The image mask (which is required) defines the region which is to be labeled by
          the Atropos algorithm.

     -c, --convergence [<numberOfIterations=5>,<convergenceThreshold=0.001>]
          Convergence is determined by calculating the mean maximum posterior probability
          over the region of interest at each iteration. When this value decreases or
          increases less than the specified threshold from the previous iteration or the
          maximum number of iterations is exceeded the program terminates.

     -k, --likelihood-model Gaussian
                            HistogramParzenWindows[<sigma=1.0>,<numberOfBins=32>]
                            ManifoldParzenWindows[<pointSetSigma=1.0>,<evaluationKNeighborhood=50>,<CovarianceKNeighborhood=0>,<kernelSigma=0>]
                            JointShapeAndOrientationProbability[<shapeSigma=1.0>,<numberOfShapeBins=64>, <orientationSigma=1.0>, <numberOfOrientationBins=32>]
                            LogEuclideanGaussian
          Both parametric and non-parametric options exist in Atropos. The Gaussian
          parametric option is commonly used (e.g. SPM & FAST) where the mean and standard
          deviation for the Gaussian of each class is calculated at each iteration. Other
          groups use non-parametric approaches exemplified by option 2. We recommend using
          options 1 or 2 as they are fairly standard and the default parameters work
          adequately.

     -m, --mrf [<smoothingFactor=0.3>,<radius=1x1x...>]
               [<mrfCoefficientImage>,<radius=1x1x...>]
          Markov random field (MRF) theory provides a general framework for enforcing
          spatially contextual constraints on the segmentation solution. The default
          smoothing factor of 0.3 provides a moderate amount of smoothing. Increasing this
          number causes more smoothing whereas decreasing the number lessens the
          smoothing. The radius parameter specifies the mrf neighborhood. Different update
          schemes are possible but only the asynchronous updating has theoretical
          convergence properties.

     -g, --icm [<useAsynchronousUpdate=1>,<maximumNumberOfICMIterations=1>,<icmCodeImage=''>]
          Asynchronous updating requires the construction of an ICM code image which is a
          label image (with labels in the range {1,..,MaximumICMCode}) constructed such
          that no MRF neighborhood has duplicate ICM code labels. Thus, to update the
          voxel class labels we iterate through the code labels and, for each code label,
          we iterate through the image and update the voxel class label that has the
          corresponding ICM code label. One can print out the ICM code image by specifying
          an ITK-compatible image filename.

     -o, --output [classifiedImage,<posteriorProbabilityImageFileNameFormat>]
          The output consists of a labeled image where each voxel in the masked region is
          assigned a label from 1, 2, ..., N. Optionally, one can also output the
          posterior probability images specified in the same format as the prior
          probability images, e.g. posterior%02d.nii.gz (C-style file name formatting).

     -u, --minimize-memory-usage (0)/1
          By default, memory usage is not minimized, however, if this is needed, the
          various probability and distance images are calculated on the fly instead of
          being stored in memory at each iteration. Also, if prior probability images are
          used, only the non-negligible pixel values are stored in memory.
          <VALUES>: 0

     -w, --winsorize-outliers BoxPlot[<lowerPercentile=0.25>,<upperPercentile=0.75>,<whiskerLength=1.5>]
                              GrubbsRosner[<significanceLevel=0.05>,<winsorizingLevel=0.10>]
          To remove the effects of outliers in calculating the weighted mean and weighted
          covariance, the user can opt to remove the outliers through the options
          specified below.

     -e, --use-euclidean-distance (0)/1
          Given prior label or probability images, the labels are propagated throughout
          the masked region so that every voxel in the mask is labeled. Propagation is
          done by using a signed distance transform of the label. Alternatively,
          propagation of the labels with the fast marching filter respects the distance
          along the shape of the mask (e.g. the sinuous sulci and gyri of the cortex.
          <VALUES>: 0

     -l, --label-propagation whichLabel[lambda=0.0,<boundaryProbability=1.0>]
          The propagation of each prior label can be controlled by the lambda and boundary
          probability parameters. The latter parameter is the probability (in the range
          [0,1]) of the label on the boundary which increases linearly to a maximum value
          of 1.0 in the interior of the labeled region. The former parameter dictates the
          exponential decay of probability propagation outside the labeled region from the
          boundary probability, i.e. boundaryProbability*exp( -lambda * distance ).

     -h
          Print the help menu (short version).
          <VALUES>: 0

     --help
          Print the help menu.
          <VALUES>: 0

==================================
cd {TEST_DATA}/EXPERIEMENTS/AtroposSimpleTest
bash -x TestAtropos.sh

{BINARIES_DIRECTORY}/bin/Atropos \
   -d 3  \
   -a T1_0.nii.gz  \
   -a T1_1_fixed.nii.gz  \
   -a T1_2_fixed.nii.gz  \
   -a T2_0_fixed.nii.gz  \
   -a T2_1_fixed.nii.gz  \
   --mask-image T1_0_roi.nii.gz  \
   -i PriorProbabilityImages[10,priorProbImages%02d.nii.gz,0.8,0.0000001]  \
   -k Gaussian  \
   -m  [0.2,1x1x1]  \
   -g [1,1]  \
   -c [5,0.000001]  \
   -p Socrates[1]  \
   -o [LabelImage.nii.gz,POSTERIOR_%02d.nii.gz]

"""
