''' Generic header class

The basic principle of the header object is that it manages and
contains header information.  Each header type may have different
attributes that can be set.  Some headers can contain only subsets of
possible passed values - for example the basic Analyze header can only
encode the zooms in an affine transform - not shears, rotations,
translations.

The attributes and methods of the object guarantee that the set values
will be consistent and valid with the header standard, in some sense.
The object API therefore gives "safe" access to the header.  You can
reach all the named fields in the header directly with the
``header_data`` attribute.  If you futz with these, the object
makes no guarantee that the data in the header are consistent.

Headers do not have filenames, they refer only the set of attributes in
the header.  The containing object manages the filenames, and therefore
must know how to predict image filenames from header filenames, whether
these are different, and so on.

You can access and set fields of a particular header type using standard
__getitem__ / __setitem__ syntax:

    hdr['field'] = 10

Headers also implement general mappingness:

    hdr.keys()
    hdr.items()
    hdr.values()
    
Class attributes are::

    .default_x_flip
    
with methods::
    
    .get/set_data_shape
    .get/set_data_dtype
    .get/set_zooms
    .get_base_affine
    .get_best_affine
    .check_fix
    .write_to(fileobj)
    .copy
    .__str__
    .__eq__
    .__ne__

and class methods::

    .from_fileobj(fileobj)

'''

class Header(object):
    pass
