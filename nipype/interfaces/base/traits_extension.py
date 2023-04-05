# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Traits extension
................

This module contains Trait classes that we've pulled from the
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
from collections.abc import Sequence

# perform all external trait imports here
from traits import __version__ as traits_version
import traits.api as traits
from traits.api import TraitType, Unicode
from traits.trait_base import _Undefined

try:
    # Moved in traits 6.0
    from traits.trait_type import NoDefaultSpecified
except ImportError:
    # Pre-6.0
    from traits.trait_handlers import NoDefaultSpecified

from pathlib import Path
from ...utils.filemanip import path_resolve

if traits_version < "3.7.0":
    raise ImportError("Traits version 3.7.0 or higher must be installed")

IMG_FORMATS = {
    "afni": (".HEAD", ".BRIK"),
    "cifti2": (".nii", ".nii.gz"),
    "dicom": (".dcm", ".IMA", ".tar", ".tar.gz"),
    "gifti": (".gii", ".gii.gz"),
    "mgh": (".mgh", ".mgz", ".mgh.gz"),
    "nifti1": (".nii", ".nii.gz", ".hdr", ".img", ".img.gz"),
    "nifti2": (".nii", ".nii.gz"),
    "nrrd": (".nrrd", ".nhdr"),
}
IMG_ZIP_FMT = set([".nii.gz", "tar.gz", ".gii.gz", ".mgz", ".mgh.gz", "img.gz"])

"""
The functions that pop-up the Traits GUIs, edit_traits and
configure_traits, were failing because all of our inputs default to
Undefined deep and down in traits/ui/wx/list_editor.py it checks for
the len() of the elements of the list.  The _Undefined class in traits
does not define the __len__ method and would error.  I tried defining
our own Undefined and even sublassing Undefined, but both of those
failed with a TraitError in our initializer when we assign the
Undefined to the inputs because of an incompatible type:

TraitError: The 'vertical_gradient' trait of a BetInputSpec instance must be \
a float, but a value of <undefined> <class 'nipype.interfaces.traits._Undefined'> was specified.

So... in order to keep the same type but add the missing method, I
monkey patched.
"""


def _length(self):
    return 0


##########################################################################
# Apply monkeypatch here
_Undefined.__len__ = _length
##########################################################################

Undefined = _Undefined()


class Str(Unicode):
    """Replaces the default traits.Str based in bytes."""


# Monkeypatch Str and DictStrStr for Python 2 compatibility
traits.Str = Str
DictStrStr = traits.Dict((bytes, str), (bytes, str))
traits.DictStrStr = DictStrStr


class BasePath(TraitType):
    """Defines a trait whose value must be a valid filesystem path."""

    # A description of the type of value this trait accepts:
    exists = False
    resolve = False
    _is_file = False
    _is_dir = False

    @property
    def info_text(self):
        """Create the trait's general description."""
        info_text = "a pathlike object or string"
        if any((self.exists, self._is_file, self._is_dir)):
            info_text += " representing a"
            if self.exists:
                info_text += "n existing"
            if self._is_file:
                info_text += " file"
            elif self._is_dir:
                info_text += " directory"
            else:
                info_text += " file or directory"
        return info_text

    def __init__(self, value=Undefined, exists=False, resolve=False, **metadata):
        """Create a BasePath trait."""
        self.exists = exists
        self.resolve = resolve
        super(BasePath, self).__init__(value, **metadata)

    def validate(self, objekt, name, value, return_pathlike=False):
        """Validate a value change."""
        try:
            value = Path(value)  # Use pathlib's validation
        except Exception:
            self.error(objekt, name, str(value))

        if self.exists:
            if not value.exists():
                self.error(objekt, name, str(value))

            if self._is_file and not value.is_file():
                self.error(objekt, name, str(value))

            if self._is_dir and not value.is_dir():
                self.error(objekt, name, str(value))

        if self.resolve:
            value = path_resolve(value, strict=self.exists)

        if not return_pathlike:
            value = str(value)

        return value


