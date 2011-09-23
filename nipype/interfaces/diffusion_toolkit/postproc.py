# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands provided by diffusion toolkit

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
import os
__docformat__ = 'restructuredtext'

from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine,
    CommandLineInputSpec)

class SplineFilterInputSpec(CommandLineInputSpec):
    track_file = File(exists=True, desc="file containing tracks to be filtered", position=0, argstr="%s", mandatory=True)
    step_length = traits.Float(desc="in the unit of minimum voxel size", position=1, argstr="%f", mandatory=True)
    output_file = File("spline_tracks.trk", desc="target file for smoothed tracks", position=2, argstr="%s", usedefault=True)

class SplineFilterOutputSpec(TraitedSpec):
    smoothed_track_file = File(exists=True)

class SplineFilter(CommandLine):
    input_spec=SplineFilterInputSpec
    output_spec=SplineFilterOutputSpec

    _cmd = "spline_filter"

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['smoothed_track_file'] = os.path.abspath(self.inputs.output_file)
        return outputs