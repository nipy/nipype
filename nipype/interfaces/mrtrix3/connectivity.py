# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# -*- coding: utf-8 -*-

"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname(os.path.realpath(__file__ ))
    >>> datadir = os.path.realpath(os.path.join(filepath,
    ...                            '../../testing/data'))
    >>> os.chdir(datadir)

"""
import os
import os.path as op

from base import MRTrix3BaseInputSpec, MRTrix3Base
from nipype.interfaces.base import (
    CommandLineInputSpec, CommandLine, traits, TraitedSpec, File)

from nipype.utils.filemanip import split_filename
from nipype.interfaces.traits_extension import isdefined


class LabelConfigInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True, position=-3,
                   desc='input anatomical image')
    in_config = File(exists=True, argstr='%s', position=-2,
                     desc='connectome configuration file')
    out_file = File(
        'parcellation.mif', argstr='%s', mandatory=True, position=-1,
        usedefault=True, desc='output file after processing')

    lut_basic = File(argstr='-lut_basic %s', desc='get information from '
                     'a basic lookup table consisting of index / name pairs')
    lut_fs = File(argstr='-lut_freesurfer %s', desc='get information from '
                  'a FreeSurfer lookup table(typically "FreeSurferColorLUT'
                  '.txt")')
    lut_aal = File(argstr='-lut_aal %s', desc='get information from the AAL '
                   'lookup table (typically "ROI_MNI_V4.txt")')
    lut_itksnap = File(argstr='-lut_itksnap %s', desc='get information from an'
                       ' ITK - SNAP lookup table(this includes the IIT atlas '
                       'file "LUT_GM.txt")')
    spine = File(argstr='-spine %s', desc='provide a manually-defined '
                 'segmentation of the base of the spine where the streamlines'
                 ' terminate, so that this can become a node in the connection'
                 ' matrix.')
    nthreads = traits.Int(
        argstr='-nthreads %d', desc='number of threads. if zero, the number'
        ' of available cpus will be used')


class LabelConfigOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='the output response file')


class LabelConfig(MRTrix3Base):

    """
    Generate anatomical information necessary for Anatomically
    Constrained Tractography (ACT).

    Example
    -------

    >>> import nipype.interfaces.mrtrix3 as mrt
    >>> labels = mrt.LabelConfig()
    >>> labels.inputs.in_file = 'aparc+aseg.nii.gz'
    >>> labels.inputs.in_config = 'mrtrix3_labelconfig.txt'
    >>> labels.cmdline                               # doctest: +ELLIPSIS
    'labelconfig aparc+aseg.nii.gz mrtrix3_labelconfig.txt parcellation.mif'
    >>> labels.run()                                 # doctest: +SKIP
    """

    _cmd = 'labelconfig:'
    input_spec = LabelConfigInputSpec
    output_spec = LabelConfigOutputSpec

    def _parse_inputs(self, skip=None):
        if skip is None:
            skip = []

        if not isdefined(self.inputs.in_config):
            from distutils.spawn import find_executable
            path = op.dirname(find_executable(self._cmd))
            self.inputs.in_config = op.abspath(
                op.join(path, '../src/dwi/tractography/connectomics/'
                              'example_configs/fs_default.txt'))
        return super(LabelConfig, self)._parse_inputs(skip=skip)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = op.abspath(self.inputs.out_file)
        return outputs
