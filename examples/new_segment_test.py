'''
Created on 13 May 2010

@author: filo
'''
from nipype.interfaces.spm.preprocess import NewSegment

interface = NewSegment()
interface.inputs.channels = [('/home/filo/data/anonymised/coD136_anont1mprnssagp2iso.nii', 0.0001, 60, (False, False))]
res = interface.run()

print res.outputs