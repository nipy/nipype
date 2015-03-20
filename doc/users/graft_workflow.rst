.. _graft_workflow:

=====================================================
Interfaced workflows and GraftWorkflow (experimental)
=====================================================

:class:`nipype.pipeline.engine.InterfacedWorkflow` provides automatic input/output
nodes generation, with some other utilities such as fast connection (avoiding
to specify the connecting fields).

:class:`nipype.pipeline.engine.GraftWorkflow` is intended to create evaluation workflows,
where all the inputs are the same but several different methods are to be compared, stacking
the outputs in lists.


Interfaced workflows
--------------------

:class:`nipype.pipeline.engine.InterfacedWorkflow` generates workflows with default
inputnode and outputnode. It also exposes the fields without the 'inputnode.' and
'outputnode.' prefix.