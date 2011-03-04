# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The Camino module provides classes for interfacing with the Camino Diffusion Toolbox
--------
See the docstrings of the individual classes for examples.

"""

from glob import glob
import os
import warnings

from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.base import CommandLine, traits, CommandLineInputSpec
from nipype.utils.misc import isdefined

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)

class Info(object):
    """Handle camino info
    """

class CaminoCommandInputSpec(CommandLineInputSpec):
    """
    Base Input Specification for all FSL Commands

    All command support specifying FSLOUTPUTTYPE dynamically
    via output_type.
    
    Example
    -------
    fsl.ExtractRoi(tmin=42, tsize=1, output_type='NIFTI')
    
    output_type =  traits.Enum('NIFTI', Info.ftypes.keys(),
                              desc='FSL output type')
	"""
    
class CaminoCommand(CommandLine):
    """Base support for Camino commands.
    
    """

    def _gen_fname(self, basename, cwd=None, suffix=None, change_ext=True, ext=None):
        """Generate a filename based on the given parameters.

        The filename will take the form: cwd/basename<suffix><ext>.
        If change_ext is True, it will use the extentions specified in
        <instance>intputs.output_type.

        Parameters
        ----------
        basename : str
            Filename to base the new filename on.
        cwd : str
            Path to prefix to the new filename. (default is os.getcwd())
        suffix : str
            Suffix to add to the `basename`.  (defaults is '' )
        change_ext : bool
            Flag to change the filename extension to the FSL output type.
            (default True)

        Returns
        -------
        fname : str
            New filename based on given parameters.

        """

        if basename == '':
            msg = 'Unable to generate filename for command %s. ' % self.cmd
            msg += 'basename is not set!'
            raise ValueError(msg)
        if cwd is None:
            cwd = os.getcwd()
        if ext is None:
            ext = ''
        if change_ext:
            if suffix:
                suffix = ''.join((suffix, ext))
            else:
                suffix = ext
        fname = fname_presuffix(basename, suffix = suffix,
                                use_ext = False, newpath = cwd)
        return fname
    
input_spec = CaminoCommandInputSpec
    #_output_type = None

#    def __init__(self):
#        super(CaminoCommand, self)

def __init__(self, **inputs):
        super(CaminoCommand, self).__init__(**inputs)
