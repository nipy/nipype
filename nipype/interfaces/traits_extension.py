# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""This module contains Trait classes that we've pulled from the
traits source and fixed due to various bugs.  File and Directory are
redefined as the release version had dependencies on TraitsUI, which
we do not want Nipype to depend on.  At least not yet.

Undefined class was missing the __len__ operator, causing edit_traits
and configure_traits to fail on List objects.  Even though we don't
require TraitsUI, this bug was the only thing preventing us from
popping up GUIs which users like.

These bugs have been in Traits v3.3.0 and v3.2.1.  We have reported
all of these bugs and they've been fixed in enthought svn repository
(usually by Robert Kern).

"""
from __future__ import print_function, division, unicode_literals, absolute_import

from builtins import filter, object, str, bytes
import os

# perform all external trait imports here
import traits
if traits.__version__ < '3.7.0':
    raise ImportError('Traits version 3.7.0 or higher must be installed')
import traits.api as traits
from traits.trait_handlers import TraitDictObject, TraitListObject
from traits.trait_errors import TraitError
from traits.trait_base import _Undefined, class_of

from traits.api import BaseUnicode
from traits.api import Unicode

DictStrStr = traits.Dict((bytes, str), (bytes, str))
Str = Unicode

class BaseFile(BaseUnicode):
    """ Defines a trait whose value must be the name of a file.
    """

    # A description of the type of value this trait accepts:
    info_text = 'a file name'

    def __init__(self, value='', filter=None, auto_set=False,
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
        *value* or ''
        """
        self.filter = filter
        self.auto_set = auto_set
        self.entries = entries
        self.exists = exists

        if exists:
            self.info_text = 'an existing file name'

        super(BaseFile, self).__init__(value, **metadata)

    def validate(self, object, name, value):
        """ Validates that a specified value is valid for this trait.

            Note: The 'fast validator' version performs this check in C.
        """
        validated_value = super(BaseFile, self).validate(object, name, value)
        if not self.exists:
            return validated_value
        elif os.path.isfile(value):
            return validated_value
        else:
            raise TraitError(
                args='The trait \'{}\' of {} instance is {}, but the path '
                     ' \'{}\' does not exist.'.format(name, class_of(object),
                                                      self.info_text, value))

        self.error(object, name, value)


class File (BaseFile):
    """
    Defines a trait whose value must be the name of a file.
    Disables the default C-level fast validator.
    """

    def __init__(self, value='', filter=None, auto_set=False,
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
        *value* or ''
        """
        # if not exists:
        #     # Define the C-level fast validator to use:
        #     fast_validate = (11, str)

        super(File, self).__init__(value, filter, auto_set, entries, exists,
                                   **metadata)

# -------------------------------------------------------------------------------
#  'BaseDirectory' and 'Directory' traits:
# -------------------------------------------------------------------------------


class BaseDirectory (BaseUnicode):
    """
    Defines a trait whose value must be the name of a directory.
    """

    # A description of the type of value this trait accepts:
    info_text = 'a directory name'

    def __init__(self, value='', auto_set=False, entries=0,
                 exists=False, **metadata):
        """ Creates a BaseDirectory trait.

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
        *value* or ''
        """
        self.entries = entries
        self.auto_set = auto_set
        self.exists = exists

        if exists:
            self.info_text = 'an existing directory name'

        super(BaseDirectory, self).__init__(value, **metadata)

    def validate(self, object, name, value):
        """ Validates that a specified value is valid for this trait.

            Note: The 'fast validator' version performs this check in C.
        """
        if isinstance(value, (str, bytes)):
            if not self.exists:
                return value
            if os.path.isdir(value):
                return value
            else:
                raise TraitError(
                    args='The trait \'{}\' of {} instance is {}, but the path '
                         ' \'{}\' does not exist.'.format(name,
                                    class_of(object), self.info_text, value))

        self.error(object, name, value)


class Directory (BaseDirectory):
    """
    Defines a trait whose value must be the name of a directory.
    Disables the default C-level fast validator.
    """

    def __init__(self, value='', auto_set=False, entries=0,
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
        *value* or ''
        """
        # Define the C-level fast validator to use if the directory existence
        # test is not required:
        # if not exists:
        #     self.fast_validate = (11, str)

        super(Directory, self).__init__(value, auto_set, entries, exists,
                                        **metadata)

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

    def validate(self, object, name, value):
        """ Validates that a specified value is valid for this trait.
        """
        validated_value = super(ImageFile, self).validate(object, name, value)
        if validated_value and self.types:
            self._exts = self.grab_exts()
            if not any(validated_value.endswith(x) for x in self._exts):
                raise TraitError(
                    args="{} is not included in allowed types: {}".format(
                        validated_value, ', '.join(self._exts)))
        return validated_value

"""
The functions that pop-up the Traits GUIs, edit_traits and
configure_traits, were failing because all of our inputs default to
Undefined deep and down in traits/ui/wx/list_editor.py it checks for
the len() of the elements of the list.  The _Undefined class in traits
does not define the __len__ method and would error.  I tried defining
our own Undefined and even sublassing Undefined, but both of those
failed with a TraitError in our initializer when we assign the
Undefined to the inputs because of an incompatible type:

TraitError: The 'vertical_gradient' trait of a BetInputSpec instance must be a float, but a value of <undefined> <class 'nipype.interfaces.traits._Undefined'> was specified.

So... in order to keep the same type but add the missing method, I
monkey patched.
"""


def length(self):
    return 0

##########################################################################
# Apply monkeypatch here
_Undefined.__len__ = length
##########################################################################

Undefined = _Undefined()


def isdefined(object):
    return not isinstance(object, _Undefined)


def has_metadata(trait, metadata, value=None, recursive=True):
    '''
    Checks if a given trait has a metadata (and optionally if it is set to particular value)
    '''
    count = 0
    if hasattr(trait, "_metadata") and metadata in list(trait._metadata.keys()) and (trait._metadata[metadata] == value or value is None):
        count += 1
    if recursive:
        if hasattr(trait, 'inner_traits'):
            for inner_trait in trait.inner_traits():
                count += has_metadata(inner_trait.trait_type, metadata, recursive)
        if hasattr(trait, 'handlers') and trait.handlers is not None:
            for handler in trait.handlers:
                count += has_metadata(handler, metadata, recursive)

    return count > 0
