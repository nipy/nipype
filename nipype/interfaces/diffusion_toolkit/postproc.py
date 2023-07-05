# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands provided by diffusion toolkit
"""

import os
from ..base import (
    TraitedSpec,
    File,
    traits,
    CommandLine,
    InputMultiPath,
    CommandLineInputSpec,
)

__docformat__ = "restructuredtext"


class SplineFilterInputSpec(CommandLineInputSpec):
    track_file = File(
        exists=True,
        desc="file containing tracks to be filtered",
        position=0,
        argstr="%s",
        mandatory=True,
    )
    step_length = traits.Float(
        desc="in the unit of minimum voxel size",
        position=1,
        argstr="%f",
        mandatory=True,
    )
    output_file = File(
        "spline_tracks.trk",
        desc="target file for smoothed tracks",
        position=2,
        argstr="%s",
        usedefault=True,
    )


class SplineFilterOutputSpec(TraitedSpec):
    smoothed_track_file = File(exists=True)


class SplineFilter(CommandLine):
    """
    Smoothes TrackVis track files with a B-Spline filter.

    Helps remove redundant track points and segments
    (thus reducing the size of the track file) and also
    make tracks nicely smoothed. It will NOT change the
    quality of the tracks or lose any original information.

    Example
    -------

    >>> import nipype.interfaces.diffusion_toolkit as dtk
    >>> filt = dtk.SplineFilter()
    >>> filt.inputs.track_file = 'tracks.trk'
    >>> filt.inputs.step_length = 0.5
    >>> filt.run()                                 # doctest: +SKIP
    """

    input_spec = SplineFilterInputSpec
    output_spec = SplineFilterOutputSpec

    _cmd = "spline_filter"

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["smoothed_track_file"] = os.path.abspath(self.inputs.output_file)
        return outputs


class TrackMergeInputSpec(CommandLineInputSpec):
    track_files = InputMultiPath(
        File(exists=True),
        desc="file containing tracks to be filtered",
        position=0,
        argstr="%s...",
        mandatory=True,
    )
    output_file = File(
        "merged_tracks.trk",
        desc="target file for merged tracks",
        position=-1,
        argstr="%s",
        usedefault=True,
    )


class TrackMergeOutputSpec(TraitedSpec):
    track_file = File(exists=True)


class TrackMerge(CommandLine):
    """
    Merges several TrackVis track files into a single track
    file.

    An id type property tag is added to each track in the
    newly merged file, with each unique id representing where
    the track was originally from. When the merged file is
    loaded in TrackVis, a property filter will show up in
    Track Property panel. Users can adjust that to distinguish
    and sub-group tracks by its id (origin).

    Example
    -------

    >>> import nipype.interfaces.diffusion_toolkit as dtk
    >>> mrg = dtk.TrackMerge()
    >>> mrg.inputs.track_files = ['track1.trk','track2.trk']
    >>> mrg.run()                                 # doctest: +SKIP
    """

    input_spec = TrackMergeInputSpec
    output_spec = TrackMergeOutputSpec

    _cmd = "track_merge"

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["track_file"] = os.path.abspath(self.inputs.output_file)
        return outputs
