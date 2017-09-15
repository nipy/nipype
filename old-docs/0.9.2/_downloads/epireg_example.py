from nipype.interfaces import fsl
from nipype.pipeline.engine import Node, Workflow

bet = Node(fsl.BET(), name="bet")
bet.inputs.in_file = "/Volumes/Samsung_T1/NKI/DiscSci_R7/A00038998/dsc_2/mprage_siemens_defaced/mprage_siemens_defaced.nii.gz"

epireg = Node(fsl.EpiReg(), name="epireg")
epireg.inputs.epi = "/Volumes/Samsung_T1/NKI/DiscSci_R7/A00038998/dsc_2/breath_hold_1400/breath_hold_1400.nii"
epireg.inputs.t1_head = "/Volumes/Samsung_T1/NKI/DiscSci_R7/A00038998/dsc_2/mprage_siemens_defaced/mprage_siemens_defaced.nii.gz"

wf = Workflow("test_epireg")
wf.base_dir = "/tmp"

wf.connect(bet, "out_file", epireg, "t1_brain")

wf.run()