class Directory(BasePath):
    """
    Defines a trait whose value must be a directory path.

    >>> from nipype.interfaces.base import Directory, TraitedSpec, TraitError
    >>> class A(TraitedSpec):
    ...     foo = Directory(exists=False)
    >>> a = A()
    >>> a.foo
    <undefined>

    >>> a.foo = '/some/made/out/path'
    >>> a.foo
    '/some/made/out/path'

    >>> class A(TraitedSpec):
    ...     foo = Directory(exists=False, resolve=True)
    >>> a = A(foo='relative_dir')
    >>> a.foo  # doctest: +ELLIPSIS
    '.../relative_dir'

    >>> class A(TraitedSpec):
    ...     foo = Directory(exists=True, resolve=True)
    >>> a = A()
    >>> a.foo = 'relative_dir'  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    TraitError:

    >>> from os import mkdir
    >>> mkdir('relative_dir')
    >>> a.foo = 'relative_dir'
    >>> a.foo  # doctest: +ELLIPSIS
    '.../relative_dir'

    >>> class A(TraitedSpec):
    ...     foo = Directory(exists=True, resolve=False)
    >>> a = A(foo='relative_dir')
    >>> a.foo
    'relative_dir'

    >>> class A(TraitedSpec):
    ...     foo = Directory('tmpdir')
    >>> a = A()
    >>> a.foo  # doctest: +ELLIPSIS
    <undefined>

    >>> class A(TraitedSpec):
    ...     foo = Directory('tmpdir', usedefault=True)
    >>> a = A()
    >>> a.foo  # doctest: +ELLIPSIS
    'tmpdir'

    """

    _is_dir = True


class File(BasePath):
    """
    Defines a trait whose value must be a file path.

    >>> from nipype.interfaces.base import File, TraitedSpec, TraitError
    >>> class A(TraitedSpec):
    ...     foo = File()
    >>> a = A()
    >>> a.foo
    <undefined>

    >>> a.foo = '/some/made/out/path/to/file'
    >>> a.foo
    '/some/made/out/path/to/file'

    >>> class A(TraitedSpec):
    ...     foo = File(exists=False, resolve=True)
    >>> a = A(foo='idontexist.txt')
    >>> a.foo  # doctest: +ELLIPSIS
    '.../idontexist.txt'

    >>> class A(TraitedSpec):
    ...     foo = File(exists=True, resolve=True)
    >>> a = A()
    >>> a.foo = 'idontexist.txt'  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    TraitError:

    >>> open('idoexist.txt', 'w').close()
    >>> a.foo = 'idoexist.txt'
    >>> a.foo  # doctest: +ELLIPSIS
    '.../idoexist.txt'

    >>> class A(TraitedSpec):
    ...     foo = File('idoexist.txt')
    >>> a = A()
    >>> a.foo
    <undefined>

    >>> class A(TraitedSpec):
    ...     foo = File('idoexist.txt', usedefault=True)
    >>> a = A()
    >>> a.foo
    'idoexist.txt'

    >>> class A(TraitedSpec):
    ...     foo = File(exists=True, resolve=True, extensions=['.txt', 'txt.gz'])
    >>> a = A()
    >>> a.foo = 'idoexist.badtxt'  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    TraitError:

    >>> a.foo = 'idoexist.txt'
    >>> a.foo  # doctest: +ELLIPSIS
    '.../idoexist.txt'

    >>> class A(TraitedSpec):
    ...     foo = File(extensions=['.nii', '.nii.gz'])
    >>> a = A()
    >>> a.foo = 'badext.txt'  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    TraitError:

    >>> class A(TraitedSpec):
    ...     foo = File(extensions=['.nii', '.nii.gz'])
    >>> a = A()
    >>> a.foo = 'goodext.nii'
    >>> a.foo
    'goodext.nii'

    >>> a = A()
    >>> a.foo = 'idontexist.000.nii'
    >>> a.foo  # doctest: +ELLIPSIS
    'idontexist.000.nii'

    >>> a = A()
    >>> a.foo = 'idontexist.000.nii.gz'
    >>> a.foo  # doctest: +ELLIPSIS
    'idontexist.000.nii.gz'

    """

    _is_file = True
    _exts = None

    def __init__(
        self,
        value=NoDefaultSpecified,
        exists=False,
        resolve=False,
        allow_compressed=True,
        extensions=None,
        **metadata
    ):
        """Create a File trait."""
        if extensions is not None:
            if isinstance(extensions, (bytes, str)):
                extensions = [extensions]

            if allow_compressed is False:
                extensions = list(set(extensions) - IMG_ZIP_FMT)

            self._exts = sorted(
                set(
                    [
                        ".%s" % ext if not ext.startswith(".") else ext
                        for ext in extensions
                    ]
                )
            )

        super(File, self).__init__(
            value=value,
            exists=exists,
            resolve=resolve,
            extensions=self._exts,
            **metadata
        )

    def validate(self, objekt, name, value, return_pathlike=False):
        """Validate a value change."""
        value = super(File, self).validate(objekt, name, value, return_pathlike=True)
        if self._exts:
            fname = value.name
            if not any((fname.endswith(e) for e in self._exts)):
                self.error(objekt, name, str(value))

        if not return_pathlike:
            value = str(value)

        return value


