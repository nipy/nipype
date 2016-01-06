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


class bseInputSpec(CommandLineInputSpec):

    inputMRIFile = File(exists=True, mandatory=True, argstr='-i %s',
                        desc='input MRI volume', position=0)
    outputMRIVolume = File(mandatory=False,
                           desc='output brain-masked MRI volume. If'
                                'unspecified, output file name will be auto'
                                'generated.',
                           argstr='-o %s', position=1, hash_files=False,
                           genfile=True)
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
    outputMaskFile = File(mandatory=False, desc='save smooth brain mask',
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
    noRotate = traits.Bool(True, usedefault=True,
                           desc='retain original orientation'
                           '(default behavior will auto-rotate input NII files'
                           'to LPI orientation)', argstr='--norotate')
    timer = traits.Bool(desc='show timing', argstr='--timer')


class bseOutputSpec(TraitedSpec):
    outputMRIVolume = File(desc='path/name of brain-masked MRI volume')
    outputMaskFile = File(desc='path/name of smooth brain mask')
    outputDiffusionFilter = File(desc='path/name of diffusion filter output')
    outputEdgeMap = File(desc='path/name of edge map output')
    outputDetailedBrainMask = File(desc='path/name of detailed brain mask')
    outputCortexFile = File(desc='path/name of cortex file')


class bse(CommandLine):
    input_spec = bseInputSpec
    output_spec = bseOutputSpec
    _cmd = 'bse'

    def _list_outputs(self):

        outputs = self.output_spec().get()
        if isdefined(self.inputs.outputMRIVolume):
            outputs['outputMRIVolume'] = (os.getcwd() + '/' +
                                          self.inputs.outputMRIVolume)
        else:
            outputs['outputMRIVolume'] = self._gen_filename('outputMRIVolume')

        if isdefined(self.inputs.outputMaskFile):
            outputs['outputMaskFile'] = (os.getcwd() + '/' +
                                         self.inputs.outputMaskFile)
        if isdefined(self.inputs.outputDiffusionFilter):
            outputs['outputDiffusionFilter'] = (os.getcwd() + '/' +
                                                self.inputs.outputDiffusionFilter)
        if isdefined(self.inputs.outputEdgeMap):
            outputs['outputEdgeMap'] = (os.getcwd() + '/' +
                                        self.inputs.outputEdgeMap)
        if isdefined(self.inputs.outputDetailedBrainMask):
            outputs['outputDetailedBrainMask'] = (os.getcwd() + '/' +
                                                  self.inputs.outputDetailedBrainMask)
        if isdefined(self.inputs.outputCortexFile):
            outputs['outputCortexFile'] = (os.getcwd() + '/' +
                                           self.inputs.outputCortexFile)

        return outputs

    def _gen_filename(self, name):
        if name == 'outputMRIVolume':
            myExtension = '.nii.gz'
            return ''.join((os.getcwd(), '/',
                            getFileName(self.inputs.inputMRIFile),
                            "___", self._cmd, 'Output_', name, myExtension))


class bfcInputSpec(CommandLineInputSpec):
    inputMRIFile = File(exists=True, mandatory=True,
                        desc='input skull-stripped MRI volume',
                        argstr='-i %s', position=0)
    outputMRIVolume = File(mandatory=False,
                           desc='output bias-corrected MRI volume.'
                                'If unspecified, output file name'
                                'will be auto generated.', argstr='-o %s',
                           position=1, hash_files=False, genfile=True)
    outputMaskFile = File(desc='mask file', argstr='-m %s', hash_files=False)
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
        desc='bias estimate convergence threshold (values > 0.1 disable)',
        argstr='--beps %f')
    verbosityLevel = traits.Int(
        desc='verbosity level (0=silent)',
        argstr='-v %d')
    timer = traits.Bool(desc='display timing information', argstr='--timer')


class bfcOutputSpec(TraitedSpec):
    outputMRIVolume = File(desc='path/name of output file')
    outputMaskFile = File(desc='path/name of mask output file')
    outputBiasField = File(desc='path/name of bias field output file')
    outputMaskedBiasField = File(desc='path/name of masked bias field output')
    correctionScheduleFile = File(desc='path/name of schedule file')


