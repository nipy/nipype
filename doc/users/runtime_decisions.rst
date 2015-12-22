.. runtime_decisions:

===========================
Runtime decisions in nipype
===========================

Adding conditional execution (https://github.com/nipy/nipype/issues/878)
other runtime decisions (https://github.com/nipy/nipype/issues/819) in
nipype is an old request. Here we introduce some logic and signalling into
the workflows.

Disable signal in nodes
=======================

The :class:`nipype.pipeline.engine.Node` now provides a `signals` attribute
with a `disable` signal by default.
When the `run()` member of a node is called, the interface will run
normally *iff* `disable` is `False` (default case).

Example
-------

For instance, the following code will run the BET interface from fsl:

    >>> from nipype.pipeline.engine import Node
    >>> from nipype.interfaces import fsl
    >>> bet = Node(fsl.BET(), 'BET')
    >>> bet.inputs.in_file = 'T1.nii'
    >>> bet.run() # doctest: +SKIP

However, if we set the disable signal, then the interface is not run.

    >>> bet.signals.disable = True
    >>> bet.run() is None
    True

Disable signal in Workflow
==========================

:class:`nipype.pipeline.engine.Workflow` also provides signals, including
`disable` by default.
It is also allowed to connect the output of a node to a signal in a workflow,
using the `signalnode.<name-of-signal>` port.


Example
-------

    >>> from nipype.pipeline import engine as pe
    >>> from nipype.interfaces import utility as niu
    >>> def _myfunc(val):
    ...     return val + 1
    >>> wf = pe.Workflow('TestDisableWorkflow')
    >>> inputnode = pe.Node(niu.IdentityInterface(
    ...                     fields=['in_value']), 'inputnode')
    >>> outputnode = pe.Node(niu.IdentityInterface(
    ...                      fields=['out_value']), 'outputnode')
    >>> func = pe.Node(niu.Function(
    ...     input_names=['val'], output_names=['out'],
    ...     function=_myfunc), 'functionnode')
    >>> wf.connect([
    ...     (inputnode, func, [('in_value', 'val')]),
    ...     (ifset, outputnode, [('out', 'out_value')])
    ... ])
    >>> wf.inputs.inputnode.in_value = 0
    >>> wf.run() # Will produce 1 in outputnode.out_value

The workflow can be disabled:
    
    >>> wf.signals.disabled = True
    >>> wf.run() # The outputnode.out_value remains <undefined>


CachedWorkflow
==============

The :class:`nipype.pipeline.engine.CachedWorkflow` is a type of workflow
that implements a conditional workflow that is executed *iff* the set of
cached inputs is not set.
More precisely, this workflow is able to decide whether its nodes should
be executed or not if all the inputs of the input node called `cachenode`
are set.
For instance, in https://github.com/nipy/nipype/pull/1081 this feature
is requested.
The implementation makes use of :class:`nipype.interfaces.utility.CheckInterface`
which produces an output `out` set to `True` if any/all the inputs are defined
and `False` otherwise.
The input `operation` allows to switch between the any and all conditions.


Example
-------

    >>> from nipype.pipeline import engine as pe
    >>> from nipype.interfaces import utility as niu
    >>> def _myfunc(a, b):
    ...     return a + b
    >>> wf = pe.CachedWorkflow('InnerWorkflow',
    ...                        cache_map=('c', 'out'))
    >>> inputnode = pe.Node(niu.IdentityInterface(
    ...                     fields=['a', 'b']), 'inputnode')
    >>> func = pe.Node(niu.Function(
    ...     input_names=['a', 'b'], output_names=['out'],
    ...     function=_myfunc), 'functionnode')
    >>> wf.connect([
    ...     (inputnode, func, [('a', 'a'), ('b', 'b')]),
    ...     (func, 'output', [('out', 'out')])
    ... ])
    >>> wf.inputs.inputnode.a = 2
    >>> wf.inputs.inputnode.b = 3
    >>> wf.run() # Will generate 5 in outputnode.out

Please note that the output node should be referred to as 'output' in
the *connect()* call.

If we set all the inputs of the cache, then the workflow is skipped and
the output is mapped from the cache:

    >>> wf.inputs.cachenode.c = 7
    >>> wf.run() # Will produce 7 in outputnode.out
