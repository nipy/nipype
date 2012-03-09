from nipype.interfaces.spm.base import SPMCommandInputSpec, SPMCommand, scans_for_fnames, scans_for_fname, traits
from nipype.interfaces.base import File, OutputMultiPath, InputMultiPath
from nipype.utils.filemanip import split_filename, fname_presuffix, filename_to_list,list_to_filename
import os
import numpy as np

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


class ApplyInverseDeformationInput(SPMCommandInputSpec):
    in_files = InputMultiPath(
        traits.Either(traits.List(File(exists=True)),File(exists=True)),
        field='fnames',
        mandatory=True,
        desc='Files on which deformation is applied')
    target = File(
        exists=True,
        field='comp{1}.inv.space',
        desc='File defining target space')
    deformation = File(
        exists=True,
        field='comp{1}.inv.comp{1}.sn2def.matname',
        desc='SN SPM deformation file')
    interpolation = traits.Range(
        low=0, hign=7, field='interp',
        desc='degree of b-spline used for interpolation')

    bounding_box = traits.List(
        traits.Float(),
        field='comp{1}.inv.comp{1}.sn2def.bb',
        minlen=6, maxlen=6,
        desc='6-element list (opt)')
    voxel_sizes = traits.List(
        traits.Float(),
        field='comp{1}.inv.comp{1}.sn2def.vox',
        minlen=3, maxlen=3,
        desc='3-element list (opt)')

    
class ApplyInverseDeformationOutput(SPMCommandInputSpec):
    out_files = OutputMultiPath(File(exists=True),
                                desc='Transformed files')

class ApplyInverseDeformation(SPMCommand):

    input_spec  = ApplyInverseDeformationInput
    output_spec = ApplyInverseDeformationOutput
    
    _jobtype = 'util'
    _jobname = 'defs'


    def _format_arg(self, opt, spec, val):
        """Convert input to appropriate format for spm
        """
        if opt == 'in_files':
            return scans_for_fnames(filename_to_list(val))
        if opt == 'target':
            return scans_for_fname(filename_to_list(val))
        if opt == 'deformation':
            return np.array([list_to_filename(val)], dtype=object)
        return val

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_files'] = []
        for imgf in filename_to_list(self.inputs.in_files):
            
            outputs['out_files'].append(
                fname_presuffix(imgf,prefix='w',newpath=os.getcwd()))
        return outputs
