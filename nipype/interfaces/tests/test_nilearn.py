# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import tempfile
import shutil

import numpy as np

from ...testing import utils

from .. import nilearn as iface
from ...pipeline import engine as pe

import pytest
import numpy.testing as npt

no_nilearn = True
try:
    __import__('nilearn')
    no_nilearn = False
except ImportError:
    pass


Filenames = {
    'in_file': 'fmri.nii',
    'label_files': 'labels.nii',
    '4d_label_file': '4dlabels.nii',
    'out_file': 'signals.tsv'
    }
Labels = ['CSF', 'GrayMatter', 'WhiteMatter']
Global_labels = ['GlobalSignal'] + Labels


@pytest.fixture()
def setup_files(request, tmpdir):
    orig_dir = os.getcwd()
    os.chdir(str(tmpdir))
    utils.save_toy_nii(FakeData.fake_fmri_data, Filenames['in_file'])
    utils.save_toy_nii(FakeData.fake_label_data, Filenames['label_files'])

    def change_directory():
        os.chdir(orig_dir)

    request.addfinalizer(change_directory)


@pytest.mark.skipif(no_nilearn, reason="the nilearn library is not available")
def test_signal_extract_no_shared(setup_files):
    # run
    iface.SignalExtraction(in_file=Filenames['in_file'],
                           label_files=Filenames['label_files'],
                           class_labels=Labels,
                           incl_shared_variance=False).run()
    # assert
    assert_expected_output(Labels, FakeData.base_wanted)


@pytest.mark.skipif(no_nilearn, reason="the nilearn library is not available")
def test_signal_extr_bad_label_list(setup_files):
    # run
    with pytest.raises(ValueError):
        iface.SignalExtraction(in_file=Filenames['in_file'],
                               label_files=Filenames['label_files'],
                               class_labels=['bad'],
                               incl_shared_variance=False).run()


@pytest.mark.skipif(no_nilearn, reason="the nilearn library is not available")
def test_signal_extr_equiv_4d_no_shared(setup_files):
    _test_4d_label(FakeData.base_wanted, FakeData.fake_equiv_4d_label_data,
                  incl_shared_variance=False)


@pytest.mark.skipif(no_nilearn, reason="the nilearn library is not available")
def test_signal_extr_4d_no_shared(setup_files):
    # set up & run & assert
    _test_4d_label(FakeData.fourd_wanted, FakeData.fake_4d_label_data, incl_shared_variance=False)


@pytest.mark.skipif(no_nilearn, reason="the nilearn library is not available")
def test_signal_extr_global_no_shared(setup_files):
    # set up
    wanted_global = [[-4./6], [-1./6], [3./6], [-1./6], [-7./6]]
    for i, vals in enumerate(FakeData.base_wanted):
        wanted_global[i].extend(vals)

    # run
    iface.SignalExtraction(in_file=Filenames['in_file'],
                           label_files=Filenames['label_files'],
                           class_labels=Labels,
                           include_global=True,
                           incl_shared_variance=False).run()

    # assert
    assert_expected_output(Global_labels, wanted_global)


@pytest.mark.skipif(no_nilearn, reason="the nilearn library is not available")
def test_signal_extr_4d_global_no_shared(setup_files):
    # set up
    wanted_global = [[3./8], [-3./8], [1./8], [-7./8], [-9./8]]
    for i, vals in enumerate(FakeData.fourd_wanted):
        wanted_global[i].extend(vals)

    # run & assert
    _test_4d_label(wanted_global, FakeData.fake_4d_label_data,
                   include_global=True, incl_shared_variance=False)


@pytest.mark.skipif(no_nilearn, reason="the nilearn library is not available")
def test_signal_extr_shared(setup_files):
    # set up
    wanted = []
    for vol in range(FakeData.fake_fmri_data.shape[3]):
        volume = FakeData.fake_fmri_data[:, :, :, vol].flatten()
        wanted_row = []
        for reg in range(FakeData.fake_4d_label_data.shape[3]):
            region = FakeData.fake_4d_label_data[:, :, :, reg].flatten()
            wanted_row.append((volume*region).sum()/(region*region).sum())

        wanted.append(wanted_row)
    # run & assert
    _test_4d_label(wanted, FakeData.fake_4d_label_data)


