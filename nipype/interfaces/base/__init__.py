# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Nipype base interfaces
----------------------

This module defines the API of all nipype interfaces.

"""
from .core import (
    BaseInterface, SimpleInterface, CommandLine, StdOutCommandLine,
    MpiCommandLine, SEMLikeCommandLine, PackageInfo
)

from .specs import (
    BaseTraitedSpec, BaseInterfaceInputSpec, CommandLineInputSpec,
)

from .traits_extension import (
    traits, Undefined, TraitDictObject, TraitListObject, TraitError, isdefined,
    File, Directory, Str, DictStrStr, has_metadata, ImageFile,
    MultiPath, OutputMultiPath, InputMultiPath)

from .support import load_template
