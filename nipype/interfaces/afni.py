"""Provide interface to AFNI commands."""

__docformat__ = 'restructuredtext'

from nipype.interfaces.base import Bunch, CommandLine

class To3d(CommandLine):
    """Create 3D dataset from 2D image files.

    Uses the AFNI command-line tool 'to3d'.

    Examples
    --------
    Basic usage examples.

    >>> to3d = afni.To3d(datatype="anat")
    >>> to3d.inputs.datum = 'float'
    >>> to3d.run()

    """

    @property
    def cmd(self):
        """Base command for To3d"""
        return 'to3d'

    def inputs_help(self):
        doc = """
        """
        print doc

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

    def _parseinputs(self):
        """Parse valid input options for To3d command.

        Ignore options set to None.

        """
        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() \
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
            [inputssub.update({k:v}) for k, v in val.iteritems() \
                if v is not None]

            # -time:zt nz nt TR tpattern  OR  -time:tz nt nz TR tpattern
            # time : list
            #    zt nz nt TR tpattern
            #    tz nt nz TR tpattern
            # TODO: ABOVE DOC IS OLD

            # dict(slice_order='zt', nz=12, nt=150, TR=2000, tpattern='alt+z')
            _time_dep_doc = \
            """
            time_dependencies should be a dictionary with the follow keys 
            assigned:
            slice_order, nz, nt, TR, tpattern

            """

            """
            if inputssub.has_key('slice_order'):
                valsub = inputssub.pop('slice_order')
                out_inputs.append('-time:%s' % valsub)
            else:
                valsub=None
                print('Warning: slice_order required for time_dependencies')
            """
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
                print '%s: unsupported time_dependencies options: %s' % (
                    self.__class__.__name__, inputssub.keys())

        if inputs.has_key('session'):
            val = inputs.pop('session')
            out_inputs.append('-session %s' % val)
        if inputs.has_key('prefix'):
            val = inputs.pop('prefix')
            out_inputs.append('-prefix %s' % val)
        if inputs.has_key('infiles'):
            val = inputs.pop('infiles')
            out_inputs.append('%s' % val)

        if len(inputs) > 0:
            print '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())

        return out_inputs

    @property
    def cmdline(self):
        """Generate the command line string from the list of arguments."""
        valid_inputs = self._parseinputs()
        allargs =  [self.cmd] + valid_inputs
        return ' '.join(allargs)


class Threedrefit(CommandLine):
    """
    """

    @property
    def cmd(self):
        """Base command for Threedrefit"""
        return '3drefit'

    def inputs_help(self):
        doc = """
          Optional Parameters
          -------------------
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""
        self.inputs = Bunch(deoblique=None,
                            xorigin=None,
                            yorigin=None,
                            zorigin=None,
                            infile=None)

    def _parseinputs(self):
        """Parse valid input options for Threedrefit command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() \
             if v is not None]

        if inputs.has_key('deoblique'):
            val = inputs.pop('deoblique')
            out_inputs.append('-deoblique')
        if inputs.has_key('xorigin'):
            val = inputs.pop('xorigin')
            out_inputs.append('-xorigin %s' % val)
        if inputs.has_key('yorigin'):
            val = inputs.pop('yorigin')
            out_inputs.append('-yorigin %s' % val)
        if inputs.has_key('zorigin'):
            val = inputs.pop('zorigin')
            out_inputs.append('-zorigin %s' % val)
        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('%s' % val)

        if len(inputs) > 0:
            print '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())

        return out_inputs

    @property
    def cmdline(self):
        """Generate the command line string from the list of arguments."""
        valid_inputs = self._parseinputs()
        allargs =  [self.cmd] + valid_inputs
        return ' '.join(allargs)


class Threedresample(CommandLine):
    """
    """

    @property
    def cmd(self):
        """Base command for Threedresample"""
        return '3dresample'

    def inputs_help(self):
        doc = """
          Optional Parameters
          -------------------
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""

        self.inputs = Bunch(orient=None,
                            outfile=None,
                            infile=None)

    def _parseinputs(self):
        """Parse valid input options for Threedresample command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() \
             if v is not None]

        if inputs.has_key('orient'):
            val = inputs.pop('orient')
            out_inputs.append('-orient %s' % val)
        if inputs.has_key('outfile'):
            val = inputs.pop('outfile')
            out_inputs.append('-prefix %s' % val)
        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('-inset %s' % val)

        if len(inputs) > 0:
            print '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())

        return out_inputs

    @property
    def cmdline(self):
        """Generate the command line string from the list of arguments."""
        valid_inputs = self._parseinputs()
        allargs = [self.cmd] + valid_inputs
        return ' '.join(allargs)


