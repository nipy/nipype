# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""This module contains ... 

"""
from __future__ import print_function, division, unicode_literals, absolute_import

from builtins import filter, object, str, bytes
import os

# perform all external trait imports here
import traitlets, pdb 


# dj NOTE: `key_trait` must be a Trait or None
# dj NOTE: when `value_trait` is a tuple, it doesn't give error, but just doesn't check the type
# dj TODO: create an issue! 
# dj NOTE: so either we created DictBytByt if needed, or write some extra class
# dj NOTE: at the end decided to move completely (it's used in one place)
#DictStrStr = traitlets.Dict(value_trait=traitlets.Unicode(), key_trait=traitlets.Unicode())


class File(traitlets.Unicode):
    """ Defines a trait whose value must be the name of a file.
    """

    # A description of the type of value this trait accepts:
    info_text = 'a file name'

    def __init__(self, value=None, filter=None, auto_set=False,
                 entries=0, exists=False, **metadata):
        """ Creates a File trait.

        Parameters
        ----------
        value : string
            The default value for the trait
        filter : string
            A wildcard string to filter filenames in the file dialog box used by
            the attribute trait editor.
        auto_set : boolean
            Indicates whether the file editor updates the trait value after
            every key stroke.
        exists : boolean
            Indicates whether the trait value must be an existing file or
            not.

        Default Value
        -------------
        *value* or None
        """

        self.filter = filter
        self.auto_set = auto_set
        self.entries = entries
        self.exists = exists
        if exists:
            self.info_text = 'an existing file name'
        super(File, self).__init__(value, allow_none=True, **metadata)

    def validate(self, object, value):
        """ Validates that a specified value is valid for this trait.

        """
        validated_value = super(File, self).validate(object, value)
        if not self.exists:
            return validated_value
        elif os.path.isfile(value):
            return validated_value

        self.error(object, value)


# -------------------------------------------------------------------------------
#  'Directory' traits:
# -------------------------------------------------------------------------------


class Directory (traitlets.Unicode):
    """
    Defines a trait whose value must be the name of a directory.
    """

    # A description of the type of value this trait accepts:
    info_text = 'a directory name'

    def __init__(self, value=None, auto_set=False, entries=0,
                 exists=False, **metadata):
        """ Creates a Directory trait.

        Parameters
        ----------
        value : string
            The default value for the trait
        auto_set : boolean
            Indicates whether the directory editor updates the trait value
            after every key stroke.
        exists : boolean
            Indicates whether the trait value must be an existing directory or
            not.

        Default Value
        -------------
        *value* or None
        """
        self.entries = entries
        self.auto_set = auto_set
        self.exists = exists

        if exists:
            self.info_text = 'an existing directory name'

        super(Directory, self).__init__(value, **metadata)

    def validate(self, object, value):
        """ Validates that a specified value is valid for this trait.

        """
        if isinstance(value, (str, bytes)):
            if not self.exists:
                return value
            if os.path.isdir(value):
                return value
        self.error(object, value)


# lists of tuples
# each element consists of :
# - uncompressed (tuple[0]) extension
# - compressed (tuple[1]) extension
img_fmt_types = {
        'nifti1': [('.nii', '.nii.gz'),
                   (('.hdr', '.img'), ('.hdr', '.img.gz'))],
        'mgh': [('.mgh', '.mgz'), ('.mgh', '.mgh.gz')],
        'nifti2': [('.nii', '.nii.gz')],
        'cifti2': [('.nii', '.nii.gz')],
        'gifti': [('.gii', '.gii.gz')],
        'dicom': [('.dcm', '.dcm'), ('.IMA', '.IMA'), ('.tar', '.tar.gz')],
        'nrrd': [('.nrrd', 'nrrd'), ('nhdr', 'nhdr')],
        'afni': [('.HEAD', '.HEAD'), ('.BRIK', '.BRIK')]
        }

class ImageFile(File):
    """ Defines a trait of specific neuroimaging files """

    def __init__(self, value='', filter=None, auto_set=False, entries=0,
                 exists=False, types=[], allow_compressed=True, **metadata):
        """ Trait handles neuroimaging files.

        Parameters
        ----------
        types : list
            Strings of file format types accepted
        compressed : boolean
            Indicates whether the file format can compressed
        """
        self.types = types
        self.allow_compressed = allow_compressed
        super(ImageFile, self).__init__(value, filter, auto_set, entries,
                                        exists, **metadata)

    def grab_exts(self):
        # TODO: file type validation
        exts = []
        for fmt in self.types:
            if fmt in img_fmt_types:
                exts.extend(sum([[u for u in y[0]] if isinstance(y[0], tuple)
                            else [y[0]] for y in img_fmt_types[fmt]], []))
                if self.allow_compressed:
                    exts.extend(sum([[u for u in y[-1]] if isinstance(y[-1],
                    tuple) else [y[-1]] for y in img_fmt_types[fmt]], []))
            else:
                raise AttributeError('Information has not been added for format'
                                     ' type {} yet. Supported formats include: '
                                     '{}'.format(fmt,
                                     ', '.join(img_fmt_types.keys())))
        return list(set(exts))

    def validate(self, object, value):
        """ Validates that a specified value is valid for this trait.
        """
        validated_value = super(ImageFile, self).validate(object, value)
        if validated_value and self.types:
            self._exts = self.grab_exts()
            if not any(validated_value.endswith(x) for x in self._exts):
                raise traitlets.TraitError(
                    "{} is not included in allowed types: {}".format(
                        validated_value, ', '.join(self._exts)))
        return validated_value


# dj NOTE: for now, everywhere where undefined was used I'm changing to None
# dj NOTE: had to add additinonal part for list, since traitlets gives `[]` as 
# dj NOTE: a default value even if I ask for None
# dj TOASK: is it ok, or should I create a special trait??
def isdefined(object):
    if type(object) is list:
        return object != []
    else:
        # dj NOTE!: if you use traitlets.Int() (and not traitlets.Int(default_value=None, allow_none=True))
        # dj NOTE!: a default value will be 0 and isdefined will return True even if you don't sepcify value
        return object is not None



def has_metadata(trait, metadata, value=None, recursive=True):
    '''
    Checks if a given trait has a metadata (and optionally if it is set to particular value)
    '''
    count = 0
    if hasattr(trait, "metadata") and metadata in list(trait.metadata.keys()) and (trait.metadata[metadata] == value or value is None):
        count += 1
    if recursive:
        # dj TODO: there is no inner_traits in traitlets!!
        if hasattr(trait, '_trait'):
            # dj TOASK: you can define a trait type for traitlets containers
            # dj TOASK: but it will be a trait type, not a list of traits
            inner_trait = trait._trait
            count += has_metadata(inner_trait, metadata, recursive)
        # dj TOASK: not sure about "handlers"? couldn't find it in traits library
        # dj: cant find also in base.py, are we planning to use it?
        #if hasattr(trait, 'handlers') and trait.handlers is not None:
        #    for handler in trait.handlers:
        #        count += has_metadata(handler, metadata, recursive)
    return count > 0


class MultiObject(traitlets.List):
    """ Abstract class - shared functionality of input and output MultiObject                                                              
    """
    # dj TOASK: is this default value ok?
    default_value = None
    allow_none = True

    def validate(self, object, value):
        # dj NOTE: for now isdefined([]) gives false, so OR part not needed
        # dj NOTE: not sure if this will stay or I'll have to change it
        # dj NOTE: might need to revert if I change isdefined for lists
        #if not isdefined(value) or \
        #        (isinstance(value, list) and len(value) == 0):
        if not isdefined(value):
            return None
        newvalue = value

        # dj TOASK: traitlets doesnt have inner_traits, not sure if changes are ok
        if not isinstance(value, list) \
             or (self._trait and
                isinstance(self._trait,
                           traitlets.List) and not
                isinstance(self._trait,
                           InputMultiPath) and
                isinstance(value, list) and
                value and not
                isinstance(value[0], list)):
            newvalue = [value]

        value = super(MultiObject, self).validate(object, newvalue)

        if len(value) > 0:
            return value

        # dj TOASK: when this error should be raised? can't think about an example
        self.error(object, value)


class OutputMultiObject(MultiObject):
    """ Implements a user friendly traits that accepts one or more
    paths to files or directories. This is the output version which
    return a single string whenever possible (when it was set to a
    single value or a list of length 1). Default value of this trait
    is _Undefined. It does not accept empty lists.

    XXX This should only be used as a final resort. We should stick to
    established Traits to the extent possible.

    XXX This needs to be vetted by somebody who understands traits

    >>> from nipype.interfaces.base import OutputMultiObject
    >>> class A(TraitedSpec):
    ...     foo = OutputMultiObject(File(exists=False))
    >>> a = A()
    >>> a.foo is None
    True

    >>> a.foo = '/software/temp/foo.txt'
    >>> a.foo # doctest: +ALLOW_UNICODE
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt']
    >>> a.foo # doctest: +ALLOW_UNICODE
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt', '/software/temp/goo.txt']
    >>> a.foo # doctest: +ALLOW_UNICODE
    ['/software/temp/foo.txt', '/software/temp/goo.txt']
    """

    # dj NOTE: method has different signature (hope this will work for other tests)
    def get(self, object, cls=None):
        value = super(OutputMultiObject, self).get(object, cls)
        if value is None:
            return None
        # dj NOTE: i think an empty list would be changed to None in validate anyway
        elif len(value) == 0:
            return None
        elif len(value) == 1:
            return value[0]
        else:
            return value


# dj TOASK: the same as MultiObject - should we keep both? somehthing should be added here?
class InputMultiObject(MultiObject):
    """ Implements a user friendly traits that accepts one or more
    paths to files or directories. This is the input version which
    always returns a list. Default value of this trait
    is _Undefined. It does not accept empty lists.

    XXX This should only be used as a final resort. We should stick to
    established Traits to the extent possible.

    XXX This needs to be vetted by somebody who understands traits

    >>> from nipype.interfaces.base import InputMultiObject
    >>> class A(TraitedSpec):
    ...     foo = InputMultiObject(File(exists=False))
    >>> a = A()
    >>> a.foo is None
    True

    >>> a.foo = '/software/temp/foo.txt'
    >>> a.foo # doctest: +ALLOW_UNICODE
    ['/software/temp/foo.txt']

    >>> a.foo = ['/software/temp/foo.txt']
    >>> a.foo # doctest: +ALLOW_UNICODE
    ['/software/temp/foo.txt']

    >>> a.foo = ['/software/temp/foo.txt', '/software/temp/goo.txt']
    >>> a.foo # doctest: +ALLOW_UNICODE 
    ['/software/temp/foo.txt', '/software/temp/goo.txt']

    """
    pass
