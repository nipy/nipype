
import neuroimaging.interfaces as nif
import neuroimaging.interfaces.fsl as fsl
import neuroimaging.pipeline.engine as pe

reload(nif)
reload(fsl)
reload(pe)

class MITSource(nif.InterfaceBase):
    def __init__(self):
        super(MITSource,self).__init__()
        self.diskbased = False
        self.name = 'mitsource'
        self.log = {}
        self.outputs['outputs'] = None

    def pre_execute(self):
        pass

    def execute(self):
        """Execute the cmd
        """
        self.log['returncode'] = 0

        self.post_execute()
        return self.outputs
    
    def post_execute(self):
        # check to see that the output file exists.
        self.outputs['outputs'] = '/software/data/functional.nii.gz'

#######################################################
M1 = pe.generate_pipeline_node(MITSource())
M2 = pe.generate_pipeline_node(fsl.Bet())

# Either
M2.inputs.update(frac=0.4,flags={'-v':''})
M2.iterables = dict(frac=lambda:[0.1,0.2,0.3])

pipeline_graph = pe.Pipeline()
pipeline_graph.add_nodes_from([M1,M2])
pipeline_graph.add_edges_from([
    (M1,M2,[('outputs','inputfile')])
    ])

# execute!!!
pe.execute_pipeline(pipeline_graph)
#####################################################