class bfc(CommandLine):
    input_spec = bfcInputSpec
    output_spec = bfcOutputSpec
    _cmd = 'bfc'

    def _gen_filename(self, name):
        if name == 'outputMRIVolume':
            myExtension = '.nii.gz'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputMRIFile),
                            "___", self._cmd, 'Output_', name, myExtension))

    def _format_arg(self, name, spec, value):
        if name == 'histogramType':
            return spec.argstr % {
                "ellipse": "--ellipse", "block": "--block"}[value]
        if name == 'biasRange':
            return spec.argstr % {"low": "--low",
                                  "medium": "--medium", "high": "--high"}[value]
        if name == 'intermediate_file_type':
            return spec.argstr % {"analyze": "--analyze", "nifti": "--nifti",
                                  "gzippedAnalyze": "--analyzegz", "gzippedNifti": "--niftigz"}[value]

        return super(bfc, self)._format_arg(name, spec, value)

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.outputMRIVolume):
            outputs['outputMRIVolume'] = (
                os.getcwd() + '/' + self.inputs.outputMRIVolume)
        else:
            outputs['outputMRIVolume'] = self._gen_filename('outputMRIVolume')

        if isdefined(self.inputs.outputMaskFile):
            outputs['outputMaskFile'] = (
                os.getcwd() + '/' + self.inputs.outputMaskFile)
        if isdefined(self.inputs.outputBiasField):
            outputs['outputBiasField'] = (
                os.getcwd() + '/' + self.inputs.outputBiasField)
        if isdefined(self.inputs.outputMaskedBiasField):
            outputs['outputMaskedBiasField'] = (
                os.getcwd() + '/' + self.inputs.outputMaskedBiasField)
        if isdefined(self.inputs.correctionScheduleFile):
            outputs['correctionScheduleFile'] = (
                os.getcwd() + '/' + self.inputs.correctionScheduleFile)

        return outputs


class pvcInputSpec(CommandLineInputSpec):
    inputMRIFile = File(mandatory=True, desc='MRI file', argstr='-i %s')
    inputMaskFile = File(desc='brain mask file', argstr='-m %s')
    outputLabelFile = File(
        mandatory=False,
        desc='output label file. If unspecified, output file name will be auto generated.',
        argstr='-o %s',
        genfile=True)
    outputTissueFractionFile = File(
        mandatory=False,
        desc='output tissue fraction file',
        argstr='-f %s',
        genfile=True)
    spatialPrior = traits.Float(desc='spatial prior strength', argstr='-l %f')
    verbosity = traits.Int(desc='verbosity level (0 = silent)', argstr='-v %d')
    threeClassFlag = traits.Bool(
        desc='use a three-class (CSF=0,GM=1,WM=2) labeling',
        argstr='-3')
    timer = traits.Bool(desc='time processing', argstr='--timer')


class pvcOutputSpec(TraitedSpec):
    outputLabelFile = File(desc='path/name of label file')
    outputTissueFractionFile = File(desc='path/name of tissue fraction file')


class pvc(CommandLine):
    input_spec = pvcInputSpec
    output_spec = pvcOutputSpec
    _cmd = 'pvc'

    def _gen_filename(self, name):
        if name == 'outputLabelFile':
            myExtension = '.nii.gz'
            return ''.join((os.getcwd(), '/', self._cmd,
                            'Output_', name, myExtension))
        if name == 'outputTissueFractionFile':
            myExtension = '.nii.gz'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputMRIFile),
                            "___", self._cmd, 'Output_', name, myExtension))

    def _list_outputs(self):

        outputs = self.output_spec().get()
        if isdefined(self.inputs.outputLabelFile):
            outputs['outputLabelFile'] = (
                os.getcwd() + '/' + self.inputs.outputLabelFile)
        else:
            outputs['outputLabelFile'] = self._gen_filename('outputLabelFile')

        if isdefined(self.inputs.outputTissueFractionFile):
            outputs['outputTissueFractionFile'] = (
                os.getcwd() + '/' + self.inputs.outputTissueFractionFile)
        else:
            outputs['outputTissueFractionFile'] = self._gen_filename(
                'outputTissueFractionFile')

        return outputs


