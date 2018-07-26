# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Nipype base interfaces
----------------------

This module defines the API of all nipype interfaces.

"""
from .core import (Interface, BaseInterface, SimpleInterface, CommandLine,
                   StdOutCommandLine, MpiCommandLine, SEMLikeCommandLine,
                   LibraryBaseInterface, PackageInfo)

from .specs import (BaseTraitedSpec, TraitedSpec, DynamicTraitedSpec,
                    BaseInterfaceInputSpec, CommandLineInputSpec,
                    StdOutCommandLineInputSpec)

from .traits_extension import (
    traits, Undefined, TraitDictObject, TraitListObject, TraitError, isdefined,
    File, Directory, Str, DictStrStr, has_metadata, ImageFile,
    OutputMultiObject, InputMultiObject,
    OutputMultiPath, InputMultiPath)

from .support import (Bunch, InterfaceResult, load_template,
                      NipypeInterfaceError)
