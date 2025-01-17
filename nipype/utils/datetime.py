# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Utilities for dates and time
"""

from datetime import datetime as dt
import sys

if sys.version_info >= (3, 11):
    from datetime import UTC

    def utcnow():
        """Adapter since 3.12 prior utcnow is deprecated,
        but not EOLed 3.8 does not have datetime.UTC"""
        return dt.now(UTC)

else:
    utcnow = dt.utcnow