class cerebroInputSpec(CommandLineInputSpec):
    inputMRIFile = File(
        mandatory=True,
        desc='input 3D MRI volume',
        argstr='-i %s')
    inputAtlasMRIFile = File(
        mandatory=True,
        desc='atlas MRI volume',
        argstr='--atlas %s')
    inputAtlasLabelFile = File(
        mandatory=True,
        desc='atlas labeling',
        argstr='--atlaslabels %s')
    inputBrainMaskFile = File(desc='brain mask file', argstr='-m %s')
    outputCerebrumMaskFile = File(
        mandatory=False,
        desc='output cerebrum mask volume. If unspecified, output file name will be auto generated.',
        argstr='-o %s',
        genfile=True)
    outputLabelMaskFile = File(
        mandatory=False,
        desc='output labeled hemisphere/cerebrum volume. If unspecified, output file name will be auto generated.',
        argstr='-l %s',
        genfile=True)
    costFunction = traits.Int(2, usedefault=True, desc='0,1,2', argstr='-c %d')
    useCentroids = traits.Bool(
        desc='use centroids of data to initialize position',
        argstr='--centroids')
    outputAffineTransformFile = File(
        desc='save affine transform to file.',
        argstr='--air %s')
    outputWarpTransformFile = File(
        desc='save warp transform to file.',
        argstr='--warp %s')
    verbosity = traits.Int(desc='verbosity level (0=silent)', argstr='-v %d')
    linearConvergence = traits.Float(
        desc='linear convergence',
        argstr='--linconv %f')
    warpLabel = traits.Int(
        desc='warp order (2,3,4,5,6,7,8)',
        argstr='--warplevel %d')
    warpConvergence = traits.Float(
        desc='warp convergence',
        argstr='--warpconv %f')
    keepTempFiles = traits.Bool(
        desc="don't remove temporary files",
        argstr='--keep')
    tempDirectory = traits.Str(
        desc='specify directory to use for temporary files',
        argstr='--tempdir %s')
    tempDirectoryBase = traits.Str(
        desc='create a temporary directory within this directory',
        argstr='--tempdirbase %s')


class cerebroOutputSpec(TraitedSpec):
    outputCerebrumMaskFile = File(desc='path/name of cerebrum mask file')
    outputLabelMaskFile = File(desc='path/name of label mask file')
    outputAffineTransformFile = File(desc='path/name of affine transform file')
    outputWarpTransformFile = File(desc='path/name of warp transform file')


class cerebro(CommandLine):
    input_spec = cerebroInputSpec
    output_spec = cerebroOutputSpec
    _cmd = 'cerebro'

    def _gen_filename(self, name):
        if name == 'outputCerebrumMaskFile':
            myExtension = '.nii.gz'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputMRIFile),
                            "___", self._cmd, 'Output_', name, myExtension))
        if name == 'outputLabelMaskFile':
            myExtension = '.nii.gz'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputMRIFile),
                            "___", self._cmd, 'Output_', name, myExtension))

    def _list_outputs(self):

        outputs = self.output_spec().get()
        if isdefined(self.inputs.outputCerebrumMaskFile):
            outputs['outputCerebrumMaskFile'] = (
                os.getcwd() + '/' + self.inputs.outputCerebrumMaskFile)
        else:
            outputs['outputCerebrumMaskFile'] = self._gen_filename(
                'outputCerebrumMaskFile')

        if isdefined(self.inputs.outputLabelMaskFile):
            outputs['outputLabelMaskFile'] = (
                os.getcwd() + '/' + self.inputs.outputLabelMaskFile)
        else:
            outputs['outputLabelMaskFile'] = self._gen_filename(
                'outputLabelMaskFile')

        if isdefined(self.inputs.outputAffineTransformFile):
            outputs['outputAffineTransformFile'] = (
                os.getcwd() + '/' + self.inputs.outputAffineTransformFile)
        if isdefined(self.inputs.outputWarpTransformFile):
            outputs['outputWarpTransformFile'] = (
                os.getcwd() + '/' + self.inputs.outputWarpTransformFile)

        return outputs


