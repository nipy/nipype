#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: oesteban
# @Date:   2014-09-05 11:23:48
# @Last Modified by:   oesteban
# @Last Modified time: 2014-09-05 11:33:27
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