@pytest.mark.skipif(no_nilearn, reason="the nilearn library is not available")
def test_signal_extr_traits_valid(setup_files):
    ''' Test a node using the SignalExtraction interface.
    Unlike interface.run(), node.run() checks the traits
    '''
    # run
    node = pe.Node(iface.SignalExtraction(in_file=os.path.abspath(Filenames['in_file']),
                                          label_files=os.path.abspath(Filenames['label_files']),
                                          class_labels=Labels,
                                          incl_shared_variance=False),
                   name='SignalExtraction')
    node.run()

    # assert
    # just checking that it passes trait validations

def _test_4d_label(wanted, fake_labels, include_global=False, incl_shared_variance=True):
    # set up
    utils.save_toy_nii(fake_labels, Filenames['4d_label_file'])
    
    # run
    iface.SignalExtraction(in_file=Filenames['in_file'],
                           label_files=Filenames['4d_label_file'],
                           class_labels=Labels,
                           incl_shared_variance=incl_shared_variance,
                           include_global=include_global).run()

    wanted_labels = Global_labels if include_global else Labels

    # assert
    assert_expected_output(wanted_labels, wanted)

def assert_expected_output(labels, wanted):
    with open(Filenames['out_file'], 'r') as output:
        got = [line.split() for line in output]
        labels_got = got.pop(0) # remove header
        assert labels_got == labels
        assert len(got) == FakeData.fake_fmri_data.shape[3],'num rows and num volumes'
        # convert from string to float
        got = [[float(num) for num in row] for row in got]
        for i, time in enumerate(got):
            assert len(labels) == len(time)
            for j, segment in enumerate(time):
                npt.assert_almost_equal(segment, wanted[i][j], decimal=1)




class FakeData(object):
    fake_fmri_data = np.array([[[[2, -1, 4, -2, 3],
                                 [4, -2, -5, -1, 0]],

                                [[-2, 0, 1, 4, 4],
                                 [-5, 3, -3, 1, -5]]],


                               [[[2, -2, -1, -2, -5],
                                 [3, 0, 3, -5, -2]],

                                [[-4, -2, -2, 1, -2],
                                 [3, 1, 4, -3, -2]]]])

    fake_label_data = np.array([[[1, 0],
                                 [3, 1]],

                                [[2, 0],
                                 [1, 3]]])

    fake_equiv_4d_label_data = np.array([[[[1., 0., 0.],
                                           [0., 0., 0.]],
                                          [[0., 0., 1.],
                                           [1., 0., 0.]]],
                                         [[[0., 1., 0.],
                                           [0., 0., 0.]],
                                          [[1., 0., 0.],
                                           [0., 0., 1.]]]])

    base_wanted = [[-2.33333, 2, .5],
                   [0, -2, .5],
                   [-.3333333, -1, 2.5],
                   [0, -2, .5],
                   [-1.3333333, -5, 1]]

    fake_4d_label_data = np.array([[[[0.2, 0.3, 0.5],
                                     [0.1, 0.1, 0.8]],

                                    [[0.1, 0.3, 0.6],
                                     [0.3, 0.4, 0.3]]],

                                   [[[0.2, 0.2, 0.6],
                                     [0., 0.3, 0.7]],

                                    [[0.3, 0.3, 0.4],
                                     [0.3, 0.4, 0.3]]]])


    fourd_wanted = [[-5.0652173913, -5.44565217391, 5.50543478261],
                    [-7.02173913043, 11.1847826087, -4.33152173913],
                    [-19.0869565217, 21.2391304348, -4.57608695652],
                    [5.19565217391, -3.66304347826, -1.51630434783],
                    [-12.0, 3., 0.5]]
