"""Trivial Interfaces and Adaptation from PyProtocols.

This package is a direct copy of a subset of the files from Phillip J. Eby's
PyProtocols package. They are only included here to help remove dependencies
on external packages from the Traits package. The only significant change is
the inclusion of a setup.py file.
"""

from __future__ import absolute_import

from .protocols import (adapt, declareAdapterForType, declareAdapterForProtocol,
    declareAdapterForObject, advise, declareImplementation, declareAdapter,
    adviseObject, InterfaceClass, Protocol, addClassAdvisor, AdaptationFailure)

