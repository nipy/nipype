# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Provides interfaces to various commands provided by diffusion toolkit

   Change directory to provide relative paths for doctests
   >>> import os
   >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
   >>> datadir = os.path.realpath(os.path.join(filepath, '../../testing/data'))
   >>> os.chdir(datadir)

"""
import re
from nipype.utils.filemanip import fname_presuffix
__docformat__ = 'restructuredtext'

from nipype.interfaces.base import (TraitedSpec, File, traits, CommandLine,
    CommandLineInputSpec)


class DTIReconInputSpec(CommandLineInputSpec):
    dwi = File(desc='Input diffusion volume', argstr='%s',exists=True, mandatory=True,position=1)
    out_prefix = traits.Str("dti", desc='Output file prefix', argstr='%s', usedefault=True,position=2)
    output_type = traits.Enum('nii', 'analyze', 'ni1', 'nii.gz', argstr='-ot %s', desc='output file type', usedefault=True)    
    bvecs = File(exists=True, desc = 'b vectors file',
                argstr='-gm %s', mandatory=True)
    bvals = File(exists=True,desc = 'b values file', mandatory=True)
    n_averages = traits.Int(desc='Number of averages', argstr='-nex %s')
    image_orientation_vectors = traits.List(traits.Float(), minlen=6, maxlen=6, desc="""specify image orientation vectors. if just one argument given,
will treat it as filename and read the orientation vectors from
the file. if 6 arguments are given, will treat them as 6 float
numbers and construct the 1st and 2nd vector and calculate the 3rd
one automatically.
this information will be used to determine image orientation,
as well as to adjust gradient vectors with oblique angle when""", argstr="-iop %f")
    oblique_correction = traits.Bool(desc="""when oblique angle(s) applied, some SIEMENS dti protocols do not
adjust gradient accordingly, thus it requires adjustment for correct
diffusion tensor calculation""", argstr="-oc")
    b0_threshold = traits.Float(desc="""program will use b0 image with the given threshold to mask out high
background of fa/adc maps. by default it will calculate threshold
automatically. but if it failed, you need to set it manually.""", argstr="-b0_th")
    
    
class DTIReconOutputSpec(TraitedSpec):
    ADC = File(exists=True)
    B0 = File(exists=True)
    L1 = File(exists=True)
    L2 = File(exists=True)
    L3 = File(exists=True)
    exp = File(exists=True)
    FA = File(exists=True)
    FA_color = File(exists=True)
    tensor = File(exists=True)
    V1 = File(exists=True)
    V2 = File(exists=True)
    V3 = File(exists=True)

class DTIRecon(CommandLine):
    """Use dti_recon to generate tensors and other maps
    """
    
    input_spec=DTIReconInputSpec
    output_spec=DTIReconOutputSpec
    
    _gradient_matrix_file = 'gradient_matrix.txt'
    _cmd = 'dti_recon'
    
    def _format_arg(self, name, spec, value):
        if name == "bvecs":
            new_val = self._create_gradient_matrix(self.inputs.bvecs, self.inputs.bvals)
            return super(DTIRecon, self)._format_arg("bvecs", spec, new_val)
        return super(DTIRecon, self)._format_arg(name, spec, value)
        
    def _create_gradient_matrix(self, bvecs_file, bvals_file):
        bvals = [val for val in  re.split('\s+', open(bvals_file).readline().strip())]
        bvecs_f = open(bvecs_file)
        bvecs_x = [val for val in  re.split('\s+', bvecs_f.readline().strip())]
        bvecs_y = [val for val in  re.split('\s+', bvecs_f.readline().strip())]
        bvecs_z = [val for val in  re.split('\s+', bvecs_f.readline().strip())]
        bvecs_f.close()
        gradient_matrix_f = open(self._gradient_matrix_file, 'w')
        print len(bvals), len(bvecs_x), len(bvecs_y), len(bvecs_z)
        for i in range(len(bvals)):
            gradient_matrix_f.write("%s, %s, %s, %s\n"%(bvecs_x[i], bvecs_y[i], bvecs_z[i], bvals[i]))
        gradient_matrix_f.close()
        return self._gradient_matrix_file

    def _list_outputs(self):
        out_prefix = self.inputs.out_prefix
        output_type = self.inputs.output_type

        outputs = self.output_spec().get()
        outputs['ADC'] = fname_presuffix("",  prefix=out_prefix, suffix='_adc.'+ output_type)
        outputs['B0'] = fname_presuffix("",  prefix=out_prefix, suffix='_b0.'+ output_type)
        outputs['L1'] = fname_presuffix("",  prefix=out_prefix, suffix='_e1.'+ output_type)
        outputs['L2'] = fname_presuffix("",  prefix=out_prefix, suffix='_e2.'+ output_type)
        outputs['L3'] = fname_presuffix("",  prefix=out_prefix, suffix='_e3.'+ output_type)
        outputs['exp'] = fname_presuffix("",  prefix=out_prefix, suffix='_exp.'+ output_type)
        outputs['FA'] = fname_presuffix("",  prefix=out_prefix, suffix='_fa.'+ output_type)
        outputs['FA_color'] = fname_presuffix("",  prefix=out_prefix, suffix='_fa_color.'+ output_type)
        outputs['tensor'] = fname_presuffix("",  prefix=out_prefix, suffix='_tensor.'+ output_type)
        outputs['V1'] = fname_presuffix("",  prefix=out_prefix, suffix='_v1.'+ output_type)
        outputs['V2'] = fname_presuffix("",  prefix=out_prefix, suffix='_v2.'+ output_type)
        outputs['V3'] = fname_presuffix("",  prefix=out_prefix, suffix='_v3.'+ output_type)

        return outputs