class ImageFile(File):
    """Defines a trait whose value must be a known neuroimaging file."""

    def __init__(
        self,
        value=NoDefaultSpecified,
        exists=False,
        resolve=False,
        types=None,
        **metadata
    ):
        """Create an ImageFile trait."""
        extensions = None
        if types is not None:
            if isinstance(types, (bytes, str)):
                types = [types]

            if set(types) - set(IMG_FORMATS.keys()):
                invalid = set(types) - set(IMG_FORMATS.keys())
                raise ValueError(
                    """\
Unknown value(s) %s for metadata type of an ImageFile input.\
"""
                    % ", ".join(['"%s"' % t for t in invalid])
                )
            extensions = [ext for t in types for ext in IMG_FORMATS[t]]

        super(ImageFile, self).__init__(
            value=value,
            exists=exists,
            extensions=extensions,
            resolve=resolve,
            **metadata
        )


def isdefined(objekt):
    return not isinstance(objekt, _Undefined)


def has_metadata(trait, metadata, value=None, recursive=True):
    """
    Checks if a given trait has a metadata (and optionally if it is set to particular value)
    """
    count = 0
    if (
        hasattr(trait, "_metadata")
        and metadata in list(trait._metadata.keys())
        and (trait._metadata[metadata] == value or value is None)
    ):
        count += 1
    if recursive:
        if hasattr(trait, "inner_traits"):
            for inner_trait in trait.inner_traits():
                count += has_metadata(inner_trait.trait_type, metadata, recursive)
        if hasattr(trait, "handlers") and trait.handlers is not None:
            for handler in trait.handlers:
                count += has_metadata(handler, metadata, recursive)

    return count > 0


class MultiObject(traits.List):
    """Abstract class - shared functionality of input and output MultiObject"""

    def validate(self, objekt, name, value):
        # want to treat range and other sequences (except str) as list
        if not isinstance(value, (str, bytes)) and isinstance(value, Sequence):
            value = list(value)

        if not isdefined(value) or (isinstance(value, list) and len(value) == 0):
            return Undefined

        newvalue = value

        inner_trait = self.inner_traits()[0]
        if not isinstance(value, list) or (
            isinstance(inner_trait.trait_type, traits.List)
            and not isinstance(inner_trait.trait_type, InputMultiObject)
            and not isinstance(value[0], list)
        ):
            newvalue = [value]
        value = super(MultiObject, self).validate(objekt, name, newvalue)

        if value:
            return value

        self.error(objekt, name, value)


class OutputMultiObject(MultiObject):
    """Implements a user friendly traits that accepts one or more
    paths to files or directories. This is the output version which
    return a single string whenever possible (when it was set to a
    single value or a list of length 1). Default value of this trait
    is _Undefined. It does not accept empty lists.

    XXX This should only be used as a final resort. We should stick to
    established Traits to the extent possible.

    XXX This needs to be vetted by somebody who understands traits

    >>> from nipype.interfaces.base import OutputMultiObject, TraitedSpec
    >>> class A(TraitedSpec):
    ...     foo = OutputMultiObject(File(exists=False))
    >>> a = A()
    >>> a.foo
    <undefined>

    >>> a.foo = '/software/temp/foo.txt'
    >>> a.foo
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt']
    >>> a.foo
    '/software/temp/foo.txt'

    >>> a.foo = ['/software/temp/foo.txt', '/software/temp/goo.txt']
    >>> a.foo
    ['/software/temp/foo.txt', '/software/temp/goo.txt']

    """

    def get(self, objekt, name):
        value = self.get_value(objekt, name)
        if len(value) == 0:
            return Undefined
        elif len(value) == 1:
            return value[0]
        else:
            return value

    def set(self, objekt, name, value):
        self.set_value(objekt, name, value)


