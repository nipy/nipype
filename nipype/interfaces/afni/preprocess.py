# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provide interface to AFNI commands."""
__docformat__ = 'restructuredtext'


import os
from glob import glob
import warnings

from nipype.interfaces.afni.base import Info, AFNITraitedSpec, AFNICommand
from nipype.interfaces.base import Bunch, TraitedSpec, File, Directory, InputMultiPath
from nipype.utils.filemanip import fname_presuffix, list_to_filename, split_filename
from nipype.utils.docparse import get_doc
from nipype.utils.misc import container_to_string, is_container, isdefined

import enthought.traits.api as traits


warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class To3dInputSpec(AFNITraitedSpec):
    infolder = Directory(desc = 'folder with DICOM images to convert',
                         argstr = '%s/*.dcm',
                         position = -1,
                         mandatory = True,
                         exists = True)
    outfile = File(desc = 'converted image file',
                   argstr = '-prefix %s',
                   position = -2,
                   mandatory = True)
    filetype = traits.Str(desc = 'type of datafile being converted',
                          argstr = '-%s')
    '''use xor'''
    skipoutliers = traits.Bool(desc = 'skip the outliers check',
                               argstr = '-skip_outliers')
    assumemosaic = traits.Bool(desc = 'assume that Siemens image is mosaic',
                               argstr = '-assume_dicom_mosaic')
    datatype = traits.Str(desc = 'set output file datatype',
                          argstr = '-datum %s')
    funcparams = traits.Str(desc = 'parameters for functional data',
                            argstr = '-time:zt %s alt+z2')

class To3dOutputSpec(TraitedSpec):
    out_file = File(desc = 'converted file',
                    exists = True)

class To3d(AFNICommand):
    """Create a 3D dataset from 2D image files using AFNI to3d command.

    For complete details, see the `to3d Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/to3d.html>`_

    To print out the command line help, use:
        To3d().inputs_help()

    Examples
    --------
    >>> from nipype.interfaces import afni
    >>> to3d = afni.To3d(datatype="anat")
    >>> to3d.inputs.datum = 'float'
    >>> res = to3d.run(infiles='data/*.dcm')

    """

    _cmd = 'to3d'
    input_spec = To3dInputSpec
    output_spec = To3dOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.outfile
        return outputs

    '''def _parseinputs_old(self):
        """Parse valid input options for To3d command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.items() \
            if v is not None]

        if inputs.has_key('datatype'):
            val = inputs.pop('datatype')
            out_inputs.append('-%s' % val)
        if inputs.has_key('skip_outliers'):
            val = inputs.pop('skip_outliers')
            out_inputs.append('-skip_outliers')
        if inputs.has_key('assume_dicom_mosaic'):
            val = inputs.pop('assume_dicom_mosaic')
            out_inputs.append('-assume_dicom_mosaic')
        if inputs.has_key('datum'):
            val = inputs.pop('datum')
            out_inputs.append('-datum %s' % val)
        if inputs.has_key('time_dependencies'):
            val = inputs.pop('time_dependencies')
            inputssub = {}
            [inputssub.update({k:v}) for k, v in val.items() \
                if v is not None]

            # The following are example input orders
            # -time:zt nz nt TR tpattern
            # -time:tz nt nz TR tpattern
            # time : list
            #    zt nz nt TR tpattern
            #    tz nt nz TR tpattern

            # dict(slice_order='zt', nz=12, nt=150, TR=2000, tpattern='alt+z')

            try:
                slice_order = inputssub.pop('slice_order')
                out_inputs.append('-time:%s' % slice_order)
            except KeyError:
                raise KeyError('slice_order is required for time_dependencies')
            try:
                nz = inputssub.pop('nz')
            except KeyError:
                raise KeyError('nz required for time_dependencies')
            try:
                nt = inputssub.pop('nt')
            except KeyError:
                raise KeyError('nt required for time_dependencies')

            if slice_order == 'tz':
                out_inputs.append('%s' % str(nt))
                out_inputs.append('%s' % str(nz))
            else:
                out_inputs.append('%s' % str(nz))
                out_inputs.append('%s' % str(nt))

            try:
                valsub = inputssub.pop('TR')
                out_inputs.append('%s' % str(valsub))
            except KeyError:
                raise KeyError('TR required for time_dependencies')
            try:
                valsub = inputssub.pop('tpattern')
                out_inputs.append('%s' % valsub)
            except KeyError:
                raise KeyError('tpattern required for time_dependencies')

            if len(inputssub) > 0:
                msg = '%s: unsupported time_dependencies options: %s' % (
                    self.__class__.__name__, inputssub.keys())
                raise AttributeError(msg)

        if inputs.has_key('session'):
            val = inputs.pop('session')
            out_inputs.append('-session %s' % val)
        if inputs.has_key('prefix'):
            val = inputs.pop('prefix')
            out_inputs.append('-prefix %s' % val)
        if inputs.has_key('infiles'):
            val = inputs.pop('infiles')
            if type(val) == list:
                out_inputs.append('%s' % ' '.join(val))
            else:
                out_inputs.append('%s' % val)

        if len(inputs) > 0:
            msg = '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())
            raise AttributeError(msg)

        return out_inputs

    def _parseinputs(self):
        allargs = super(To3d, self)._parseinputs(skip=('infiles',
                                                       'time_dependencies'))
        if self.inputs.time_dependencies:
            # Accept time_dependencies as input from a dictionary or
            # any container.
            tin = self.inputs.time_dependencies
            if hasattr(tin, 'keys'):
                # XXX Not checking if any invalid keys have been passed in.
                try:
                    slice_order = tin['slice_order']
                    nz = tin['nz']
                    nt = tin['nt']
                    TR = tin['TR']
                    tpattern = tin['tpattern']
                    tflag = ['-time:%s' % slice_order]
                    if slice_order == 'zt':
                        tflag.append(str(nz))
                        tflag.append(str(nt))
                    else:
                        tflag.append(str(nt))
                        tflag.append(str(nz))
                    tflag.append(str(TR))
                    tflag.append(str(tpattern))
                    allargs.append(' '.join(tflag))
                except KeyError:
                    msg = 'time_dependencies is missing a required key!\n'
                    msg += 'It should have: slice_order, nz, nt, TR, tpattern\n'
                    msg += 'But is currently set to:\n%s' % tin
                    raise KeyError(msg)
            else:
                # Assume it's just a container (list or tuple) and
                # just use the format string.
                allargs.append(self.opt_map['time_dependencies'] % tin)

        if self.inputs.infiles:
            allargs.append(container_to_string(self.inputs.infiles))
        return allargs
    '''


