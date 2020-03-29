# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

from ...testing import utils
from ..confounds import TSNR
from .. import misc

import pytest
import numpy.testing as npt
from unittest import mock
import nibabel as nb
import numpy as np
import os


class TestTSNR:
    """ Note: Tests currently do a poor job of testing functionality """

    in_filenames = {"in_file": "tsnrinfile.nii"}

    out_filenames = {  # default output file names
        "detrended_file": "detrend.nii.gz",
        "mean_file": "mean.nii.gz",
        "stddev_file": "stdev.nii.gz",
        "tsnr_file": "tsnr.nii.gz",
    }

    @pytest.fixture(autouse=True)
    def setup_class(self, tmpdir):
        # setup temp folder
        tmpdir.chdir()

        utils.save_toy_nii(self.fake_data, self.in_filenames["in_file"])

    def test_tsnr(self):
        # run
        tsnrresult = TSNR(in_file=self.in_filenames["in_file"]).run()

        # assert
        self.assert_expected_outputs(
            tsnrresult,
            {
                "mean_file": (2.8, 7.4),
                "stddev_file": (0.8, 2.9),
                "tsnr_file": (1.3, 9.25),
            },
        )

    def test_tsnr_withpoly1(self):
        # run
        tsnrresult = TSNR(in_file=self.in_filenames["in_file"], regress_poly=1).run()

        # assert
        self.assert_expected_outputs_poly(
            tsnrresult,
            {
                "detrended_file": (-0.1, 8.7),
                "mean_file": (2.8, 7.4),
                "stddev_file": (0.75, 2.75),
                "tsnr_file": (1.4, 9.9),
            },
        )

    def test_tsnr_withpoly2(self):
        # run
        tsnrresult = TSNR(in_file=self.in_filenames["in_file"], regress_poly=2).run()

        # assert
        self.assert_expected_outputs_poly(
            tsnrresult,
            {
                "detrended_file": (-0.22, 8.55),
                "mean_file": (2.8, 7.7),
                "stddev_file": (0.21, 2.4),
                "tsnr_file": (1.7, 35.9),
            },
        )

    def test_tsnr_withpoly3(self):
        # run
        tsnrresult = TSNR(in_file=self.in_filenames["in_file"], regress_poly=3).run()

        # assert
        self.assert_expected_outputs_poly(
            tsnrresult,
            {
                "detrended_file": (1.8, 7.95),
                "mean_file": (2.8, 7.7),
                "stddev_file": (0.1, 1.7),
                "tsnr_file": (2.6, 57.3),
            },
        )

    @mock.patch("warnings.warn")
    def test_warning(self, mock_warn):
        """ test that usage of misc.TSNR trips a warning to use
        confounds.TSNR instead """
        # run
        misc.TSNR(in_file=self.in_filenames["in_file"])

        # assert
        assert True in [
            args[0].count("confounds") > 0 for _, args, _ in mock_warn.mock_calls
        ]

    def assert_expected_outputs_poly(self, tsnrresult, expected_ranges):
        assert (
            os.path.basename(tsnrresult.outputs.detrended_file)
            == self.out_filenames["detrended_file"]
        )
        self.assert_expected_outputs(tsnrresult, expected_ranges)

    def assert_expected_outputs(self, tsnrresult, expected_ranges):
        self.assert_default_outputs(tsnrresult.outputs)
        self.assert_unchanged(expected_ranges)

    def assert_default_outputs(self, outputs):
        assert os.path.basename(outputs.mean_file) == self.out_filenames["mean_file"]
        assert (
            os.path.basename(outputs.stddev_file) == self.out_filenames["stddev_file"]
        )
        assert os.path.basename(outputs.tsnr_file) == self.out_filenames["tsnr_file"]

    def assert_unchanged(self, expected_ranges):
        for key, (min_, max_) in expected_ranges.items():
            data = np.asarray(nb.load(self.out_filenames[key]).dataobj)
            npt.assert_almost_equal(np.amin(data), min_, decimal=1)
            npt.assert_almost_equal(np.amax(data), max_, decimal=1)

    fake_data = np.array(
        [
            [[[2, 4, 3, 9, 1], [3, 6, 4, 7, 4]], [[8, 3, 4, 6, 2], [4, 0, 4, 4, 2]]],
            [[[9, 7, 5, 5, 7], [7, 8, 4, 8, 4]], [[0, 4, 7, 1, 7], [6, 8, 8, 8, 7]]],
        ]
    )
