"""
    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
    >>> os.chdir(datadir)

"""
import os

from nipype.interfaces.base import (CommandLineInputSpec, CommandLine, traits,
                                    TraitedSpec, File, StdOutCommandLine,
                                    StdOutCommandLineInputSpec, isdefined)
from nipype.utils.filemanip import split_filename

class FSL2SchemeInputSpec(StdOutCommandLineInputSpec):
    bvec_file = File(exists=True, argstr='-bvecfile %s',
                    mandatory=True, position=1,
                    desc='b vector file')

    bval_file = File(exists=True, argstr='-bvalfile %s',
                    mandatory=True, position=2,
                    desc='b value file')

    numscans = traits.Int(argstr='-numscans %d', units='NA',
                desc="Output all measurements numerous (n) times, used when combining multiple scans from the same imaging session.")

    interleave = traits.Bool(argstr='-interleave', desc="Interleave repeated scans. Only used with -numscans.")

    bscale = traits.Float(argstr='-bscale %d', units='NA',
                desc="Scaling factor to convert the b-values into different units. Default is 10^6.")

    diffusiontime = traits.Float(argstr = '-diffusiontime %f', units = 'NA',
                desc="Diffusion time")

    flipx = traits.Bool(argstr='-flipx', desc="Negate the x component of all the vectors.")
    flipy = traits.Bool(argstr='-flipy', desc="Negate the y component of all the vectors.")
    flipz = traits.Bool(argstr='-flipz', desc="Negate the z component of all the vectors.")
    usegradmod = traits.Bool(argstr='-usegradmod', desc="Use the gradient magnitude to scale b. This option has no effect if your gradient directions have unit magnitude.")

class FSL2SchemeOutputSpec(TraitedSpec):
    scheme = File(exists=True, desc='Scheme file')

class FSL2Scheme(StdOutCommandLine):
    """
    Converts b-vectors and b-values from FSL format to a Camino scheme file.

    Examples
    --------

    >>> import nipype.interfaces.camino as cmon
    >>> makescheme = cmon.FSL2Scheme()
    >>> makescheme.inputs.bvec_file = 'bvecs'
    >>> makescheme.inputs.bvec_file = 'bvals'
    >>> makescheme.run()                  # doctest: +SKIP

    """
    _cmd = 'fsl2scheme'
    input_spec=FSL2SchemeInputSpec
    output_spec=FSL2SchemeOutputSpec

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['scheme'] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.bvec_file)
        return name + '.scheme'
