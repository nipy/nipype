### WIP: moving tests from nose framework, based on nipype/nipype/interfaces/tests/test_utility.py
### TODO: move ALL tests from nose file
import pytest
import os 
from nipype.interfaces import utility
import nipype.pipeline.engine as pe

import pdb

def test_function(tmpdir):

    def gen_random_array(size):
        import numpy as np
        return np.random.rand(size, size)

    f1 = pe.MapNode(utility.Function(input_names=['size'], output_names=['random_array'], function=gen_random_array), name='random_array', iterfield=['size'])
    f1.inputs.size = [2, 3, 5]

    wf = pe.Workflow(name="test_workflow")

    def increment_array(in_array):
        return in_array + 1

    f2 = pe.MapNode(utility.Function(input_names=['in_array'], output_names=['out_array'], function=increment_array), name='increment_array', iterfield=['in_array'])

    wf.connect(f1, 'random_array', f2, 'in_array')
    wf.run()



def make_random_array(size):
    return np.random.randn(size, size)


def should_fail(tempdir):
    os.chdir(tempdir)

    node = pe.Node(utility.Function(input_names=["size"],
                                    output_names=["random_array"],
                                    function=make_random_array),
                   name="should_fail")
    node.inputs.size = 10
    node.run()

 
def test_should_fail(tmpdir):
    with pytest.raises(NameError) as excinfo:
        should_fail(str(tmpdir))


def test_function_with_imports(tmpdir):
    os.chdir(str(tmpdir))

    node = pe.Node(utility.Function(input_names=["size"],
                                    output_names=["random_array"],
                                    function=make_random_array,
                                    imports=["import numpy as np"]),
                   name="should_not_fail")
    print(node.inputs.function_str)
    node.inputs.size = 10
    node.run()
