# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The ASL module of niftyfit, which wraps the fitting methods in NiftyFit.
"""

from nipype.interfaces.niftyfit.base import NIFTYFITCommandInputSpec, NIFTYFITCommand
from nipype.interfaces.base import (TraitedSpec, File, traits, isdefined)

#-----------------------------------------------------------
# FitAsl wrapper interface
#-----------------------------------------------------------

# Input spec
class FitAslInputSpec(NIFTYFITCommandInputSpec):

    source_file = File(exists=True, desc='Filename of the 4D ASL (control/label) source image (mandatory)',
                       argstr='-source %s', mandatory=True)
    pasl   = traits.Bool(desc='Fit PASL ASL data [default]', argstr='-pasl')
    pcasl  = traits.Bool(desc='Fit PCASL ASL data', argstr='-pcasl')

# *** Output options:
    cbf_file     = File(genfile = True, exists=True, desc='Filename of the Cerebral Blood Flow map (in ml/100g/min).',
                   argstr='-cbf %s', name_source = ['source'], name_template = '%s_cbf')
    error_file   = File(genfile = True, exists=True, desc='Filename of the CBF error map.',
                   argstr='-error %s', name_source = ['source'], name_template = '%s_error')
    syn_file     = File(genfile = True, exists=True, desc='Filename of the synthetic ASL data.',
                   argstr='-syn %s', name_source = ['source'], name_template = '%s_syn')

# *** Input options (see also fit_qt1 for generic T1 fitting):
    t1map = File(exists=True, desc='Filename of the estimated input T1 map (in ms).',
                   argstr='-t1map %s')
    m0map = File(exists=True, desc='Filename of the estimated input M0 map.',
                   argstr='-m0map %s')
    m0mape = File(exists=True, desc='Filename of the estimated input M0 map error.',
                   argstr='-m0mape %s')
    IRvolume = File(exists=True, desc='Filename of a [1,2,5]s Inversion Recovery volume (T1/M0 fitting carried out internally).',
                   argstr='-IRvolume %s')
    IRoutput = File(exists=True, desc='Output of [1,2,5]s Inversion Recovery fitting.',
                   argstr='-IRoutput %s')

# *** Experimental options (Choose those suitable for the model!):
    mask  = File(exists=True, desc='Filename of image mask.',
                   argstr='-source %s')
    T1a  = traits.Float(desc='T1 of arterial component [1650ms].',
                        argstr = '-T1a %f')
    L    = traits.Float(desc='Single plasma/tissue partition coefficient [0.9ml/g].',
                        argstr = '-L %f')
    eff  = traits.Float(desc='Labelling efficiency [0.99 (pasl), 0.85 (pcasl)], ensure any background suppression pulses are included in -eff',
                        argstr = '-eff %f')
    out  = traits.Float(desc='Outlier rejection for multi CL volumes (enter z-score threshold (e.g. 2.5)) [off].',
                        argstr = '-out %f')

# *** PCASL options (Choose those suitable for the model!):
    PLD = traits.Float(desc='Post Labelling Delay [2000ms].',
                        argstr = '-PLD %f')
    LDD = traits.Float(desc='Labelling Duration [1800ms].',
                        argstr = '-LDD %f')

# *** PASL options (Choose those suitable for the model!):
    Tinv1 = traits.Float(desc='Saturation pulse time [800ms].',
                        argstr = '-Tinv1 %f')
    Tinv2 = traits.Float(desc='Inversion time [2000ms].',
                        argstr = '-Tinv2 %f')

# *** Other experimental assumptions:
    ATT   = traits.Float(desc='Slope and intercept for Arterial Transit Time [0ms/slice 1000ms].',
                        argstr = '-ATT %f')
    gmT1  = traits.Float(desc='T1 of GM [1150ms].',
                        argstr = '-gmT1 %f')
    gmL   = traits.Float(desc='Plasma/GM water partition [0.95ml/g].',
                        argstr = '-gmL %f')
    gmTTT = traits.Float(desc='Time to GM [ATT+0ms].',
                        argstr = '-gmTTT %f')
    wmT1  = traits.Float(desc='T1 of WM [800ms].',
                        argstr = '-wmT1 %f')
    wmL   = traits.Float(desc='Plasma/WM water partition [0.82ml/g].',
                        argstr = '-wmL %f')
    wmTTT = traits.Float(desc='Time to WM [ATT+0ms].',
                        argstr = '-wmTTT %f')

# *** Segmentation options:
    seg   = File(exists=True, desc='Filename of the 4D segmentation (in ASL space) for L/T1 estimation and PV correction {WM,GM,CSF}.',
                 argstr = '-seg %s')
    sig   = traits.Bool(desc='Use sigmoid to estimate L from T1: L(T1|gmL,wmL) [Off].',
                     argstr = '-sig')
    pv2 = traits.Int(desc = 'In plane PV kernel size [3x3].',
                     argstr = 'pv2 %d')
    pv3  = traits.Int(desc = '3D kernel size [3x3x1].',
                      argstr = 'pv3 %d')
    mul = traits.Float(desc='Multiply CBF by this value (e.g. if CL are mislabelled use -1.0)...',
                        argstr = '-mul %f')
    mulgm       = traits.Bool(desc='Multiply CBF by segmentation [Off].',
                              argstr = '-sig')
    pvthreshold = traits.Bool(desc='Set PV threshold for switching off LSQR [O.05].',
                              argstr = '-pvthreshold')
    segstyle    = traits.Bool(desc='Set CBF as [gm,wm] not [wm,gm].',
                              argstr = '-segstyle')

# Output spec
class FitAslOutputSpec(TraitedSpec):
    cbf_file     = File(exists=True, desc='Filename of the Cerebral Blood Flow map (in ml/100g/min).')
    error_file   = File(exists=True, desc='Filename of the CBF error map.')
    syn_file     = File(exists=True, desc='Filename of the synthetic ASL data.')

# FitAsl function
class FitAsl(NIFTYFITCommand):
    """ Use NiftyFit to perform ASL fitting.
    
    Examples
    --------
    
    >>> from nipype.interfaces import niftyfit
    """
    _cmd = 'fit_asl'
    input_spec = FitAslInputSpec
    output_spec = FitAslOutputSpec
    
    _suffix = '_fit_asl'
