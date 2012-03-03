# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""

from nipype.interfaces.base import (CommandLineInputSpec, CommandLine, BaseInterface, BaseInterfaceInputSpec,
                                    traits, File, TraitedSpec, Directory, InputMultiPath, OutputMultiPath, isdefined)
from nipype.utils.filemanip import split_filename
import os, os.path as op
import numpy as np
import nibabel as nb
import logging

logging.basicConfig()
iflogger = logging.getLogger('interface')

class DWI2SphericalHarmonicsImageInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-2, desc='Diffusion-weighted images')
    out_filename = File(genfile=True, argstr='%s', position=-1, desc='Output filename')
    encoding_file = File(exists=True, argstr='-grad %s', mandatory=True, position=1,
    desc='Gradient encoding, supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient, and b gives the b-value in units (1000 s/mm^2). See FSL2MRTrix')
    maximum_harmonic_order = traits.Float(argstr='-lmax %s', desc='set the maximum harmonic order for the output series. By default, the program will use the highest possible lmax given the number of diffusion-weighted images.')
    normalise = traits.Bool(argstr='-normalise', position=3, desc="normalise the DW signal to the b=0 image")

class DWI2SphericalHarmonicsImageOutputSpec(TraitedSpec):
    spherical_harmonics_image = File(exists=True, desc='Spherical harmonics image')

class DWI2SphericalHarmonicsImage(CommandLine):
    """
    Convert base diffusion-weighted images to their spherical harmonic representation.

    This program outputs the spherical harmonic decomposition for the set measured signal attenuations.
    The signal attenuations are calculated by identifying the b-zero images from the diffusion encoding supplied
    (i.e. those with zero as the b-value), and dividing the remaining signals by the mean b-zero signal intensity.
    The spherical harmonic decomposition is then calculated by least-squares linear fitting.
    Note that this program makes use of implied symmetries in the diffusion profile.

    First, the fact the signal attenuation profile is real implies that it has conjugate symmetry,
    i.e. Y(l,-m) = Y(l,m)* (where * denotes the complex conjugate). Second, the diffusion profile should be
    antipodally symmetric (i.e. S(x) = S(-x)), implying that all odd l components should be zero. Therefore,
    this program only computes the even elements.

    Note that the spherical harmonics equations used here differ slightly from those conventionally used,
    in that the (-1)^m factor has been omitted. This should be taken into account in all subsequent calculations.

    Each volume in the output image corresponds to a different spherical harmonic component, according to the following convention:

    * [0] Y(0,0)
    * [1] Im {Y(2,2)}
    * [2] Im {Y(2,1)}
    * [3] Y(2,0)
    * [4] Re {Y(2,1)}
    * [5] Re {Y(2,2)}
    * [6] Im {Y(4,4)}
    * [7] Im {Y(4,3)}

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> dwi2SH = mrt.DWI2SphericalHarmonicsImage()
    >>> dwi2SH.inputs.in_file = 'diffusion.nii'
    >>> dwi2SH.inputs.encoding_file = 'encoding.txt'
    >>> dwi2SH.run()                                    # doctest: +SKIP
    """
    _cmd = 'dwi2SH'
    input_spec=DWI2SphericalHarmonicsImageInputSpec
    output_spec=DWI2SphericalHarmonicsImageOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['spherical_harmonics_image'] = op.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_SH.mif'

class ConstrainedSphericalDeconvolutionInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-3, desc='diffusion-weighted image')
    response_file = File(exists=True, argstr='%s', mandatory=True, position=-2,
    desc='the diffusion-weighted signal response function for a single fibre population (see EstimateResponse)')
    out_filename = File(genfile=True, argstr='%s', position=-1, desc='Output filename')
    mask_image = File(exists=True, argstr='-mask %s', position=2, desc='only perform computation within the specified binary brain mask image')
    encoding_file = File(exists=True, argstr='-grad %s', position=1,
    desc='Gradient encoding, supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient, and b gives the b-value in units (1000 s/mm^2). See FSL2MRTrix')
    filter_file = File(exists=True, argstr='-filter %s', position=-2,
    desc='a text file containing the filtering coefficients for each even harmonic order.' \
    'the linear frequency filtering parameters used for the initial linear spherical deconvolution step (default = [ 1 1 1 0 0 ]).')

    lambda_value = traits.Float(argstr='-lambda %s', desc='the regularisation parameter lambda that controls the strength of the constraint (default = 1.0).')
    maximum_harmonic_order = traits.Float(argstr='-lmax %s', desc='set the maximum harmonic order for the output series. By default, the program will use the highest possible lmax given the number of diffusion-weighted images.')
    threshold_value = traits.Float(argstr='-threshold %s', desc='the threshold below which the amplitude of the FOD is assumed to be zero, expressed as a fraction of the mean value of the initial FOD (default = 0.1)')
    iterations = traits.Int(argstr='-niter %s', desc='the maximum number of iterations to perform for each voxel (default = 50)')

    directions_file = File(exists=True, argstr='-directions %s', position=-2,
    desc='a text file containing the [ el az ] pairs for the directions: Specify the directions over which to apply the non-negativity constraint (by default, the built-in 300 direction set is used)')

    normalise = traits.Bool(argstr='-normalise', position=3, desc="normalise the DW signal to the b=0 image")

class ConstrainedSphericalDeconvolutionOutputSpec(TraitedSpec):
    spherical_harmonics_image = File(exists=True, desc='Spherical harmonics image')

class ConstrainedSphericalDeconvolution(CommandLine):
    """
    Perform non-negativity constrained spherical deconvolution.

    Note that this program makes use of implied symmetries in the diffusion profile.
    First, the fact the signal attenuation profile is real implies that it has conjugate symmetry,
    i.e. Y(l,-m) = Y(l,m)* (where * denotes the complex conjugate). Second, the diffusion profile should be
    antipodally symmetric (i.e. S(x) = S(-x)), implying that all odd l components should be zero.
    Therefore, this program only computes the even elements. 	Note that the spherical harmonics equations used here
    differ slightly from those conventionally used, in that the (-1)^m factor has been omitted. This should be taken
    into account in all subsequent calculations. Each volume in the output image corresponds to a different spherical
    harmonic component, according to the following convention:

    * [0] Y(0,0)
    * [1] Im {Y(2,2)}
    * [2] Im {Y(2,1)}
    * [3] Y(2,0)
    * [4] Re {Y(2,1)}
    * [5] Re {Y(2,2)}
    * [6] Im {Y(4,4)}
    * [7] Im {Y(4,3)}

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> csdeconv = mrt.ConstrainedSphericalDeconvolution()
    >>> csdeconv.inputs.in_file = 'dwi.mif'
    >>> csdeconv.inputs.encoding_file = 'encoding.txt'
    >>> csdeconv.run()                                          # doctest: +SKIP
    """

    _cmd = 'csdeconv'
    input_spec=ConstrainedSphericalDeconvolutionInputSpec
    output_spec=ConstrainedSphericalDeconvolutionOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['spherical_harmonics_image'] = op.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_CSD.mif'

class EstimateResponseForSHInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-3, desc='Diffusion-weighted images')
    mask_image = File(exists=True, mandatory=True, argstr='%s', position=-2, desc='only perform computation within the specified binary brain mask image')
    out_filename = File(genfile=True, argstr='%s', position=-1, desc='Output filename')
    encoding_file = File(exists=True, argstr='-grad %s', mandatory=True, position=1,
    desc='Gradient encoding, supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient, and b gives the b-value in units (1000 s/mm^2). See FSL2MRTrix')
    maximum_harmonic_order = traits.Float(argstr='-lmax %s', desc='set the maximum harmonic order for the output series. By default, the program will use the highest possible lmax given the number of diffusion-weighted images.')
    normalise = traits.Bool(argstr='-normalise', desc='normalise the DW signal to the b=0 image')
    quiet = traits.Bool(argstr='-quiet', desc='Do not display information messages or progress status.')
    debug = traits.Bool(argstr='-debug', desc='Display debugging messages.')

class EstimateResponseForSHOutputSpec(TraitedSpec):
    response = File(exists=True, desc='Spherical harmonics image')