class InputMultiObject(MultiObject):
    """Implements a user friendly traits that accepts one or more
    paths to files or directories. This is the input version which
    always returns a list. Default value of this trait
    is _Undefined. It does not accept empty lists.

    XXX This should only be used as a final resort. We should stick to
    established Traits to the extent possible.

    XXX This needs to be vetted by somebody who understands traits

    >>> from nipype.interfaces.base import InputMultiObject, TraitedSpec
    >>> class A(TraitedSpec):
    ...     foo = InputMultiObject(File(exists=False))
    >>> a = A()
    >>> a.foo
    <undefined>

    >>> a.foo = '/software/temp/foo.txt'
    >>> a.foo
    ['/software/temp/foo.txt']

    >>> a.foo = ['/software/temp/foo.txt']
    >>> a.foo
    ['/software/temp/foo.txt']

    >>> a.foo = ['/software/temp/foo.txt', '/software/temp/goo.txt']
    >>> a.foo
    ['/software/temp/foo.txt', '/software/temp/goo.txt']

    """

    pass


InputMultiPath = InputMultiObject
OutputMultiPath = OutputMultiObject


def _rebase_path(value, cwd):
    if isinstance(value, list):
        return [_rebase_path(v, cwd) for v in value]

    try:
        value = Path(value)
    except TypeError:
        pass
    else:
        try:
            value = value.relative_to(cwd)
        except ValueError:
            pass
    return value


def _resolve_path(value, cwd):
    if isinstance(value, list):
        return [_resolve_path(v, cwd) for v in value]

    try:
        value = Path(value)
    except TypeError:
        pass
    else:
        if not value.is_absolute():
            value = Path(cwd).absolute() / value
    return value


def _recurse_on_path_traits(func, thistrait, value, cwd):
    """Run func recursively on BasePath-derived traits."""
    if thistrait.is_trait_type(BasePath):
        value = func(value, cwd)
    elif thistrait.is_trait_type(traits.List):
        (innertrait,) = thistrait.inner_traits
        if not isinstance(value, (list, tuple)):
            return _recurse_on_path_traits(func, innertrait, value, cwd)

        value = [_recurse_on_path_traits(func, innertrait, v, cwd) for v in value]
    elif isinstance(value, dict) and thistrait.is_trait_type(traits.Dict):
        _, innertrait = thistrait.inner_traits
        value = {
            k: _recurse_on_path_traits(func, innertrait, v, cwd)
            for k, v in value.items()
        }
    elif isinstance(value, tuple) and thistrait.is_trait_type(traits.Tuple):
        value = tuple(
            [
                _recurse_on_path_traits(func, subtrait, v, cwd)
                for subtrait, v in zip(thistrait.handler.types, value)
            ]
        )
    elif thistrait.is_trait_type(traits.TraitCompound):
        is_str = [
            isinstance(f, (traits.String, traits.BaseStr, traits.BaseBytes, Str))
            for f in thistrait.handler.handlers
        ]
        if (
            any(is_str)
            and isinstance(value, (bytes, str))
            and not value.startswith("/")
        ):
            return value

        for subtrait in thistrait.handler.handlers:
            try:
                sb_instance = subtrait()
            except TypeError:
                return value
            else:
                value = _recurse_on_path_traits(func, sb_instance, value, cwd)

    return value


def rebase_path_traits(thistrait, value, cwd):
    """Rebase a BasePath-derived trait given an interface spec."""
    return _recurse_on_path_traits(_rebase_path, thistrait, value, cwd)


def resolve_path_traits(thistrait, value, cwd):
    """Resolve a BasePath-derived trait given an interface spec."""
    return _recurse_on_path_traits(_resolve_path, thistrait, value, cwd)
