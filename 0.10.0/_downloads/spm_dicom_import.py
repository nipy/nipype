from nipype.interfaces.spm import DicomImport
from nipype.pipeline.engine import Node, Workflow
from glob import glob

dcmimp = Node(DicomImport(), name="dcmimp")
dcmimp.inputs.in_files = glob("/Volumes/Samsung_T1/NKI_dicoms/group_0/0197570/anat/IM*.dcm")
dcmimp.iterables = ('output_dir_struct', ['flat', 'series', 'patname', 'patid_date', 'patid', 'date_time'])

wf = Workflow("test")
wf.base_dir = "/tmp"
wf.add_nodes([dcmimp])
wf.run()