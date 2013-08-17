"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""
import os

from nipype.interfaces.base import (CommandLineInputSpec, CommandLine, traits,
                                    TraitedSpec, File, StdOutCommandLine,
                                    StdOutCommandLineInputSpec, isdefined)
from nipype.utils.filemanip import split_filename

class SFPICOCalibDataInputSpec(StdOutCommandLineInputSpec):
    snr = traits.Float(argstr='-snr %f', units='NA',
                       desc='Specifies  the  signal-to-noise ratio of the' \
                            'non-diffusion-weighted measurements to use in simulations.')
    scheme_file = File(exists=True, argstr='-schemefile %s', mandatory=True,
                  desc='Specifies the scheme file for the diffusion MRI data')
    info_file = File(desc='The name to be given to the information output filename.',
                     argstr='-infooutputfile %s', genfile=True, hash_files=False) # Genfile and hash_files?
    trace = traits.Float(argstr='-trace %f', units='NA',
                         desc='Trace of the diffusion tensor(s) used in the test function.')       
    onedtfarange = traits.List(traits.Float, argstr='-onedtfarange %s', 
                               minlen=2, maxlen=2, units='NA',
                               desc = 'Minimum and maximum FA for the single tensor' \
                                      'synthetic data.')
    onedtfastep = traits.Float(argstr='-onedtfastep %f', units='NA',
                               desc='FA step size controlling how many steps there are' \
                                    'between the minimum and maximum FA settings.')
    twodtfarange = traits.List(traits.Float, argstr='-twodtfarange %s', 
                               minlen=2, maxlen=2, units='NA',
                               desc = 'Minimum and maximum FA for the two tensor' \
                                      'synthetic data. FA is varied for both tensors'\
                                      'to give all the different permutations.')
    twodtfastep = traits.Float(argstr='-twodtfastep %f', units='NA',
                               desc='FA step size controlling how many steps there are' \
                                    'between the minimum and maximum FA settings' \
                                    'for the two tensor cases.')
    twodtanglerange = traits.List(traits.Float, argstr='-twodtanglerange %s', 
                                  minlen=2, maxlen=2, units='NA',
                                  desc = 'Minimum and maximum crossing angles' \
                                         'between the two fibres.')
    twodtanglestep = traits.Float(argstr='-twodtanglestep %f', units='NA',
                               desc='Angle step size controlling how many steps there are' \
                                    'between the minimum and maximum crossing angles for' \
                                    'the two tensor cases.')
    twodtmixmax = traits.Float(argstr='-twodtmixmax %f', units='NA',
                               desc='Mixing parameter controlling the proportion of one fibre population' \
                                    'to the other. The minimum mixing parameter is (1 - twodtmixmax).')
    twodtmixstep = traits.Float(argstr='-twodtmixstep %f', units='NA',
                                desc='Mixing parameter step size for the two tensor cases.' \
                                     'Specify how many mixing parameter increments to use.')                           
    seed = traits.Float(argstr='-seed %f', units='NA',
                        desc='Specifies the random seed to use for noise generation in simulation trials.')                             

class SFPICOCalibDataOutputSpec(TraitedSpec):
    PICOCalib = File(exists=True, desc='Calibration dataset')

class SFPICOCalibData(StdOutCommandLine):
    """
    Generates Spherical Function PICo Calibration Data.
    
    SFPICOCalibData creates synthetic data for use with SFLUTGen. The 
    synthetic data is generated using a mixture of gaussians, in the 
    same way datasynth generates data.  Each voxel of data models a 
    slightly different fibre configuration (varying FA and fibre-
    crossings) and undergoes a random rotation to help account for any 
    directional bias in the chosen acquisition scheme.  A second file, 
    which stores information about the datafile, is generated along with
    the datafile.

    Example 1
    ---------
    To create a calibration dataset using the default settings
    
    >>> import nipype.interfaces.camino as cam
    >>> calib = cam.SFPICOCalibData()
    >>> calib.inputs.scheme_file = 'A.scheme'
    >>> calib.inputs.snr = 20
    >>> calib.inputs.info_file = 'PICO_calib.info'
    >>> calib.run()                  # doctest: +SKIP
    
    The default settings create a large dataset (249,231 voxels), of 
    which 3401 voxels contain a single fibre population per voxel and 
    the rest of the voxels contain two fibre-populations. The amount of 
    data produced can be varied by specifying the ranges and steps of 
    the parameters for both the one and two fibre datasets used.
    
    Example 2
    ---------
    To create a custom calibration dataset
    
    >>> import nipype.interfaces.camino as cam
    >>> calib = cam.SFPICOCalibData()
    >>> calib.inputs.scheme_file = 'A.scheme'
    >>> calib.inputs.snr = 20
    >>> calib.inputs.info_file = 'PICO_calib.info'
    >>> calib.inputs.twodtfarange = [0.3, 0.9]
    >>> calib.inputs.twodtfastep = 0.02
    >>> calib.inputs.twodtanglerange = [0, 0.785]
    >>> calib.inputs.twodtanglestep = 0.03925
    >>> calib.inputs.twodtmixmax = 0.8
    >>> calib.inputs.twodtmixstep = 0.1
    >>> calib.run()                  
    
    This would provide 76,313 voxels of synthetic data, where 3401 voxels
    simulate the one fibre cases and 72,912 voxels simulate the various 
    two fibre cases. However, care should be taken to ensure that enough 
    data is generated for calculating the LUT.      # doctest: +SKIP
    """
    _cmd = 'sfpicocalibdata'
    input_spec=SFPICOCalibDataInputSpec
    output_spec=SFPICOCalibDataOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['PICOCalib'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.scheme_file)
        return name + '_PICOCalib.Bfloat'
