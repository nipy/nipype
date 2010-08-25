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
__docformat__ = 'restructuredtext'


"""from nipype.interfaces.dtk.base import (DTKCommandInputSpec, DTKCommand)"""
"""@TEMP"""
from base import (DTKCommandInputSpec, DTKCommand)
"""@TEMP"""
from nipype.interfaces.base import (TraitedSpec, File, traits)
from nipype.utils.misc import isdefined


class DTIReconInputSpec(DTKCommandInputSpec):
    dwi = File(desc='Input diffusion volume', argstr='%s',exists=True, mandatory=True,position=1)
    out_prefix = traits.Str("dti", desc='Output file prefix', argstr='%s', usedefault=True,position=2)
    output_type = traits.Enum('analyze', 'ni1', 'nii', 'nii.gz', argstr='-ot %s', desc='output file type')    
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
    adc_img = File(exists=True)
    b0_img = File(exists=True)
    dwi_img = File(exists=True)
    e1_img = File(exists=True)
    e2_img = File(exists=True)
    e3_img = File(exists=True)
    exp_img = File(exists=True)
    fa_img = File(exists=True)
    fa_color_img = File(exists=True)
    tensor_img = File(exists=True)
    v1_img = File(exists=True)
    v2_img = File(exists=True)
    v3_img = File(exists=True)

class DTIRecon(DTKCommand):
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
        if not isdefined(output_type):
            output_type='nii'

        outputs = self.output_spec().get()
        outputs['adc_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_adc')
        outputs['b0_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_b0')
        outputs['dwi_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_dwi')
        outputs['e1_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_e1')
        outputs['e2_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_e2')
        outputs['e3_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_e3')
        outputs['exp_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_exp')
        outputs['fa_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_fa')
        outputs['fa_color_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_fa_color')
        outputs['tensor_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_tensor')
        outputs['v1_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_v1')
        outputs['v2_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_v2')
        outputs['v3_img'] = self._gen_fname('%s.%s' % (out_prefix, output_type), suffix='_v3')

        return outputs