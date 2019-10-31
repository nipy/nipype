# -*- coding: utf-8 -*-
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)
from builtins import str, bytes

import os
import os.path as op
import glob

from ... import logging
from ...utils.filemanip import simplify_list
from ..base import (traits, File, Bool, Int, Str, Directory, TraitedSpec,
                    OutputMultiPath, isdefined, CommandLine)
from ..freesurfer.base import FSCommand, FSTraitedSpec

iflogger = logging.getLogger('nipype.interface')


class WatershedBEMInputSpec(FSTraitedSpec):
    subject_id = traits.Str(
        argstr='--subject %s',
        mandatory=True,
        desc='Subject ID (must have a complete Freesurfer directory)')
    subjects_dir = Directory(
        exists=True,
        mandatory=True,
        usedefault=True,
        desc='Path to Freesurfer subjects directory')
    volume = traits.Enum(
        'T1',
        'aparc+aseg',
        'aseg',
        'brain',
        'orig',
        'brainmask',
        'ribbon',
        argstr='--volume %s',
        usedefault=True,
        desc='The volume from the "mri" directory to use (defaults to T1)')
    overwrite = traits.Bool(
        True,
        usedefault=True,
        argstr='--overwrite',
        desc='Overwrites the existing files')
    atlas_mode = traits.Bool(
        argstr='--atlas',
        desc='Use atlas mode for registration (default: no rigid alignment)')


class WatershedBEMOutputSpec(TraitedSpec):
    mesh_files = OutputMultiPath(
        File(exists=True),
        desc=('Paths to the output meshes (brain, inner '
              'skull, outer skull, outer skin)'))
    brain_surface = File(
        exists=True,
        loc='bem/watershed',
        desc='Brain surface (in Freesurfer format)')
    inner_skull_surface = File(
        exists=True,
        loc='bem/watershed',
        desc='Inner skull surface (in Freesurfer format)')
    outer_skull_surface = File(
        exists=True,
        loc='bem/watershed',
        desc='Outer skull surface (in Freesurfer format)')
    outer_skin_surface = File(
        exists=True,
        loc='bem/watershed',
        desc='Outer skin surface (in Freesurfer format)')
    fif_file = File(
        exists=True,
        loc='bem',
        altkey='fif',
        desc='"fif" format file for EEG processing in MNE')
    cor_files = OutputMultiPath(
        File(exists=True),
        loc='bem/watershed/ws',
        altkey='COR',
        desc='"COR" format files')


class WatershedBEM(FSCommand):
    """Uses mne_watershed_bem to get information from dicom directories

    Examples
    --------

    >>> from nipype.interfaces.mne import WatershedBEM
    >>> bem = WatershedBEM()
    >>> bem.inputs.subject_id = 'subj1'
    >>> bem.inputs.subjects_dir = '.'
    >>> bem.cmdline
    'mne watershed_bem --overwrite --subject subj1 --volume T1'
    >>> bem.run() 				# doctest: +SKIP

   """

    _cmd = 'mne watershed_bem'
    input_spec = WatershedBEMInputSpec
    output_spec = WatershedBEMOutputSpec
    _additional_metadata = ['loc', 'altkey']

    def _get_files(self, path, key, dirval, altkey=None):
        globsuffix = '*'
        globprefix = '*'
        keydir = op.join(path, dirval)
        if altkey:
            key = altkey
        globpattern = op.join(keydir, ''.join((globprefix, key, globsuffix)))
        return glob.glob(globpattern)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        subjects_dir = self.inputs.subjects_dir
        subject_path = op.join(subjects_dir, self.inputs.subject_id)
        output_traits = self._outputs()
        mesh_paths = []
        for k in list(outputs.keys()):
            if k != 'mesh_files':
                val = self._get_files(subject_path, k,
                                      output_traits.traits()[k].loc,
                                      output_traits.traits()[k].altkey)
                if val:
                    value_list = simplify_list(val)
                    if isinstance(value_list, list):
                        out_files = []
                        for value in value_list:
                            out_files.append(op.abspath(value))
                    elif isinstance(value_list, (str, bytes)):
                        out_files = op.abspath(value_list)
                    else:
                        raise TypeError
                    outputs[k] = out_files
                    if not k.rfind('surface') == -1:
                        mesh_paths.append(out_files)
        outputs['mesh_files'] = mesh_paths
        return outputs


