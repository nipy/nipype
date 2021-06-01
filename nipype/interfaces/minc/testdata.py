# -*- coding: utf-8 -*-

import os
from ...testing import example_data

minc2Dfile = example_data("minc_test_2D_00.mnc")
minc3Dfile = example_data("minc_test_3D_00.mnc")

nlp_config = example_data("minc_nlp.conf")


def nonempty_minc_data(i, shape="2D"):
    return example_data("minc_test_%s_%.2d.mnc" % (shape, i))
