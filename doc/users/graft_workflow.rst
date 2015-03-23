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

:class:`~nipype.pipeline.engine.InterfacedWorkflow` generates workflows with default
``inputnode`` and ``outputnode``. It also exposes the fields without the ``inputnode.`` and
``outputnode.`` prefix.

Let's create a very simple workflow with a segmentation node. Please, notice the fundamental
differences with a standard :class:`~nipype.pipeline.engine.Workflow`:
1) No need for ``inputnode`` and ``outputnode``; 2) fast connection of fields.
::

    import nipype.pipeline.engine as pe
    from nipype.interfaces import fsl
    segm0 = pe.Node(fsl.FAST(number_classes=3, probability_maps=True),
                    name='FSLFAST')
    ifwf0 = pe.InterfacedWorkflow(name='testname0', input_names=['in_t1w'],
                                 output_names=['out_tpm'])
    ifwf0.connect([
        ('in', segm0,  [('in_t1w', 'in_files')]),
        (segm0, 'out', [('probability_maps', 'out_tpm')])
    ])


We can connect an input to this workflow as usual
::

    import nipype.interfaces.io as nio
    ds = pe.Node(nio.DataGrabber(base_directory=os.getcwd(), template='t1.nii'),
                 name='DataSource')
    mywf = pe.Workflow(name='FullWorkflow')
    mywf.connect(ds, 't1', ifwf0, 'inputnode.in_t1w')


The InterfacedWorkflow is useful to create several segmentation alternatives that always take one input
named ``in_t1w`` and return one output named ``out_tpm``. Independently,
:class:`InterfacedWorkflows <nipype.pipeline.engine.InterfacedWorkflow>` do not add much value
to the conventional :class:`Workflows <nipype.pipeline.engine.Workflow>`, but they are interesting as units inside
:class:`GraftWorkflows <nipype.pipeline.engine.GraftWorkflow>`.



Workflows to run cross-comparisons of methods
---------------------------------------------

Say we want to compare segmentation algorithms: FAST from FSL, and Atropos from ANTS.
We want all the comparing methods to have the same names and number of inputs and outputs.

We first create the :class:`~nipype.pipeline.engine.GraftWorkflow`, using a existing workflow
as reference.

::

    compare_wf = pe.GraftWorkflow(name='Comparison', fields_from=ifwf0)

We create the alternate segmentation workflow::

    from nipype.interfaces import ants
    segm1 = pe.Node(ants.Atropos(dimension=3, number_of_tissue_classes=3),
                    name='Atropos')
    ifwf1 = pe.InterfacedWorkflow(name='testname1', input_names=['in_t1w'],
                                 output_names=['out_tpm'])
    ifwf1.connect([
        ('in', segm1,  [('in_t1w', 'intensity_images')]),
        (segm1, 'out', [('posteriors', 'out_tpm')])
    ])

Finally, our workflows under comparison are inserted in the :class:`~nipype.pipeline.engine.GraftWorkflow` using
the ``insert()`` method::

    compare_wf.insert([ifwf0, ifwf1])

