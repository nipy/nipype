# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from future import standard_library
standard_library.install_aliases()

from ..nipype2boutiques import generate_boutiques_descriptor


def test_generate():
    generate_boutiques_descriptor(module='nipype.interfaces.ants.registration',
                                  interface_name='ANTS',
                                  ignored_template_inputs=(),
                                  docker_image=None,
                                  docker_index=None,
                                  verbose=False,
                                  ignore_template_numbers=False)
