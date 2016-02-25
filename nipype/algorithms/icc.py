# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Algorithms to compute the Interclass Correlation Coefficient

    Change directory to provide relative paths for doctests
    >>> import os
    >>> filepath = os.path.dirname( os.path.realpath( __file__ ) )
    >>> datadir = os.path.realpath(os.path.join(filepath, '../testing/data'))
    >>> os.chdir(datadir)

"""

from __future__ import division
import os
import numpy as np
from numpy import ones, kron, mean, eye, hstack, dot, tile
from scipy.linalg import pinv
import nibabel as nb

from builtins import range
from ..interfaces.base import (traits, File, BaseInterface, BaseInputSpec,
                               TraitedSpec)

class ICCInputSpec(BaseInputSpec):
    subjects_sessions = traits.List(traits.List(File(exists=True)),
                                    desc="n subjects m sessions 3D stat files",
                                    mandatory=True)
    mask = File(exists=True, mandatory=True)
    icc_map = File('icc_map.nii', desc='name of output ICC map')
    session_var_map = File('session_var_map.nii', desc="variance between sessions")
    session_F_map = File('session_F_map.nii', desc="F map of sessions")
    subject_var_map = File('subject_var_map.nii', desc="variance between subjects")


class ICCOutputSpec(TraitedSpec):
    icc_map = File(exists=True)
    session_var_map = File(exists=True, desc="variance between sessions")
    session_F_map = File(exists=True, desc="variance between sessions")
    subject_var_map = File(exists=True, desc="variance between subjects")


class ICC(BaseInterface):
    """
    Calculates Interclass Correlation Coefficient (3,1) as defined in
    P. E. Shrout & Joseph L. Fleiss (1979). "Intraclass Correlations: Uses in
    Assessing Rater Reliability". Psychological Bulletin 86 (2): 420-428. This
    particular implementation is aimed at relaibility (test-retest) studies.
    """
    _input_spec = ICCInputSpec
    _output_spec = ICCOutputSpec

    def _run_interface(self, runtime):
        maskdata = nb.load(self.inputs.mask).get_data()
        maskdata = np.logical_not(np.logical_or(maskdata == 0, np.isnan(maskdata)))

        session_datas = [[nb.load(fname).get_data()[maskdata].reshape(-1, 1) for fname in sessions] for sessions in self.inputs.subjects_sessions]
        list_of_sessions = [np.dstack(session_data) for session_data in session_datas]
        all_data = np.hstack(list_of_sessions)
        icc = np.zeros(session_datas[0][0].shape)
        session_F = np.zeros(session_datas[0][0].shape)
        session_var = np.zeros(session_datas[0][0].shape)
        subject_var = np.zeros(session_datas[0][0].shape)

        for i in range(icc.shape[0]):
            data = all_data[i, :, :]
            icc[i], subject_var[i], session_var[i], session_F[i], _, _ = ICC_rep_anova(data)

        nim = nb.load(self.inputs.subjects_sessions[0][0])
        new_data = np.zeros(nim.shape)
        new_data[maskdata] = icc.reshape(-1,)
        new_img = nb.Nifti1Image(new_data, nim.affine, nim.header)
        nb.save(new_img, self.inputs.icc_map)

        new_data = np.zeros(nim.shape)
        new_data[maskdata] = session_var.reshape(-1,)
        new_img = nb.Nifti1Image(new_data, nim.affine, nim.header)
        nb.save(new_img, self.inputs.session_var_map)

        new_data = np.zeros(nim.shape)
        new_data[maskdata] = subject_var.reshape(-1,)
        new_img = nb.Nifti1Image(new_data, nim.affine, nim.header)
        nb.save(new_img, self.inputs.subject_var_map.nii)

        new_data = np.zeros(nim.shape)
        new_data[maskdata] = session_F.reshape(-1,)
        new_img = nb.Nifti1Image(new_data, nim.affine, nim.header)
        nb.save(new_img, self.inputs.session_F_map)
        return runtime


def ICC_rep_anova(data):
    """
    the data (Y) are entered as a 'table' ie subjects are in rows and repeated
    measures in columns

    One Sample Repeated measure ANOVA

    .. math::

      Y = XB + E with X = [FaTor / Subjects]
    """

    [nb_subjects, nb_conditions] = data.shape
    dfc = nb_conditions - 1
    dfe = (nb_subjects - 1) * dfc
    dfr = nb_subjects - 1

    # Compute the repeated measure effect
    # ------------------------------------

    # Sum Square Total
    mean_Y = mean(data)
    SST = ((data - mean_Y) ** 2).sum()

    # create the design matrix for the different levels
    x = kron(eye(nb_conditions), ones((nb_subjects, 1)))  # sessions
    x0 = tile(eye(nb_subjects), (nb_conditions, 1))  # subjects
    X = hstack([x, x0])

    # Sum Square Error
    predicted_Y = dot(dot(dot(X, pinv(dot(X.T, X))), X.T), data.flatten('F'))
    residuals = data.flatten('F') - predicted_Y
    SSE = (residuals ** 2).sum()

    residuals.shape = data.shape

    MSE = SSE / dfe

    # Sum square session effect - between colums/sessions
    SSC = ((mean(data, 0) - mean_Y) ** 2).sum() * nb_subjects
    MSC = SSC / dfc / nb_subjects

    session_effect_F = MSC / MSE

    # Sum Square subject effect - between rows/subjects
    SSR = SST - SSC - SSE
    MSR = SSR / dfr

    # ICC(3,1) = (mean square subjeT - mean square error) / (mean square subjeT + (k-1)*-mean square error)
    ICC = (MSR - MSE) / (MSR + dfc * MSE)

    e_var = MSE  # variance of error
    r_var = (MSR - MSE) / nb_conditions  # variance between subjects

    return ICC, r_var, e_var, session_effect_F, dfc, dfe
