# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Tests for the engine module
"""
import numpy as np
import scipy.sparse as ssp
import re

import mock

from nipype.testing import (assert_raises, assert_equal, assert_true,
                            assert_false, skipif, assert_regexp_matches)
import nipype.pipeline.plugins.base as pb

def test_scipy_sparse():
    foo = ssp.lil_matrix(np.eye(3, k=1))
    goo = foo.getrowview(0)
    goo[goo.nonzero()] = 0
    yield assert_equal, foo[0, 1], 0

def test_report_crash():
    with mock.patch('pickle.dump', mock.MagicMock()) as mock_pickle_dump:
        with mock.patch('nipype.pipeline.plugins.base.format_exception', mock.MagicMock()): # see iss 1517
            mock_pickle_dump.return_value = True
            mock_node = mock.MagicMock(name='mock_node')
            mock_node._id = 'an_id'
            mock_node.config = {
                'execution' : {
                    'crashdump_dir' : '.'
                }
            }

            actual_crashfile = pb.report_crash(mock_node)

            expected_crashfile = re.compile('.*/crash-.*-an_id-[0-9a-f\-]*.pklz')

            yield assert_regexp_matches, actual_crashfile, expected_crashfile
            yield assert_true, mock_pickle_dump.call_count == 1

'''
Can use the following code to test that a mapnode crash continues successfully
Need to put this into a nose-test with a timeout

import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe

wf = pe.Workflow(name='test')

def func(arg1):
    if arg1 == 2:
        raise Exception('arg cannot be ' + str(arg1))
    return arg1

funkynode = pe.MapNode(niu.Function(function=func, input_names=['arg1'], output_names=['out']),
                       iterfield=['arg1'],
                       name = 'functor')
funkynode.inputs.arg1 = [1,2]

wf.add_nodes([funkynode])
wf.base_dir = '/tmp'

wf.run(plugin='MultiProc')
'''
