# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""References for this interface"""

from .due import due, Doi, BibTeX

# http://www.fil.ion.ucl.ac.uk/spm
due.dcite(BibTeX("""book{FrackowiakFristonFrithDolanMazziotta1997,
        author={R.S.J. Frackowiak, K.J. Friston, C.D. Frith, R.J. Dolan, and J.C. Mazziotta},
        title={Human Brain Function},
        publisher={Academic Press USA}
        year={1997},
        }"""),
    description='The fundamental text on Statistical Parametric Mapping (SPM)',
    path="nipype.interfaces.spm",
    tags=['implementation'])
