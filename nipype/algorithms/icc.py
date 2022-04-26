# -*- coding: utf-8 -*-
import os
from functools import lru_cache
import numpy as np
from numpy import ones, kron, mean, eye, hstack, tile
from numpy.linalg import pinv
import nibabel as nb
from ..interfaces.base import (
    BaseInterfaceInputSpec,
    TraitedSpec,
    BaseInterface,
    traits,
    File,
)


class ICCInputSpec(BaseInterfaceInputSpec):
    subjects_sessions = traits.List(
        traits.List(File(exists=True)),
        desc="n subjects m sessions 3D stat files",
        mandatory=True,
    )
    mask = File(exists=True, mandatory=True)


class ICCOutputSpec(TraitedSpec):
    icc_map = File(exists=True)
    session_var_map = File(exists=True, desc="variance between sessions")
    subject_var_map = File(exists=True, desc="variance between subjects")


class ICC(BaseInterface):
    """
    Calculates Interclass Correlation Coefficient (3,1) as defined in
    P. E. Shrout & Joseph L. Fleiss (1979). "Intraclass Correlations: Uses in
    Assessing Rater Reliability". Psychological Bulletin 86 (2): 420-428. This
    particular implementation is aimed at relaibility (test-retest) studies.
    """

    input_spec = ICCInputSpec
    output_spec = ICCOutputSpec

    def _run_interface(self, runtime):
        maskdata = nb.load(self.inputs.mask).get_fdata()
        maskdata = np.logical_not(np.logical_or(maskdata == 0, np.isnan(maskdata)))

        session_datas = [
            [nb.load(fname).get_fdata()[maskdata].reshape(-1, 1) for fname in sessions]
            for sessions in self.inputs.subjects_sessions
        ]
        list_of_sessions = [np.dstack(session_data) for session_data in session_datas]
        all_data = np.hstack(list_of_sessions)
        icc = np.zeros(session_datas[0][0].shape)
        session_F = np.zeros(session_datas[0][0].shape)
        session_var = np.zeros(session_datas[0][0].shape)
        subject_var = np.zeros(session_datas[0][0].shape)

        for x in range(icc.shape[0]):
            Y = all_data[x, :, :]
            icc[x], subject_var[x], session_var[x], session_F[x], _, _ = ICC_rep_anova(
                Y
            )

        nim = nb.load(self.inputs.subjects_sessions[0][0])
        new_data = np.zeros(nim.shape)
        new_data[maskdata] = icc.reshape(-1)
        new_img = nb.Nifti1Image(new_data, nim.affine, nim.header)
        nb.save(new_img, "icc_map.nii")

        new_data = np.zeros(nim.shape)
        new_data[maskdata] = session_var.reshape(-1)
        new_img = nb.Nifti1Image(new_data, nim.affine, nim.header)
        nb.save(new_img, "session_var_map.nii")

        new_data = np.zeros(nim.shape)
        new_data[maskdata] = subject_var.reshape(-1)
        new_img = nb.Nifti1Image(new_data, nim.affine, nim.header)
        nb.save(new_img, "subject_var_map.nii")

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs["icc_map"] = os.path.abspath("icc_map.nii")
        outputs["session_var_map"] = os.path.abspath("session_var_map.nii")
        outputs["subject_var_map"] = os.path.abspath("subject_var_map.nii")
        return outputs


@lru_cache(maxsize=1)
def ICC_projection_matrix(shape):
    nb_subjects, nb_conditions = shape

    x = kron(eye(nb_conditions), ones((nb_subjects, 1)))  # sessions
    x0 = tile(eye(nb_subjects), (nb_conditions, 1))  # subjects
    X = hstack([x, x0])
    return X @ pinv(X.T @ X, hermitian=True) @ X.T


def ICC_rep_anova(Y, projection_matrix=None):
    """
    the data Y are entered as a 'table' ie subjects are in rows and repeated
    measures in columns

    One Sample Repeated measure ANOVA

    Y = XB + E with X = [FaTor / Subjects]

    ``ICC_rep_anova`` involves an expensive operation to compute a projection
    matrix, which depends only on the shape of ``Y``, which is computed by
    calling ``ICC_projection_matrix(Y.shape)``. If arrays of multiple shapes are
    expected, it may be worth pre-computing and passing directly as an
    argument to ``ICC_rep_anova``.

    If only one ``Y.shape`` will occur, you do not need to explicitly handle
    these, as the most recently calculated matrix is cached automatically.
    For example, if you are running the same computation on every voxel of
    an image, you will see significant speedups.

    If a ``Y`` is passed with a new shape, a new matrix will be calculated
    automatically.
    """
    [nb_subjects, nb_conditions] = Y.shape
    dfc = nb_conditions - 1
    dfr = nb_subjects - 1
    dfe = dfr * dfc

    # Compute the repeated measure effect
    # ------------------------------------

    # Sum Square Total
    demeaned_Y = Y - mean(Y)
    SST = np.sum(demeaned_Y**2)

    # Sum Square Error
    if projection_matrix is None:
        projection_matrix = ICC_projection_matrix(Y.shape)
    residuals = Y.flatten("F") - (projection_matrix @ Y.flatten("F"))
    SSE = np.sum(residuals**2)

    MSE = SSE / dfe

    # Sum square session effect - between columns/sessions
    SSC = np.sum(mean(demeaned_Y, 0) ** 2) * nb_subjects
    MSC = SSC / dfc / nb_subjects

    session_effect_F = MSC / MSE

    # Sum Square subject effect - between rows/subjects
    SSR = SST - SSC - SSE
    MSR = SSR / dfr

    # ICC(3,1) = (mean square subjeT - mean square error) /
    #            (mean square subjeT + (k-1)*-mean square error)
    ICC = (MSR - MSE) / (MSR + dfc * MSE)

    e_var = MSE  # variance of error
    r_var = (MSR - MSE) / nb_conditions  # variance between subjects

    return ICC, r_var, e_var, session_effect_F, dfc, dfe
