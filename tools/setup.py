#!/usr/bin/env python

from __future__ import unicode_literals
from distutils.core import setup

setup(name='Nipype Tools',
      version='0.1',
      description='Utilities used in nipype development',
      author='Nipype Developers',
      author_email='nipy-devel@neuroimaging.scipy.org',
      url='http://nipy.sourceforge.net',
      scripts=['./nipype_nightly.py', './report_coverage.py']
     )

