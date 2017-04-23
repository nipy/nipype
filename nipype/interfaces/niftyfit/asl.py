# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

"""
The ASL module of niftyfit, which wraps the fitting methods in NiftyFit.
"""

from ..base import TraitedSpec, traits, isdefined, CommandLineInputSpec
from .base import NiftyFitCommand, get_custom_path


class FitAslInputSpec(CommandLineInputSpec):
    """ Input Spec for FitAsl. """
    desc = 'Filename of the 4D ASL (control/label) source image (mandatory).'
    source_file = traits.File(position=1,
                              exists=True,
                              argstr='-source %s',
                              mandatory=True,
                              desc=desc)
    pasl = traits.Bool(desc='Fit PASL ASL data [default]', argstr='-pasl')
    pcasl = traits.Bool(desc='Fit PCASL ASL data', argstr='-pcasl')

    # *** Output options:
    desc = 'Filename of the Cerebral Blood Flow map (in ml/100g/min).'
    cbf_file = traits.File(genfile=True, argstr='-cbf %s', desc=desc)
    desc = 'Filename of the CBF error map.'
    error_file = traits.File(genfile=True, argstr='-error %s', desc=desc)
    desc = 'Filename of the synthetic ASL data.'
    syn_file = traits.File(genfile=True, argstr='-syn %s', desc=desc)

    # *** Input options (see also fit_qt1 for generic T1 fitting):
    desc = 'Filename of the estimated input T1 map (in ms).'
    t1map = traits.File(exists=True, argstr='-t1map %s', desc=desc)
    desc = 'Filename of the estimated input M0 map.'
    m0map = traits.File(exists=True, argstr='-m0map %s', desc=desc)
    desc = 'Filename of the estimated input M0 map error.'
    m0mape = traits.File(exists=True, argstr='-m0mape %s', desc=desc)
    desc = 'Filename of a [1,2,5]s Inversion Recovery volume (T1/M0 fitting \
carried out internally).'
    IRvolume = traits.File(exists=True, argstr='-IRvolume %s', desc=desc)
    desc = 'Output of [1,2,5]s Inversion Recovery fitting.'
    IRoutput = traits.File(exists=True, argstr='-IRoutput %s', desc=desc)

    # *** Experimental options (Choose those suitable for the model!):
    mask = traits.File(position=2,
                       exists=True,
                       desc='Filename of image mask.',
                       argstr='-mask %s')
    T1a = traits.Float(desc='T1 of arterial component [1650ms].',
                       argstr='-T1a %f')
    desc = 'Single plasma/tissue partition coefficient [0.9ml/g].'
    L = traits.Float(desc=desc, argstr='-L %f')
    desc = 'Labelling efficiency [0.99 (pasl), 0.85 (pcasl)], ensure any \
background suppression pulses are included in -eff'
    eff = traits.Float(desc=desc, argstr='-eff %f')
    desc = 'Outlier rejection for multi CL volumes (enter z-score threshold \
(e.g. 2.5)) [off].'
    out = traits.Float(desc=desc, argstr='-out %f')

    # *** PCASL options (Choose those suitable for the model!):
    PLD = traits.Float(desc='Post Labelling Delay [2000ms].', argstr='-PLD %f')
    LDD = traits.Float(desc='Labelling Duration [1800ms].', argstr='-LDD %f')
    desc = 'Difference in labelling delay per slice [0.0 ms/slice.'
    dPLD = traits.Float(desc=desc, argstr='-dPLD %f')

    # *** PASL options (Choose those suitable for the model!):
    Tinv1 = traits.Float(desc='Saturation pulse time [800ms].',
                         argstr='-Tinv1 %f')
    Tinv2 = traits.Float(desc='Inversion time [2000ms].', argstr='-Tinv2 %f')
    desc = 'Difference in inversion time per slice [0ms/slice].'
    dTinv2 = traits.Float(desc=desc, argstr='-dTinv2 %f')

    # *** Other experimental assumptions:

    # Not programmed yet
    # desc = 'Slope and intercept for Arterial Transit Time.'
    # ATT = traits.Float(desc=desc, argstr='-ATT %f')

    gmT1 = traits.Float(desc='T1 of GM [1150ms].', argstr='-gmT1 %f')
    gmL = traits.Float(desc='Plasma/GM water partition [0.95ml/g].',
                       argstr='-gmL %f')
    gmTTT = traits.Float(desc='Time to GM [ATT+0ms].', argstr='-gmTTT %f')
    wmT1 = traits.Float(desc='T1 of WM [800ms].', argstr='-wmT1 %f')
    wmL = traits.Float(desc='Plasma/WM water partition [0.82ml/g].',
                       argstr='-wmL %f')
    wmTTT = traits.Float(desc='Time to WM [ATT+0ms].', argstr='-wmTTT %f')

    # *** Segmentation options:
    desc = 'Filename of the 4D segmentation (in ASL space) for L/T1 \
estimation and PV correction {WM,GM,CSF}.'
    seg = traits.File(exists=True, argstr='-seg %s', desc=desc)
    desc = 'Use sigmoid to estimate L from T1: L(T1|gmL,wmL) [Off].'
    sig = traits.Bool(desc=desc, argstr='-sig')
    desc = 'Simple PV correction (CBF=vg*CBFg + vw*CBFw, with CBFw=f*CBFg) \
[0.25].'
    pv0 = traits.Int(desc=desc, argstr='-pv0 %d')
    pv2 = traits.Int(desc='In plane PV kernel size [3x3].', argstr='-pv2 %d')
    pv3 = traits.Tuple(traits.Int, traits.Int, traits.Int,
                       desc='3D kernel size [3x3x1].',
                       argstr='-pv3 %d %d %d')
    desc = 'Multiply CBF by this value (e.g. if CL are mislabelled use -1.0).'
    mul = traits.Float(desc=desc, argstr='-mul %f')
    mulgm = traits.Bool(desc='Multiply CBF by segmentation [Off].',
                        argstr='-sig')
    desc = 'Set PV threshold for switching off LSQR [O.05].'
    pvthreshold = traits.Bool(desc=desc, argstr='-pvthreshold')
    segstyle = traits.Bool(desc='Set CBF as [gm,wm] not [wm,gm].',
                           argstr='-segstyle')


