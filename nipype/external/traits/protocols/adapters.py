"""Basic Adapters and Adapter Operations"""

from __future__ import absolute_import

from .protocols import (NO_ADAPTER_NEEDED, DOES_NOT_SUPPORT, Adapter,
    minimumAdapter, composeAdapters, updateWithSimplestAdapter, StickyAdapter,
    AdaptationFailure, bindAdapter)