class EstimateResponseForSH(CommandLine):
    """
    Estimates the fibre response function for use in spherical deconvolution.

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> estresp = mrt.EstimateResponseForSH()
    >>> estresp.inputs.in_file = 'dwi.mif'
    >>> estresp.inputs.mask_image = 'dwi_WMProb.mif'
    >>> estresp.inputs.encoding_file = 'encoding.txt'
    >>> estresp.run()                                   # doctest: +SKIP
    """
    _cmd = 'estimate_response'
    input_spec=EstimateResponseForSHInputSpec
    output_spec=EstimateResponseForSHOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['response'] = op.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '_ER.mif'

def concat_files(bvec_file, bval_file, invert_x, invert_y, invert_z):
    bvecs = np.loadtxt(bvec_file)
    bvals = np.loadtxt(bval_file)
    flip = False
    if np.shape(bvecs)[0] > np.shape(bvecs)[1]:
        flip = True
        bvecs = np.transpose(bvecs)
    if invert_x:
        bvecs[0,:] = -bvecs[0,:]
        iflogger.info('Inverting b-vectors in the x direction')
    if invert_y:
        bvecs[1,:] = -bvecs[1,:]
        iflogger.info('Inverting b-vectors in the y direction')
    if invert_z:
        bvecs[2,:] = -bvecs[2,:]
        iflogger.info('Inverting b-vectors in the z direction')
    iflogger.info(np.shape(bvecs))
    iflogger.info(np.shape(bvals))
    encoding = np.transpose(np.vstack((bvecs,bvals)))
    _, bvec , _ = split_filename(bvec_file)
    _, bval , _ = split_filename(bval_file)
    out_encoding_file = bvec + '_' + bval + '.txt'
    np.savetxt(out_encoding_file, encoding)
    return out_encoding_file

class FSL2MRTrixInputSpec(TraitedSpec):
    bvec_file = File(exists=True, mandatory=True, desc='FSL b-vectors file (3xN text file)')
    bval_file = File(exists=True, mandatory=True, desc='FSL b-values file (1xN text file)')
    invert_x = traits.Bool(False, usedefault=True, desc='Inverts the b-vectors along the x-axis')
    invert_y = traits.Bool(False, usedefault=True, desc='Inverts the b-vectors along the y-axis')
    invert_z = traits.Bool(False, usedefault=True, desc='Inverts the b-vectors along the z-axis')
    out_encoding_file = File(genfile=True, desc='Output encoding filename')

class FSL2MRTrixOutputSpec(TraitedSpec):
    encoding_file = File(desc='The gradient encoding, supplied as a 4xN text file with each line is in the format [ X Y Z b ], where [ X Y Z ] describe the direction of the applied gradient' \
        'and b gives the b-value in units (1000 s/mm^2).')

class FSL2MRTrix(BaseInterface):
    """
    Converts separate b-values and b-vectors from text files (FSL style) into a
    4xN text file in which each line is in the format [ X Y Z b ], where [ X Y Z ]
    describe the direction of the applied gradient, and b gives the
    b-value in units (1000 s/mm^2).

    Example
    -------

    >>> import nipype.interfaces.mrtrix as mrt
    >>> fsl2mrtrix = mrt.FSL2MRTrix()
    >>> fsl2mrtrix.inputs.bvec_file = 'bvecs'
    >>> fsl2mrtrix.inputs.bval_file = 'bvals'
    >>> fsl2mrtrix.inputs.invert_y = True
    >>> fsl2mrtrix.run()                                # doctest: +SKIP
    """
    input_spec = FSL2MRTrixInputSpec
    output_spec = FSL2MRTrixOutputSpec

    def _run_interface(self, runtime):
        encoding = concat_files(self.inputs.bvec_file, self.inputs.bval_file, self.inputs.invert_x, self.inputs.invert_y, self.inputs.invert_z)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['encoding_file'] = op.abspath(self._gen_filename('out_encoding_file'))
        return outputs

    def _gen_filename(self, name):
        if name is 'out_encoding_file':
            return self._gen_outfilename()
        else:
            return None

    def _gen_outfilename(self):
        _, bvec , _ = split_filename(self.inputs.bvec_file)
        _, bval , _ = split_filename(self.inputs.bval_file)
        return bvec + '_' + bval + '.txt'
