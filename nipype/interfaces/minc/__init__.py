# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""The MINC (McConnell Brain Imaging Centre, Montreal Neurological Institute) toolkit.

The minc module provides classes for interfacing with the `MINC
<http://www.bic.mni.mcgill.ca/ServicesSoftware/MINC>`_ command line tools. This
module was written to work with MINC version 2.2.00.

Author: Carlo Hamalainen <carlo@carlo-hamalainen.net>
        http://carlo-hamalainen.net
"""

from .base import Info

from .minc import (
    Average,
    BBox,
    Beast,
    BestLinReg,
    BigAverage,
    Blob,
    Blur,
    Calc,
    Convert,
    Copy,
    Dump,
    Extract,
    Gennlxfm,
    Math,
    NlpFit,
    Norm,
    Pik,
    Resample,
    Reshape,
    ToEcat,
    ToRaw,
    Volcentre,
    Voliso,
    Volpad,
    VolSymm,
    XfmAvg,
    XfmConcat,
    XfmInvert,
)
