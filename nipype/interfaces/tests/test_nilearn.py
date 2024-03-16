# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import numpy as np

from ...testing import utils

from .. import nilearn as iface
from ...pipeline import engine as pe

import pytest
import numpy.testing as npt

no_nilearn = True
try:
    __import__("nilearn")
    no_nilearn = False
except ImportError:
    pass


@pytest.mark.skipif(no_nilearn, reason="the nilearn library is not available")
class TestSignalExtraction:
    filenames = {
        "in_file": "fmri.nii",
        "label_files": "labels.nii",
        "4d_label_file": "4dlabels.nii",
        "out_file": "signals.tsv",
    }
    labels = ["CSF", "GrayMatter", "WhiteMatter"]
    global_labels = ["GlobalSignal"] + labels

    @pytest.fixture(autouse=True, scope="class")
    def setup_class(self, tmpdir_factory):
        tempdir = tmpdir_factory.mktemp("test")
        self.orig_dir = tempdir.chdir()
        utils.save_toy_nii(self.fake_fmri_data, self.filenames["in_file"])
        utils.save_toy_nii(self.fake_label_data, self.filenames["label_files"])

    def test_signal_extract_no_shared(self):
        # run
        iface.SignalExtraction(
            in_file=self.filenames["in_file"],
            label_files=self.filenames["label_files"],
            class_labels=self.labels,
            incl_shared_variance=False,
        ).run()
        # assert
        self.assert_expected_output(self.labels, self.base_wanted)

    def test_signal_extr_bad_label_list(self):
        # run
        with pytest.raises(ValueError):
            iface.SignalExtraction(
                in_file=self.filenames["in_file"],
                label_files=self.filenames["label_files"],
                class_labels=["bad"],
                incl_shared_variance=False,
            ).run()

    def test_signal_extr_equiv_4d_no_shared(self):
        self._test_4d_label(
            self.base_wanted, self.fake_equiv_4d_label_data, incl_shared_variance=False
        )

    def test_signal_extr_4d_no_shared(self):
        # set up & run & assert
        self._test_4d_label(
            self.fourd_wanted, self.fake_4d_label_data, incl_shared_variance=False
        )

    def test_signal_extr_global_no_shared(self):
        # set up
        wanted_global = [[-4.0 / 6], [-1.0 / 6], [3.0 / 6], [-1.0 / 6], [-7.0 / 6]]
        for i, vals in enumerate(self.base_wanted):
            wanted_global[i].extend(vals)

        # run
        iface.SignalExtraction(
            in_file=self.filenames["in_file"],
            label_files=self.filenames["label_files"],
            class_labels=self.labels,
            include_global=True,
            incl_shared_variance=False,
        ).run()

        # assert
        self.assert_expected_output(self.global_labels, wanted_global)

    def test_signal_extr_4d_global_no_shared(self):
        # set up
        wanted_global = [[3.0 / 8], [-3.0 / 8], [1.0 / 8], [-7.0 / 8], [-9.0 / 8]]
        for i, vals in enumerate(self.fourd_wanted):
            wanted_global[i].extend(vals)

        # run & assert
        self._test_4d_label(
            wanted_global,
            self.fake_4d_label_data,
            include_global=True,
            incl_shared_variance=False,
        )

    def test_signal_extr_shared(self):
        # set up
        wanted = []
        for vol in range(self.fake_fmri_data.shape[3]):
            volume = self.fake_fmri_data[:, :, :, vol].flatten()
            wanted_row = []
            for reg in range(self.fake_4d_label_data.shape[3]):
                region = self.fake_4d_label_data[:, :, :, reg].flatten()
                wanted_row.append((volume * region).sum() / (region * region).sum())

            wanted.append(wanted_row)
        # run & assert
        self._test_4d_label(wanted, self.fake_4d_label_data)

    def test_signal_extr_traits_valid(self):
        """Test a node using the SignalExtraction interface.
        Unlike interface.run(), node.run() checks the traits
        """
        # run
        node = pe.Node(
            iface.SignalExtraction(
                in_file=os.path.abspath(self.filenames["in_file"]),
                label_files=os.path.abspath(self.filenames["label_files"]),
                class_labels=self.labels,
                incl_shared_variance=False,
            ),
            name="SignalExtraction",
        )
        node.run()

        # assert
        # just checking that it passes trait validations

    def _test_4d_label(
        self, wanted, fake_labels, include_global=False, incl_shared_variance=True
    ):
        # set up
        utils.save_toy_nii(fake_labels, self.filenames["4d_label_file"])

        # run
        iface.SignalExtraction(
            in_file=self.filenames["in_file"],
            label_files=self.filenames["4d_label_file"],
            class_labels=self.labels,
            incl_shared_variance=incl_shared_variance,
            include_global=include_global,
        ).run()

        wanted_labels = self.global_labels if include_global else self.labels

        # assert
        self.assert_expected_output(wanted_labels, wanted)

    def assert_expected_output(self, labels, wanted):
        with open(self.filenames["out_file"]) as output:
            got = [line.split() for line in output]
            labels_got = got.pop(0)  # remove header
            assert labels_got == labels
            assert len(got) == self.fake_fmri_data.shape[3], "num rows and num volumes"
            # convert from string to float
            got = [[float(num) for num in row] for row in got]
            for i, time in enumerate(got):
                assert len(labels) == len(time)
                for j, segment in enumerate(time):
                    npt.assert_almost_equal(segment, wanted[i][j], decimal=1)

    # dj: self doesn't have orig_dir at this point, not sure how to change it.
    # should work without it
    #    def teardown_class(self):
    #        self.orig_dir.chdir()

    fake_fmri_data = np.array(
        [
            [
                [[2, -1, 4, -2, 3], [4, -2, -5, -1, 0]],
                [[-2, 0, 1, 4, 4], [-5, 3, -3, 1, -5]],
            ],
            [
                [[2, -2, -1, -2, -5], [3, 0, 3, -5, -2]],
                [[-4, -2, -2, 1, -2], [3, 1, 4, -3, -2]],
            ],
        ],
        np.int16,
    )

    fake_label_data = np.array([[[1, 0], [3, 1]], [[2, 0], [1, 3]]], np.uint8)

    fake_equiv_4d_label_data = np.array(
        [
            [[[1.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [[0.0, 0.0, 1.0], [1.0, 0.0, 0.0]]],
            [[[0.0, 1.0, 0.0], [0.0, 0.0, 0.0]], [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]],
        ]
    )

    base_wanted = [
        [-2.33333, 2, 0.5],
        [0, -2, 0.5],
        [-0.3333333, -1, 2.5],
        [0, -2, 0.5],
        [-1.3333333, -5, 1],
    ]

    fake_4d_label_data = np.array(
        [
            [[[0.2, 0.3, 0.5], [0.1, 0.1, 0.8]], [[0.1, 0.3, 0.6], [0.3, 0.4, 0.3]]],
            [[[0.2, 0.2, 0.6], [0.0, 0.3, 0.7]], [[0.3, 0.3, 0.4], [0.3, 0.4, 0.3]]],
        ]
    )

    fourd_wanted = [
        [-5.0652173913, -5.44565217391, 5.50543478261],
        [-7.02173913043, 11.1847826087, -4.33152173913],
        [-19.0869565217, 21.2391304348, -4.57608695652],
        [5.19565217391, -3.66304347826, -1.51630434783],
        [-12.0, 3.0, 0.5],
    ]
