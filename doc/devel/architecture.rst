======================================
 Architecture (discussions from 2009)
======================================

This section reflects notes and discussion between developers during the
start of the nipype project in 2009.

Design Guidelines
-----------------

These are guidelines that the core nipype developers have agreed on:

Interfaces should keep all parameters affecting construction of the
appropriate command in the "input" bunch.

The .run() method of an Interface should include all required inputs
as explicitly named parameters, and they should take a default value
of None.

Any Interface should at a minimum support cwd as a command-line
argument to .run(). This may be accomplished by allowing cwd as an
element of the input Bunch, or handled as a separate case.

Relatedly, any Interface should output all files to cwd if it is set,
and otherwise to os.getcwd() (or equivalent).

We need to decide on a consistent policy towards the maintinence of
paths to files. It seems like the best strategy might be to do
absolute (os.realpath?)  filenames by default, allowing for relative
paths by explicitly including something that doesn't start with a
'/'. This could include '.' in some sort of path-spec.

Class attributes should never be modified by an instance of that class. And
probably not ever.

Providing for Provenance
------------------------
The following is a specific discussion that should be thought out an more
generally applied to the way we handle auto-generation / or "sourcing" of
settings in an interface.

There are two possible sources (at a minimum) from which the interface instance could obtain "outputtype" - itself, or FSLInfo. Currently, the outputtype gets read from FSLInfo if self.outputtype (er, _outputtype?) is None.

In the case of other opt_map specifications, there are defaults that get specified if the value is None. For example output filenames are often auto-generated. If you look at the code for fsl.Bet for example, there is no way for the outfile to get picked up at the pipeline level, because it is a transient variable. This is OK, as the generation of the outfile name is contingent ONLY on inputs which ARE available to the pipeline machinery (i.e., via inspection of the Bet instance's attributes).

However, with outputtype, we are in a situation in which "autogeneration" incorporates potentially transient information external to the instance itself. Thus, some care needs to be taken in always ensuring this information is hashable.


Design Principles
-----------------

These are (currently) Dav Clark's best guess at what the group might agree on:

It should be very easy to figure out what was done by the pypeline.

Code should support relocatability - this could be via URIs, relative
paths or potentially other mechanisms.

Unless otherwise called for, code should be thread safe, just in case.

The pipeline should make it easy to change aspects of an analysis with
minimal recomputation, downloading, etc. (This is not the case
currently - any change will overwrite the old node). Also, the fact
that multiple files get rolled into a single node is problematic for
similar reasons. E.g. - node([file1 ...  file100]) will get recomputed
if we add only one file!.

However, it should also be easy to identify and delete things you
don't need anymore.

Pipelines and bits of pipelines should be easy to share.

Things that are the same should be called the same thing in most
places. For interfaces that have an obvious meaning for the terms,
"infiles" and "outfile(s)". If a file is in both the inputs and
outputs, it should be called the same thing in both places. If it is
produced by one interface and consumed by another, same thing should
be used.

Discussions
-----------

.. toctree::
   :maxdepth: 1

   filename_generation