class cortexInputSpec(CommandLineInputSpec):
    inputHemisphereLabelFile = File(
        mandatory=True,
        desc='hemisphere / lobe label volume',
        argstr='-h %s')
    outputCerebrumMask = File(
        mandatory=False,
        desc='output structure mask. If unspecified, output file name will be auto generated.',
        argstr='-o %s',
        genfile=True)
    inputTissueFractionFile = File(
        mandatory=True,
        desc='tissue fraction file (32-bit float)',
        argstr='-f %s')
    tissueFractionThreshold = traits.Float(
        50.0,
        usedefault=True,
        desc='tissue fraction threshold (percentage)',
        argstr='-p %f')
    computeWGBoundary = traits.Bool(
        True,
        usedefault=True,
        desc='compute WM/GM boundary',
        argstr='-w')
    computeGCBoundary = traits.Bool(
        desc='compute GM/CSF boundary', argstr='-g')
    includeAllSubcorticalAreas = traits.Bool(
        True,
        usedefault=True,
        esc='include all subcortical areas in WM mask',
        argstr='-a')
    verbosity = traits.Int(desc='verbosity level', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class cortexOutputSpec(TraitedSpec):
    outputCerebrumMask = File(desc='path/name of cerebrum mask')


class cortex(CommandLine):
    input_spec = cortexInputSpec
    output_spec = cortexOutputSpec
    _cmd = 'cortex'

    def _gen_filename(self, name):
        if name == 'outputCerebrumMask':
            myExtension = '.nii.gz'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputHemisphereLabelFile),
                            "___", self._cmd, 'Output_', name, myExtension))

    def _list_outputs(self):

        outputs = self.output_spec().get()
        if isdefined(self.inputs.outputCerebrumMask):
            outputs['outputCerebrumMask'] = (
                os.getcwd() + '/' + self.inputs.outputCerebrumMask)
        else:
            outputs['outputCerebrumMask'] = self._gen_filename(
                'outputCerebrumMask')

        return outputs


class scrubmaskInputSpec(CommandLineInputSpec):
    inputMaskFile = File(
        mandatory=True,
        desc='input structure mask file',
        argstr='-i %s')
    outputMaskFile = File(
        mandatory=False,
        desc='output structure mask file. If unspecified, output file name will be auto generated.',
        argstr='-o %s',
        genfile=True)
    backgroundFillThreshold = traits.Int(
        2,
        usedefault=True,
        desc='background fill threshold',
        argstr='-b %d')
    foregroundTrimThreshold = traits.Int(
        0,
        usedefault=True,
        desc='foreground trim threshold',
        argstr='-f %d')
    numberIterations = traits.Int(desc='number of iterations', argstr='-n %d')
    verbosity = traits.Int(desc='verbosity (0=silent)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class scrubmaskOutputSpec(TraitedSpec):
    outputMaskFile = File(desc='path/name of mask file')


class scrubmask(CommandLine):
    input_spec = scrubmaskInputSpec
    output_spec = scrubmaskOutputSpec
    _cmd = 'scrubmask'

    def _gen_filename(self, name):
        if name == 'outputMaskFile':
            myExtension = '.nii.gz'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputMaskFile),
                            "___", self._cmd, 'Output_', name, myExtension))

    def _list_outputs(self):

        outputs = self.output_spec().get()
        if isdefined(self.inputs.outputMaskFile):
            outputs['outputMaskFile'] = (
                os.getcwd() + '/' + self.inputs.outputMaskFile)
        else:
            outputs['outputMaskFile'] = self._gen_filename('outputMaskFile')

        return outputs


