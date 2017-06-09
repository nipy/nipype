"""
Demonstration workflow for linking singularity containers
Depends on containers/demo_container.img existing.
This file isn't committed as it's pretty big. Once Singularity engine is
installed it can be created by running containers/build_container as root.

$ cd containers
$ sudo ./build_container

"""


import os
import inspect
from nipype.interfaces.singularity import demo
from nipype import SelectFiles, Node, Workflow

working_dir = os.path.abspath('working_dir')

script_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))

demo_container = os.path.abspath(os.path.join(script_dir,
                                              'containers/demo_container.img'))

data_dir = os.path.abspath(os.path.join(script_dir, 'data'))


maps = [data_dir + ':/input',
        working_dir + ':/working',
        '.:/output']

node1 = Node(demo.DemoTask_1(container=demo_container,
                             map_dirs_list=maps),
             name="Node1")
node2 = Node(demo.DemoTask_2(container=demo_container,
                             map_dirs_list=maps),
             name="Node2")

templates = {'input': '{subject_id}.txt'}

sf = Node(SelectFiles(templates),
          name="SelectFiles")

sf.inputs.base_directory = data_dir
sf.inputs.subject_id = 'Sub0001'

wf = Workflow(name="DemoWorkflow", base_dir=working_dir)

wf.connect([(sf, node1, [("input", "in_file")]),
            (node1, node2, [("out_file", "in_file")])])

wf.run()