class ThreedrefitInputSpec(AFNITraitedSpec):
    infile = File(desc = 'input file to 3drefit',
                  argstr = '%s',
                  position = -1,
                  mandatory = True,
                  exists = True)
    deoblique = traits.Bool(desc = 'replace current transformation matrix with cardinal matrix',
                            argstr = '-deoblique')
    xorigin = traits.Str(desc = 'x distance for edge voxel offset',
                         argstr = '-xorigin %s')
    yorigin = traits.Str(desc = 'y distance for edge voxel offset',
                         argstr = '-yorigin %s')
    zorigin = traits.Str(desc = 'y distance for edge voxel offset',
                         argstr = '-yorigin %s')

class ThreedrefitOutputSpec(AFNITraitedSpec):
    out_file = File(desc = 'Same file as original infile with modified matrix',
                    exists = True)

class Threedrefit(AFNICommand):
    """ Use 3drefit for altering header info.

        NOTES
        -----
        The original file is returned but it is CHANGED
    """

    _cmd = '3drefit'
    input_spec = ThreedrefitInputSpec
    output_spec = ThreedrefitOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.infile
        return outputs


class ThreedresampleInputSpec(AFNITraitedSpec):
    infile = File(desc = 'input file to 3dresample',
                  argstr = '-inset %s',
                  position = -1,
                  mandatory = True,
                  exists = True)
    outfile = File(desc = 'output file from 3dresample',
                   argstr = '-prefix %s',
                   position = -2,
                   mandatory = True)
    orientation = traits.Str(desc = 'new orientation code',
                             argstr = '-orient %s')

class ThreedresampleOutputSpec(AFNITraitedSpec):
    out_file = File(desc = 'reoriented or resampled file',
                    exists = True)

class Threedresample(AFNICommand):
    """Resample or reorient an image using AFNI 3dresample command.

    For complete details, see the `3dresample Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dresample.html>`_
    """

    _cmd = '3dresample'
    input_spec = ThreedresampleInputSpec
    output_spec = ThreedresampleOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.outfile
        return outputs