class SetupSourceSpaceInputSpec(FSTraitedSpec):
    subject = Str(
        argstr='--subject %s',
        mandatory=True,
        desc='Subject name')
    fname = File(
        argstr='--src %s',
        mandatory=False,
        default=None,
        desc='Output file name. Use a name <dir>/<name>-src.fif')
    subject_to = Str(
        argstr='--morph %s',
        mandatory=False,
        default=None,
        desc='morph the source space to this subject')
    surface = Str(
        'white',
        argstr='--surf %s',
        mandatory=False,
        usedefault=True,
        desc='The surface to use.')
    ico = Int(
        argstr='--ico %s',
        mandatory=False,
        default=None,
        desc='use the recursively subdivided icosahedron '
             'to create the source space.')
    oct_ = Int(
        argstr='--oct %s',
        mandatory=False,
        default=None,
        desc='use the recursively subdivided octahedron '
             'to create the source space.',
        xor=['ico'])
    spacing = Int(
        7,
        argstr='--spacing %s',
        mandatory=False,
        usedefault=True,
        desc='Specifies the approximate grid spacing of the '
             'source space in mm.',
        xor=['oct_', 'ico'])
    n_jobs = Int(
        1,
        argstr='--n-jobs %s',
        mandatory=False,
        usedefault=True,
        desc='The number of jobs to run in parallel '
             '(default 1). Requires the joblib package. '
             'Will use at most 2 jobs'
             ' (one for each hemisphere).')
    verbose = Bool(
        False,
        argstr='--verbose',
        mandatory=False,
        usedefault=True,
        desc='Turn on verbose mode.')
    overwrite = Bool(
        False,
        argstr='--overwrite',
        mandatory=False,
        usedefault=True,
        desc='Overwrites the existing files')


class SetupSourceSpaceOutputSpec(TraitedSpec):
    source = File(exists=True,
                  desc='File containing the setup_source_space')


class SetupSourceSpace(CommandLine):
    """Uses mne_setup_source_space to create a source space.

    Examples
    --------

    >>> from nipype.interfaces.mne import SetupSourceSpace
    >>> setup_source_space = SetupSourceSpace()
    >>> setup_source_space.inputs.subject = 'subj1'
    >>> setup_source_space.inputs.subjects_dir = '.'
    >>> setup_source_space.cmdline
    'mne setup_source_space --cps --n-jobs 1 --spacing 7 \
    --subject subj1 --surf white'
    >>> setup_source_space.run() 				# doctest: +SKIP

   """

    _cmd = 'mne setup_source_space'
    input_spec = SetupSourceSpaceInputSpec
    output_spec = SetupSourceSpaceOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        fname = self.inputs.fname
        ico = self.inputs.ico
        oct_ = self.inputs.oct_
        spacing = self.inputs.spacing
        subject = self.inputs.subject
        subject_to = self.inputs.subject_to

        if not isdefined(fname):
            if isdefined(ico):
                use_spacing = "ico" + str(ico)
            elif isdefined(oct_):
                use_spacing = "oct" + str(oct_)
            elif isdefined(spacing):
                use_spacing = spacing
            if not isdefined(subject_to):
                fname = subject + '-' + str(use_spacing) + '-src.fif'
            else:
                fname = (subject_to + '-' + subject + '-' +
                         str(use_spacing) + '-src.fif')
        else:
            if not (fname.endswith('_src.fif') or fname.endswith('-src.fif')):
                fname = fname + "-src.fif"
        outputs['source'] = os.path.join(os.getcwd(), fname)
        return outputs
