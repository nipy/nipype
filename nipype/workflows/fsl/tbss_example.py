# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
A pipeline to perform TBSS.
"""

"""
Tell python where to find the appropriate functions.
"""
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.fsl as fsl          # fsl
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import os                                    # system functions
import tbss

"""
Confirm package dependencies installed.
"""
from nipype.utils.misc import package_check
package_check('numpy', '1.3', 'tbss_test') 
package_check('scipy', '0.7', 'tbss_test')
package_check('networkx', '1.0', 'tbss_test')
package_check('IPython', '0.10', 'tbss_test')

"""
Specify the related directories
"""
dataDir = '/nfs/s2/dticenter/data4test/tbss/mydata'
workingdir = '/nfs/s2/dticenter/data4test/tbss/tbss_test_workingdir'
subject_list = ['S0001', 'S0005', 'S0036', 'S0038', 'S0085', 'S0099', 'S0004', 'S0032', 'S0037', 'S0057', 'S0098']
"""
Here we get the FA list including all the subjects.
"""
def getFAList(subject_list):
    fa_list = []
    for subject_id in subject_list:
        fa_list.append(subject_id)
    return fa_list
tbss_source = pe.Node(interface=nio.DataGrabber(outfiles=['fa_list']),name='tbss_source')
tbss_source.inputs.base_directory = os.path.abspath(dataDir)
tbss_source.inputs.template = '%s_FA.nii.gz'
tbss_source.inputs.template_args = dict(fa_list=[[getFAList(subject_list)]])

'''
TBSS analysis
'''
tbss_all = tbss.create_tbss_all(name='tbss_all')
#tbss.base_dir = os.path.abspath(workingdir)
tbss_all.inputs.inputnode.target = fsl.Info.standard_image("FMRIB58_FA_1mm.nii.gz")
tbss_all.inputs.inputnode.skeleton_thresh = 0.2

tbssproc = pe.Workflow(name="tbssproc")
tbssproc.base_dir = os.path.abspath(workingdir)
tbssproc.connect([
                (tbss_source, tbss_all,[('fa_list','inputnode.fa_list')])
                ])


if __name__=='__main__':
    tbssproc.run()
    tbssproc.write_graph()