class ThreedTstatInputSpec(AFNITraitedSpec):
    infile = File(desc = 'input file to 3dTstat',
                  argstr = '%s',
                  position = -1,
                  mandatory = True,
                  exists = True)
    outfile = File(desc = 'output file from 3dTstat',
                   argstr = '-prefix %s',
                   position = -2,
                   mandatory = True)
    options = traits.Str(desc = 'selected statistical output',
                         argstr = '%s')

class ThreedTstatOutputSpec(AFNITraitedSpec):
    out_file = File(desc = 'statistical file',
                    exists = True)

class ThreedTstat(AFNICommand):
    """Compute voxel-wise statistics using AFNI 3dTstat command.

    For complete details, see the `3dTstat Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dTstat.html>`_
    """

    _cmd = '3dTstat'
    input_spec = ThreedTstatInputSpec
    output_spec = ThreedTstatOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.outfile
        return outputs


    '''    def _parseinputs(self):
        """Parse valid input options for ThreedTstat command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.items() \
             if v is not None]

        if inputs.has_key('outfile'):
            val = inputs.pop('outfile')
            out_inputs.append('-prefix %s' % val)
        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('%s' % val)

        if len(inputs) > 0:
            msg = '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())
            raise AttributeError(msg)

        return out_inputs
    '''


class ThreedAutomaskInputSpec(AFNITraitedSpec):
    infile = File(desc = 'input file to 3dAutomask',
                  argstr = '%s',
                  position = -1,
                  mandatory = True,
                  exists = True)
    outfile = File(desc = 'output file from 3dAutomask',
                   argstr = '-prefix %s',
                   position = -2,
                   mandatory = True)
    options = traits.Str(desc = 'automask settings',
                         argstr = '%s')

class ThreedAutomaskOutputSpec(AFNITraitedSpec):
    out_file = File(desc = 'mask file',
                    exists = True)

class ThreedAutomask(AFNICommand):
    """Create a brain-only mask of the image using AFNI 3dAutomask command.

    For complete details, see the `3dAutomask Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAutomask.html>`_
    """

    _cmd = '3dAutomask'
    input_spec = ThreedAutomaskInputSpec
    output_spec = ThreedAutomaskOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.outfile
        return outputs


    '''def _parseinputs(self):
        """Parse valid input options for ThreedAutomask command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.items() \
             if v is not None]

        if inputs.has_key('outfile'):
            val = inputs.pop('outfile')
            out_inputs.append('-prefix %s' % val)
        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('%s' % val)

        if len(inputs) > 0:
            msg = '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())
            raise AttributeError(msg)

        return out_inputs
    '''


class ThreedvolregInputSpec(AFNITraitedSpec):
    infile = File(desc = 'input file to 3dvolreg',
                  argstr = '%s',
                  position = -1,
                  mandatory = True,
                  exists = True)
    outfile = File(desc = 'output file from 3dvolreg',
                   argstr = '-prefix %s',
                   position = -2,
                   mandatory = True)
    basefile = File(desc = 'base file for registration',
                    argstr = '-base %s',
                    position = -5)
    md1dfile = File(desc = 'max displacement output file',
                    argstr = '-maxdisp1D %s',
                    position = -4)
    onedfile = File(desc = '1D movement parameters output file',
                    argstr = '-1Dfile %s',
                    position = -3)
    verbose = traits.Bool(desc = 'more detailed description of the process',
                          argstr = '-verbose')
    timeshift = traits.Bool(desc = 'time shift to mean slice time offset',
                            argstr = '-tshift 0')
    copyorigin = traits.Bool(desc = 'copy base file origin coords to output',
                            argstr = '-twodup')
    other = traits.Str(desc = 'other options',
                         argstr = '%s')

class ThreedvolregOutputSpec(AFNITraitedSpec):
    out_file = File(desc = 'registered file',
                    exists = True)
    md1d_file = File(desc = 'max displacement info file')
    oned_file = File(desc = 'movement parameters info file')

class Threedvolreg(AFNICommand):
    """Register input volumes to a base volume using AFNI 3dvolreg command.

    For complete details, see the `3dvolreg Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dvolreg.html>`_
    """

    _cmd = '3dvolreg'
    input_spec = ThreedvolregInputSpec
    output_spec = ThreedvolregOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.outfile
        return outputs


