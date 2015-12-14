.. runtime_decisions:

===========================
Runtime decisions in nipype
===========================

Adding conditional execution (https://github.com/nipy/nipype/issues/878)
other runtime decisions (https://github.com/nipy/nipype/issues/819) in
nipype is an old request. Here we introduce some logic and signalling into
the workflows.

ConditionalNode
===============

The :class:`nipype.pipeline.engine.ConditionalNode` wrapping any interface
will add an input called `donotrun` that will switch between run/donotrun
modes. When the `run()` member of a node is called, the interface will run
normally *iff* `donotrun` is `False` (default case).

Additional elements
===================

Therefore, :class:`nipype.pipeline.engine.ConditionalNode` can be connected
from any Boolean output of other interfaces and using inline functions.
To help introduce logical operations that produce boolean signals to switch
conditional nodes, nipype provides the
:class:`nipype.interfaces.utility.CheckInterface` which produces an
output `out` set to `True` if any/all the inputs are defined and `False`
otherwise. The input `operation` allows to switch between the any and all
conditions.

Example: CachedWorkflow
=======================

An application of the mentioned elements is the
:class:`nipype.pipeline.engine.CachedWorkflow`.
This workflow is able to decide whether its nodes should be executed or
not if all the inputs of the input node called `cachenode` are set.
For instance, in https://github.com/nipy/nipype/pull/1081 this feature
is requested.