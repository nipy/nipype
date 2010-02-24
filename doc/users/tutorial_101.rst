.. _tutorial_101:

============
Pipeline 101
============

A workflow or pipeline is built by connecting processes or nodes to each
other. In the context of nipype, every interface can be treated as a pipeline
node having defined inputs and outputs. Creating a workflow then is a matter
of connecting appropriate outputs to inputs. Currently, workflows are limited
to being directional and cannot have any loops, thereby creating an ordering to
data flow. The following nipype component architecture might help understanding
some of the tutorials presented here.

.. image:: images/componentarchitecture.png
   :width: 600 px

My first pipeline
=================

Although the most trivial pipeline consists of a single node, we will
create a pipeline with two nodes: a realign node that will send
the realigned functional data to a smoothing node. It is important to note that
setting up a pipeline is separate from executing it.

**1. Import appropriate modules**

.. testcode::
   
   import nipype.interfaces.spm as spm          # the spm interfaces
   import nipype.pipeline.node_wrapper as nw    # the wrapper
   import nipype.pipeline.engine as pe          # the workflow

**2. Define nodes**

Here we take instances of interfaces and make them pipeline compatible by
wrapping them with pipeline specific elements. To determine the inputs and outputs
of a given interface, please see :ref:`interface_tutorial`. Let's
start with defining a realign node using the interface
:class:`nipype.interfaces.spm.Realign`

.. testcode::
   
   realigner = nw.NodeWrapper(interface=spm.Realign())
   realigner.inputs.infile = 'somefuncrun.nii'
   realigner.inputs.register_to_mean = True

This would be equivalent to:

.. testcode::
   
   realigner = nw.NodeWrapper(interface=spm.Realign(infile='somefuncrun.nii',
                                                    register_to_mean = True))

In Pythonic terms, this is saying that interface option in NodeWrapper accepts
an *instance* of an interface. The inputs to this interface can be set either
later or while initializing the interface. Similar to the realigner node, we
now set up a smoothing node.

.. testcode::

   smoother = nw.NodeWrapper(interface=spm.Smooth(fwhm=6))

Now we have two nodes with their inputs defined. Note that we have not defined
an input file for the smoothing node. This will be done by connecting the
realigner to the smoother in step 5.

**3. Creating and configuring a pipeline**

Here we create an instance of a pipeline and indicate that it should operate in
the current directory.

.. testcode::
   
   workflow = pe.Pipeline()
   workflow.config['workdir'] = '.'

**4. Adding nodes to pipelines (optional)**

If nodes are going to be connected (see step 5), this step is not
necessary. However, if you would like to run a node by itself without
connecting it to any other node, then you need to add it to the
workflow. For adding nodes, order of nodes is not important.

.. testcode::
   
   workflow.add_nodes([smoother, realigner])

This results in a workflow containing two isolated nodes:

.. image:: images/smoothrealignunconnected.png

**5. Connecting nodes to each other**

We want to connect the output produced by realignment to the input of
smoothing. This is done as follows.

.. testcode::
   
   workflow.connect(realigner, 'realigned_files', smoother, 'infile')

or alternatively, a more flexible notation can be used. Although not shown here,
the following notation can be used to connect multiple outputs from one node to
multiple inputs (see step 7 below).

.. testcode::
   
   workflow.connect([(realigner, smoother, [('realigned_files', 'infile')])])

This results in a workflow containing two connected nodes:

.. image:: images/smoothrealignconnected.png

**6. Visualizing the workflow**

The workflow is represented as a directed acyclic graph (DAG) and one
can visualize this using the following command. In fact, the pictures
above were generated using this.

.. testcode::
   
   workflow.export_graph()

This creates two files graph.dot and graph_detailed.dot and if
graphviz_ is installed on your system it automatically converts it
to png files. If graphviz is not installed you can take the dot files
and load them in a graphviz visualizer elsewhere.


**7. Extend it**

Now that you have seen a basic pipeline let's add another node to the
above pipeline.

.. testcode::
   
   import nipype.algorithms.rapidart as ra
   artdetect = nw.NodeWrapper(interface=ra.ArtifactDetect())
   artdetect.inputs.use_differences  = [True, False]
   art.inputs.use_norm = True
   art.inputs.norm_threshold = 0.5
   art.inputs.zintensity_threshold = 3
   workflow.connect([(realigner, artdetect,
                      [('realigned_files', 'realigned_files'),
                       ('realignment_parameters','realignment_parameters')]
                     )])

.. note::

      a) How an alternative form of connect was used to connect multiple
      output fields from the realign node to corresponding input
      fields of the artifact detection node.

      b) The current visualization only shows connected input and
      output ports. It does not show all the parameters that you have
      set for a node.

This results in

.. image:: images/threecomponentpipe.png
   :width: 650 px

**8. Execute the workflow**

Assuming that **somefuncrun.nii** is actually a file or you've
replaced it with an appropriate one, you can run the pipeline with:

.. testcode::
   
   workflow.run()

This should create three folders in your current directory:
Realign.spm, ArtifactDetect.rapidart and Smooth.spm. The outputs of
these routines are in these folders.


.. include:: ../links_names.txt
