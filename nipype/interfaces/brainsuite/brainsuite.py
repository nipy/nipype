import os
import re as regex

from nipype.interfaces.base import(
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    File,
    traits,
    isdefined,
)


class BseInputSpec(CommandLineInputSpec):

    inputMRIFile = File(mandatory=True, argstr='-i %s',
                        desc='input MRI volume')
    outputMRIVolume = File(desc='output brain-masked MRI volume. If'
                                'unspecified, output file name will be auto'
                                'generated.',
                           argstr='-o %s', hash_files=False, genfile=True)
    diffusionConstant = traits.Float(25, usedefault=True,
                                     desc='diffusion constant', argstr='-d %f')
    diffusionIterations = traits.Int(3, usedefault=True,
                                     desc='diffusion iterations',
                                     argstr='-n %d')
    edgeDetectionConstant = traits.Float(0.64, usedefault=True,
                                         desc='edge detection constant',
                                         argstr='-s %f')
    radius = traits.Float(1, usedefault=True,
                          desc='radius of erosion/dilation filter',
                          argstr='-r %f')
    dilateFinalMask = traits.Bool(True, usedefault=True,
                                  desc='dilate final mask', argstr='-p')
    trim = traits.Bool(True, usedefault=True, desc='trim brainstem',
                       argstr='--trim')
    outputMaskFile = File(desc='save smooth brain mask',
                          argstr='--mask %s', hash_files=False)
    outputDiffusionFilter = File(desc='diffusion filter output',
                                 argstr='--adf %s', hash_files=False)
    outputEdgeMap = File(desc='edge map output', argstr='--edge %s',
                         hash_files=False)
    outputDetailedBrainMask = File(desc='save detailed brain mask',
                                   argstr='--hires %s', hash_files=False)
    outputCortexFile = File(desc='cortex file', argstr='--cortex %s',
                            hash_files=False)
    verbosityLevel = traits.Float(1, usedefault=True,
                                  desc=' verbosity level (0=silent)',
                                  argstr='-v %f')
    noRotate = traits.Bool(desc='retain original orientation'
                           '(default behavior will auto-rotate input NII files'
                           'to LPI orientation)', argstr='--norotate')
    timer = traits.Bool(desc='show timing', argstr='--timer')


class BseOutputSpec(TraitedSpec):
    outputMRIVolume = File(desc='path/name of brain-masked MRI volume')
    outputMaskFile = File(desc='path/name of smooth brain mask')
    outputDiffusionFilter = File(desc='path/name of diffusion filter output')
    outputEdgeMap = File(desc='path/name of edge map output')
    outputDetailedBrainMask = File(desc='path/name of detailed brain mask')
    outputCortexFile = File(desc='path/name of cortex file')


