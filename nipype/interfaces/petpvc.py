# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""PETPVC is a toolbox for partial volume correction in positron emission tomography."""
import os

from .base import (
    TraitedSpec,
    CommandLineInputSpec,
    CommandLine,
    File,
    isdefined,
    traits,
)
from ..utils.filemanip import fname_presuffix
from ..external.due import BibTeX

pvc_methods = [
    "GTM",
    "IY",
    "IY+RL",
    "IY+VC",
    "LABBE",
    "LABBE+MTC",
    "LABBE+MTC+RL",
    "LABBE+MTC+VC",
    "LABBE+RBV",
    "LABBE+RBV+RL",
    "LABBE+RBV+VC",
    "MG",
    "MG+RL",
    "MG+VC",
    "MTC",
    "MTC+RL",
    "MTC+VC",
    "RBV",
    "RBV+RL",
    "RBV+VC",
    "RL",
    "VC",
]


class PETPVCInputSpec(CommandLineInputSpec):
    in_file = File(desc="PET image file", exists=True, mandatory=True, argstr="-i %s")
    out_file = File(desc="Output file", genfile=True, hash_files=False, argstr="-o %s")
    mask_file = File(
        desc="Mask image file", exists=True, mandatory=True, argstr="-m %s"
    )
    pvc = traits.Enum(
        pvc_methods,
        mandatory=True,
        argstr="-p %s",
        desc="""\
Desired PVC method:

    * Geometric transfer matrix -- ``GTM``
    * Labbe approach -- ``LABBE``
    * Richardson-Lucy -- ``RL``
    * Van-Cittert -- ``VC``
    * Region-based voxel-wise correction -- ``RBV``
    * RBV with Labbe -- ``LABBE+RBV``
    * RBV with Van-Cittert -- ``RBV+VC``
    * RBV with Richardson-Lucy -- ``RBV+RL``
    * RBV with Labbe and Van-Cittert -- ``LABBE+RBV+VC``
    * RBV with Labbe and Richardson-Lucy -- ``LABBE+RBV+RL``
    * Multi-target correction -- ``MTC``
    * MTC with Labbe -- ``LABBE+MTC``
    * MTC with Van-Cittert -- ``MTC+VC``
    * MTC with Richardson-Lucy -- ``MTC+RL``
    * MTC with Labbe and Van-Cittert -- ``LABBE+MTC+VC``
    * MTC with Labbe and Richardson-Lucy -- ``LABBE+MTC+RL``
    * Iterative Yang -- ``IY``
    * Iterative Yang with Van-Cittert -- ``IY+VC``
    * Iterative Yang with Richardson-Lucy -- ``IY+RL``
    * Muller Gartner -- ``MG``
    * Muller Gartner with Van-Cittert -- ``MG+VC``
    * Muller Gartner with Richardson-Lucy -- ``MG+RL``

""",
    )
    fwhm_x = traits.Float(
        desc="The full-width at half maximum in mm along x-axis",
        mandatory=True,
        argstr="-x %.4f",
    )
    fwhm_y = traits.Float(
        desc="The full-width at half maximum in mm along y-axis",
        mandatory=True,
        argstr="-y %.4f",
    )
    fwhm_z = traits.Float(
        desc="The full-width at half maximum in mm along z-axis",
        mandatory=True,
        argstr="-z %.4f",
    )
    debug = traits.Bool(
        desc="Prints debug information",
        usedefault=True,
        default_value=False,
        argstr="-d",
    )
    n_iter = traits.Int(
        desc="Number of iterations", default_value=10, usedefault=True, argstr="-n %d"
    )
    n_deconv = traits.Int(
        desc="Number of deconvolution iterations",
        default_value=10,
        usedefault=True,
        argstr="-k %d",
    )
    alpha = traits.Float(
        desc="Alpha value", default_value=1.5, usedefault=True, argstr="-a %.4f"
    )
    stop_crit = traits.Float(
        desc="Stopping criterion", default_value=0.01, usedefault=True, argstr="-s %.4f"
    )


