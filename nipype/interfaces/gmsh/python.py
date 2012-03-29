# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from nipype.interfaces.base import (TraitedSpec, BaseInterface, BaseInterfaceInputSpec,
                                    File, isdefined, traits)
from nipype.utils.filemanip import split_filename
import os, os.path as op
from nipype.workflows.misc.utils import get_data_dims, get_vox_dims
import nibabel as nb, nibabel.trackvis as trk
import numpy as np
from nibabel.trackvis import HeaderError
from nibabel.volumeutils import native_code
from nipype.utils.misc import package_check
import warnings

try:
    package_check('dipy')
except Exception, e:
    warnings.warn('dipy not installed')

from ... import logging

iflogger = logging.getLogger('interface')


def nifti_to_gmsh_tensor_elements(in_file, out_file, mask_file, fa_file, mask_threshold=0.1, fa_threshold=0.3, above=True):
    tensor_image = nb.load(in_file)
    mask_image = nb.load(mask_file)
    fa_image = nb.load(fa_file)
    path, name, ext = split_filename(in_file)
    f = open(out_file,'w')
    iflogger.info('Writing tensors to {f}'.format(f=out_file))
    data = tensor_image.get_data()
    fa_data = fa_image.get_data()
    mask_data = mask_image.get_data()
    data = np.flipud(data)
    mask_data = np.flipud(mask_data)
    fa_data = np.flipud(fa_data)
    header = tensor_image.get_header()
    zooms = header.get_zooms()
    elements = []
    tensors = {}
    node_positions = {}

    node_id = 0
    element_id = 10000000
    vx = zooms[0]
    vy = zooms[1]
    vz = zooms[2]
    halfx = np.shape(data)[0]/2
    halfy = np.shape(data)[1]/2
    halfz = np.shape(data)[2]/2

    iflogger.info('Writing the header for the file...')
    intro_list = ['$MeshFormat']
    intro_list.append('2.0 0 8')
    intro_list.append('$EndMeshFormat')
    intro_list.append('$Nodes')
    for intro_str in intro_list:
        f.write(intro_str + '\n')

    node_info = []
    nodes = np.zeros((np.shape(data)[0:3]))
    iflogger.info('Writing the position of each node...')
    iflogger.info(np.shape(data))
    for x in range(0,np.shape(data)[0]):
        for y in range(0,np.shape(data)[1]):
            for z in range(0,np.shape(data)[2]):
                    node_id += 1
                    nodes[x,y,z] = node_id
                    node_str = ('%d %f %f %f' % (node_id, x*vx-halfx*vx, z*vz-halfz*vz, -y*vy+halfy*vy))
                    node_info.append(node_str)

    n_node_str = ('%d' % (len(node_info)))
    f.write(n_node_str + '\n')
    for node_str in node_info:
        f.write(node_str + '\n')

    iflogger.info('Calculating the tensor for each element...')
    for x in range(0,np.shape(data)[0]-1):
        for y in range(0,np.shape(data)[1]-1):
            for z in range(0,np.shape(data)[2]-1):
                if above == True:
                    if mask_data[x,y,z] >= mask_threshold and fa_data[x,y,z] >= fa_threshold:
                        tensor = np.zeros((3,3))
                        tensor[0,0] = data[x,y,z,0]
                        tensor[1,0] = data[x,y,z,1]
                        tensor[1,1] = data[x,y,z,2]
                        tensor[2,0] = data[x,y,z,3]
                        tensor[2,1] = data[x,y,z,4]
                        tensor[2,2] = data[x,y,z,5]
                        tensor = tensor + tensor.T
                        element_id += 1
                        elements.append(element_id)
                        try:
                            node_positions[element_id] = [nodes[x,y,z], nodes[x+1,y,z], nodes[x+1,y+1,z], nodes[x,y+1,z], nodes[x,y,z+1], nodes[x+1,y,z+1], nodes[x+1,y+1,z+1], nodes[x,y+1,z+1]]
                            tensors[element_id] = tensor
                        except IndexError:
                            continue
                else:
                    if mask_data[x,y,z] >= mask_threshold and fa_data[x,y,z] <= fa_threshold:
                        tensor = np.zeros((3,3))
                        tensor[0,0] = data[x,y,z,0]
                        tensor[1,0] = data[x,y,z,1]
                        tensor[1,1] = data[x,y,z,2]
                        tensor[2,0] = data[x,y,z,3]
                        tensor[2,1] = data[x,y,z,4]
                        tensor[2,2] = data[x,y,z,5]
                        tensor = tensor + tensor.T
                        element_id += 1
                        elements.append(element_id)
                        try:
                            node_positions[element_id] = [nodes[x,y,z], nodes[x+1,y,z], nodes[x+1,y+1,z], nodes[x,y+1,z], nodes[x,y,z+1], nodes[x+1,y,z+1], nodes[x+1,y+1,z+1], nodes[x,y+1,z+1]]
                            tensors[element_id] = tensor
                        except IndexError:
                            continue
                
    f.write('$EndNodes\n')

    iflogger.info('Write the Elements block')
    f.write('$Elements\n')
    n_elements = ('%f' % (len(node_positions.keys())))
    f.write(n_elements + '\n')
    block_type = 5 # Hexahedron aka Cube
    number_of_tags = 2
    tag_1 = 6
    material_tag = 100
    for element_id in elements:
        try:
            node = node_positions[element_id]
            element_str = ('%d %d %d %d %d %d %d %d %d %d %d %d %d' % (element_id, block_type, number_of_tags, tag_1, material_tag,
            node[0], node[1], node[2], node[3], node[4], node[5], node[6], node[7]))
            f.write(element_str + '\n')
        except KeyError:
            continue
    f.write('$EndElements\n')
    iflogger.info('End of the Elements Block')

    f.write('$ElementData\n')
    n_str_tags = str(1)
    str_tag = '"Diffusion"'

    f.write(n_str_tags + '\n')
    f.write(str_tag + '\n')

    n_real_tags = str(1)
    real_tag = str(10)

    f.write(n_real_tags + '\n')
    f.write(real_tag + '\n')

    n_int_tags = str(3)
    int_tags = []
    int_tags.append(3)
    int_tags.append(0)
    int_tags.append(9) # 9 for tensor
    for tag in int_tags:
        f.write(str(tag) + '\n')
        
    elementdata_list = []
    iflogger.info('Writing the element data block...')
    for element_id in elements:
        tensor = tensors[element_id]
        t_list = list(tensor.flatten())
        elementdata_str = ('%d %f %f %f %f %f %f %f %f %f' % (element_id, t_list[0], 
        t_list[1], t_list[2], t_list[3], t_list[4], t_list[5], t_list[6], t_list[7], t_list[8]))
        elementdata_list.append(elementdata_str)
        
    n_elementdata = str(len(elementdata_list))
    f.write(n_elementdata + '\n')	
    for elementdata_str in elementdata_list:
        f.write(elementdata_str + '\n')
    f.write('$EndElementData\n')
    f.close()
    iflogger.info('Tensor image successfully saved as {out}'.format(out=out_file))

