# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os

import nibabel as nb
import numpy as np

import pytest
from ...testing import utils
from ..confounds import CompCor, TCompCor, ACompCor


def close_up_to_column_sign(a, b, rtol=1e-05, atol=1e-08, equal_nan=False):
    """SVD can produce sign flips on a per-column basis."""
    a = np.asanyarray(a)
    b = np.asanyarray(b)
    kwargs = dict(rtol=rtol, atol=atol, equal_nan=equal_nan)
    if np.allclose(a, b, **kwargs):
        return True

    ret = True
    for acol, bcol in zip(a.T, b.T):
        ret &= np.allclose(acol, bcol, **kwargs) or np.allclose(acol, -bcol, **kwargs)
        if not ret:
            break

    return ret


@pytest.mark.parametrize(
    "a, b, close",
    [
        ([[0.1, 0.2], [0.3, 0.4]], [[-0.1, 0.2], [-0.3, 0.4]], True),
        ([[0.1, 0.2], [0.3, 0.4]], [[-0.1, 0.2], [0.3, -0.4]], False),
    ],
)
def test_close_up_to_column_sign(a, b, close):
    a = np.asanyarray(a)
    b = np.asanyarray(b)
    assert close_up_to_column_sign(a, b) == close
    # Sign flips of all columns never changes result
    assert close_up_to_column_sign(a, -b) == close
    assert close_up_to_column_sign(-a, b) == close
    assert close_up_to_column_sign(-a, -b) == close
    # Trivial case
    assert close_up_to_column_sign(a, a)
    assert close_up_to_column_sign(b, b)


