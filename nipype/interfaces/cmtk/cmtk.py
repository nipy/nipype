from nipype.interfaces.base import BaseInterface, BaseInterfaceInputSpec, traits, File, TraitedSpec, Directory
from nipype.utils.filemanip import split_filename
import os
import re
from glob import glob
from nibabel import load
from nipype.utils.filemanip import fname_presuffix, split_filename, copyfile
import pickle
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
    LUT_file = File(exists=True, xor=['use_freesurfer_LUT'], desc='Custom lookup table (cf. FreeSurferColorLUT.txt)')
    use_freesurfer_LUT = traits.Bool(xor=['LUT_file'],desc='Boolean value; Set to True to use default Freesurfer LUT, False for custom LUT')
    freesurfer_dir = Directory(requires=['use_freesurfer_LUT'],desc='Freesurfer main directory')
    roi_file = File(genfile = True, desc='Region of Interest file for connectivity mapping')
    dict_file = File(genfile = True, desc='Label dictionary saved in Pickle format')

class ROIGenOutputSpec(TraitedSpec):
    out_roi_file = File(desc='Region of Interest file for connectivity mapping')
    out_dict_file = File(desc='Label dictionary saved in Pickle format')

class ROIGen(BaseInterface):
    '''
    Generates a ROI file for connectivity mapping and a dictionary file containing relevant node information

    import nipype.interfaces.cmtk.cmtk as ck
    ck.ROIGen()
    rg = ck.ROIGen()
    rg.inputs.aparc_aseg_file = 'aparc+aseg.nii'
    rg.inputs.use_freesurfer_LUT = True
    rg.inputs.freesurfer_dir = '/usr/local/freesurfer'
    rg.run()

    The label dictionary is written to disk using Pickle. Resulting data can be loaded using:

    file = open("FreeSurferColorLUT_adapted_aparc+aseg_out.pck", "r")
    file = open("fsLUT_aparc+aseg.pck", "r")
    labelDict = pickle.load(file)

    print labelDict
    '''

    input_spec = ROIGenInputSpec
    output_spec = ROIGenOutputSpec

    def _run_interface(self, runtime):
        if self.inputs.use_freesurfer_LUT:
            self.LUT_file = self.inputs.freesurfer_dir + '/FreeSurferColorLUT.txt'
            print 'Using Freesurfer LUT: {name}'.format(name=self.LUT_file)
            aparcpath, aparcname, aparcext = split_filename(self.inputs.aparc_aseg_file)
            print 'Using Aparc+Aseg file: {name}'.format(name=aparcname+aparcext)
            self.out_roi_file = os.path.abspath("fsLUT" + '_' + aparcname)
            self.out_dict_file = os.path.abspath("fsLUT" + '_' + aparcname + ".pck")

        elif not self.inputs.use_freesurfer_LUT and isdefined(self.inputs.LUT_file):
            self.LUT_file = os.path.abspath(self.inputs.LUT_file)
            lutpath, lutname, lutext = split_filename(self.LUT_file)
            print 'Using Custom LUT file: {name}'.format(name=lutname+lutext)
            aparcpath, aparcname, aparcext = split_filename(self.inputs.aparc_aseg_file)
            print 'Using Aparc+Aseg file: {name}'.format(name=aparcname+aparcext)
            self.out_roi_file = os.path.abspath(lutname + '_' + aparcname)
            self.out_dict_file = os.path.abspath(lutname + '_' + aparcname + ".pck")
            print 'Output names generated'

        if isdefined(self.inputs.roi_file):
            self.out_roi_file = os.path.abspath(self.inputs.roi_file)

        if isdefined(self.inputs.dict_file):
            self.out_dict_file = os.path.abspath(self.inputs.dict_file)

        MAPPING = [[1,2012],[2,2019],[3,2032],[4,2014],[5,2020],[6,2018],[7,2027],[8,2028],[9,2003],[10,2024],[11,2017],[12,2026],
               [13,2002],[14,2023],[15,2010],[16,2022],[17,2031],[18,2029],[19,2008],[20,2025],[21,2005],[22,2021],[23,2011],
               [24,2013],[25,2007],[26,2016],[27,2006],[28,2033],[29,2009],[30,2015],[31,2001],[32,2030],[33,2034],[34,2035],
               [35,49],[36,50],[37,51],[38,52],[39,58],[40,53],[41,54],[42,1012],[43,1019],[44,1032],[45,1014],[46,1020],[47,1018],
               [48,1027],[49,1028],[50,1003],[51,1024],[52,1017],[53,1026],[54,1002],[55,1023],[56,1010],[57,1022],[58,1031],
               [59,1029],[60,1008],[61,1025],[62,1005],[63,1021],[64,1011],[65,1013],[66,1007],[67,1016],[68,1006],[69,1033],
               [70,1009],[71,1015],[72,1001],[73,1030],[74,1034],[75,1035],[76,10],[77,11],[78,12],[79,13],[80,26],[81,17],
               [82,18],[83,16]]
        print 'Lookup table: {name}'.format(name=self.LUT_file)
        print 'LUT path: {name}'.format(name=os.path.abspath(self.LUT_file))
        LUTlabelsRGBA = np.loadtxt(self.LUT_file, skiprows=4, usecols=[0,1,2,3,4,5], comments='#',
                        dtype={'names': ('index', 'label', 'R', 'G', 'B', 'A'),'formats': ('int', '|S30', 'int', 'int', 'int', 'int')})
        print 'Lookup table labels recorded'
        print LUTlabelsRGBA
        self.aparc_aseg_file = os.path.abspath(self.inputs.aparc_aseg_file)
        print 'Aparc path: {name}'.format(name=self.aparc_aseg_file)
        niiAPARCimg = nb.load(self.aparc_aseg_file)
        print 'Aparc Image Loaded'
        niiAPARCdata = niiAPARCimg.get_data()
        print 'Aparc Data Extracted'
        niiDataLabels = np.unique(niiAPARCdata)
        print 'Data labels recorded'
        print niiDataLabels

        numDataLabels = np.size(niiDataLabels)
        numLUTLabels = np.size(LUTlabelsRGBA)
        print 'Number of labels in image: {n}'.format(n=numDataLabels)
        print 'Number of labels in LUT: {n}'.format(n=numLUTLabels)
        if numLUTLabels < numDataLabels:
            print 'LUT file provided does not contain all of the regions in the image'
            print 'Removing unmapped regions'

        labelDict = {}
        GMlabelDict = {}
        LUTlabelDict = {}
        mapDict = {}

        ''' Create dictionary for input LUT table'''
        for labels in range(0,numLUTLabels):
            #I'm sure there's a better way of writing the right side of this...
            LUTlabelDict[LUTlabelsRGBA[labels][0]] = [LUTlabelsRGBA[labels][1],LUTlabelsRGBA[labels][2], LUTlabelsRGBA[labels][3], LUTlabelsRGBA[labels][4], LUTlabelsRGBA[labels][5]]


        print 'Printing LUT label dictionary'
        print LUTlabelDict

        ''' Create empty grey matter mask, Populate with only those regions defined in the mapping.'''
        niiGM = np.zeros( niiAPARCdata.shape, dtype = np.uint8 )
        for ma in MAPPING:
            niiGM[ niiAPARCdata == ma[1]] = ma[0]
            mapDict[ma[0]] = ma[1]

        print 'Printing Map dictionary'
        print mapDict

        print 'Printing GM label dictionary'
        print LUTlabelDict

        print 'Grey matter mask created'
        greyMaskLabels = np.unique(niiGM)
        numGMLabels = np.size(greyMaskLabels)
        print 'Number of grey matter labels: {num}'.format(num=numGMLabels)
        print greyMaskLabels

        for label in greyMaskLabels:
            del GMlabelDict
            GMlabelDict = {}
            GMlabelDict['labels'] = LUTlabelDict[label][0]
            GMlabelDict['colors']  = [LUTlabelDict[label][1], LUTlabelDict[label][2], LUTlabelDict[label][3]]
            GMlabelDict['a'] = LUTlabelDict[label][4]
            try:
                mapDict[label]
                GMlabelDict['originalID'] = mapDict[label]
            except:
                print 'Label {lbl} not in provided mapping'.format(lbl=label)
            print GMlabelDict
            labelDict[label] = GMlabelDict

        roi_file = nb.Nifti1Image(niiGM, niiAPARCimg.get_affine(), niiAPARCimg.get_header())

        print 'Printing final label dictionary'
        print labelDict

        print 'Printing unique labels in remapped ROI file'
        print np.unique(roi_file.get_data())

        print 'Saving ROI File to {path}'.format(path=self.out_roi_file)
        nb.save(roi_file, self.out_roi_file)
        print 'Saving Dictionary File to {path} in Pickle format'.format(path=self.out_dict_file)
        file = open(os.path.abspath(self.out_dict_file), "w")
        pickle.dump(labelDict, file)
        file.close()

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        aparcpath, aparcname, aparcext = split_filename(os.path.abspath(self.inputs.aparc_aseg_file))
        if self.inputs.use_freesurfer_LUT:
            prefix = "fsLUT"
        elif not self.inputs.use_freesurfer_LUT and isdefined(self.inputs.LUT_file):
            lutpath, lutname, lutext = split_filename(self.inputs.LUT_file)
            prefix = lutname
        outputs['out_roi_file'] = self._gen_outfilename('nii')
        outputs['out_dict_file'] = self._gen_outfilename('pck')

        if isdefined(self.inputs.roi_file):
            outputs['out_roi_file'] = os.path.abspath(self.inputs.roi_file)

        if isdefined(self.inputs.dict_file):
            outputs['out_dict_file'] = os.path.abspath(self.inputs.dict_file)

        return outputs

    def _gen_outfilename(self, ext):
        _, name , _ = split_filename(self.inputs.aparc_aseg_file)
        return name + "." + ext