class TensorImage2GmshInputSpec(TraitedSpec):
    in_file = File(exists=True, mandatory=True, desc='The input nifti tensor image')
    mask_file = File(exists=True, desc='An input (e.g. white matter) mask image. Only tensors in non-zero voxels in this image will be saved')
    mask_threshold = traits.Float(0, usedefault=True, desc='Value with which to threshold the input mask image')
    threshold_file = File(exists=True, desc='An input mask image. Only tensors in voxels that are greater'  \
                                                            'than or equal to the "threshold" input will be saved.'  \
                                                            'This CAN be used in conjunction with a mask file.'  \
                                                            '(e.g. Fractional Anisotropy image with threshold = 0.4')
    threshold = traits.Float(0.4, usedefault=True, desc='Value with which to threshold the input threshold image')
    threshold_above = traits.Bool(True, usedefault=True, desc='By default, voxels >= the threshold will be saved.' \
                                                              'If this is false, the voxels <= the threshold will be saved')
    out_filename = File(genfile=True, desc='The output filename for the tensor image in GMSH .msh format')

class TensorImage2GmshOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Tensor image saved as a GMSH .msh file')

class TensorImage2Gmsh(BaseInterface):
    """
    Converts Nifti (.nii) tensor images into GMSH (.msh) format

    Example
    -------

    >>> import nipype.interfaces.gmsh as gmsh
    >>> nii2msh = gmsh.TensorImage2Gmsh()
    >>> nii2msh.inputs.in_file = 'tensors.nii'
    >>> nii2msh.inputs.mask_file = 'wm_mask.nii'
    >>> nii2msh.inputs.threshold_file = 'fa.nii'
    >>> nii2msh.inputs.threshold = 0.6
    >>> nii2msh.run()                                   # doctest: +SKIP
    """
    input_spec = TensorImage2GmshInputSpec
    output_spec = TensorImage2GmshOutputSpec

    def _run_interface(self, runtime):
        _, name , _ = split_filename(self.inputs.in_file)
        out_file = op.abspath(name + '.msh')
        nifti_to_gmsh_tensor_elements(self.inputs.in_file, out_file, self.inputs.mask_file, 
        self.inputs.threshold_file, self.inputs.mask_threshold, self.inputs.threshold, self.inputs.threshold_above)
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_file'] = op.abspath(self._gen_outfilename())
        return outputs

    def _gen_filename(self, name):
        if name is 'out_filename':
            return self._gen_outfilename()
        else:
            return None
    def _gen_outfilename(self):
        _, name , _ = split_filename(self.inputs.in_file)
        return name + '.msh'
