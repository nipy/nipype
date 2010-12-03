# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Created on 24 Feb 2010

@author: filo
'''
from nipype.interfaces.base import BaseInterface,\
    traits, TraitedSpec, File, InputMultiPath, OutputMultiPath
from nipype.utils.misc import isdefined
import nibabel as nb
import numpy as np
from math import floor, ceil
from scipy.ndimage.morphology import grey_dilation
import os
from nipype.utils.filemanip import fname_presuffix, split_filename
from scipy.ndimage.morphology import binary_erosion
from scipy.spatial.distance import cdist, euclidean, dice, jaccard
from scipy.ndimage.measurements import center_of_mass, label
import matplotlib
#matplotlib.use('Cairo')
import matplotlib.pyplot as plt

class PickAtlasInputSpec(TraitedSpec):
    atlas = File(exists=True, desc="Location of the atlas that will be used.", compulsory=True)
    labels = traits.Either(traits.Int, traits.List(traits.Int), 
                           desc="Labels of regions that will be included in the mask. Must be \
compatible with the atlas used.", compulsory=True)
    hemi = traits.Enum('both','left','right', desc="Restrict the mask to only one hemisphere: left or right", usedefault=True)
    dilation_size = traits.Int(desc="Defines how much the mask will be dilated (expanded in 3D).", usedefault = True)
    output_file = File(desc="Where to store the output mask.")

class PickAtlasOutputSpec(TraitedSpec):
    mask_file = File(exists=True, desc="output mask file")

class PickAtlas(BaseInterface):
    '''
    Returns ROI masks given an atlas and a list of labels. Supports dilation
    and left right masking (assuming the atlas is properly aligned).
    '''
    input_spec = PickAtlasInputSpec
    output_spec = PickAtlasOutputSpec

    def _run_interface(self, runtime):
        nim = self._get_brodmann_area()
        nb.save(nim, self._gen_output_filename())

        runtime.returncode = 0
        return runtime

    def _gen_output_filename(self):
        if not isdefined(self.inputs.output_file):
            output = fname_presuffix(fname=self.inputs.atlas, suffix = "_mask",
                                     newpath= os.getcwd(), use_ext = True)
        else:
            output = self.inputs.output_file
        return output
        
    def _get_brodmann_area(self):
        nii = nb.load(self.inputs.atlas)
        origdata = nii.get_data()
        newdata = np.zeros(origdata.shape)
        
        if not isinstance(self.inputs.labels, list):
            labels = [self.inputs.labels]
        else:
            labels = self.inputs.labels
        for label in labels:
            newdata[origdata == label] = 1
        if self.inputs.hemi == 'right':
            newdata[floor(float(origdata.shape[0]) / 2):, :, :] = 0
        elif self.inputs.hemi == 'left':
            newdata[:ceil(float(origdata.shape[0]) / 2), :, : ] = 0

        if self.inputs.dilation_size != 0:
            newdata = grey_dilation(newdata , (2 * self.inputs.dilation_size + 1,
                                               2 * self.inputs.dilation_size + 1,
                                               2 * self.inputs.dilation_size + 1))

        return nb.Nifti1Image(newdata, nii.get_affine(), nii.get_header())

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['mask_file'] = self._gen_output_filename()
        return outputs
    
class SimpleThresholdInputSpec(TraitedSpec):
    volumes = InputMultiPath(File(exists=True), desc='volumes to be thresholded', mandatory=True)
    threshold = traits.Float(desc='volumes to be thresholdedeverything below this value will be set to zero', mandatory=True)
    
    
class SimpleThresholdOutputSpec(TraitedSpec):
    thresholded_volumes = OutputMultiPath(File(exists=True), desc="thresholded volumes")
    

class SimpleThreshold(BaseInterface):
    input_spec = SimpleThresholdInputSpec
    output_spec = SimpleThresholdOutputSpec
    
    def _run_interface(self, runtime):
        for fname in self.inputs.volumes:
            img = nb.load(fname)
            data = np.array(img.get_data())
            
            active_map = data > self.inputs.threshold
            
            thresholded_map = np.zeros(data.shape)
            thresholded_map[active_map] = data[active_map]

            new_img = nb.Nifti1Image(thresholded_map, img.get_affine(), img.get_header())
            _, base, _ = split_filename(fname)
            nb.save(new_img, base + '_thresholded.nii') 
        
        runtime.returncode=0
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["thresholded_volumes"] = []
        for fname in self.inputs.volumes:
            _, base, _ = split_filename(fname)
            outputs["thresholded_volumes"].append(os.path.abspath(base + '_thresholded.nii'))
        return outputs

class ModifyAffineInputSpec(TraitedSpec):
    volumes = InputMultiPath(File(exists=True), desc='volumes which affine matrices will be modified', mandatory=True)
    transformation_matrix = traits.Array(value=np.eye(4), shape=(4,4), desc="transformation matrix that will be left multiplied by the affine matrix", usedefault=True)
    
class ModifyAffineOutputSpec(TraitedSpec):
    transformed_volumes = OutputMultiPath(File(exist=True))
    
class ModifyAffine(BaseInterface):
    '''
    Left multiplies the affine matrix with a specified values. Saves the volume as a nifti file.
    '''
    input_spec = ModifyAffineInputSpec
    output_spec = ModifyAffineOutputSpec
    
    def _gen_output_filename(self, name):
        _, base, _ = split_filename(name)
        return os.path.abspath(base + "_transformed.nii")
    
    def _run_interface(self, runtime):
        for fname in self.inputs.volumes:
            img = nb.load(fname)
            
            affine = img.get_affine()
            affine = np.dot(self.inputs.transformation_matrix,affine)

            nb.save(nb.Nifti1Image(img.get_data(), affine, img.get_header()), self._gen_output_filename(fname))
            
        runtime.returncode=0
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['transformed_volumes'] = []
        for fname in self.inputs.volumes:
            outputs['transformed_volumes'].append(self._gen_output_filename(fname))
        return outputs

class DistanceInputSpec(TraitedSpec):
    volume1 = File(exists=True, mandatory=True, desc="Has to have the same dimensions as volume2.")
    volume2 = File(exists=True, mandatory=True, desc="Has to have the same dimensions as volume1.")
    method = traits.Enum("eucl_min", "eucl_cog", "eucl_mean", "eucl_wmean", desc='""eucl_min": Euclidean distance between two closest points\
    "eucl_cog": mean Euclidian distance between the Center of Gravity of volume1 and CoGs of volume2\
    "eucl_mean": mean Euclidian minimum distance of all volume2 voxels to volume1\
    "eucl_wmean": mean Euclidian minimum distance of all volume2 voxels to volume1 weighted by their values', usedefault = True)

class DistanceOutputSpec(TraitedSpec):
    distance = traits.Float()
    point1 = traits.Array(shape=(3,))
    point2 = traits.Array(shape=(3,))
    histogram = File()
    
class Distance(BaseInterface):
    '''
    Calculates distance between two volumes.
    '''
    input_spec = DistanceInputSpec
    output_spec = DistanceOutputSpec
    
    _hist_filename = "hist.pdf"
    
    def _find_border(self,data):
        eroded = binary_erosion(data)
        border = np.logical_and(data, np.logical_not(eroded))
        return border
    
    def _get_coordinates(self, data, affine):
        if len(data.shape) == 4:
            data = data[:,:,:,0]
        indices = np.vstack(np.nonzero(data))
        indices = np.vstack((indices, np.ones(indices.shape[1])))
        coordinates = np.dot(affine,indices)
        return coordinates[:3,:]
    
    def _eucl_min(self, nii1, nii2):
        origdata1 = nii1.get_data().astype(np.bool)
        border1 = self._find_border(origdata1)
              
        origdata2 = nii2.get_data().astype(np.bool)
        border2 = self._find_border(origdata2)
        
        set1_coordinates = self._get_coordinates(border1, nii1.get_affine())
        
        set2_coordinates = self._get_coordinates(border2, nii2.get_affine())
        
        dist_matrix = cdist(set1_coordinates.T, set2_coordinates.T)
        (point1, point2) = np.unravel_index(np.argmin(dist_matrix), dist_matrix.shape)
        return (euclidean(set1_coordinates.T[point1,:], set2_coordinates.T[point2,:]), set1_coordinates.T[point1,:], set2_coordinates.T[point2,:])
    
    def _eucl_cog(self, nii1, nii2):
        origdata1 = nii1.get_data().astype(np.bool)  
        cog_t = np.array(center_of_mass(origdata1)).reshape(-1,1)
        cog_t = np.vstack((cog_t, np.array([1])))
        cog_t_coor = np.dot(nii1.get_affine(),cog_t)[:3,:]
        
        origdata2 = nii2.get_data().astype(np.bool)
        (labeled_data, n_labels) = label(origdata2)
        
        cogs = np.ones((4,n_labels))
        
        for i in range(n_labels):
            cogs[:3,i] = np.array(center_of_mass(origdata2, labeled_data, i+1))
            
        cogs_coor = np.dot(nii2.get_affine(),cogs)[:3,:]
        
        dist_matrix = cdist(cog_t_coor.T, cogs_coor.T)
        
        return np.mean(dist_matrix)
    
    def _eucl_mean(self, nii1, nii2, weighted=False):
        origdata1 = nii1.get_data().astype(np.bool)
        border1 = self._find_border(origdata1)
              
        origdata2 = nii2.get_data().astype(np.bool)
       
        set1_coordinates = self._get_coordinates(border1, nii1.get_affine()) 
        set2_coordinates = self._get_coordinates(origdata2, nii2.get_affine())
        
        dist_matrix = cdist(set1_coordinates.T, set2_coordinates.T)
        min_dist_matrix = np.amin(dist_matrix, axis = 0)
        plt.figure()
        plt.hist(min_dist_matrix, 50, normed=1, facecolor='green')
        plt.savefig(self._hist_filename)
        plt.clf()
        plt.close()
        
        if weighted:
            return np.average(min_dist_matrix, weights=nii2.get_data()[origdata2].flat)
        else:
            return np.mean(min_dist_matrix)
        

    
    def _run_interface(self, runtime):
        nii1 = nb.load(self.inputs.volume1)
        nii2 = nb.load(self.inputs.volume2)
        
        if self.inputs.method == "eucl_min":
            self._distance, self._point1, self._point2 = self._eucl_min(nii1, nii2)
            
        elif self.inputs.method == "eucl_cog":
            self._distance = self._eucl_cog(nii1, nii2)
            
        elif self.inputs.method == "eucl_mean":
            self._distance = self._eucl_mean(nii1, nii2)            
            
        elif self.inputs.method == "eucl_wmean":
            self._distance = self._eucl_mean(nii1, nii2, weighted=True)


        runtime.returncode=0
        return runtime
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['distance'] = self._distance
        if self.inputs.method == "eucl_min":
            outputs['point1'] = self._point1
            outputs['point2'] = self._point2
        elif self.inputs.method in ["eucl_mean", "eucl_wmean"]:
            outputs['histogram'] = os.path.abspath(self._hist_filename)
        return outputs
    
class DissimilarityInputSpec(TraitedSpec):
    volume1 = File(exists=True, mandatory=True, desc="Has to have the same dimensions as volume2.")
    volume2 = File(exists=True, mandatory=True, desc="Has to have the same dimensions as volume1.")
    method = traits.Enum("dice", "jaccard", desc='"dice": Dice\'s dissimilarity,\
    "jaccard": Jaccards\'s dissimilarity', usedefault = True
    )
    
class DissimilarityOutputSpec(TraitedSpec):
    dissimilarity = traits.Float()
    
class Dissimilarity(BaseInterface):
    """
    Calculates dissimilarity between two maps.
    """
    input_spec = DissimilarityInputSpec
    output_spec = DissimilarityOutputSpec
    
    def _bool_vec_dissimilarity(self, booldata1, booldata2, method):
        methods = {"dice": dice, "jaccard": jaccard}       
        return methods[method](booldata1.flat, booldata2.flat)
    
    def _run_interface(self, runtime):
        nii1 = nb.load(self.inputs.volume1)
        nii2 = nb.load(self.inputs.volume2)
        
        if self.inputs.method in ("dice", "jaccard"):
            origdata1 = nii1.get_data().astype(np.bool)
            origdata2 = nii2.get_data().astype(np.bool)
            self._dissimilarity = self._bool_vec_dissimilarity(origdata1, origdata2, method = self.inputs.method)
        
        runtime.returncode=0
        return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['dissimilarity'] = self._dissimilarity
        return outputs
