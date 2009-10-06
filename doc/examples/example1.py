import nipype.interfaces.spm as spm
import nipype.pipeline.node_wrapper as nw
import nipype.pipeline.engine as pe
import os

# interface example
realign1 = spm.Realign()
realign1.inputs.infile = os.path.abspath('data/funcrun.nii')
realign1.inputs.register_to_mean = True
realign1.inputs.cwd = os.path.abspath('test2')
#results1 = realign1.run()


# node_wrapper example
realign2 = nw.NodeWrapper(interface=spm.Realign(),
                          base_directory='test2',
                          diskbased=True)
realign2.inputs.infile = os.path.abspath('data/funcrun.nii')
realign2.inputs.register_to_mean = True
#results2 = realign2.run()


# pipeline example
realign3 = nw.NodeWrapper(interface=spm.Realign(), diskbased=True)
realign3.inputs.infile = os.path.abspath('data/funcrun.nii')
realign3.inputs.register_to_mean = True

coregister = nw.NodeWrapper(interface=spm.Coregister(), diskbased=True)
coregister.inputs.target = os.path.abspath('data/struct.nii')

pipeline = pe.Pipeline()
pipeline.config['workdir'] = os.path.abspath('test3')
pipeline.connect([(realign3, coregister, 
                   [('mean_image', 'source'), 
                    ('realigned_files', 'apply_to_files')]
                   )])
#pipeline.run()
