# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
A pipeline that uses several interfaces to compute tensor.
"""

"""
Import related packages.
"""
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import os                                    # system functions
import dtieb # use the workflow for Eddycorrect not fsl.Eddycorrect
import xlrd

"""
Confirm package dependencies installed.
"""
from nipype.utils.misc import package_check
package_check('numpy', '1.3', 'dti_test') 
package_check('scipy', '0.7', 'dti_test')
package_check('networkx', '1.0', 'dti_test')
package_check('IPython', '0.10', 'dti_test')

'''
Parallel computation exec config
'''
pluginName = 'IPython'

"""
Specify the related directories
"""
fname = "tbss_conf.xls"
bk = xlrd.open_workbook(fname)
shxrange = range(bk.nsheets)
sh = bk.sheet_by_name("tbss_conf")

subjnum = int(sh.cell_value(0,1))
databank = sh.cell_value(1,1)
sinkdir = sh.cell_value(2,1)
workingdir = sh.cell_value(3,1)
print workingdir
bet_frac = sh.cell_value(4,1)
subject_list = []
for i in range(9,9+subjnum-1):
    sessid = sh.cell_value(i,1)
    subject_list.append(sessid)
    
"""
Map field names to individual subject runs
"""
def subjrlf(subject_id):
    import os
    databank = '/nfs/s1/nspdatabank/data'
    dtirlf = open(os.path.join(databank,subject_id,'dti','dti.rlf'))
    runList = [line.strip() for line in dtirlf]
    info = dict(dwi=[[subject_id,'dti',runList[0],'d.nii.gz']],
                bvecs=[[subject_id,'dti',runList[0],'bvecs']],
                bvals=[[subject_id,'dti',runList[0],'bvals']])
    return info

subjsource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="subjsource")
subjsource.iterables = ('subject_id', subject_list)

"""
Now we create DataGrabber and fill in the information from above. 
"""
datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=['dwi','bvecs','bvals']),
                     name = 'datasource')
datasource.inputs.template = "%s/%s/%s/%s"
datasource.inputs.base_directory = os.path.abspath(databank)

"""
Setup for Diffusion Tensor Computation
--------------------------------------
a generic workflow for DTI computation
"""
computeTensor = pe.Workflow(name='computeTensor')

"""
extract the volume with b=0 (nodif_brain)
"""
extractb0 = pe.Node(interface=fsl.ExtractROI(),name='extractb0')
extractb0.inputs.t_min = 0
extractb0.inputs.t_size = 1
extractb0.inputs.roi_file = 'd_roi.nii.gz'

"""
create a brain mask from the nodif_brain
"""
bet = pe.Node(interface=fsl.BET(),name='bet')
bet.inputs.mask=True
bet.inputs.frac=bet_frac

"""
correct the diffusion weighted images for eddy_currents
"""
eddycorrect = dtieb.create_eddy_correct_pipeline(name='eddycorrect')
eddycorrect.inputs.inputnode.ref_num=0

"""
compute the diffusion tensor in each voxel
"""
dtifit = pe.Node(interface=fsl.DTIFit(),name='dtifit')
dtifit.inputs.save_tensor=True

"""
connect all the nodes for this workflow
"""
computeTensor.connect([
                        (extractb0,bet,[('roi_file','in_file')]),
                        (eddycorrect,dtifit,[('outputnode.eddy_corrected','dwi')]),
                        (subjsource, dtifit,[['subject_id','base_name']]),
                        (bet,dtifit,[('mask_file','mask')])
                      ])

'''
compute AD/RD
'''
def forRD_op_string(infile2):
                        op_string = []
                        op_string = '-add %s -div 2'%infile2
                        return op_string
def renameRD(org_RD):
                        import os
                        RD_suffix = '_RD.nii.gz'
                        RD_prefix = org_RD[:-13]
                        RD = RD_prefix + RD_suffix
                        os.rename(org_RD,RD)
                        return RD
forRD =pe.Node(fsl.ImageMaths(suffix="_RD"),name='forRD')

def renameAD(org_AD):
                        import os
                        AD_suffix = '_AD.nii.gz'
                        AD_prefix = org_AD[:-13]
                        AD = AD_prefix + AD_suffix
                        os.rename(org_AD,AD)
                        return AD 
forAD =pe.Node(fsl.ImageMaths(suffix="_AD"),name='forAD')
forAD.inputs.op_string = '-add 0'

computeTensor.connect([
                        (dtifit,forRD,[
                                       ('L2','in_file'),
                                       #('L3','in_file2'),
                                       (('L3',forRD_op_string),'op_string')
                                       ]),
                        (dtifit,forAD,[('L1','in_file')])
                        ])

"""
Setup data storage area
"""
datasink = pe.Node(interface=nio.DataSink(parameterization=False),name='datasink')
datasink.inputs.base_directory = os.path.abspath(sinkdir)

"""
Setup the pipeline 
----------------------------------------------------------------------------------
"""

dtiproc = pe.Workflow(name="dtiproc")
dtiproc.base_dir = os.path.abspath(workingdir)
dtiproc.connect([
                    (subjsource,datasource,[('subject_id', 'subject_id'),
                                                (('subject_id',subjrlf),'template_args')
                                                ]),
                    (datasource,computeTensor,[('dwi','extractb0.in_file'),
                                               ('bvals','dtifit.bvals'),
                                               ('bvecs','dtifit.bvecs'),
                                               ('dwi','eddycorrect.inputnode.in_file')
                                               ]),
                    (computeTensor,datasink,[   ('dtifit.FA','FA.@FA'),
                                               # ('dtifit.L1','L1.@L1'),
                                               # ('dtifit.L2','L2.@L2'),
                                               # ('dtifit.L3','L3.@L3'),
                                                ('dtifit.MD','MD.@MD'),
                                               # ('dtifit.S0','S0.@S0'),
                                                ('dtifit.tensor','tensor.@tensor'),
                                                ('dtifit.V1','V1.@V1'),
                                               # ('dtifit.V2','V2.@V2'),
                                               # ('dtifit.V3','V3.@V3'),
                                                (('forRD.out_file',renameRD),'RD.@out_file'),
                                                (('forAD.out_file',renameAD),'AD.@out_file'),
                                                ]),
                    ])

if __name__=='__main__':
#     dtiproc.run()
    dtiproc.run(plugin = pluginName)
#    dtiproc.write_graph(graph2use='orig')
#    dtiproc.write_graph(graph2use='hierarchical')
#    dtiproc.write_graph(graph2use='flat')
#    dtiproc.write_graph(graph2use='exec')
