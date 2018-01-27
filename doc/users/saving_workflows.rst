.. _saving_workflows:

===================================================
Saving Workflows and Nodes to a file (experimental)
===================================================

On top of the standard way of saving (i.e. serializing) objects in Python
(see `pickle <http://docs.python.org/2/library/pickle.html>`_) Nipype
provides methods to turn Workflows and nodes into human readable code.
This is useful if you want to save a Workflow that you have generated
on the fly for future use.

To generate Python code for a Workflow use the export method:

.. testcode::

	from nipype.interfaces.fsl import BET, ImageMaths
	from nipype.pipeline.engine import Workflow, Node, MapNode, format_node
	from nipype.interfaces.utility import Function, IdentityInterface

	bet = Node(BET(), name='bet')
	bet.iterables = ('frac', [0.3, 0.4])

	bet2 = MapNode(BET(), name='bet2', iterfield=['infile'])
	bet2.iterables = ('frac', [0.4, 0.5])

	maths = Node(ImageMaths(), name='maths')

	def testfunc(in1):
	    """dummy func
	    """
	    out = in1 + 'foo' + "out1"
	    return out

	funcnode = Node(Function(input_names=['a'], output_names=['output'], function=testfunc),
	                name='testfunc')
	funcnode.inputs.in1 = '-sub'
	func = lambda x: x

	inode = Node(IdentityInterface(fields=['a']), name='inode')

	wf = Workflow('testsave')
	wf.add_nodes([bet2])
	wf.connect(bet, 'mask_file', maths, 'in_file')
	wf.connect(bet2, ('mask_file', func), maths, 'in_file2')
	wf.connect(inode, 'a', funcnode, 'in1')
	wf.connect(funcnode, 'output', maths, 'op_string')

	wf.export()

This will create a file "outputtestsave.py" with the following content:

.. testcode::

	from nipype.pipeline.engine import Workflow, Node, MapNode
	from nipype.interfaces.utility import IdentityInterface
	from nipype.interfaces.utility import Function
	from nipype.utils.functions import getsource
	from nipype.interfaces.fsl.preprocess import BET
	from nipype.interfaces.fsl.utils import ImageMaths
	# Functions
	func = lambda x: x
	# Workflow
	testsave = Workflow("testsave")
	# Node: testsave.inode
	inode = Node(IdentityInterface(fields=['a'], mandatory_inputs=True), name="inode")
	# Node: testsave.testfunc
	testfunc = Node(Function(input_names=['a'], output_names=['output']), name="testfunc")
	testfunc.interface.ignore_exception = False
	def testfunc_1(in1):
	    """dummy func
	    """
	    out = in1 + 'foo' + "out1"
	    return out

	testfunc.inputs.function_str = getsource(testfunc_1)
	testfunc.inputs.in1 = '-sub'
	testsave.connect(inode, "a", testfunc, "in1")
	# Node: testsave.bet2
	bet2 = MapNode(BET(), iterfield=['infile'], name="bet2")
	bet2.interface.ignore_exception = False
	bet2.iterables = ('frac', [0.4, 0.5])
	bet2.inputs.environ = {'FSLOUTPUTTYPE': 'NIFTI_GZ'}
	bet2.inputs.output_type = 'NIFTI_GZ'
	bet2.terminal_output = 'stream'
	# Node: testsave.bet
	bet = Node(BET(), name="bet")
	bet.interface.ignore_exception = False
	bet.iterables = ('frac', [0.3, 0.4])
	bet.inputs.environ = {'FSLOUTPUTTYPE': 'NIFTI_GZ'}
	bet.inputs.output_type = 'NIFTI_GZ'
	bet.terminal_output = 'stream'
	# Node: testsave.maths
	maths = Node(ImageMaths(), name="maths")
	maths.interface.ignore_exception = False
	maths.inputs.environ = {'FSLOUTPUTTYPE': 'NIFTI_GZ'}
	maths.inputs.output_type = 'NIFTI_GZ'
	maths.terminal_output = 'stream'
	testsave.connect(bet2, ('mask_file', func), maths, "in_file2")
	testsave.connect(bet, "mask_file", maths, "in_file")
	testsave.connect(testfunc, "output", maths, "op_string")

The file is ready to use and includes all the necessary imports.

.. include:: ../links_names.txt
