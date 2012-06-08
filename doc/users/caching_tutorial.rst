
.. _caching:

===========================
Interface caching 
===========================

This section details the interface-caching mechanism, exposed in the
:mod:`nipype.caching` module.

.. currentmodule:: nipype.caching

Interface caching: why and how
===============================

* :ref:`Pipelines <tutorial_101>` (also called `workflows`) specify
  processing by an execution graph. This is useful because it opens the
  door to dependency checking and enable `i)` to minimize
  recomputations, `ii)` to have the execution engine transparently deal
  with intermediate file manipulations.

  They however do not blend in well with arbitrary Python code, as they
  must rely on their own execution engine.

* :ref:`Interfaces <interface_tutorial>` give fine control of the
  execution of each step with a thin wrapper on the underlying software.
  As a result that can easily be inserted in Python code.

  However, they force the user to specify explicit input and output file
  names and cannot do any caching.

This is why nipype exposes an intermediate mechanism, `caching` that 
provides transparent output file management and caching within imperative
Python code rather than a workflow.

A big picture view: using the :class:`Memory` object
=======================================================

nipype caching relies on the :class:`Memory` class: it creates an
execution context that is bound to a disk cache::

    >>> from nipype.caching import Memory
    >>> mem = Memory(base_dir='.')

Note that the caching directory is a subdirectory called `nipype_mem` of
the given `base_dir`. This is done to avoid polluting the base director.

In the corresponding execution context, nipype interfaces can be turned
into callables that can be used as functions using the
:meth:`Memory.cache` method. For instance if we want to run the fslMerge
command on a set of files::

    >>> from nipype.interface import fsl
    >>> fsl_merge = mem.cache(fsl.Merge)

Note that the :meth:`Memory.cache` method takes interfaces **classes**,
and not instances.

The resulting `fsl_merge` object can be applied as a function to
parameters, that will form the inputs of the `merge` fsl commands. Those
inputs are given as keyword arguments, bearing the same name as the
name in the inputs specs of the interface. In IPython, you can also get
the argument list by using the `fsl_merge?` synthax to inspect the docs::

    In [10]: fsl_merge?
    String Form:PipeFunc(nipype.interfaces.fsl.utils.Merge, base_dir=/home/varoquau/dev/nipype/nipype/caching/nipype_mem)
    Namespace:  Interactive
    File:       /home/varoquau/dev/nipype/nipype/caching/memory.py
    Definition: fsl_merge(self, **kwargs)
    Docstring:
    Use fslmerge to concatenate images
        
    Inputs
    ------

    Mandatory:
    dimension: dimension along which the file will be merged
    in_files: None

    Optional:
    args: Additional parameters to the command
    environ: Environment variables (default={})
    ignore_exception: Print an error message instead of throwing an exception in case the interface fails to run (default=False)
    merged_file: None
    output_type: FSL output type

    Outputs
    -------
    merged_file: None
    Class Docstring:
    ...

Thus `fsl_merge` is applied to parameters as such::

    >>> results = fsl_merge(dimension='t', in_files=['a.nii.gz', 'b.nii.gz'])
    INFO:workflow:Executing node faa7888f5955c961e5c6aa70cbd5c807 in dir: /home/varoquau/dev/nipype/nipype/caching/nipype_mem/nipype-interfaces-fsl-utils-Merge/faa7888f5955c961e5c6aa70cbd5c807
    INFO:workflow:Running: fslmerge -t /home/varoquau/dev/nipype/nipype/caching/nipype_mem/nipype-interfaces-fsl-utils-Merge/faa7888f5955c961e5c6aa70cbd5c807/a_merged.nii /home/varoquau/dev/nipype/nipype/caching/a.nii.gz /home/varoquau/dev/nipype/nipype/caching/b.nii.gz

The results are standard nipype nodes results. In particular, they expose
an `outputs` attribute that carries all the outputs of the process, as
specified by the docs.

    >>> results.outputs.merged_file
    '/home/varoquau/dev/nipype/nipype/caching/nipype_mem/nipype-interfaces-fsl-utils-Merge/faa7888f5955c961e5c6aa70cbd5c807/a_merged.nii'

Finally, and most important, if the node is applied to the same input
parameters, it is not computed, and the results are reloaded from the
disk::

    >>> results = fsl_merge(dimension='t', in_files=['a.nii.gz', 'b.nii.gz'])
    INFO:workflow:Executing node faa7888f5955c961e5c6aa70cbd5c807 in dir: /home/varoquau/dev/nipype/nipype/caching/nipype_mem/nipype-interfaces-fsl-utils-Merge/faa7888f5955c961e5c6aa70cbd5c807
    INFO:workflow:Collecting precomputed outputs

Once the :class:`Memory` is set up and you are applying it to data, an
important thing to keep in mind is that you are using up disk cache. It
might be useful to clean it using the methods that :class:`Memory`
provides for this: :meth:`Memory.clear_previous_runs`,
:meth:`Memory.clear_runs_since`.

.. topic:: Example

   A full-blown example showing how to stage multiple operations can be
   found in the :download:`caching_example.py <../../examples/caching_example.py>` file.

Usage patterns: working efficiently with caching
===================================================

The goal of the `caching` module is to enable writing plain Python code
rather than workflows. Use it: instead of data grabber nodes, use for
instance the `glob` module. To vary parameters, use `for` loops. To make
reusable code, write Python functions.

One good rule of thumb to respect is to avoid the usage of explicit
filenames apart from the outermost inputs and outputs of your
processing. The reason being that the caching mechanism of
:mod:`nipy.caching` takes care of generating the unique hashes, ensuring
that, when you vary parameters, files are not overridden by the output of
different computations.

.. topic:: Debuging
    
    If you need to inspect the running environment of the nodes, it may
    be useful to know where they were executed. With `nipype.caching`,
    you do not control this location as it is encoded by hashes.

    To find out where an operation has been persisted, simply look in
    it's output variable::

        out.runtime.cwd

Finally, the more you explore different parameters, the more you risk
creating cached results that will never be reused. Keep in mind that it
may be useful to flush the cache using :meth:`Memory.clear_previous_runs`
or :meth:`Memory.clear_runs_since`.

API reference
===============

The main class of the :mod:`nipype.caching` module is the :class:`Memory`
class:

.. autoclass:: Memory
    :members: __init__, cache, clear_previous_runs, clear_runs_since

____

Also used are the :class:`PipeFunc`, callables that are returned by the
:meth:`Memory.cache` decorator:

.. currentmodule:: nipype.caching.memory

.. autoclass:: PipeFunc
    :members:  __init__

