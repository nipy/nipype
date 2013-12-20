# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provide interface to AFNI commands."""


import os
import warnings

from ...utils.filemanip import split_filename
from ..base import (
    CommandLine, traits, CommandLineInputSpec, isdefined, File, TraitedSpec)

warn = warnings.warn
warnings.filterwarnings('always', category=UserWarning)


class Info(object):
    """Handle afni output type and version information.
    """
    __outputtype = 'AFNI'
    ftypes = {'NIFTI': '.nii',
              'AFNI': '',
              'NIFTI_GZ': '.nii.gz'}

    @staticmethod
    def version():
        """Check for afni version on system

        Parameters
        ----------
        None

        Returns
        -------
        version : str
           Version number as string or None if AFNI not found

        """
        clout = CommandLine(command='afni_vcheck',
                            terminal_output='allatonce').run()
        out = clout.runtime.stdout
        return out.split('\n')[1]

    @classmethod
    def outputtype_to_ext(cls, outputtype):
        """Get the file extension for the given output type.

        Parameters
        ----------
        outputtype : {'NIFTI', 'NIFTI_GZ', 'AFNI'}
            String specifying the output type.

        Returns
        -------
        extension : str
            The file extension for the output type.
        """

        try:
            return cls.ftypes[outputtype]
        except KeyError:
            msg = 'Invalid AFNIOUTPUTTYPE: ', outputtype
            raise KeyError(msg)

    @classmethod
    def outputtype(cls):
        """AFNI has no environment variables,
        Output filetypes get set in command line calls
        Nipype uses AFNI as default


        Returns
        -------
        None
        """
        #warn(('AFNI has no environment variable that sets filetype '
        #      'Nipype uses NIFTI_GZ as default'))
        return 'AFNI'

    @staticmethod
    def standard_image(img_name):
        '''Grab an image from the standard location.

        Could be made more fancy to allow for more relocatability'''
        clout = CommandLine('which afni',
                            terminal_output='allatonce').run()
        if clout.runtime.returncode is not 0:
            return None

        out = clout.runtime.stdout
        basedir = os.path.split(out)[0]
        return os.path.join(basedir, img_name)


class AFNICommandInputSpec(CommandLineInputSpec):
    outputtype = traits.Enum('AFNI', Info.ftypes.keys(),
                             desc='AFNI output filetype')
    out_file = File(name_template="%s_afni", desc='output image file name',
                    argstr='-prefix %s',
                    name_source=["in_file"])

class AFNICommandOutputSpec(TraitedSpec):
    out_file = File(desc='output file',
                    exists=True)


class AFNICommand(CommandLine):

    input_spec = AFNICommandInputSpec
    _outputtype = None


    def __init__(self, **inputs):
        super(AFNICommand, self).__init__(**inputs)
        self.inputs.on_trait_change(self._output_update, 'outputtype')

        if self._outputtype is None:
            self._outputtype = Info.outputtype()

        if not isdefined(self.inputs.outputtype):
            self.inputs.outputtype = self._outputtype
        else:
            self._output_update()

    def _output_update(self):
        """ i think? updates class private attribute based on instance input
         in fsl also updates ENVIRON variable....not valid in afni
         as it uses no environment variables
        """
        self._outputtype = self.inputs.outputtype

    @classmethod
    def set_default_output_type(cls, outputtype):
        """Set the default output type for AFNI classes.

        This method is used to set the default output type for all afni
        subclasses.  However, setting this will not update the output
        type for any existing instances.  For these, assign the
        <instance>.inputs.outputtype.
        """

        if outputtype in Info.ftypes:
            cls._outputtype = outputtype
        else:
            raise AttributeError('Invalid AFNI outputtype: %s' % outputtype)

    def _overload_extension(self, value):
        path, base, _ = split_filename(value)
        return os.path.join(path, base + Info.outputtype_to_ext(self.inputs.outputtype))

    def _list_outputs(self):
        outputs = super(AFNICommand, self)._list_outputs()
        metadata = dict(name_source=lambda t: t is not None)
        out_names = self.inputs.traits(**metadata).keys()
        if out_names:
            for name in out_names:
                if outputs[name]:
                    _,_,ext = split_filename(outputs[name])
                    if ext == "":
                        outputs[name] = outputs[name] + "+orig.BRIK"
        return outputs