class tcaInputSpec(CommandLineInputSpec):
    inputMaskFile = File(
        mandatory=True,
        desc='input mask volume',
        argstr='-i %s')
    outputMaskFile = File(
        mandatory=False,
        desc='output mask volume. If unspecified, output file name will be auto generated.',
        argstr='-o %s',
        genfile=True)
    minCorrectionSize = traits.Int(
        2500,
        usedefault=True,
        desc='maximum correction size',
        argstr='-m %d')
    maxCorrectionSize = traits.Int(
        desc='minimum correction size',
        argstr='-n %d')
    foregroundDelta = traits.Int(
        20,
        usedefault=True,
        desc='foreground delta',
        argstr='--delta %d')
    verbosity = traits.Int(desc='verbosity (0 = quiet)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class tcaOutputSpec(TraitedSpec):
    outputMaskFile = File(desc='path/name of mask file')


class tca(CommandLine):
    input_spec = tcaInputSpec
    output_spec = tcaOutputSpec
    _cmd = 'tca'

    def _gen_filename(self, name):
        if name == 'outputMaskFile':
            myExtension = '.nii.gz'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputMaskFile),
                            "___", self._cmd, 'Output_', name, myExtension))

    def _list_outputs(self):

        outputs = self.output_spec().get()
        if isdefined(self.inputs.outputMaskFile):
            outputs['outputMaskFile'] = (
                os.getcwd() + '/' + self.inputs.outputMaskFile)
        else:
            outputs['outputMaskFile'] = self._gen_filename('outputMaskFile')

        return outputs


class dewispInputSpec(CommandLineInputSpec):
    inputMaskFile = File(mandatory=True, desc='input file', argstr='-i %s')
    outputMaskFile = File(
        mandatory=False,
        desc='output file. If unspecified, output file name will be auto generated.',
        argstr='-o %s',
        genfile=True)
    verbosity = traits.Int(desc='verbosity', argstr='-v %d')
    sizeThreshold = traits.Int(desc='size threshold', argstr='-t %d')
    maximumIterations = traits.Int(
        desc='maximum number of iterations',
        argstr='-n %d')
    timer = traits.Bool(desc='time processing', argstr='--timer')


class dewispOutputSpec(TraitedSpec):
    outputMaskFile = File(desc='path/name of mask file')


class dewisp(CommandLine):
    input_spec = dewispInputSpec
    output_spec = dewispOutputSpec
    _cmd = 'dewisp'

    def _gen_filename(self, name):
        if name == 'outputMaskFile':
            myExtension = '.nii.gz'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputMaskFile),
                            "___", self._cmd, 'Output_', name, myExtension))

    def _list_outputs(self):

        outputs = self.output_spec().get()
        if isdefined(self.inputs.outputMaskFile):
            outputs['outputMaskFile'] = (
                os.getcwd() + '/' + self.inputs.outputMaskFile)
        else:
            outputs['outputMaskFile'] = self._gen_filename('outputMaskFile')

        return outputs


