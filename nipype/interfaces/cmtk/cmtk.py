from nipype.interfaces.base import BaseInterface, BaseInterfaceInputSpec, traits, File, TraitedSpec, Directory
from nipype.utils.filemanip import split_filename
import os
import re
from glob import glob
from nibabel import load
from nipype.utils.filemanip import fname_presuffix, split_filename, copyfile
import scipy as sp
import os, os.path as op
from time import time
from glob import glob
import numpy as np
import nibabel as nb
import networkx as nx
from nipype.utils.misc import isdefined

class ROIGenInputSpec(BaseInterfaceInputSpec):
	aparc_aseg_file = File(exists=True, mandatory=True, desc='Freesurfer aparc+aseg file')
	LUT_file = File(exists=True, xor=['use_freesurfer_LUT'])
	use_freesurfer_LUT = traits.Bool(xor=['LUT_file'])
	freesurfer_dir = Directory(requires=['use_freesurfer_LUT'])
	roi_file = File(genfile = True)
	dict_file = File(genfile = True)
    
class ROIGenOutputSpec(TraitedSpec):
    out_roi_file = File()
    out_dict_file = File()
    
class ROIGen(BaseInterface):
    '''
	Generates a ROI file for connectivity mapping

	import nipype.interfaces.cmtk.cmtk as ck
	ck.ROIGen()
	rg = ck.ROIGen()
	rg.inputs.aparc_aseg_file = 'aparc+aseg.nii'
	rg.inputs.use_freesurfer_LUT = True
	rg.inputs.freesurfer_dir = '/usr/local/freesurfer'
	rg.run()

    '''
	
    input_spec = ROIGenInputSpec
    output_spec = ROIGenOutputSpec
	
    def _run_interface(self, runtime):
		if self.inputs.use_freesurfer_LUT:
			print('Using Freesurfer LUT')
			self.LUT_file = self.inputs.freesurfer_dir + '/FreeSurferColorLUT.txt'
			if isdefined(self.inputs.roi_file):
				roipath, roiname, roiext = split_filename(self.inputs.roi_file)
				print 'Using Custom ROI file: {name}'.format(name=roiname+roiext)
				self.out_roi_file = "fsLUT" + '_' + roiname
				self.out_dict_file = "fsLUT" + '_' + roiname + ".dict"
			else:
				aparcpath, aparcname, aparcext = split_filename(self.inputs.aparc_aseg_file)
				print 'Using Aparc+Aseg file: {name}'.format(name=aparcname+aparcext)
				self.out_roi_file = "fsLUT" + '_' + aparcname
				self.out_dict_file = "fsLUT" + '_' + aparcname + ".dict"
		elif not self.inputs.use_freesurfer_LUT and isdefined(self.inputs.LUT_file):
			self.LUT_file = self.inputs.LUT_file
			lutpath, lutname, lutext = split_filename(self.inputs.LUT_file)
			print 'Using Custom LUT file: {name}'.format(name=lutname+lutext)			
			if isdefined(self.inputs.roi_file):
				roipath, roiname, roiext = split_filename(self.inputs.roi_file)
				print 'Using custom ROI file: {name}'.format(name=roiname+roiext)
				self.out_roi_file = lutname + '_' + roiname
				self.out_dict_file = lutname + '_' + roiname + ".dict"
			else:
				aparcpath, aparcname, aparcext = split_filename(self.inputs.aparc_aseg_file)
				print 'Using Aparc+Aseg file: {name}'.format(name=aparcname+aparcext)
				self.out_roi_file = lutname + '_' + aparcname
				self.out_dict_file = lutname + '_' + aparcname + ".dict"

		niiAPARCimg = nb.load(self.inputs.aparc_aseg_file)
		niiAPARCdata = niiAPARCimg.get_data()

		MAPPING = [[1,2012],[2,2019],[3,2032],[4,2014],[5,2020],[6,2018],[7,2027],[8,2028],[9,2003],[10,2024],[11,2017],[12,2026],
				   [13,2002],[14,2023],[15,2010],[16,2022],[17,2031],[18,2029],[19,2008],[20,2025],[21,2005],[22,2021],[23,2011],
				   [24,2013],[25,2007],[26,2016],[27,2006],[28,2033],[29,2009],[30,2015],[31,2001],[32,2030],[33,2034],[34,2035],
				   [35,49],[36,50],[37,51],[38,52],[39,58],[40,53],[41,54],[42,1012],[43,1019],[44,1032],[45,1014],[46,1020],[47,1018],
				   [48,1027],[49,1028],[50,1003],[51,1024],[52,1017],[53,1026],[54,1002],[55,1023],[56,1010],[57,1022],[58,1031],
				   [59,1029],[60,1008],[61,1025],[62,1005],[63,1021],[64,1011],[65,1013],[66,1007],[67,1016],[68,1006],[69,1033],
				   [70,1009],[71,1015],[72,1001],[73,1030],[74,1034],[75,1035],[76,10],[77,11],[78,12],[79,13],[80,26],[81,17],
				   [82,18],[83,16]]
		
		niiGM = np.zeros( niiAPARCdata.shape, dtype = np.uint8 )

		for ma in MAPPING:
			niiGM[ niiAPARCdata == ma[1]] = ma[0]

		roi_file = nb.Nifti1Image(niiGM, niiAPARCimg.get_affine(), niiAPARCimg.get_header())

		#Write dictionary for all regions in ROI File
		#Save as .dict file
		
		print 'Saving ROI File to {path}'.format(path=self.out_roi_file)
		nb.save(roi_file, self.out_roi_file)
		print 'Saving Dictionary File to {path}'.format(path=self.out_dict_file)
		#nb.save(roi_file, self.out_dict_file)
		return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        if self.inputs.use_freesurfer_LUT:
			outputs['out_dict_file'] = "fsLUT" + self.inputs.aparc_aseg_file + ".dict"
			if isdefined(self.inputs.roi_file):
				roipath, roiname, roiext = split_filename(self.inputs.roi_file)
				outputs['out_roi_file'] = "fsLUT" + '_' + roiname
				outputs['out_dict_file'] = "fsLUT" + '_' + roiname + ".dict"
			else:
				aparcpath, aparcname, aparcext = split_filename(self.inputs.aparc_aseg_file)
				outputs['out_roi_file'] = "fsLUT" + '_' + aparcname
				outputs['out_dict_file'] = "fsLUT" + '_' + aparcname + ".dict"			
        elif not self.inputs.use_freesurfer_LUT and isdefined(self.inputs.LUT_file):
			lutpath, lutname, lutext = split_filename(self.inputs.LUT_file)
			if isdefined(self.inputs.roi_file):
				roipath, roiname, roiext = split_filename(self.inputs.roi_file)
				outputs['out_roi_file'] = lutname + '_' + roiname
				outputs['out_dict_file'] = lutname + '_' + roiname + ".dict"
			else:
				aparcpath, aparcname, aparcext = split_filename(self.inputs.aparc_aseg_file)
				outputs['out_roi_file'] = lutname + '_' + aparcname
				outputs['out_dict_file'] = lutname + '_' + aparcname + ".dict"
        return outputs
