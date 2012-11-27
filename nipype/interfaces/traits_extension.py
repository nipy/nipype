# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""This module contains Trait classes that we've pulled from the
traits source and fixed due to various bugs.  File and Directory are
redefined as the release version had dependencies on TraitsUI, which
we do not want Nipype to depend on.  At least not yet.
"""

from ..external import traitlets as traits
from ..external.traitlets import TraitError
from ..external.traitlets import Undefined
from ..external.traitlets import Dict as TraitDictObject
from ..external.traitlets import List as TraitListObject
from ..external.traitlets import

def isdefined(object):
    return not isinstance(object, traits.Undefined)

def has_metadata(trait, metadata, value=None, recursive=True):
    '''
    Checks if a given trait has a metadata (and optionally if it is set to particular value)
    '''
    count = 0
    if hasattr(trait, "_metadata") and metadata in trait._metadata.keys() and (trait._metadata[metadata] == value or value==None):
        count += 1
    if recursive:
        if hasattr(trait, 'inner_traits'):
            for inner_trait in trait.inner_traits():
                count += has_metadata(inner_trait.trait_type, metadata, recursive)
        if hasattr(trait, 'handlers') and trait.handlers != None:
            for handler in trait.handlers:
                count += has_metadata(handler, metadata, recursive)

    return count > 0