class FitAslOutputSpec(TraitedSpec):
    """ Output Spec for FitAsl. """
    desc = 'Filename of the Cerebral Blood Flow map (in ml/100g/min).'
    cbf_file = traits.File(exists=True, desc=desc)
    desc = 'Filename of the CBF error map.'
    error_file = traits.File(exists=True, desc=desc)
    desc = 'Filename of the synthetic ASL data.'
    syn_file = traits.File(exists=True, desc=desc)


class FitAsl(NiftyFitCommand):
    """Interface for executable fit_asl from Niftyfit platform.

    Use NiftyFit to perform ASL fitting.

    ASL fitting routines (following EU Cost Action White Paper recommendations)
    Fits Cerebral Blood Flow maps in the first instance.

    For source code, see https://cmiclab.cs.ucl.ac.uk/CMIC/NiftyFit-Release

    Examples
    --------
    >>> from nipype.interfaces.niftyfit import FitAsl
    >>> node = FitAsl()
    >>> node.inputs.source_file = "asl.nii.gz"  # doctest: +SKIP
    >>> node.cmdline  # doctest: +SKIP
    'fit_asl -source asl.nii -cbf asl_cbf.nii.gz -error asl_error.nii.gz \
-syn asl_syn.nii.gz'

    """
    _cmd = get_custom_path('fit_asl')
    input_spec = FitAslInputSpec
    output_spec = FitAslOutputSpec
    _suffix = '_fit_asl'

    def _gen_filename(self, name):
        if name == 'error_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_error', ext='.nii.gz')
        if name == 'syn_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_syn', ext='.nii.gz')
        if name == 'cbf_file':
            return self._gen_fname(self.inputs.source_file,
                                   suffix='_cbf', ext='.nii.gz')
        return None

    def _list_outputs(self):
        outputs = self.output_spec().get()

        if isdefined(self.inputs.error_file):
            outputs['error_file'] = self.inputs.error_file
        else:
            outputs['error_file'] = self._gen_filename('error_file')

        if isdefined(self.inputs.syn_file):
            outputs['syn_file'] = self.inputs.syn_file
        else:
            outputs['syn_file'] = self._gen_filename('syn_file')

        if isdefined(self.inputs.cbf_file):
            outputs['cbf_file'] = self.inputs.cbf_file
        else:
            outputs['cbf_file'] = self._gen_filename('cbf_file')

        return outputs
