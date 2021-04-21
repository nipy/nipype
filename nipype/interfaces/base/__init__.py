# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Nipype base interfaces
----------------------

This module defines the API of all nipype interfaces.

"""
from traits.trait_handlers import TraitDictObject, TraitListObject
from traits.trait_errors import TraitError

from .core import (
    Interface,
    BaseInterface,
    SimpleInterface,
    CommandLine,
    StdOutCommandLine,
    MpiCommandLine,
    SEMLikeCommandLine,
    LibraryBaseInterface,
    PackageInfo,
)

from .specs import (
    BaseTraitedSpec,
    TraitedSpec,
    DynamicTraitedSpec,
    BaseInterfaceInputSpec,
    CommandLineInputSpec,
    StdOutCommandLineInputSpec,
)

from .traits_extension import (
    traits,
    Undefined,
    isdefined,
    has_metadata,
    File,
    ImageFile,
    Directory,
    Str,
    DictStrStr,
    OutputMultiObject,
    InputMultiObject,
    OutputMultiPath,
    InputMultiPath,
)

from .support import Bunch, InterfaceResult, NipypeInterfaceError
