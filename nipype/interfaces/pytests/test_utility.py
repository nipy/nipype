import os, shutil
from nipype.interfaces import utility
import nipype.pipeline.engine as pe

from tempfile import mkdtemp, mkstemp

from nose.tools import assert_true, assert_raises #TODO: remove it!

#TODO: usung py.test to create and clean tmpfile
def test_function():
    tempdir = os.path.realpath(mkdtemp())
    origdir = os.getcwd()
    os.chdir(tempdir)

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

    # Clean up
    os.chdir(origdir)
    shutil.rmtree(tempdir)



##############################

def make_random_array(size):

    return np.random.randn(size, size)


def should_fail():

    tempdir = os.path.realpath(mkdtemp())
    origdir = os.getcwd()
    os.chdir(tempdir)

    node = pe.Node(utility.Function(input_names=["size"],
                                    output_names=["random_array"],
                                    function=make_random_array),
                   name="should_fail")
    try:
        node.inputs.size = 10
        node.run()
    finally:
        os.chdir(origdir)
        shutil.rmtree(tempdir)

def test_should_fail():
    assert_raises(NameError, should_fail)

##################################

def test_function_with_imports():

    tempdir = os.path.realpath(mkdtemp())
    origdir = os.getcwd()
    os.chdir(tempdir)

    node = pe.Node(utility.Function(input_names=["size"],
                                    output_names=["random_array"],
                                    function=make_random_array,
                                    imports=["import numpy as np"]),
                   name="should_not_fail")
    print(node.inputs.function_str)
    try:
        node.inputs.size = 10
        node.run()
    finally:
        os.chdir(origdir)

#################################
