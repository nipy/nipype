==============
 Architecture
==============

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

Dancing about Architecture
--------------------------

Somewhat like talking about Jazz.