class PETPVCOutputSpec(TraitedSpec):
    out_file = File(desc="Output file")


class PETPVC(CommandLine):
    """Use PETPVC for partial volume correction of PET images.

    PETPVC ([1]_, [2]_) is a software from the Nuclear Medicine Department
    of the UCL University Hospital, London, UK.

    Examples
    --------
    >>> from ..testing import example_data
    >>> #TODO get data for PETPVC
    >>> pvc = PETPVC()
    >>> pvc.inputs.in_file   = 'pet.nii.gz'
    >>> pvc.inputs.mask_file = 'tissues.nii.gz'
    >>> pvc.inputs.out_file  = 'pet_pvc_rbv.nii.gz'
    >>> pvc.inputs.pvc = 'RBV'
    >>> pvc.inputs.fwhm_x = 2.0
    >>> pvc.inputs.fwhm_y = 2.0
    >>> pvc.inputs.fwhm_z = 2.0
    >>> outs = pvc.run() #doctest: +SKIP

    References
    ----------
    .. [1] K. Erlandsson, I. Buvat, P. H. Pretorius, B. A. Thomas, and B. F. Hutton,
           "A review of partial volume correction techniques for emission tomography
           and their applications in neurology, cardiology and oncology," Phys. Med.
           Biol., vol. 57, no. 21, p. R119, 2012.
    .. [2] https://github.com/UCL/PETPVC

    """

    input_spec = PETPVCInputSpec
    output_spec = PETPVCOutputSpec
    _cmd = "petpvc"

    _references = [
        {
            "entry": BibTeX(
                "@article{0031-9155-61-22-7975,"
                "author={Benjamin A Thomas and Vesna Cuplov and Alexandre Bousse and "
                "Adriana Mendes and Kris Thielemans and Brian F Hutton and Kjell Erlandsson},"
                "title={PETPVC: a toolbox for performing partial volume correction "
                "techniques in positron emission tomography},"
                "journal={Physics in Medicine and Biology},"
                "volume={61},"
                "number={22},"
                "pages={7975},"
                "url={http://stacks.iop.org/0031-9155/61/i=22/a=7975},"
                "doi={https://doi.org/10.1088/0031-9155/61/22/7975},"
                "year={2016},"
                "}"
            ),
            "description": "PETPVC software implementation publication",
            "tags": ["implementation"],
        }
    ]

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs["out_file"] = self.inputs.out_file
        if not isdefined(outputs["out_file"]):
            method_name = self.inputs.pvc.lower()
            outputs["out_file"] = self._gen_fname(
                self.inputs.in_file, suffix="_{}_pvc".format(method_name)
            )

        outputs["out_file"] = os.path.abspath(outputs["out_file"])
        return outputs

    def _gen_fname(
        self, basename, cwd=None, suffix=None, change_ext=True, ext=".nii.gz"
    ):
        """Generate a filename based on the given parameters.

        The filename will take the form: cwd/basename<suffix><ext>.
        If change_ext is True, it will use the extensions specified in
        <instance>inputs.output_type.

        Parameters
        ----------
        basename : str
            Filename to base the new filename on.
        cwd : str
            Path to prefix to the new filename. (default is os.getcwd())
        suffix : str
            Suffix to add to the `basename`.  (defaults is '' )
        change_ext : bool
            Flag to change the filename extension to the given `ext`.
            (Default is False)

        Returns
        -------
        fname : str
            New filename based on given parameters.

        """
        if basename == "":
            msg = "Unable to generate filename for command %s. " % self.cmd
            msg += "basename is not set!"
            raise ValueError(msg)
        if cwd is None:
            cwd = os.getcwd()
        if change_ext:
            if suffix:
                suffix = "".join((suffix, ext))
            else:
                suffix = ext
        if suffix is None:
            suffix = ""
        fname = fname_presuffix(basename, suffix=suffix, use_ext=False, newpath=cwd)
        return fname

    def _gen_filename(self, name):
        if name == "out_file":
            return self._list_outputs()["out_file"]
        return None