class TestCompCor:
    """Note: Tests currently do a poor job of testing functionality"""

    filenames = {
        "functionalnii": "compcorfunc.nii",
        "masknii": "compcormask.nii",
        "masknii2": "compcormask2.nii",
        "components_file": None,
    }

    @pytest.fixture(autouse=True)
    def setup_class(self, tmpdir):
        # setup
        tmpdir.chdir()
        noise = np.fromfunction(self.fake_noise_fun, self.fake_data.shape)
        self.realigned_file = utils.save_toy_nii(
            self.fake_data + noise, self.filenames["functionalnii"]
        )
        mask = np.ones(self.fake_data.shape[:3])
        mask[0, 0, 0] = 0
        mask[0, 0, 1] = 0
        mask1 = utils.save_toy_nii(mask, self.filenames["masknii"])

        other_mask = np.ones(self.fake_data.shape[:3])
        other_mask[0, 1, 0] = 0
        other_mask[1, 1, 0] = 0
        mask2 = utils.save_toy_nii(other_mask, self.filenames["masknii2"])

        self.mask_files = [mask1, mask2]

    def test_compcor(self):
        expected_components = [
            [-0.1989607212, -0.5753813646],
            [0.5692369697, 0.5674945949],
            [-0.6662573243, 0.4675843432],
            [0.4206466244, -0.3361270124],
            [-0.1246655485, -0.1235705610],
        ]

        self.run_cc(
            CompCor(
                num_components=6,
                realigned_file=self.realigned_file,
                mask_files=self.mask_files,
                mask_index=0,
            ),
            expected_components,
        )

        self.run_cc(
            ACompCor(
                num_components=6,
                realigned_file=self.realigned_file,
                mask_files=self.mask_files,
                mask_index=0,
                components_file="acc_components_file",
            ),
            expected_components,
            "aCompCor",
        )

    def test_compcor_variance_threshold_and_metadata(self):
        expected_components = [
            [-0.2027150345, -0.4954813834],
            [0.2565929051, 0.7866217875],
            [-0.3550986008, -0.0089784905],
            [0.7512786244, -0.3599828482],
            [-0.4500578942, 0.0778209345],
        ]
        expected_metadata = {
            "component": "CompCor00",
            "mask": "mask",
            "singular_value": "4.0720553036",
            "variance_explained": "0.5527211465",
            "cumulative_variance_explained": "0.5527211465",
            "retained": "True",
        }
        ccinterface = CompCor(
            variance_threshold=0.7,
            realigned_file=self.realigned_file,
            mask_files=self.mask_files,
            mask_names=["mask"],
            mask_index=1,
            save_metadata=True,
        )
        self.run_cc(
            ccinterface=ccinterface,
            expected_components=expected_components,
            expected_n_components=2,
            expected_metadata=expected_metadata,
        )

    def test_tcompcor(self):
        ccinterface = TCompCor(
            num_components=6,
            realigned_file=self.realigned_file,
            percentile_threshold=0.75,
        )
        self.run_cc(
            ccinterface,
            [
                [-0.1114536190, -0.4632908609],
                [0.4566907310, 0.6983205193],
                [-0.7132557407, 0.1340170559],
                [0.5022537643, -0.5098322262],
                [-0.1342351356, 0.1407855119],
            ],
            "tCompCor",
        )

    def test_tcompcor_no_percentile(self):
        ccinterface = TCompCor(num_components=6, realigned_file=self.realigned_file)
        ccinterface.run()

        mask = nb.load("mask_000.nii.gz").dataobj
        num_nonmasked_voxels = np.count_nonzero(mask)
        assert num_nonmasked_voxels == 1

    def test_compcor_no_regress_poly(self):
        self.run_cc(
            CompCor(
                num_components=6,
                realigned_file=self.realigned_file,
                mask_files=self.mask_files,
                mask_index=0,
                pre_filter=False,
            ),
            [
                [0.4451946442, -0.7683311482],
                [-0.4285129505, -0.0926034137],
                [0.5721540256, 0.5608764842],
                [-0.5367548139, 0.0059943226],
                [-0.0520809054, 0.2940637551],
            ],
        )

    def test_tcompcor_asymmetric_dim(self):
        asymmetric_shape = (2, 3, 4, 5)
        asymmetric_data = utils.save_toy_nii(
            np.zeros(asymmetric_shape), "asymmetric.nii"
        )

        TCompCor(realigned_file=asymmetric_data).run()
        assert nb.load("mask_000.nii.gz").shape == asymmetric_shape[:3]

    def test_compcor_bad_input_shapes(self):
        # dim 0 is < dim 0 of self.mask_files (2)
        shape_less_than = (1, 2, 2, 5)
        # dim 0 is > dim 0 of self.mask_files (2)
        shape_more_than = (3, 3, 3, 5)

        for data_shape in (shape_less_than, shape_more_than):
            data_file = utils.save_toy_nii(np.zeros(data_shape), "temp.nii")
            interface = CompCor(realigned_file=data_file, mask_files=self.mask_files[0])
            with pytest.raises(ValueError):
                interface.run()  # Dimension mismatch

    def test_tcompcor_bad_input_dim(self):
        bad_dims = (2, 2, 2)
        data_file = utils.save_toy_nii(np.zeros(bad_dims), "temp.nii")
        interface = TCompCor(realigned_file=data_file)
        with pytest.raises(ValueError):
            interface.run()  # Not a 4D file

    def test_tcompcor_merge_intersect_masks(self):
        for method in ["union", "intersect"]:
            TCompCor(
                realigned_file=self.realigned_file,
                mask_files=self.mask_files,
                merge_method=method,
            ).run()
            if method == "union":
                assert np.array_equal(
                    nb.load("mask_000.nii.gz").dataobj,
                    ([[[0, 0], [0, 0]], [[0, 0], [1, 0]]]),
                )
            if method == "intersect":
                assert np.array_equal(
                    nb.load("mask_000.nii.gz").dataobj,
                    ([[[0, 0], [0, 0]], [[0, 1], [0, 0]]]),
                )

    def test_tcompcor_index_mask(self):
        TCompCor(
            realigned_file=self.realigned_file, mask_files=self.mask_files, mask_index=1
        ).run()
        assert np.array_equal(
            nb.load("mask_000.nii.gz").dataobj, ([[[0, 0], [0, 0]], [[0, 1], [0, 0]]])
        )

    def test_tcompcor_multi_mask_no_index(self):
        interface = TCompCor(
            realigned_file=self.realigned_file, mask_files=self.mask_files
        )
        with pytest.raises(ValueError):
            interface.run()  # more than one mask file

    def run_cc(
        self,
        ccinterface,
        expected_components,
        expected_header="CompCor",
        expected_n_components=None,
        expected_metadata=None,
    ):
        # run
        ccresult = ccinterface.run()

        # assert
        expected_file = ccinterface._list_outputs()["components_file"]
        assert ccresult.outputs.components_file == expected_file
        assert os.path.exists(expected_file)
        assert os.path.getsize(expected_file) > 0

        with open(ccresult.outputs.components_file, "r") as components_file:
            header = components_file.readline().rstrip().split("\t")
            components_data = np.loadtxt(components_file, delimiter="\t")

        if expected_n_components is None:
            expected_n_components = min(
                ccinterface.inputs.num_components, self.fake_data.shape[3]
            )

        assert header == [
            f"{expected_header}{i:02d}" for i in range(expected_n_components)
        ]

        assert components_data.shape == (self.fake_data.shape[3], expected_n_components)
        assert close_up_to_column_sign(components_data[:, :2], expected_components)

        if ccinterface.inputs.save_metadata:
            expected_metadata_file = ccinterface._list_outputs()["metadata_file"]
            assert ccresult.outputs.metadata_file == expected_metadata_file
            assert os.path.exists(expected_metadata_file)
            assert os.path.getsize(expected_metadata_file) > 0

            with open(ccresult.outputs.metadata_file, "r") as metadata_file:
                components_metadata = [
                    line.rstrip().split("\t") for line in metadata_file
                ]
                components_metadata = {
                    i: j for i, j in zip(components_metadata[0], components_metadata[1])
                }
                assert components_metadata == expected_metadata

        return ccresult

    @staticmethod
    def fake_noise_fun(i, j, l, m):
        return m * i + l - j

    fake_data = np.array(
        [
            [[[8, 5, 3, 8, 0], [6, 7, 4, 7, 1]], [[7, 9, 1, 6, 5], [0, 7, 4, 7, 7]]],
            [[[2, 4, 5, 7, 0], [1, 7, 0, 5, 4]], [[7, 3, 9, 0, 4], [9, 4, 1, 5, 0]]],
        ]
    )
