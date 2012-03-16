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
    Assessing Rater Reliability". Psychological Bulletin 86 (2): 420–428. This
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
    #print nb_subjects, nb_conditions
    df = nb_conditions - 1
    dfe = nb_subjects * nb_conditions - nb_subjects - df
    dfmodel = nb_subjects - df

    # create the design matrix for the different levels
    # ------------------------------------------------

    x = kron(eye(nb_conditions), ones((nb_subjects, 1)))  # effect
    x0 = tile(eye(nb_subjects), (nb_conditions, 1))  # subjeT
    X = hstack([x, x0])

    # Compute the repeated measure effect
    # ------------------------------------
    Y = Y.flatten(1)

    # Sum Square Total
    SST = dot((Y.reshape(-1, 1) - tile(mean(Y), (Y.shape[0], 1))).T, (Y.reshape(-1, 1) - tile(mean(Y), (Y.shape[0], 1))))

    # Sum Square SubjeT (error in the ANOVA model)
    M = dot(dot(X, pinv(dot(X.T, X))), X.T)
    R = eye(Y.shape[0]) - M
    SSS = dot(dot(Y.T, R), Y)
    MSS = SSS / dfe

    # Sum square effect (repeated measure)
    Betas = dot(pinv(x), Y)  # compute without cst/subjects
    yhat = dot(x, Betas)
    SSE = diag(dot((yhat.reshape(-1, 1) - tile(mean(yhat), (yhat.shape[0], 1))).T, (yhat.reshape(-1, 1) - tile(mean(yhat), (yhat.shape[0], 1)))))

    # Sum Square error
    SSError = SST - SSS - SSE
    MSError = SSError / dfmodel

    # ICC(3,1) = (mean square subjeT - mean square error) / (mean square subjeT + (k-1)*-mean square error)
    return -((MSS - MSError) / (MSS + df * MSError))