class dfsInputSpec(CommandLineInputSpec):
    inputVolumeFile = File(
        mandatory=True,
        desc='input 3D volume',
        argstr='-i %s')
    outputSurfaceFile = File(
        mandatory=False,
        desc='output surface mesh file. If unspecified, output file name will be auto generated.',
        argstr='-o %s',
        genfile=True)
    inputShadingVolume = File(
        desc='shade surface model with data from image volume',
        argstr='-c %s')
    smoothingIterations = traits.Int(
        10,
        usedefault=True,
        desc='number of smoothing iterations',
        argstr='-n %d')
    smoothingConstant = traits.Float(
        0.5,
        usedefault=True,
        desc='smoothing constant',
        argstr='-a %f')
    curvatureWeighting = traits.Float(
        5.0,
        usedefault=True,
        desc='curvature weighting',
        argstr='-w %f')
    scalingPercentile = traits.Float(desc='scaling percentile', argstr='-f %f')
    nonZeroTessellation = traits.Bool(
        desc='tessellate non-zero voxels',
        argstr='-nz',
        xor=(
            'nonZeroTessellation',
            'specialTessellation'))
    tessellationThreshold = traits.Float(
        desc='To be used with specialTessellation. Set this value first, then set specialTessellation value.\nUsage: tessellate voxels greater_than, less_than, or equal_to <tessellationThreshold>',
        argstr='%f')
    specialTessellation = traits.Enum(
        'greater_than',
        'less_than',
        'equal_to',
        desc='To avoid throwing a UserWarning, set tessellationThreshold first. Then set this attribute.\nUsage: tessellate voxels greater_than, less_than, or equal_to <tessellationThreshold>',
        argstr='%s',
        xor=(
            'nonZeroTessellation',
            'specialTessellation'),
        requires=['tessellationThreshold'],
        position=-
        1)
    zeroPadFlag = traits.Bool(
        desc='zero-pad volume (avoids clipping at edges)',
        argstr='-z')
    noNormalsFlag = traits.Bool(
        desc='do not compute vertex normals',
        argstr='--nonormals')
    postSmoothFlag = traits.Bool(
        desc='smooth vertices after coloring',
        argstr='--postsmooth')
    verbosity = traits.Int(desc='verbosity (0 = quiet)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class dfsOutputSpec(TraitedSpec):
    outputSurfaceFile = File(desc='path/name of surface file')


class dfs(CommandLine):
    input_spec = dfsInputSpec
    output_spec = dfsOutputSpec
    _cmd = 'dfs'

    def _format_arg(self, name, spec, value):
        if name == 'tessellationThreshold':
            return ''  # blank argstr
        if name == 'specialTessellation':
            threshold = self.inputs.tessellationThreshold
            return spec.argstr % {"greater_than": ''.join(("-gt %f" % threshold)), "less_than": ''.join(
                ("-lt %f" % threshold)), "equal_to": ''.join(("-eq %f" % threshold))}[value]
        return super(dfs, self)._format_arg(name, spec, value)

    def _gen_filename(self, name):
        if name == 'outputSurfaceFile':
            myExtension = '.dfs'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputVolumeFile),
                            "___", self._cmd, 'Output_', name, myExtension))

    def _list_outputs(self):

        outputs = self.output_spec().get()
        if isdefined(self.inputs.outputSurfaceFile):
            outputs['outputSurfaceFile'] = (
                os.getcwd() + '/' + self.inputs.outputSurfaceFile)
        else:
            outputs['outputSurfaceFile'] = self._gen_filename(
                'outputSurfaceFile')

        return outputs


class pialmeshInputSpec(CommandLineInputSpec):
    inputSurfaceFile = File(mandatory=True, desc='input file', argstr='-i %s')
    outputSurfaceFile = File(
        mandatory=False,
        desc='output file. If unspecified, output file name will be auto generated.',
        argstr='-o %s',
        genfile=True)
    verbosity = traits.Int(desc='verbosity', argstr='-v %d')
    inputTissueFractionFile = File(
        mandatory=True,
        desc='floating point (32) tissue fraction image',
        argstr='-f %s')
    numIterations = traits.Int(
        100,
        usedefault=True,
        desc='number of iterations',
        argstr='-n %d')
    searchRadius = traits.Float(
        1,
        usedefault=True,
        desc='search radius',
        argstr='-r %f')
    stepSize = traits.Float(
        0.4,
        usedefault=True,
        desc='step size',
        argstr='-s %f')
    inputMaskFile = File(
        mandatory=True,
        desc='restrict growth to mask file region',
        argstr='-m %s')
    maxThickness = traits.Float(
        20,
        usedefault=True,
        desc='maximum allowed tissue thickness',
        argstr='--max %f')
    tissueThreshold = traits.Float(
        1.05,
        usedefault=True,
        desc='tissue threshold',
        argstr='-t %f')
