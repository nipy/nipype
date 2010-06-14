# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype.pipeline.engine as pe
import nipype.interfaces.spm as spm
import nipype.interfaces.fsl as fsl

reload(pe)

realign = pe.Node(spm.Realign(), name = 'spmrealign')
coreg = pe.Node(spm.Coregister(), name = 'coreg')
realign2 = pe.Node(spm.Realign(), name = 'spmrealign2')
bet = pe.MapNode(fsl.BET(), iterfield=['infile'], name='bet')

w1 = pe.Workflow(name='spm')
w1.connect([(realign, coreg, [('realigned_files', 'source')])])

w1.inputs.spmrealign.fwhm = 0.5
assert(realign.inputs.fwhm == 0.5)

w2 = pe.Workflow(name='cplx')
w2.connect(w1, 'coreg.coregistered_files', realign2, 'infile')

inputs = w2.inputs
w2._generate_execgraph()
