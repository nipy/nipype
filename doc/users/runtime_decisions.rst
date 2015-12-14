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
normally iif `donotrun == False` (default).