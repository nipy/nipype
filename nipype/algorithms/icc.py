from numpy import ones, kron, mean, diag, eye, hstack, dot, tile
from scipy.linalg import pinv
from ..interfaces.base import BaseInterfaceInputSpec, TraitedSpec, \
    BaseInterface, traits, File
import nibabel as nb
import numpy as np
import os


class ICCInputSpec(BaseInterfaceInputSpec):
    first_session_t_maps = traits.List(File(exists=True),
                                       desc="both list have to have the same length")
    second_session_t_maps = traits.List(File(exists=True),
                                        desc="both list have to have the same length")
    mask = File(exists=True)


class ICCOutputSpec(TraitedSpec):
    icc_map = File(exists=True)


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

        first_session_nims = [nb.load(fname).get_data()[maskdata].reshape(-1, 1) for fname in self.inputs.first_session_t_maps]
        second_session_nims = [nb.load(fname).get_data()[maskdata].reshape(-1, 1) for fname in self.inputs.second_session_t_maps]
        all_data = np.dstack([np.hstack(first_session_nims), np.hstack(second_session_nims)])

        icc = np.zeros(first_session_nims[0].shape)

        for x in range(icc.shape[0]):
            Y = all_data[x, :, :]
            icc[x] = ICC_rep_anova(Y)

        nim = nb.load(self.inputs.first_session_t_maps[0])
        new_data = np.zeros(nim.get_shape())
        new_data[maskdata] = icc.reshape(-1,)
        new_img = nb.Nifti1Image(new_data, nim.get_affine(), nim.get_header())
        nb.save(new_img, 'icc_map.nii')

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['icc_map'] = os.path.abspath('icc_map.nii')
        return outputs


def ICC_rep_anova(Y):

    # the data Y are entered as a 'table' ie subjects are in rows and repeated
    # measures in columns
    #
    # ------------------------------------------------------------------------------------------
    #                   One Sample Repeated measure ANOVA
    #                   Y = XB + E with X = [FaTor / SubjeT]
    # ------------------------------------------------------------------------------------------

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

    MSE = SSE / dfe

    # Sum square session effect - between colums/sessions
    SSC = ((mean(Y, 0) - mean_Y) ** 2).sum() * nb_subjects
    MSC = SSC / dfc

    F_value = MSC / MSE

    # Sum Square subject effect - between rows/subjects
    SSR = SST - SSC - SSE
    MSR = SSR / dfr

    # ICC(3,1) = (mean square subjeT - mean square error) / (mean square subjeT + (k-1)*-mean square error)
    return (MSR - MSE) / (MSR + dfc * MSE)
