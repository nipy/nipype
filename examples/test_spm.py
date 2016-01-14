from __future__ import division
from builtins import range
import nipype.pipeline.engine as pe
from nipype.interfaces import spm
from nipype.interfaces import fsl
from nipype.algorithms.misc import Gunzip
import os

in_file = "feeds/data/fmri.nii.gz"

split = pe.Node(fsl.Split(dimension="t", output_type="NIFTI"), name="split")
split.inputs.in_file = os.path.abspath(in_file)

stc = pe.Node(interface=spm.SliceTiming(), name='stc')
stc.inputs.num_slices = 21
stc.inputs.time_repetition = 1.0
stc.inputs.time_acquisition = 2. - 2. / 32
stc.inputs.slice_order = list(range(21, 0, -1))
stc.inputs.ref_slice = 10

realign_estimate = pe.Node(interface=spm.Realign(), name='realign_estimate')
realign_estimate.inputs.jobtype = "estimate"

realign_write = pe.Node(interface=spm.Realign(), name='realign_write')
realign_write.inputs.jobtype = "write"

realign_estwrite = pe.Node(interface=spm.Realign(), name='realign_estwrite')
realign_estwrite.inputs.jobtype = "estwrite"
realign_estwrite.inputs.register_to_mean = True

smooth = pe.Node(interface=spm.Smooth(), name='smooth')
smooth.inputs.fwhm = [6, 6, 6]

workflow3d = pe.Workflow(name='test_3d')
workflow3d.base_dir = "/tmp"

workflow3d.connect([(split, stc, [("out_files", "in_files")]),
                    (stc, realign_estimate, [('timecorrected_files', 'in_files')]),
                    (realign_estimate, realign_write, [('modified_in_files', 'in_files')]),
                    (stc, realign_estwrite, [('timecorrected_files', 'in_files')]),
                    (realign_write, smooth, [('realigned_files', 'in_files')])])

workflow3d.run()


gunzip = pe.Node(Gunzip(), name="gunzip")
gunzip.inputs.in_file = os.path.abspath(in_file)

stc = pe.Node(interface=spm.SliceTiming(), name='stc')
stc.inputs.num_slices = 21
stc.inputs.time_repetition = 1.0
stc.inputs.time_acquisition = 2. - 2. / 32
stc.inputs.slice_order = list(range(21, 0, -1))
stc.inputs.ref_slice = 10

realign_estimate = pe.Node(interface=spm.Realign(), name='realign_estimate')
realign_estimate.inputs.jobtype = "estimate"

realign_write = pe.Node(interface=spm.Realign(), name='realign_write')
realign_write.inputs.jobtype = "write"

realign_estwrite = pe.Node(interface=spm.Realign(), name='realign_estwrite')
realign_estwrite.inputs.jobtype = "estwrite"

smooth = pe.Node(interface=spm.Smooth(), name='smooth')
smooth.inputs.fwhm = [6, 6, 6]

workflow4d = pe.Workflow(name='test_4d')
workflow4d.base_dir = "/tmp"

workflow4d.connect([(gunzip, stc, [("out_file", "in_files")]),
                    (stc, realign_estimate, [('timecorrected_files', 'in_files')]),
                    (realign_estimate, realign_write, [('modified_in_files', 'in_files')]),
                    (stc, realign_estwrite, [('timecorrected_files', 'in_files')]),
                    (realign_write, smooth, [('realigned_files', 'in_files')])])

workflow4d.run()
