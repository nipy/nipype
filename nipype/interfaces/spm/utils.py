# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from nipype.interfaces.spm.base import SPMCommandInputSpec, SPMCommand, Info
from nipype.interfaces.matlab import MatlabCommand
from nipype.interfaces.base import TraitedSpec, BaseInterface, BaseInterfaceInputSpec
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

class CalcCoregAffineInputSpec(SPMCommandInputSpec):
    target = File(exists=True, mandatory=True,
                  desc='target for generating affine transform')
    moving = File(exists=True,mandatory=True, 
                  desc='volume transform can be applied to register with target')
    mat = File( desc = 'Filename used to store affine matrix')

class CalcCoregAffineOutputSpec(SPMCommandInputSpec):
    mat = File(exists=True, desc = 'Matlab file holding transform')

class CalcCoregAffine(SPMCommand):
    """ Uses SPM (spm_coreg) to calculate the transform mapping
    moving to target. Saves Transform in mat (matlab binary file)
    
    Examples
    --------

    >>> import nipype.interfaces.spm.utils as spmu
    >>> coreg = spmu.CalcCoregAffine(matlab_cmd='matlab-spm8')
    >>> coreg.inputs.target = 'structural.nii'
    >>> coreg.inputs.moving = 'functional.nii'
    >>> coreg.inputs.mat = 'func_to_struct.mat'
    >>> coreg.run() # doctest: +SKIP

    Notes
    -----
    
     * the output file mat is saves as a matlab binary file
     * calculating the transforms does NOT change either input image
       it does not **move** the moving image, only calculates the transform
       that can be used to move it 
    """
    
    input_spec = CalcCoregAffineInputSpec
    output_spec = CalcCoregAffineOutputSpec

    def _make_matlab_command(self, _):
        """checks for SPM, generates script"""
        try:
            ver = Info.version(matlab_cmd = self.inputs.matlab_cmd)
        except:
            ver = Info.version()
        if ver is None:
            raise RuntimeError('spm not found')
            # No spm
        script = """
        target = '%s';
        moving = '%s';
        targetv = spm_vol(target);
        movingv = spm_vol(moving);
        x = spm_coreg(movingv, targetv);
        M = spm_matrix(x(:)');
        save('%s' , 'M' );            
        """%(self.inputs.target, 
             self.inputs.moving,
             self.inputs.mat)
        return script        
        
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['mat'] = os.path.abspath(self.inputs.mat)
        return outputs

class ApplyTransformInputSpec(SPMCommandInputSpec):
    pass