# output interval is not an output -- it specifies how frequently the
# output surfaces are generated
    outputInterval = traits.Int(
        10,
        usedefault=True,
        desc='output interval',
        argstr='--interval %d')
    exportPrefix = traits.Str(
        desc='prefix for exporting surfaces if interval is set',
        argstr='--prefix %s')
    laplacianSmoothing = traits.Float(
        0.025,
        usedefault=True,
        desc='apply Laplacian smoothing',
        argstr='--smooth %f')
    timer = traits.Bool(desc='show timing', argstr='--timer')
    recomputNormals = traits.Bool(
        desc='recompute normals at each iteration',
        argstr='--norm')
    normalSmoother = traits.Float(
        0.2,
        usedefault=True,
        desc='strength of normal smoother.',
        argstr='--nc %f')
    tangentSmoother = traits.Float(
        desc='strength of tangential smoother.',
        argstr='--tc %f')


class pialmeshOutputSpec(TraitedSpec):
    outputSurfaceFile = File(desc='path/name of surface file')


class pialmesh(CommandLine):
    input_spec = pialmeshInputSpec
    output_spec = pialmeshOutputSpec
    _cmd = 'pialmesh'

    def _gen_filename(self, name):
        if name == 'outputSurfaceFile':
            myExtension = '.dfs'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputSurfaceFile),
                            "___", self._cmd, 'Output_', name, myExtension))

    def _list_outputs(self):

        outputs = self.output_spec().get()
        if isdefined(self.inputs.outputSurfaceFile):
            outputs['outputSurfaceFile'] = (
                os.getcwd() + '/' + self.inputs.outputSurfaceFile)
        else:
            outputs['outputSurfaceFile'] = self._gen_filename(
                'outputSurfaceFile')

        return outputs


class skullfinderInputSpec(CommandLineInputSpec):
    inputMRIFile = File(mandatory=True, desc='input file', argstr='-i %s')
    inputMaskFile = File(
        mandatory=True,
        desc='A brain mask file, 8-bit image (0=non-brain, 255=brain)',
        argstr='-m %s')
    outputLabelFile = File(
        mandatory=False,
        desc='output file. If unspecified, output file name will be auto generated.',
        argstr='-o %s',
        genfile=True)
    verbosity = traits.Int(desc='verbosity', argstr='-v %d')
    lowerThreshold = traits.Int(
        desc='Lower threshold for segmentation',
        argstr='-l %d')
    upperThreshold = traits.Int(
        desc='Upper threshold for segmentation',
        argstr='-u %d')
    surfaceFilePrefix = traits.Str(
        desc='if specified, generate surface files for brain, skull, and scalp',
        argstr='-s %s')
    bgLabelValue = traits.Int(
        desc='background label value (0-255)',
        argstr='--bglabel %d')
    scalpLabelValue = traits.Int(
        desc='scalp label value (0-255)',
        argstr='--scalplabel %d')
    skullLabelValue = traits.Int(
        desc='skull label value (0-255)',
        argstr='--skulllabel %d')
    spaceLabelValue = traits.Int(
        desc='space label value (0-255)',
        argstr='--spacelabel %d')
    brainLabelValue = traits.Int(
        desc='brain label value (0-255)',
        argstr='--brainlabel %d')
    performFinalOpening = traits.Bool(
        desc='perform a final opening operation on the scalp mask',
        argstr='--finalOpening')


class skullfinderOutputSpec(TraitedSpec):
    outputLabelFile = File(desc='path/name of label file')


class skullfinder(CommandLine):
    input_spec = skullfinderInputSpec
    output_spec = skullfinderOutputSpec
    _cmd = 'skullfinder'

    def _gen_filename(self, name):
        if name == 'outputLabelFile':
            myExtension = '.nii.gz'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputMRIFile),
                            "___", self._cmd, 'Output_', name, myExtension))

    def _list_outputs(self):

        outputs = self.output_spec().get()
        if isdefined(self.inputs.outputLabelFile):
            outputs['outputLabelFile'] = (
                os.getcwd() + '/' + self.inputs.outputLabelFile)
        else:
            outputs['outputLabelFile'] = self._gen_filename('outputLabelFile')

        return outputs


