from nipype.interfaces.base import BaseInterface, BaseTraitedSpec, traits, File, TraitedSpec, Directory
from nipype.utils.filemanip import split_filename

import scipy as sp
import os, os.path as op
from time import time
from glob import glob
import numpy as np
import nibabel
import networkx as nx

class ROIGenInputSpec(BaseTraitedSpec):
	aparc_aseg_file = File(exists=True, mandatory=True, desc='Freesurfer aseg+aparc file')
	LUT_file = File(exists=True, xor=['use_freesurfer_LUT'])
	use_freesurfer_LUT = traits.Bool(xor=['LUT_file'])
	freesurfer_dir = Directory(requires=use_freesurfer_LUT)
    
class ROIGenOutputSpec(TraitedSpec):
    roi_file = File(exists=True)
    dict_file = File(exists=True)	
    
class ROIGen(BaseInterface):
    '''
	Generates a ROI file for connectivity mapping
    '''
	
    input_spec = ROIGenInputSpec
    output_spec = ROIGenOutputSpec
	
    def _run_interface(self, runtime):
		niiAPARCimg = ni.load(self.inputs.aparc_aseg_file)
		niiAPARCdata = niiAPARCimg.get_data()

		MAPPING = [[1,2012],[2,2019],[3,2032],[4,2014],[5,2020],[6,2018],[7,2027],[8,2028],[9,2003],[10,2024],[11,2017],[12,2026],
				   [13,2002],[14,2023],[15,2010],[16,2022],[17,2031],[18,2029],[19,2008],[20,2025],[21,2005],[22,2021],[23,2011],
				   [24,2013],[25,2007],[26,2016],[27,2006],[28,2033],[29,2009],[30,2015],[31,2001],[32,2030],[33,2034],[34,2035],
				   [35,49],[36,50],[37,51],[38,52],[39,58],[40,53],[41,54],[42,1012],[43,1019],[44,1032],[45,1014],[46,1020],[47,1018],
				   [48,1027],[49,1028],[50,1003],[51,1024],[52,1017],[53,1026],[54,1002],[55,1023],[56,1010],[57,1022],[58,1031],
				   [59,1029],[60,1008],[61,1025],[62,1005],[63,1021],[64,1011],[65,1013],[66,1007],[67,1016],[68,1006],[69,1033],
				   [70,1009],[71,1015],[72,1001],[73,1030],[74,1034],[75,1035],[76,10],[77,11],[78,12],[79,13],[80,26],[81,17],
				   [82,18],[83,16]]

		roi_file = ni.Nifti1Image(niiWM, niiAPARCimg.get_affine(), niiAPARCimg.get_header())
		return runtime
    
    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['roi_file'] = os.path.abspath(self.inputs.out_file)
        outputs['dict_file'] = os.path.abspath(self.inputs.out_file)		
        return outputs