class ThreedmergeInputSpec(AFNITraitedSpec):
    infile = File(desc = 'input file to 3dvolreg',
                  argstr = '%s',
                  position = -1,
                  mandatory = True,
                  exists = True)
    outfile = File(desc = 'output file from 3dvolreg',
                   argstr = '-prefix %s',
                   position = -2,
                   mandatory = True)
    doall = traits.Bool(desc = 'apply options to all sub-bricks in dataset',
                        argstr = '-doall')
    blurfwhm = traits.Int(desc = 'FWHM blur value (mm)',
                          argstr = '-1blur_fwhm %d',
                          units = 'mm')
    other = traits.Str(desc = 'other options',
                         argstr = '%s')

class ThreedmergeOutputSpec(AFNITraitedSpec):
    out_file = File(desc = 'smoothed file',
                    exists = True)

class Threedmerge(AFNICommand):
    """Merge or edit volumes using AFNI 3dmerge command.

    For complete details, see the `3dmerge Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmerge.html>`_
    """

    _cmd = '3dmerge'
    input_spec = ThreedmergeInputSpec
    output_spec = ThreedmergeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.outfile
        return outputs


class ThreedZcutupInputSpec(AFNITraitedSpec):
    infile = File(desc = 'input file to 3dZcutup',
                  argstr = '%s',
                  position = -1,
                  mandatory = True,
                  exists = True)
    outfile = File(desc = 'output file from 3dZcutup',
                   argstr = '-prefix %s',
                   position = -2,
                   mandatory = True)
    keep = traits.Str(desc = 'slice range to keep in output',
                      argstr = '-keep %s')
    other = traits.Str(desc = 'other options',
                         argstr = '%s')

class ThreedZcutupOutputSpec(AFNITraitedSpec):
    out_file = File(desc = 'cut file',
                    exists = True)

class ThreedZcutup(AFNICommand):
    """Cut z-slices from a volume using AFNI 3dZcutup command.

    For complete details, see the `3dZcutup Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dZcutup.html>`_
    """

    _cmd = '3dZcutup'
    input_spec = ThreedZcutupInputSpec
    output_spec = ThreedZcutupOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.outfile
        return outputs



    '''def _parseinputs(self):
        """Parse valid input options for ThreedZcutup command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.items() \
             if v is not None]

        if inputs.has_key('keep'):
            val = inputs.pop('keep')
            inputssub = {}
            [inputssub.update({k:v}) for k, v in val.items() \
                if v is not None]

            if inputssub.has_key('from'):
                valsub = inputssub.pop('from')
                out_inputs.append('-keep %s' % str(valsub))
            else:
                valsub=None
                print('Warning: value \'from\' required for keep')
            if inputssub.has_key('to'):
                valsub = inputssub.pop('to')
                out_inputs.append('%s' % str(valsub))
            else:
                valsub=None
                print('Warning: value \'to\' required for keep')
        if inputs.has_key('outfile'):
            val = inputs.pop('outfile')
            out_inputs.append('-prefix %s' % val)
        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('%s' % val)

        if len(inputs) > 0:
            msg = '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())
            raise AttributeError(msg)

        return out_inputs
    '''


class ThreedSkullStrip(AFNICommand):
    """
    For complete details, see the `3dSkullStrip Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dSkullStrip.html>`_
    """

    @property
    def cmd(self):
        """Base command for ThreedSkullStrip"""
        return '3dSkullStrip'

    def inputs_help(self):
        doc = """
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""

        self.inputs = Bunch(outfile=None,
                            infile=None)

    def _parseinputs(self):
        """Parse valid input options for ThreedSkullStrip command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.items() \
             if v is not None]

        if inputs.has_key('outfile'):
            val = inputs.pop('outfile')
            out_inputs.append('-prefix %s' % val)
        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('-input %s' % val)

        if len(inputs) > 0:
            print '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())

        return out_inputs


