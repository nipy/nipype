#!/usr/bin/python
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:


import os
from glob import glob
from copy import deepcopy



from nipype.interfaces.base import Bunch, InterfaceResult, Interface
from nipype.utils.filemanip import fname_presuffix, fnames_presuffix, filename_to_list, list_to_filename
from nipype.utils.misc import find_indices, is_container

import mvpa
from mvpa import pymvpa_dataroot
from mvpa.algorithms.cvtranserror import CrossValidatedTransferError
from mvpa.base import debug
from mvpa.clfs.svm import LinearCSVMC
from mvpa.clfs.transerror import TransferError
from mvpa.mappers.zscore import zscore
from mvpa.datasets.mri import fmri_dataset
from mvpa.datasets.splitters import NFoldSplitter
from mvpa.mappers.fx import mean_sample
from mvpa.measures.searchlight import sphere_searchlight
from mvpa.misc.io.base import SampleAttributes

import nipype.interfaces.fsl as fsl
#import matplotlib as mpl
#import matplotlib.pyplot as plt
#import traceback


class PyMVPA(Interface):
    """Detects outliers in a functional imaging series depending on the
    intensity and motion parameters.  It also generates other statistics.
    """

    def __init__(self, *args, **inputs):
        self._populate_inputs()
        self.inputs.update(**inputs)

    def inputs_help(self):
        """
        Parameters
        ----------

        """
        print self.inputs_help.__doc__

    def _populate_inputs(self):
        self.inputs = Bunch(samples_file=None,
                            mask_file=None,
                            attributes_file=None,
                            radius=1,
                            outfile=None)

    def outputs_help(self):
        """print out the help from the outputs routine
        """
        print self.outputs.__doc__

    def outputs(self):
        """Generate a bunch containing the output fields.

        Parameters
        ----------
        """
        outputs = Bunch(outfile=None)
        return outputs

    def _get_output_filename(self):
        outfile = self.inputs.outfile
        if not outfile:
            outfile = fname_presuffix(self.inputs.samples_file,
                                      suffix='_searchlight',
                                      newpath=os.getcwd())
        return outfile

    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.outfile = glob(self._get_output_filename())[0]
        return outputs

    def get_input_info(self):
        return []

    def _run_core(self,):
        """
        Core routine for detecting outliers

        Parameters
        ----------
        imgfile :
        motionfile :
        """
        attr = SampleAttributes(self.inputs.attributes_file)

        dataset = fmri_dataset(
            samples=self.inputs.samples_file,
            labels=attr.labels,
            chunks=attr.chunks,
            mask=self.inputs.mask_file)

        if 'rest' in dataset.uniquelabels:
            dataset = dataset[dataset.sa.labels != 'rest']

        # zscore dataset relative to baseline ('rest') mean
        zscore(dataset, chunks_attr=True, dtype='float32')

        # choose classifier
        clf = LinearCSVMC()

        # setup measure to be computed by Searchlight
        # cross-validated mean transfer using an N-fold dataset splitter
        cv = CrossValidatedTransferError(TransferError(clf),
                                         NFoldSplitter())


        sl = sphere_searchlight(cv, radius=self.inputs.radius,
                                space='voxel_indices',
                                nproc=2, mapper=mean_sample())

        ds = dataset.copy(deep=False,
                      sa=['labels', 'chunks'], fa=['voxel_indices'], a=[])

        sl_map = sl(ds)
        # map sensitivity map into original dataspace
        orig_sl_map = dataset.map2nifti(sl_map)

        orig_sl_map.save(self._get_output_filename())


    def run(self, samples_file=None, mask_file=None,
            attributes_file=None, radius=None, cwd=None, **inputs):
        """Execute this module.
        """
        if samples_file:
            self.inputs.samples_file = samples_file
        if attributes_file:
            self.inputs.attributes_file = attributes_file
        if mask_file:
            self.inputs.mask_file = mask_file
        if radius:
            self.inputs.radius = radius

        self._run_core()
        runtime = Bunch(returncode=0,
                        messages=None,
                        errmessages=None)
        outputs=self.aggregate_outputs()

        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)


if __name__ == '__main__':
    inputfile = os.path.join(pymvpa_dataroot, 'bold.nii.gz')
    mvpa.debug.active += ['SLC']

    if False:
        maths = fsl.Fslmaths(infile=inputfile, optstring= '-bptf 20 -1',
                         outfile='bold_fslhp.nii.gz')
        maths.run()
        mvpa_sl = PyMVPA()
        mvpa_sl.run(samples_file='bold_fslhp.nii.gz',
                 mask_file=os.path.join(pymvpa_dataroot, 'mask.nii.gz'),
                 attributes_file=os.path.join(pymvpa_dataroot,
                                             'attributes_literal.txt'),
                 radius=0
                 )

    import nipype.pipeline.engine as pe
    import nipype.pipeline.node_wrapper as nw

    hpfnode = nw.NodeWrapper(interface=fsl.Fslmaths(),diskbased=True)
    hpfnode.inputs.optstring = '-bptf 20 -1'
    hpfnode.inputs.infile = inputfile
    mvpanode = nw.NodeWrapper(interface=PyMVPA(),diskbased=True)
    mvpanode.inputs.update(
        mask_file=os.path.join(pymvpa_dataroot, 'mask.nii.gz'),
        attributes_file=os.path.join(pymvpa_dataroot,
                                     'attributes_literal.txt'),
        radius=0
        )
    mvpapipe = pe.Pipeline()
    mvpapipe.config['workdir'] = '/tmp/mvpapipe'
    mvpapipe.connect([(hpfnode,mvpanode,[('outfile','samples_file')])])
    mvpapipe.export_graph()
    #mvpapipe.run()

