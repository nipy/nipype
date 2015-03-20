# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os.path as op


def get_flirt_schedule(name):
    if name == 'ecc':
        return op.abspath(op.join(op.dirname(__file__),
                          'ecc.sch'))
    elif name == 'hmc':
        return op.abspath(op.join(op.dirname(__file__),
                          'hmc.sch'))
    else:
        raise RuntimeError('Requested file does not exist.')
