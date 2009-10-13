Design Guidelines
-----------------

These are guidelines that the core nipype developers have agreed on:

Interfaces should keep all parameters affecting construction of the appropriate
command in the "input" bunch.

The .run() method of an Interface should include all required inputs as
explicitly named parameters, and they should take a default value of None.

Any Interface should at a minimum support cwd as a command-line argument to
.run(). This may be accomplished by allowing cwd as an element of the input
Bunch, or handled as a separate case.

Design Principles
-----------------

These are (currently) Dav Clark's best guess at what the group might agree on:

It should be very easy to figure out what was done by the pypeline.

Code should support relocatability - this could be via URIs, relative paths or
potentially other mechanisms.

Unless otherwise called for, code should be thread safe, just in case.

The pipeline should make it easy to change aspects of an analysis with minimal
recomputation, downloading, etc. (This is not the case currently - any change
will overwrite the old node)

However, it should also be easy to identify and delete things you don't need anymore.

Pipelines and bits of pipelines should be easy to share.
