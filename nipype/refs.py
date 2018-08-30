# Use duecredit (duecredit.org) to provide a citation to relevant work to
# be cited. This does nothing, unless the user has duecredit installed,
# And calls this with duecredit (as in `python -m duecredit script.py`):
from .external.due import due, Doi, BibTeX

due.cite(
    Doi("10.3389/fninf.2011.00013"),
    description="A flexible, lightweight and extensible neuroimaging data"
    " processing framework in Python",
    path="nipype",
    tags=["implementation"],
)

due.cite(
    Doi("10.5281/zenodo.50186"),
    description="A flexible, lightweight and extensible neuroimaging data"
    " processing framework in Python",
    path="nipype",
    tags=["implementation"],
)
