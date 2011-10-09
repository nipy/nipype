from nipype.interfaces.spm.base import SPMCommandInputSpec, SPMCommand
from nipype.interfaces.base import File
from nipype.utils.filemanip import split_filename
import os

class Analyze2niiInputSpec(SPMCommandInputSpec):
    analyze_file = File(exists=True, mandatory=True)

class Analyze2niiOutputSpec(SPMCommandInputSpec):
    nifti_file = File(exists=True)

class Analyze2nii(SPMCommand):

    input_spec = Analyze2niiInputSpec
    output_spec = Analyze2niiOutputSpec

    def _make_matlab_command(self, _):
        script = "V = spm_vol('%s');\n"%self.inputs.analyze_file
        _, name,_ = split_filename(self.inputs.analyze_file)
        self.output_name = os.path.join(os.getcwd(), name + ".nii")
        script += "[Y, XYZ] = spm_read_vols(V);\n"
        script += "V.fname = '%s';\n"%self.output_name
        script += "spm_write_vol(V, Y);\n"

        return script

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['nifti_file'] = self.output_name
        return outputs
