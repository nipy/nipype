from numpy import ones, kron, mean, eye, hstack, dot, tile
from scipy.linalg import pinv
from ..interfaces.base import BaseInterfaceInputSpec, TraitedSpec, \
    BaseInterface, traits, File
import nibabel as nb
import numpy as np
import os


class ICCInputSpec(BaseInterfaceInputSpec):
    subjects_sessions = traits.List(traits.List(File(exists=True)),
                           desc="n subjects m sessions 3D stat files",
                           mandatory=True)
    mask = File(exists=True, mandatory=True)


class ICCOutputSpec(TraitedSpec):
    icc_map = File(exists=True)
    session_var_map = File(exists=True, desc="variance between sessions")
    subject_var_map = File(exists=True, desc="variance between subjects")


class ICC(BaseInterface):
    '''
    Calculates Interclass Correlation Coefficient (3,1) as defined in
    P. E. Shrout & Joseph L. Fleiss (1979). "Intraclass Correlations: Uses in
    Assessing Rater Reliability". Psychological Bulletin 86 (2): 420-428. This
    particular implementation is aimed at relaibility (test-retest) studies.
    '''
    input_spec = ICCInputSpec
    output_spec = ICCOutputSpec

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

        for x in range(icc.shape[0]):
            Y = all_data[x, :, :]
            icc[x], subject_var[x], session_var[x],  session_F[x], _, _ = ICC_rep_anova(Y)

        nim = nb.load(self.inputs.subjects_sessions[0][0])
        new_data = np.zeros(nim.get_shape())
        new_data[maskdata] = icc.reshape(-1,)
        new_img = nb.Nifti1Image(new_data, nim.get_affine(), nim.get_header())
        nb.save(new_img, 'icc_map.nii')

        new_data = np.zeros(nim.get_shape())
        new_data[maskdata] = session_var.reshape(-1,)
        new_img = nb.Nifti1Image(new_data, nim.get_affine(), nim.get_header())
        nb.save(new_img, 'session_var_map.nii')

        new_data = np.zeros(nim.get_shape())
        new_data[maskdata] = subject_var.reshape(-1,)
        new_img = nb.Nifti1Image(new_data, nim.get_affine(), nim.get_header())
        nb.save(new_img, 'subject_var_map.nii')

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['icc_map'] = os.path.abspath('icc_map.nii')
        outputs['sessions_F_map'] = os.path.abspath('sessions_F_map.nii')
        outputs['session_var_map'] = os.path.abspath('session_var_map.nii')
        outputs['subject_var_map'] = os.path.abspath('subject_var_map.nii')
        return outputs


def ICC_rep_anova(Y):
    '''
    the data Y are entered as a 'table' ie subjects are in rows and repeated
    measures in columns

    --------------------------------------------------------------------------
                       One Sample Repeated measure ANOVA
                       Y = XB + E with X = [FaTor / Subjects]
    --------------------------------------------------------------------------
    '''

    [nb_subjects, nb_conditions] = Y.shape
    dfc = nb_conditions - 1
    dfe = (nb_subjects - 1) * dfc
    dfr = nb_subjects - 1

    # Compute the repeated measure effect
    # ------------------------------------

    # Sum Square Total
    mean_Y = mean(Y)
    SST = ((Y - mean_Y) ** 2).sum()

    # create the design matrix for the different levels
    x = kron(eye(nb_conditions), ones((nb_subjects, 1)))  # sessions
    x0 = tile(eye(nb_subjects), (nb_conditions, 1))  # subjects
    X = hstack([x, x0])

    # Sum Square Error
    predicted_Y = dot(dot(dot(X, pinv(dot(X.T, X))), X.T), Y.flatten('F'))
    residuals = Y.flatten('F') - predicted_Y
    SSE = (residuals ** 2).sum()

    residuals.shape = Y.shape

    MSE = SSE / dfe

    # Sum square session effect - between colums/sessions
    SSC = ((mean(Y, 0) - mean_Y) ** 2).sum() * nb_subjects
    MSC = SSC / dfc / nb_subjects

    session_effect_F = MSC / MSE

    # Sum Square subject effect - between rows/subjects
    SSR = SST - SSC - SSE
    MSR = SSR / dfr

    # ICC(3,1) = (mean square subjeT - mean square error) / (mean square subjeT + (k-1)*-mean square error)
    ICC = (MSR - MSE) / (MSR + dfc * MSE)

    e_var = MSE #variance of error
    r_var = (MSR - MSE)/nb_conditions #variance between subjects

    return ICC, r_var, e_var, session_effect_F, dfc, dfe