class ThreedTstat(CommandLine):
    """
    """

    @property
    def cmd(self):
        """Base command for ThreedTstat"""
        return '3dTstat'

    def inputs_help(self):
        doc = """
          Optional Parameters
          -------------------
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""

        self.inputs = Bunch(outfile=None,
                            infile=None)

    def _parseinputs(self):
        """Parse valid input options for ThreedTstat command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() \
             if v is not None]

        if inputs.has_key('outfile'):
            val = inputs.pop('outfile')
            out_inputs.append('-prefix %s' % val)
        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('%s' % val)

        if len(inputs) > 0:
            print '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())

        return out_inputs

    @property
    def cmdline(self):
        """Generate the command line string from the list of arguments."""
        valid_inputs = self._parseinputs()
        allargs =  [self.cmd] + valid_inputs
        return ' '.join(allargs)


class ThreedAutomask(CommandLine):
    """
    """

    @property
    def cmd(self):
        """Base command for ThreedAutomask"""
        return '3dAutomask'

    def inputs_help(self):
        doc = """
          Optional Parameters
          -------------------
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""

        self.inputs = Bunch(outfile=None,
                            infile=None)

    def _parseinputs(self):
        """Parse valid input options for ThreedAutomask command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() \
             if v is not None]

        if inputs.has_key('outfile'):
            val = inputs.pop('outfile')
            out_inputs.append('-prefix %s' % val)
        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('%s' % val)

        if len(inputs) > 0:
            print '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())

        return out_inputs

    @property
    def cmdline(self):
        """Generate the command line string from the list of arguments."""
        valid_inputs = self._parseinputs()
        allargs =  [self.cmd] + valid_inputs
        return ' '.join(allargs)


class Threedvolreg(CommandLine):
    """
    """

    @property
    def cmd(self):
        """Base command for Threedvolreg"""
        return '3dvolreg'

    def inputs_help(self):
        doc = """
          Optional Parameters
          -------------------
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""

        self.inputs = Bunch(
            verbose=None,
            copy_origin=None,
            time_shift=None,
            basefile=None,
            md1dfile=None,
            onedfile=None,
            outfile=None,
            infile=None)

    def _parseinputs(self):
        """Parse valid input options for Threedvolreg command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() \
             if v is not None]

        if inputs.has_key('verbose'):
            val = inputs.pop('verbose')
            out_inputs.append('-verbose')
        if inputs.has_key('copy_origin'):
            val = inputs.pop('copy_origin')
            out_inputs.append('-twodup')
        if inputs.has_key('time_shift'):
            val = inputs.pop('time_shift')
            out_inputs.append('-tshift %s' % str(val))
        if inputs.has_key('basefile'):
            val = inputs.pop('basefile')
            out_inputs.append('-base %s' % val)
        if inputs.has_key('md1dfile'):
            val = inputs.pop('md1dfile')
            out_inputs.append('-maxdisp1D %s' % val)
        if inputs.has_key('onedfile'):
            val = inputs.pop('onedfile')
            out_inputs.append('-1Dfile %s' % val)
        if inputs.has_key('outfile'):
            val = inputs.pop('outfile')
            out_inputs.append('-prefix %s' % val)
        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('%s' % val)

        if len(inputs) > 0:
            print '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())

        return out_inputs

    @property
    def cmdline(self):
        """Generate the command line string from the list of arguments."""
        valid_inputs = self._parseinputs()
        allargs =  [self.cmd] + valid_inputs
        return ' '.join(allargs)


class Threedmerge(CommandLine):
    """
    """

    @property
    def cmd(self):
        """Base command for Threedmerge"""
        return '3dmerge'

    def inputs_help(self):
        doc = """
          Optional Parameters
          -------------------
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""

        self.inputs = Bunch(doall = True,
                            gblur_fwhm = 5,
                            outfile=None,
                            infile=None)

    def _parseinputs(self):
        """Parse valid input options for Threedmerge command.

        Ignore options set to None.

        """

        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() \
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
        if inputs.has_key('infile'):
            val = inputs.pop('infile')
            out_inputs.append('%s' % val)

        if len(inputs) > 0:
            print '%s: unsupported options: %s' % (
                self.__class__.__name__, inputs.keys())

        return out_inputs

    @property
    def cmdline(self):
        """Generate the command line string from the list of arguments."""
        valid_inputs = self._parseinputs()
        allargs =  [self.cmd] + valid_inputs
        return ' '.join(allargs)


