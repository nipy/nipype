"""Provide interface to AFNI commands."""
__docformat__ = 'restructuredtext'


import os
from glob import glob
import warnings

from nipype.interfaces.afni.base import Info, AFNITraitedSpec, AFNICommand
from nipype.interfaces.base import Bunch, TraitedSpec, File, InputMultiPath
from nipype.utils.filemanip import fname_presuffix, list_to_filename, split_filename
from nipype.utils.docparse import get_doc
from nipype.utils.misc import container_to_string, is_container, isdefined

import enthought.traits.api as traits

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class To3dInputSpec(AFNITraitedSpec):
    pass

class To3dOutputSpec(TraitedSpec):
    pass

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

    @property
    def cmd(self):
        """Base command for To3d"""
        return 'to3d'

    def inputs_help(self):
        """Print command line documentation for to3d."""
        #print get_doc(self.cmd, self.opt_map)
        raise NotImplementedError

    def _populate_inputs(self):
        """Initialize the inputs attribute."""
        self.inputs = Bunch(datatype=None,
                            skip_outliers=None,
                            assume_dicom_mosaic=None,
                            datum=None,
                            time_dependencies=None,
                            session=None,
                            prefix=None,
                            infiles=None)

    opt_map = {'datatype' : '-%s',
               'skip_outliers' : '-skip_outliers',
               'assume_dicom_mosaic' : '-assume_dicom_mosaic',
               'datum' : '-datum %s',
               'time_dependencies' : '-time:%s %d %d %.2f %s',
               'session' : '-session %s',
               'prefix' : '-prefix %s',
               }

    def _parseinputs_old(self):
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


    def run(self, infiles=None, **inputs):
        """Execute the command.

        Parameters
        ----------
        infiles : string or list of strings
            File or list of files to combine into 3d file.
        inputs : dict
            Dictionary of any additional flags to send to to3d
        
        Returns
        -------
        results : InterfaceResult
            A `InterfaceResult` object with a copy of self in `interface`

        """
        if infiles:
            self.inputs.infiles = infiles
        if not self.inputs.infiles:
            raise AttributeError('To3d requires infiles.')
        self.inputs.update(**inputs)
        results = self._runner()
        # XXX implement aggregate_outputs
        return results


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

        return out_inputs'''


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


class Threedmerge(AFNICommand):
    """Merge or edit volumes using AFNI 3dmerge command.

    For complete details, see the `3dmerge Documentation. 
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmerge.html>`_
    """

    @property
    def cmd(self):
        """Base command for Threedmerge"""
        return '3dmerge'

    def inputs_help(self):
        doc = """
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""

        self.inputs = Bunch(
            doall=None,
            gblur_fwhm=None,
            outfile=None,
            infiles=None)

    def _parseinputs(self):
        """Parse valid input options for Threedmerge command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.items() \
             if v is not None]

        if inputs.has_key('doall'):
            val = inputs.pop('doall')
            out_inputs.append('-doall')
        if inputs.has_key('gblur_fwhm'):
            val = inputs.pop('gblur_fwhm')
            out_inputs.append('-1blur_fwhm %s' % str(val))
        if inputs.has_key('outfile'):
            val = inputs.pop('outfile')
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

    def run(self, infiles=None, **inputs):
        """Execute 3dmerge

        Parameters
        ----------
        infiles : string or list of strings
            Files to edit or merge
        inputs : dict
            Dictionary of any additional flags to send to 3dmerge

        Returns
        -------
        results : InterfaceResult
            A `InterfaceResult` object with a copy of self in `interface`

        """
        if infiles:
            self.inputs.infiles = infiles
        if not self.inputs.infiles:
            raise AttributeError('Threedmerge requires an infile.')
        self.inputs.update(**inputs)
        results = self._runner()
        # XXX implement aggregate_outputs
        return results


class ThreedZcutup(AFNICommand):
    """Cut z-slices from a volume using AFNI 3dZcutup command.

    For complete details, see the `3dZcutup Documentation. 
    <http://afni.nimh.nih.gov/pub/dist/doc/program_help/3dZcutup.html>`_
    """

    @property
    def cmd(self):
        """Base command for ThreedZcutup"""
        return '3dZcutup'

    def inputs_help(self):
        doc = """
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""

        self.inputs = Bunch(
            keep=None,
            outfile=None,
            infile=None)

    def _parseinputs(self):
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