class Bse(CommandLine):
    """
    brain surface extractor (BSE)
    This program performs automated skull and scalp removal on T1-weighted MRI volumes.

    http://brainsuite.org/processing/surfaceextraction/bse/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> bse = brainsuite.Bse()
    >>> bse.inputs.inputMRIFile = example_data('structural.nii')
    >>> results = bse.run() #doctest: +SKIP

    """

    input_spec = BseInputSpec
    output_spec = BseOutputSpec
    _cmd = 'bse'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputMRIVolume':
            return getFileName(self, self.inputs.inputMRIFile, name, '.nii.gz')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class BfcInputSpec(CommandLineInputSpec):
    inputMRIFile = File(mandatory=True,
                        desc='input skull-stripped MRI volume', argstr='-i %s')
    inputMaskFile = File(desc='mask file', argstr='-m %s', hash_files=False)
    outputMRIVolume = File(desc='output bias-corrected MRI volume.'
                                'If unspecified, output file name'
                                'will be auto generated.', argstr='-o %s',
                           hash_files=False, genfile=True)
    outputBiasField = File(desc='save bias field estimate',
                           argstr='--bias %s', hash_files=False)
    outputMaskedBiasField = File(desc='save bias field estimate (masked)',
                                 argstr='--maskedbias %s', hash_files=False)
    histogramRadius = traits.Int(desc='histogram radius (voxels)',
                                 argstr='-r %d')
    biasEstimateSpacing = traits.Int(desc='bias sample spacing (voxels)',
                                     argstr='-s %d')
    controlPointSpacing = traits.Int(desc='control point spacing (voxels)',
                                     argstr='-c %d')
    splineLambda = traits.Float(desc='spline stiffness weighting parameter',
                                argstr='-w %f')
    histogramType = traits.Enum('ellipse', 'block',
                                desc='Options for type of histogram\nellipse:'
                                     'use ellipsoid for ROI histogram\nblock'
                                     ':use block for ROI histogram',
                                argstr='%s')
    iterativeMode = traits.Bool(desc='iterative mode (overrides -r, -s, -c,'
                                     '-w settings)',
                                argstr='--iterate')
    correctionScheduleFile = File(desc='list of parameters ',
                                  argstr='--schedule %s')
    biasFieldEstimatesOutputPrefix = traits.Str(desc='save iterative bias'
                                                     'field estimates as'
                                                     '<prefix>.n.field.nii.gz',
                                                argstr='--biasprefix %s')
    correctedImagesOutputPrefix = traits.Str(desc='save iterative corrected'
                                                  'images as'
                                                  '<prefix>.n.bfc.nii.gz',
                                             argstr='--prefix %s')
    correctWholeVolume = traits.Bool(desc='apply correction field to entire'
                                          'volume', argstr='--extrapolate')
    minBias = traits.Float(0.5, usedefault=True, desc='minimum allowed bias'
                                                      'value',
                           argstr='-L %f')
    maxBias = traits.Float(1.5, usedefault=True, desc='maximum allowed bias' ''
                                                      'value',
                           argstr='-U %f')
    biasRange = traits.Enum("low", "medium", "high",
                            desc='Preset options for bias_model\n'
                                 'low: small bias model [0.95,1.05]\n'
                                 'medium: medium bias model [0.90,1.10]\n'
                                 'high: high bias model [0.80,1.20]',
                            argstr='%s')
    intermediate_file_type = traits.Enum("analyze", "nifti",
                                         "gzippedAnalyze", "gzippedNifti",
                                         desc='Options for the format in'
                                              'which intermediate files are' ""
                                              'generated',
                                         argstr='%s')
    convergenceThreshold = traits.Float(desc='convergence threshold',
                                        argstr='--eps %f')
    biasEstimateConvergenceThreshold = traits.Float(
        desc='bias estimate convergence threshold (values > 0.1 disable)', argstr='--beps %f')
    verbosityLevel = traits.Int(
        desc='verbosity level (0=silent)', argstr='-v %d')
    timer = traits.Bool(desc='display timing information', argstr='--timer')


class BfcOutputSpec(TraitedSpec):
    outputMRIVolume = File(desc='path/name of output file')
    outputBiasField = File(desc='path/name of bias field output file')
    outputMaskedBiasField = File(desc='path/name of masked bias field output')
    correctionScheduleFile = File(desc='path/name of schedule file')


