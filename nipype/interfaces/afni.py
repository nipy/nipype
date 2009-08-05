"""Provide interface classed to AFNI commands."""


from nipype.interfaces.base import Bunch, CommandLine


class to3d(CommandLine):
    """

    Examples
    --------
    
    >>> to3d = afni.to3d(anat=True)
    >>> to3d.inputs.datum = 'float'
    >>> to3d.run()

    """

    @property
    def cmd(self):
        """Base command for to3d"""
        return 'to3d'

    def inputs_help(self):
        doc = """
          Optional Parameters
          -------------------
        """
        print doc


    def copy(self):
       """Return a copy of the interface object."""
       return to3d(**self.inputs.dictcopy())

    def _populate_inputs(self):
       """Initialize the inputs attribute."""
       self.inputs = Bunch(anat=None,
                           datum=None,
                           session=None,
                           prefix=None,
                           infiles=None)

    def _parseinputs(self):
        """validate fsl bet options
        if set to None ignore
        """
        out_inputs = []
        inputs = {}
        [inputs.update({k:v}) for k, v in self.inputs.iteritems() \
             if v is not None]
        for opt in inputs:
            if opt is 'anat':
                if inputs[opt]:
                    out_inputs.append('-anat')
                continue
            if opt is 'datum':
                if inputs[opt]:
                    out_inputs.extend(['-datum %s' % inputs[opt]])
                continue
            if opt is 'session':
                if inputs[opt]:
                    out_inputs.extend(['-session %s' % inputs[opt]])
                continue
            if opt is 'prefix':
                if inputs[opt]:
                    out_inputs.extend(['-prefix %s' % inputs[opt]])
                continue

        # Handle positional arguments independently
        if inputs['infiles']:
            out_inputs.append('%s' % inputs['infiles'])

        return out_inputs

    def _compile_command(self):
       """Generate the command line string from the list of arguments."""
       valid_inputs = self._parseinputs()
       allargs =  [self.cmd] + valid_inputs
       self.cmdline = ' '.join(allargs)
    
