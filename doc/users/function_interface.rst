.. _function_interface:

======================
The Function Interface
======================

Most Nipype interfaces provide access to external programs, such as FSL
binaries or SPM routines. However, a special interface, 
:class:`nipype.interfaces.utility.Function`,
allows you to wrap arbitrary Python code in the Interface framework and 
seamlessly integrate it into your workflows.

A Simple Function Interface
---------------------------

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
(Specifcally, it can't use functions that live in the ``__main__`` namespace).

Using External Packages
-----------------------

Chances are, you will want to write functions that do more complicated
processing, particularly using the growing stack of Python packages 
geared towards neuroimaging, such as Nibabel_, Nipy_, or PyMVPA_.

While this is completely possible (and, indeed, an intended use of the
Function interface), it does come with one important constraint. The
function code you write is excecuted in a standalone environment, 
which means that any external functions or classes you use have to
be imported within the function itself::

    def get_n_trs(in_file):
        import nibabel
        f = nibabel.load(in_file)
        return f.shape[-1]

Without explicitly importing Nibabel in the body of the function, this
would fail.

Hello World - Function interface in a workflow
----------------------------------------------

Contributed by: Hänel Nikolaus Valentin 

The following snippet of code demonstrates the use of the function interface in
the context of a workflow. Note the use of `import os` within the function as
well as returning the absolute path from the Hello function. The `import` inside
is necessary because functions are coded as strings and do not have to be on the
PYTHONPATH. However any function called by this function has to be available on
the PYTHONPATH. The `absolute path` is necessary because all workflow nodes are
executed in their own directory and therefore there is no way of determining
that the input file came from a different directory::

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
------------

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
meaning that you could write a function that outputs differnet function
strings depending on some run-time contingencies, and connect that output
the the ``function_str`` input of a downstream Function interface. 

.. include:: ../links_names.txt