class ThreedBrickStat(AFNICommand):
    """
    For complete details, see the `3dBrickStat Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dBrickStat.html>`_
    """

    @property
    def cmd(self):
        """Base command for ThreedBrickStat"""
        return '3dBrickStat'

    def inputs_help(self):
        doc = """
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""

        self.inputs = Bunch(automask=None,
                            percentile=None,
                            infile=None)

    def _parseinputs(self):
        """Parse valid input options for ThreedBrickStat command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.items() \
             if v is not None]

        if inputs.has_key('automask'):
            val = inputs.pop('automask')
            out_inputs.append('-automask')
        if inputs.has_key('percentile'):
            val = inputs.pop('percentile')
            inputssub = {}
            [inputssub.update({k:v}) for k, v in val.items() \
                if v is not None]

            if inputssub.has_key('p0'):
                valsub = inputssub.pop('p0')
                out_inputs.append('-percentile %s' % str(valsub))
            else:
                valsub=None
                print('Warning: value \'p0\' required for percentile')
            if inputssub.has_key('pstep'):
                valsub = inputssub.pop('pstep')
                out_inputs.append('%s' % str(valsub))
            else:
                valsub=None
                print('Warning: value \'pstep\' required for percentile')
            if inputssub.has_key('p1'):
                valsub = inputssub.pop('p1')
                out_inputs.append('%s' % str(valsub))
            else:
                valsub=None
                print('Warning: value \'p1\' required for percentile')

        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('%s' % val)

        if len(inputs) > 0:
            print '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())

        return out_inputs


class Threedcalc(AFNICommand):
    """
    For complete details, see the `3dcalc Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dcalc.html>`_
    """

    @property
    def cmd(self):
        """Base command for Threedcalc"""
        return '3dcalc'

    def inputs_help(self):
        doc = """
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""

        self.inputs = Bunch(
            infile_a=None,
            expr=None,
            session=None,
            datum=None,
            outfile=None,
            )

    def _parseinputs(self):
        """Parse valid input options for Threedcalc command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.items() \
             if v is not None]

        if inputs.has_key('infile_a'):
            val = inputs.pop('infile_a')
            out_inputs.append('-a %s' % val)
        if inputs.has_key('expr'):
            val = inputs.pop('expr')
            out_inputs.append('-expr %s' % val)
        if inputs.has_key('session'):
            val = inputs.pop('session')
            out_inputs.append('-session %s' % val)
        if inputs.has_key('datum'):
            val = inputs.pop('datum')
            out_inputs.append('-datum %s' % val)
        if inputs.has_key('outfile'):
            val = inputs.pop('outfile')
            out_inputs.append('-prefix %s' % val)

        if len(inputs) > 0:
            print '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())

        return out_inputs


class ThreedAllineate(AFNICommand):
    """
    For complete details, see the `3dAllineate Documentation.
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dAllineate.html>`_
    """

    @property
    def cmd(self):
        """Base command for ThreedAllineate"""
        return '3dAllineate'

    def inputs_help(self):
        doc = """
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""

        self.inputs = Bunch(
            lpc=None,
            weight_frac=None,
            verbose=None,
            warp=None,
            maxrot=None,
            maxshf=None,
            source_automask=None,
            transform_matrix=None,
            base=None,
            weight=None,
            outfile=None,
            infile=None)

    def _parseinputs(self):
        """Parse valid input options for ThreedSkullStrip command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.items() \
             if v is not None]

        if inputs.has_key('lpc'):
            val = inputs.pop('lpc')
            out_inputs.append('-lpc')
        if inputs.has_key('weight_frac'):
            val = inputs.pop('weight_frac')
            out_inputs.append('-weight_frac %s' % str(val))
        if inputs.has_key('verbose'):
            val = inputs.pop('verbose')
            out_inputs.append('-VERB')
        if inputs.has_key('warp'):
            val = inputs.pop('warp')
            out_inputs.append('-warp %s' % val)
        if inputs.has_key('maxrot'):
            val = inputs.pop('maxrot')
            out_inputs.append('-maxrot %s' % str(val))
        if inputs.has_key('maxshf'):
            val = inputs.pop('maxshf')
            out_inputs.append('-maxshf %s' % str(val))
        if inputs.has_key('source_automask'):
            val = inputs.pop('source_automask')
            out_inputs.append('-source_automask+%s' % str(val))
        if inputs.has_key('transform_matrix'):
            val = inputs.pop('transform_matrix')
            out_inputs.append('-1Dmatrix_save %s' % val)
        if inputs.has_key('base'):
            val = inputs.pop('base')
            out_inputs.append('-base %s' % val)
        if inputs.has_key('weight'):
            val = inputs.pop('weight')
            out_inputs.append('-weight %s' % val)
        if inputs.has_key('outfile'):
            val = inputs.pop('outfile')
            out_inputs.append('-prefix %s' % val)
        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('-source %s' % val)

        if len(inputs) > 0:
            print '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())

        return out_inputs

