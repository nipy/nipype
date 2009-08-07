"""Provide interface classed to AFNI commands."""


from nipype.interfaces.base import Bunch, CommandLine


class To3d(CommandLine):
    """

    Examples
    --------

    >>> to3d = afni.To3d(anat=True)
    >>> to3d.inputs.datum = 'float'
    >>> to3d.run()

    """

    @property
    def cmd(self):
        """Base command for To3d"""
        return 'to3d'

    def inputs_help(self):
        doc = """
          Optional Parameters
          -------------------
        """
        print doc

    def _populate_inputs(self):
        """Initialize the inputs attribute."""
        self.inputs = Bunch(infiles=None,
                            anat=None,
                            datum=None,
                            session=None,
                            prefix=None,
                            epan=None,
                            skip_outliers=None,
                            assume_dicom_mosaic=None,
                            )

    def _parseinputs(self):
        """Parse valid input options for To3d command.

        Ignore options set to None.

        """

        # Time: -time:zt nz nt TR tpattern  OR  -time:tz nt nz TR tpattern


        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() \
             if v is not None]
        for opt in inputs:
            if opt is 'infiles':
                pass # placeholder to suppress not supported warning
            elif opt is 'anat':
                out_inputs.append('-anat')
            elif opt is 'datum':
                out_inputs.append('-datum %s' % inputs[opt])
            elif opt is 'session':
                out_inputs.append('-session %s' % inputs[opt])
            elif opt is 'prefix':
                out_inputs.append('-prefix %s' % inputs[opt])
            elif opt is 'epan':
                out_inputs.append('-epan')
            elif opt is 'skip_outliers':
                out_inputs.append('-skip_outliers')
            elif opt is 'assume_dicom_mosaic':
                out_inputs.append('-assume_dicom_mosaic')
            else:
                print '%s: option %s is not supported!' % (
                    self.__class__.__name__, opt)

        # Handle positional arguments independently
        if self.inputs['infiles']:
            out_inputs.append('%s' % self.inputs['infiles'])

        return out_inputs

    def _compile_command(self):
        """Generate the command line string from the list of arguments."""
        valid_inputs = self._parseinputs()
        allargs =  [self.cmd] + valid_inputs
        self.cmdline = ' '.join(allargs)
