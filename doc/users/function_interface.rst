.. _function_interface:

==============================================
Wrapping Python functions and Nipype Workflows
==============================================

Most Nipype interfaces provide access to external programs, such as FSL
binaries or SPM routines. However, Nipype has two special interfaces
that allow you to wrap arbitrary Python code 
(:class:`nipype.interfaces.utility.wrappers.Function`)
or full Nipype workflows (:class:`nipype.interfaces.utility.wrappers.WorkflowInterface`)
in the Interface framework and seamlessly integrate them
into your workflows.


The Function Interface
----------------------

A Simple Function Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most important component of a working Function interface is a Python
function. There are several ways to associate a function with a Function
interface, but the most common way will involve functions you code
yourself as part of your Nipype scripts. Consider the following function::

    def add_two(val):
        return val + 2

This simple function takes a value, adds 2 to it, and returns that new value.

Just as Nipype interfaces have inputs and outputs, Python functions have
inputs, in the form of parameters or arguments, and outputs, in the form
of their return values. When you define a Function interface object with
an existing function, as in the case of ``add_two()`` above, you must pass the
constructor information about the function's inputs, its outputs, and the
function itself.  For example,

::

    from nipype.interfaces.utility import Function
    add_two_interface = Function(input_names=["val"],
                                 output_names=["out_val"],
                                 function=add_two)

Then you can set the inputs and run just as you would with any other
interface::

    add_two_interface.inputs.val = 2
    res = add_two_interface.run()
    print res.outputs.out_val

Which would print ``4``.

Note that, if you are working interactively, the Function interface is
unable to use functions that are defined within your interpreter session.
(Specifically, it can't use functions that live in the ``__main__`` namespace).


Using External Packages
~~~~~~~~~~~~~~~~~~~~~~~

Chances are, you will want to write functions that do more complicated
processing, particularly using the growing stack of Python packages
geared towards neuroimaging, such as Nibabel_, Nipy_, or PyMVPA_.

While this is completely possible (and, indeed, an intended use of the
Function interface), it does come with one important constraint. The
function code you write is executed in a standalone environment,
which means that any external functions or classes you use have to
be imported within the function itself::

    def get_n_trs(in_file):
        import nibabel
        f = nibabel.load(in_file)
        return f.shape[-1]

Without explicitly importing Nibabel in the body of the function, this
would fail.

Alternatively, it is possible to provide a list of strings corresponding
to the imports needed to execute a function as a parameter of the `Function`
constructor. This allows for the use of external functions that do not
import all external definitions inside the function body.

Hello World - Function interface in a workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following snippet of code demonstrates the use of the function interface in
the context of a workflow. Note the use of ``import os`` within the function as
well as returning the absolute path from the Hello function. The `import` inside
is necessary because functions are coded as strings and do not have to be on the
PYTHONPATH. However any function called by this function has to be available on
the PYTHONPATH. The `absolute path` is necessary because all workflow nodes are
executed in their own directory and therefore there is no way of determining
that the input file came from a different directory:

  ::

    import nipype.pipeline.engine as pe
    from nipype.interfaces.utility import Function

    def Hello():
       import os
       from nipype import logging
       iflogger = logging.getLogger('interface')
       message = "Hello "
       file_name =  'hello.txt'
       iflogger.info(message)
       with open(file_name, 'w') as fp:
           fp.write(message)
       return os.path.abspath(file_name)

    def World(in_file):
       from nipype import logging
       iflogger = logging.getLogger('interface')
       message = "World!"
       iflogger.info(message)
       with open(in_file, 'a') as fp:
           fp.write(message)

    hello = pe.Node(name='hello',
                   interface=Function(input_names=[],
                                      output_names=['out_file'],
                                      function=Hello))
    world = pe.Node(name='world',
                   interface=Function(input_names=['in_file'],
                                      output_names=[],
                                      function=World))

    pipeline = pe.Workflow(name='nipype_demo')
    pipeline.connect([(hello, world, [('out_file', 'in_file')])])
    pipeline.run()
    pipeline.write_graph(graph2use='flat')


Advanced Use
~~~~~~~~~~~~

To use an existing function object (as we have been doing so far) with a Function
interface, it must be passed to the constructor. However, it is also possible
to dynamically set how a Function interface will process its inputs using the
special ``function_str`` input.

This input takes not a function object, but actually a single string that can
be parsed to define a function. In the equivalent case to our example above,
the string would be

::

    add_two_str = "def add_two(val):\n    return val + 2\n"

Unlike when using a function object, this input can be set like any other,
meaning that you could write a function that outputs different function
strings depending on some run-time contingencies, and connect that output
the the ``function_str`` input of a downstream Function interface.

The Workflow Interface
----------------------

Along the same lines of the Function interface, it is possible to wrap
nipype workflows inside the
:class:`nipype.interfaces.utility.wrappers.WorkflowInterface`.
Wrapping workflows enables subworkflows to dinamically iterate over
inputs using ``MapNode`` (`#819 <https://github.com/nipy/nipype/issues/819>`_),
and allows for the  conditional execution of subworkflows
(see for instance, `#878 <https://github.com/nipy/nipype/issues/878>`_,
`#1081 <https://github.com/nipy/nipype/issues/1081>`_, and
`#1299 <https://github.com/nipy/nipype/issues/1299>`_).
  
A use case
~~~~~~~~~~

Say we have the following workflow:

  ::

    def _sum(a, b):
        return a + b

    def sum_workflow(name='SumWorkflow'):
        inputnode = pe.Node(niu.IdentityInterface(
            fields=['a', 'b']), name='inputnode')

        sumnode = pe.Node(niu.Function(
            input_names=['a', 'b'], output_names=['c'],
            function=_sum), name='sumnode')

        outputnode = pe.Node(niu.IdentityInterface(
            fields=['c']), name='outputnode')

        wf = pe.Workflow(name=name)
        wf.connect([
            (inputnode, sumnode, [('a', 'a'), ('b', 'b')]),
            (sumnode, outpunode, [('c', 'c')])
        ])

        return wf


We want to run the workflow over a number of combinations of
the inputs ``a`` and ``b``. However, these combinations should
be generated by a previous workflow. Therefore, we cannot
use the ``iterables`` feature of Nipype ``Node``. In this case,
we need to use a ``MapNode``, with our workflow wrapped within
a ``WorkflowInterface``:

  ::

      wrapped = pe.MapNode(niu.WorkflowInterface(workflow=sum_workflow),
                           iterfield=['a', 'b'], name='dyniterable')


This ``wrapped`` map node can be used in a workflow, and set the inputs
``'a'`` and ``'b'`` the same way it is done in a regular interface:

  ::

      wrapped.inputs.a = [10, 15, 2, 12]
      wrapped.inputs.b = [1, 14, -1, 23]


Both inputs will work as expected when connected from other nodes in
a Nipype Workflow.


Limitations
~~~~~~~~~~~

The main limitation of :class:`nipype.interfaces.utility.wrappers.WorkflowInterface`
is that the workflow can only be run internally using the ``Linear`` or ``MultiProc``
plugins. Further work could be directed towards running using other synchronous
plugins. The only restriction for the plugin used to run the inner interface is
that it should be synchronous, in order to collect the workflow outputs after execution.



.. include:: ../links_names.txt
