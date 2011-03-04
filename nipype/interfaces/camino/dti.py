from nipype.interfaces.base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File
from nipype.utils.filemanip import split_filename
import os

class DTIFitInputSpec(CommandLineInputSpec):
    """
    * Reads diffusion MRI data, acquired using the acquisition scheme detailed in the scheme file, from the data file. 
    * For help with scheme files, please see the section "scheme files" in camino(1).  OPTIONS

    dtfit <data file> <scheme file> [-nonlinear] [options] --nonlinear
    
        Use non-linear fitting instead of the default linear regression to the log measurements. 
    The data file stores the diffusion MRI data in voxel order with the measurements stored in big-endian format and ordered as in the scheme file.
    The default input data type is four-byte float. The default output data type is eight-byte double.
    See modelfit and camino for the format of the data file and scheme file.
    The program fits the diffusion tensor to each voxel and outputs the results, 
    in voxel order and as big-endian eight-byte doubles, to the standard output. 
    The program outputs eight values in each voxel: [exit code, ln(S(0)), D_xx, D_xy, D_xz, D_yy, D_yz, D_zz]. 
    An exit code of zero indicates no problems. For a list of other exit codes, see modelfit(1). The entry S(0) is an estimate of the signal at q=0. 
    """
    
    in_file = File(exists=True, argstr='%s',
                    mandatory=True, position=1,
                    desc='voxel-order data filename')
    
    scheme_file = File(exists=True, argstr='%s',
                    mandatory=True, position=2,
                    desc='Camino scheme file (b values / vectors, see camino.fsl2scheme)')
    
    non_linear = traits.Bool(argstr='-nonlinear', position=3, desc="Use non-linear fitting instead of the default linear regression to the log measurements. ")
    
    out_file = File(argstr="> %s", position=4, genfile=True)              
            
class DTIFitOutputSpec(TraitedSpec):
    """Use dtfit to fit tensors to each voxel
    """
    out_file = File(exists=True, desc='path/name of 4D volume in voxel order') 

class DTIFit(CommandLine):
    """Use dtfit to fit tensors to each voxel
    """
    _cmd = 'dtfit'
    input_spec=DTIFitInputSpec
    output_spec=DTIFitOutputSpec
    
    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = os.path.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_file':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + "_DT.Bdouble"
        