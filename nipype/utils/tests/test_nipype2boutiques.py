# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from future import standard_library
standard_library.install_aliases()

from ..nipype2boutiques import generate_boutiques_descriptor


def test_generate():
    generate_boutiques_descriptor(module='nipype.interfaces.ants.registration',
                                  interface_name='ANTS',
                                  container_image=None,
                                  container_index=None,
                                  container_type=None,
                                  verbose=False,
                                  save=False)