class Bfc(CommandLine):
    """
    bias field corrector (BFC)
    This program corrects gain variation in T1-weighted MRI.

    http://brainsuite.org/processing/surfaceextraction/bfc/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> bfc = brainsuite.Bfc()
    >>> bfc.inputs.inputMRIFile = example_data('structural.nii')
    >>> bfc.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = bfc.run() #doctest: +SKIP

    """


    input_spec = BfcInputSpec
    output_spec = BfcOutputSpec
    _cmd = 'bfc'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputMRIVolume':
            return getFileName(self, self.inputs.inputMRIFile, name, '.nii.gz')

        return None

    def _format_arg(self, name, spec, value):
        if name == 'histogramType':
            return spec.argstr % {"ellipse": "--ellipse", "block": "--block"}[value]
        if name == 'biasRange':
            return spec.argstr % {"low": "--low", "medium": "--medium", "high": "--high"}[value]
        if name == 'intermediate_file_type':
            return spec.argstr % {"analyze": "--analyze", "nifti": "--nifti", "gzippedAnalyze": "--analyzegz", "gzippedNifti": "--niftigz"}[value]

        return super(Bfc, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        return l_outputs(self)


class PvcInputSpec(CommandLineInputSpec):
    inputMRIFile = File(mandatory=True, desc='MRI file', argstr='-i %s')
    inputMaskFile = File(desc='brain mask file', argstr='-m %s')
    outputLabelFile = File(desc='output label file. If unspecified, output file name will be auto generated.', argstr='-o %s', genfile=True)
    outputTissueFractionFile = File(desc='output tissue fraction file', argstr='-f %s', genfile=True)
    spatialPrior = traits.Float(desc='spatial prior strength', argstr='-l %f')
    verbosity = traits.Int(desc='verbosity level (0 = silent)', argstr='-v %d')
    threeClassFlag = traits.Bool(
        desc='use a three-class (CSF=0,GM=1,WM=2) labeling', argstr='-3')
    timer = traits.Bool(desc='time processing', argstr='--timer')


class PvcOutputSpec(TraitedSpec):
    outputLabelFile = File(desc='path/name of label file')
    outputTissueFractionFile = File(desc='path/name of tissue fraction file')


class Pvc(CommandLine):
    """
    partial volume classifier (PVC) tool.
    This program performs voxel-wise tissue classification T1-weighted MRI.
    Image should be skull-stripped and bias-corrected before tissue classification.

    http://brainsuite.org/processing/surfaceextraction/pvc/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> pvc = brainsuite.Pvc()
    >>> pvc.inputs.inputMRIFile = example_data('structural.nii')
    >>> pvc.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = pvc.run() #doctest: +SKIP

    """

    input_spec = PvcInputSpec
    output_spec = PvcOutputSpec
    _cmd = 'pvc'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputLabelFile' or name == 'outputTissueFractionFile':
            return getFileName(self, self.inputs.inputMRIFile, name, '.nii.gz')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class CerebroInputSpec(CommandLineInputSpec):
    inputMRIFile = File(
        mandatory=True, desc='input 3D MRI volume', argstr='-i %s')
    inputAtlasMRIFile = File(
        mandatory=True, desc='atlas MRI volume', argstr='--atlas %s')
    inputAtlasLabelFile = File(
        mandatory=True, desc='atlas labeling', argstr='--atlaslabels %s')
    inputBrainMaskFile = File(desc='brain mask file', argstr='-m %s')
    outputCerebrumMaskFile = File(desc='output cerebrum mask volume. If unspecified, output file name will be auto generated.',
                                  argstr='-o %s', genfile=True)
    outputLabelMaskFile = File(desc='output labeled hemisphere/cerebrum volume. If unspecified, output file name will be auto generated.',
                               argstr='-l %s', genfile=True)
    costFunction = traits.Int(2, usedefault=True, desc='0,1,2', argstr='-c %d')
    useCentroids = traits.Bool(
        desc='use centroids of data to initialize position', argstr='--centroids')
    outputAffineTransformFile = File(
        desc='save affine transform to file.', argstr='--air %s')
    outputWarpTransformFile = File(
        desc='save warp transform to file.', argstr='--warp %s')
    verbosity = traits.Int(desc='verbosity level (0=silent)', argstr='-v %d')
    linearConvergence = traits.Float(
        desc='linear convergence', argstr='--linconv %f')
    warpLabel = traits.Int(
        desc='warp order (2,3,4,5,6,7,8)', argstr='--warplevel %d')
    warpConvergence = traits.Float(
        desc='warp convergence', argstr='--warpconv %f')
    keepTempFiles = traits.Bool(
        desc="don't remove temporary files", argstr='--keep')
    tempDirectory = traits.Str(
        desc='specify directory to use for temporary files', argstr='--tempdir %s')
    tempDirectoryBase = traits.Str(
        desc='create a temporary directory within this directory', argstr='--tempdirbase %s')


class CerebroOutputSpec(TraitedSpec):
    outputCerebrumMaskFile = File(desc='path/name of cerebrum mask file')
    outputLabelMaskFile = File(desc='path/name of label mask file')
    outputAffineTransformFile = File(desc='path/name of affine transform file')
    outputWarpTransformFile = File(desc='path/name of warp transform file')


class Cerebro(CommandLine):
    """
    Cerebrum/cerebellum labeling tool
    This program performs automated labeling of cerebellum and cerebrum in T1 MRI.
    Input MRI should be skull-stripped or a brain-only mask should be provided.


    http://brainsuite.org/processing/surfaceextraction/cerebrum/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> cerebro = brainsuite.Cerebro()
    >>> cerebro.inputs.inputMRIFile = example_data('structural.nii')
    >>> cerebro.inputs.inputAtlasMRIFile = 'atlasMRIVolume.img'
    >>> cerebro.inputs.inputAtlasLabelFile = 'atlasLabels.img'
    >>> cerebro.inputs.inputBrainMaskFile = example_data('mask.nii')
    >>> results = cerebro.run() #doctest: +SKIP

    """

    input_spec = CerebroInputSpec
    output_spec = CerebroOutputSpec
    _cmd = 'cerebro'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputCerebrumMaskFile' or name == 'outputLabelMaskFile':
            return getFileName(self, self.inputs.inputMRIFile, name, '.nii.gz')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class CortexInputSpec(CommandLineInputSpec):
    inputHemisphereLabelFile = File(
        mandatory=True, desc='hemisphere / lobe label volume', argstr='-h %s')
    outputCerebrumMask = File(
        desc='output structure mask. If unspecified, output file name will be auto generated.', argstr='-o %s', genfile=True)
    inputTissueFractionFile = File(
        mandatory=True, desc='tissue fraction file (32-bit float)', argstr='-f %s')
    tissueFractionThreshold = traits.Float(
        50.0, usedefault=True, desc='tissue fraction threshold (percentage)', argstr='-p %f')
    computeWGBoundary = traits.Bool(
        True, usedefault=True, desc='compute WM/GM boundary', argstr='-w')
    computeGCBoundary = traits.Bool(
        desc='compute GM/CSF boundary', argstr='-g')
    includeAllSubcorticalAreas = traits.Bool(
        True, usedefault=True, desc='include all subcortical areas in WM mask', argstr='-a')
    verbosity = traits.Int(desc='verbosity level', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class CortexOutputSpec(TraitedSpec):
    outputCerebrumMask = File(desc='path/name of cerebrum mask')


class Cortex(CommandLine):
    """
    cortex extractor
    This program produces a cortical mask using tissue fraction estimates
    and a co-registered cerebellum/hemisphere mask.

    http://brainsuite.org/processing/surfaceextraction/cortex/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> cortex = brainsuite.Cortex()
    >>> cortex.inputs.inputHemisphereLabelFile = example_data('mask.nii')
    >>> cortex.inputs.inputTissueFractionFile = example_data('tissues.nii.gz')
    >>> results = cortex.run() #doctest: +SKIP

    """

    input_spec = CortexInputSpec
    output_spec = CortexOutputSpec
    _cmd = 'cortex'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputCerebrumMask':
            return getFileName(self, self.inputs.inputHemisphereLabelFile, name, '.nii.gz')
        return None

    def _list_outputs(self):
        return l_outputs(self)


class ScrubmaskInputSpec(CommandLineInputSpec):
    inputMaskFile = File(
        mandatory=True, desc='input structure mask file', argstr='-i %s')
    outputMaskFile = File(
        desc='output structure mask file. If unspecified, output file name will be auto generated.', argstr='-o %s', genfile=True)
    backgroundFillThreshold = traits.Int(
        2, usedefault=True, desc='background fill threshold', argstr='-b %d')
    foregroundTrimThreshold = traits.Int(
        0, usedefault=True, desc='foreground trim threshold', argstr='-f %d')
    numberIterations = traits.Int(desc='number of iterations', argstr='-n %d')
    verbosity = traits.Int(desc='verbosity (0=silent)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class ScrubmaskOutputSpec(TraitedSpec):
    outputMaskFile = File(desc='path/name of mask file')


class Scrubmask(CommandLine):
    """
    ScrubMask tool
    scrubmask filters binary masks to trim loosely connected voxels that may
    result from segmentation errors and produce bumps on tessellated surfaces.

    http://brainsuite.org/processing/surfaceextraction/scrubmask/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> scrubmask = brainsuite.Scrubmask()
    >>> scrubmask.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = scrubmask.run() #doctest: +SKIP

    """
    input_spec = ScrubmaskInputSpec
    output_spec = ScrubmaskOutputSpec
    _cmd = 'scrubmask'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputMaskFile':
            return getFileName(self, self.inputs.inputMaskFile, name, '.nii.gz')


        return None

    def _list_outputs(self):
        return l_outputs(self)


class TcaInputSpec(CommandLineInputSpec):
    inputMaskFile = File(
        mandatory=True, desc='input mask volume', argstr='-i %s')
    outputMaskFile = File(
        desc='output mask volume. If unspecified, output file name will be auto generated.', argstr='-o %s', genfile=True)
    minCorrectionSize = traits.Int(
        2500, usedefault=True, desc='maximum correction size', argstr='-m %d')
    maxCorrectionSize = traits.Int(
        desc='minimum correction size', argstr='-n %d')
    foregroundDelta = traits.Int(
        20, usedefault=True, desc='foreground delta', argstr='--delta %d')
    verbosity = traits.Int(desc='verbosity (0 = quiet)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class TcaOutputSpec(TraitedSpec):
    outputMaskFile = File(desc='path/name of mask file')


class Tca(CommandLine):
    """
    topological correction algorithm (TCA)
    This program removes topological handles from a binary object.

    http://brainsuite.org/processing/surfaceextraction/tca/

    Examples
    --------
    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> tca = brainsuite.Tca()
    >>> tca.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = tca.run() #doctest: +SKIP

    """
    input_spec = TcaInputSpec
    output_spec = TcaOutputSpec
    _cmd = 'tca'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputMaskFile':
            return getFileName(self, self.inputs.inputMaskFile, name, '.nii.gz')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class DewispInputSpec(CommandLineInputSpec):
    inputMaskFile = File(mandatory=True, desc='input file', argstr='-i %s')
    outputMaskFile = File(
        desc='output file. If unspecified, output file name will be auto generated.', argstr='-o %s', genfile=True)
    verbosity = traits.Int(desc='verbosity', argstr='-v %d')
    sizeThreshold = traits.Int(desc='size threshold', argstr='-t %d')
    maximumIterations = traits.Int(
        desc='maximum number of iterations', argstr='-n %d')
    timer = traits.Bool(desc='time processing', argstr='--timer')


class DewispOutputSpec(TraitedSpec):
    outputMaskFile = File(desc='path/name of mask file')


class Dewisp(CommandLine):
    """
    dewisp
    removes wispy tendril structures from cortex model binary masks.
    It does so based on graph theoretic analysis of connected components,
    similar to TCA. Each branch of the structure graph is analyzed to determine
    pinch points that indicate a likely error in segmentation that attaches noise
    to the image. The pinch threshold determines how many voxels the cross-section
    can be before it is considered part of the image.

    http://brainsuite.org/processing/surfaceextraction/dewisp/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> dewisp = brainsuite.Dewisp()
    >>> dewisp.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = dewisp.run() #doctest: +SKIP

    """

    input_spec = DewispInputSpec
    output_spec = DewispOutputSpec
    _cmd = 'dewisp'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputMaskFile':
            return getFileName(self, self.inputs.inputMaskFile, name, '.nii.gz')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class DfsInputSpec(CommandLineInputSpec):
    inputVolumeFile = File(
        mandatory=True, desc='input 3D volume', argstr='-i %s')
    outputSurfaceFile = File(
        desc='output surface mesh file. If unspecified, output file name will be auto generated.', argstr='-o %s', genfile=True)
    inputShadingVolume = File(
        desc='shade surface model with data from image volume', argstr='-c %s')
    smoothingIterations = traits.Int(
        10, usedefault=True, desc='number of smoothing iterations', argstr='-n %d')
    smoothingConstant = traits.Float(
        0.5, usedefault=True, desc='smoothing constant', argstr='-a %f')
    curvatureWeighting = traits.Float(
        5.0, usedefault=True, desc='curvature weighting', argstr='-w %f')
    scalingPercentile = traits.Float(desc='scaling percentile', argstr='-f %f')
    nonZeroTessellation = traits.Bool(
        desc='tessellate non-zero voxels', argstr='-nz', xor=('nonZeroTessellation', 'specialTessellation'))
    tessellationThreshold = traits.Float(
        desc='To be used with specialTessellation. Set this value first, then set specialTessellation value.\nUsage: tessellate voxels greater_than, less_than, or equal_to <tessellationThreshold>', argstr='%f')
    specialTessellation = traits.Enum('greater_than', 'less_than', 'equal_to', desc='To avoid throwing a UserWarning, set tessellationThreshold first. Then set this attribute.\nUsage: tessellate voxels greater_than, less_than, or equal_to <tessellationThreshold>', argstr='%s', xor=(
        'nonZeroTessellation', 'specialTessellation'), requires=['tessellationThreshold'], position=-1)
    zeroPadFlag = traits.Bool(
        desc='zero-pad volume (avoids clipping at edges)', argstr='-z')
    noNormalsFlag = traits.Bool(
        desc='do not compute vertex normals', argstr='--nonormals')
    postSmoothFlag = traits.Bool(
        desc='smooth vertices after coloring', argstr='--postsmooth')
    verbosity = traits.Int(desc='verbosity (0 = quiet)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class DfsOutputSpec(TraitedSpec):
    outputSurfaceFile = File(desc='path/name of surface file')


class Dfs(CommandLine):
    """
    Surface Generator
    Generates mesh surfaces using an isosurface algorithm.

    http://brainsuite.org/processing/surfaceextraction/inner-cortical-surface/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> dfs = brainsuite.Dfs()
    >>> dfs.inputs.inputVolumeFile = example_data('structural.nii')
    >>> results = dfs.run() #doctest: +SKIP

    """

    input_spec = DfsInputSpec
    output_spec = DfsOutputSpec
    _cmd = 'dfs'

    def _format_arg(self, name, spec, value):
        if name == 'tessellationThreshold':
            return ''  # blank argstr
        if name == 'specialTessellation':
            threshold = self.inputs.tessellationThreshold
            return spec.argstr % {"greater_than": ''.join(("-gt %f" % threshold)), "less_than": ''.join(("-lt %f" % threshold)), "equal_to": ''.join(("-eq %f" % threshold))}[value]
        return super(Dfs, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputSurfaceFile':
            return getFileName(self, self.inputs.inputVolumeFile, name, '.dfs')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class PialmeshInputSpec(CommandLineInputSpec):
    inputSurfaceFile = File(mandatory=True, desc='input file', argstr='-i %s')
    outputSurfaceFile = File(
        desc='output file. If unspecified, output file name will be auto generated.', argstr='-o %s', genfile=True)
    verbosity = traits.Int(desc='verbosity', argstr='-v %d')
    inputTissueFractionFile = File(
        mandatory=True, desc='floating point (32) tissue fraction image', argstr='-f %s')
    numIterations = traits.Int(
        100, usedefault=True, desc='number of iterations', argstr='-n %d')
    searchRadius = traits.Float(
        1, usedefault=True, desc='search radius', argstr='-r %f')
    stepSize = traits.Float(0.4, usedefault=True,
                            desc='step size', argstr='-s %f')
    inputMaskFile = File(
        mandatory=True, desc='restrict growth to mask file region', argstr='-m %s')
    maxThickness = traits.Float(
        20, usedefault=True, desc='maximum allowed tissue thickness', argstr='--max %f')
    tissueThreshold = traits.Float(
        1.05, usedefault=True, desc='tissue threshold', argstr='-t %f')
# output interval is not an output -- it specifies how frequently the
# output surfaces are generated
    outputInterval = traits.Int(
        10, usedefault=True, desc='output interval', argstr='--interval %d')
    exportPrefix = traits.Str(
        desc='prefix for exporting surfaces if interval is set', argstr='--prefix %s')
    laplacianSmoothing = traits.Float(
        0.025, usedefault=True, desc='apply Laplacian smoothing', argstr='--smooth %f')
    timer = traits.Bool(desc='show timing', argstr='--timer')
    recomputeNormals = traits.Bool(
        desc='recompute normals at each iteration', argstr='--norm')
    normalSmoother = traits.Float(
        0.2, usedefault=True, desc='strength of normal smoother.', argstr='--nc %f')
    tangentSmoother = traits.Float(
        desc='strength of tangential smoother.', argstr='--tc %f')


class PialmeshOutputSpec(TraitedSpec):
    outputSurfaceFile = File(desc='path/name of surface file')


class Pialmesh(CommandLine):
    """
    pialmesh
    computes a pial surface model using an inner WM/GM mesh and a tissue fraction map.

    http://brainsuite.org/processing/surfaceextraction/pial/

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> pialmesh = brainsuite.Pialmesh()
    >>> pialmesh.inputs.inputSurfaceFile = 'input_mesh.dfs'
    >>> pialmesh.inputs.inputTissueFractionFile = 'frac_file.nii.gz'
    >>> pialmesh.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = pialmesh.run() #doctest: +SKIP

    """

    input_spec = PialmeshInputSpec
    output_spec = PialmeshOutputSpec
    _cmd = 'pialmesh'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputSurfaceFile':
            return getFileName(self, self.inputs.inputSurfaceFile, name, '.dfs')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class SkullfinderInputSpec(CommandLineInputSpec):
    inputMRIFile = File(mandatory=True, desc='input file', argstr='-i %s')
    inputMaskFile = File(
        mandatory=True, desc='A brain mask file, 8-bit image (0=non-brain, 255=brain)', argstr='-m %s')
    outputLabelFile = File(
        desc='output file. If unspecified, output file name will be auto generated.', argstr='-o %s', genfile=True)
    verbosity = traits.Int(desc='verbosity', argstr='-v %d')
    lowerThreshold = traits.Int(
        desc='Lower threshold for segmentation', argstr='-l %d')
    upperThreshold = traits.Int(
        desc='Upper threshold for segmentation', argstr='-u %d')
    surfaceFilePrefix = traits.Str(
        desc='if specified, generate surface files for brain, skull, and scalp', argstr='-s %s')
    bgLabelValue = traits.Int(
        desc='background label value (0-255)', argstr='--bglabel %d')
    scalpLabelValue = traits.Int(
        desc='scalp label value (0-255)', argstr='--scalplabel %d')
    skullLabelValue = traits.Int(
        desc='skull label value (0-255)', argstr='--skulllabel %d')
    spaceLabelValue = traits.Int(
        desc='space label value (0-255)', argstr='--spacelabel %d')
    brainLabelValue = traits.Int(
        desc='brain label value (0-255)', argstr='--brainlabel %d')
    performFinalOpening = traits.Bool(
        desc='perform a final opening operation on the scalp mask', argstr='--finalOpening')


class SkullfinderOutputSpec(TraitedSpec):
    outputLabelFile = File(desc='path/name of label file')


class Skullfinder(CommandLine):
    """
    Skull and scalp segmentation algorithm.

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> skullfinder = brainsuite.Skullfinder()
    >>> skullfinder.inputs.inputMRIFile = example_data('structural.nii')
    >>> skullfinder.inputs.inputMaskFile = example_data('mask.nii')
    >>> results = skullfinder.run() #doctest: +SKIP

    """
    input_spec = SkullfinderInputSpec
    output_spec = SkullfinderOutputSpec
    _cmd = 'skullfinder'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])

        if name == 'outputLabelFile':
            return getFileName(self, self.inputs.inputMRIFile, name, '.nii.gz')

        return None

    def _list_outputs(self):
        return l_outputs(self)


class HemisplitInputSpec(CommandLineInputSpec):
    inputSurfaceFile = File(
        mandatory=True, desc='input surface', argstr='-i %s')
    inputHemisphereLabelFile = File(
        mandatory=True, desc='input hemisphere label volume', argstr='-l %s')
    outputLeftHemisphere = File(
        desc='output surface file, left hemisphere. If unspecified, output file name will be auto generated.', argstr='--left %s', genfile=True)
    outputRightHemisphere = File(
        desc='output surface file, right hemisphere. If unspecified, output file name will be auto generated.', argstr='--right %s', genfile=True)
    pialSurfaceFile = File(
        desc='pial surface file -- must have same geometry as input surface', argstr='-p %s')
    outputLeftPialHemisphere = File(
        desc='output pial surface file, left hemisphere. If unspecified, output file name will be auto generated.', argstr='-pl %s', genfile=True)
    outputRightPialHemisphere = File(
        desc='output pial surface file, right hemisphere. If unspecified, output file name will be auto generated.', argstr='-pr %s', genfile=True)
    verbosity = traits.Int(desc='verbosity (0 = silent)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class HemisplitOutputSpec(TraitedSpec):
    outputLeftHemisphere = File(desc='path/name of left hemisphere')
    outputRightHemisphere = File(desc='path/name of right hemisphere')
    outputLeftPialHemisphere = File(desc='path/name of left pial hemisphere')
    outputRightPialHemisphere = File(desc='path/name of right pial hemisphere')


class Hemisplit(CommandLine):
    """
    Hemisphere splitter
    Splits a surface object into two separate surfaces given an input label volume.
    Each vertex is labeled left or right based on the labels being odd (left) or even (right).
    The largest contour on the split surface is then found and used as the separation between left and right.

    Examples
    --------

    >>> from nipype.interfaces import brainsuite
    >>> from nipype.testing import example_data
    >>> hemisplit = brainsuite.Hemisplit()
    >>> hemisplit.inputs.inputSurfaceFile = 'input_surf.dfs'
    >>> hemisplit.inputs.inputHemisphereLabelFile = 'label.nii'
    >>> hemisplit.inputs.pialSurfaceFile = 'pial.dfs'
    >>> results = hemisplit.run() #doctest: +SKIP

    """

    input_spec = HemisplitInputSpec
    output_spec = HemisplitOutputSpec
    _cmd = 'hemisplit'

    def _gen_filename(self, name):
        inputs = self.inputs.get()
        if isdefined(inputs[name]):
            return os.path.abspath(inputs[name])


        if (name == 'outputLeftHemisphere'
            or name == 'outputRightHemisphere'
            or name == 'outputLeftPialHemisphere'
            or name == 'outputRightPialHemisphere'):
            return getFileName(self, self.inputs.inputSurfaceFile, name, '.dfs')

        return None

    def _list_outputs(self):
        return l_outputs(self)

# used to generate file names for outputs
# removes pathway and extension of inputName, returns concatenation of]
# inputName, command, name, and extension
def getFileName(self, inputName, name, extension):
    fullInput = os.path.basename(inputName)
    dotRegex = regex.compile("[^.]+")
    inputNoExtension = dotRegex.findall(fullInput)[0]
    return os.path.abspath(
        ''.join((inputNoExtension, '_', self._cmd, '_', name, extension)))

def l_outputs(self):
    outputs = self.output_spec().get()
    for key in outputs:
        name = self._gen_filename(key)
        if not name is None:
            outputs[key] = name

    return outputs