class hemisplitInputSpec(CommandLineInputSpec):
    inputSurfaceFile = File(
        mandatory=True,
        desc='input surface',
        argstr='-i %s')
    inputHemisphereLabelFile = File(
        mandatory=True,
        desc='input hemisphere label volume',
        argstr='-l %s')
    outputLeftHemisphere = File(
        mandatory=False,
        desc='output surface file, left hemisphere. If unspecified, output file name will be auto generated.',
        argstr='--left %s',
        genfile=True)
    outputRightHemisphere = File(
        mandatory=False,
        desc='output surface file, right hemisphere. If unspecified, output file name will be auto generated.',
        argstr='--right %s',
        genfile=True)
    pialSurfaceFile = File(
        desc='pial surface file -- must have same geometry as input surface',
        argstr='-p %s')
    outputLeftPialHemisphere = File(
        mandatory=False,
        desc='output pial surface file, left hemisphere. If unspecified, output file name will be auto generated.',
        argstr='-pl %s',
        genfile=True)
    outputRightPialHemisphere = File(
        mandatory=False,
        desc='output pial surface file, right hemisphere. If unspecified, output file name will be auto generated.',
        argstr='-pr %s',
        genfile=True)
    verbosity = traits.Int(desc='verbosity (0 = silent)', argstr='-v %d')
    timer = traits.Bool(desc='timing function', argstr='--timer')


class hemisplitOutputSpec(TraitedSpec):
    outputLeftHemisphere = File(desc='path/name of left hemisphere')
    outputRightHemisphere = File(desc='path/name of right hemisphere')
    outputLeftPialHemisphere = File(desc='path/name of left pial hemisphere')
    outputRightPialHemisphere = File(desc='path/name of right pial hemisphere')


class hemisplit(CommandLine):
    input_spec = hemisplitInputSpec
    output_spec = hemisplitOutputSpec
    _cmd = 'hemisplit'

    def _gen_filename(self, name):
        if name == 'outputLeftHemisphere':
            myExtension = '.dfs'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputSurfaceFile),
                            "___", self._cmd, 'Output_', name, myExtension))
        if name == 'outputRightHemisphere':
            myExtension = '.dfs'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputSurfaceFile),
                            "___", self._cmd, 'Output_', name, myExtension))
        if name == 'outputLeftPialHemisphere':
            myExtension = '.dfs'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputSurfaceFile),
                            "___", self._cmd, 'Output_', name, myExtension))
        if name == 'outputRightPialHemisphere':
            myExtension = '.dfs'
            return ''.join((os.getcwd(), '/', getFileName(self.inputs.inputSurfaceFile),
                            "___", self._cmd, 'Output_', name, myExtension))

    def _list_outputs(self):

        outputs = self.output_spec().get()
        if isdefined(self.inputs.outputLeftHemisphere):
            outputs['outputLeftHemisphere'] = (os.getcwd() + '/' +
                                               self.inputs.outputLeftHemisphere)
        else:
            outputs['outputLeftHemisphere'] = self._gen_filename(
                'outputLeftHemisphere')

        if isdefined(self.inputs.outputRightHemisphere):
            outputs['outputRightHemisphere'] = (os.getcwd() + '/' +
                                                self.inputs.outputRightHemisphere)
        else:
            outputs['outputRightHemisphere'] = self._gen_filename(
                'outputRightHemisphere')

        if isdefined(self.inputs.outputLeftPialHemisphere):
            outputs['outputLeftPialHemisphere'] = (
                os.getcwd() + '/' + self.inputs.outputLeftPialHemisphere)
        if isdefined(self.inputs.outputRightPialHemisphere):
            outputs['outputRightPialHemisphere'] = (
                os.getcwd() + '/' + self.inputs.outputRightPialHemisphere)

        return outputs


# removes directory of a pathway to a file, removes extension, returns file name
# up to first occurence of three consecutive underscore characters (if any)
# ex: /home/abc/testData___bseOutput_output_file.nii.gz --> testData
def getFileName(string):
    underscoreRegex = regex.compile("[_]{3}")
    dotRegex = regex.compile("[^.]+")
    slashRegex = regex.compile("[^/]+")
    arr = underscoreRegex.split(string)
    arr2 = dotRegex.findall(arr[0])
    arr3 = slashRegex.findall(arr2[0])
    return arr3[len(arr3) - 1]
