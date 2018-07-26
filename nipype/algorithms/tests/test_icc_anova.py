# -*- coding: utf-8 -*-
from __future__ import division
import numpy as np
from nipype.algorithms.icc import ICC_rep_anova


def test_ICC_rep_anova():
    # see table 2 in P. E. Shrout & Joseph L. Fleiss (1979). "Intraclass
    # Correlations: Uses in Assessing Rater Reliability". Psychological
    # Bulletin 86 (2): 420-428
    Y = np.array([[9, 2, 5, 8], [6, 1, 3, 2], [8, 4, 6, 8], [7, 1, 2, 6],
                  [10, 5, 6, 9], [6, 2, 4, 7]])

    icc, r_var, e_var, _, dfc, dfe = ICC_rep_anova(Y)
    # see table 4
    assert round(icc, 2) == 0.71
    assert dfc == 3
    assert dfe == 15
    assert np.isclose(r_var / (r_var + e_var), icc)
