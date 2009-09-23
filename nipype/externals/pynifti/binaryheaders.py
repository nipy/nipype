''' Binary headers differ from headers in that they are represented
internally with a numpy structured array

This binary representation means that there are additional properties
and methods:

Properties::

    .endianness (read only)
    .binaryblock (read only)
    .structarr (read only)

Methods::

    .as_byteswapped(endianness)

and class methods::

    .from_string
    .diagnose_binaryblock

    
'''

from nipype.externals.pynifti.headers import Header

class BinaryHeader(Header):
    pass
