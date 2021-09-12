# -*- coding: utf-8 -*-
"""Quickshear is a simple geometric defacing algorithm."""

from .base import CommandLineInputSpec, CommandLine, traits, TraitedSpec, File
from ..external.due import BibTeX


class QuickshearInputSpec(CommandLineInputSpec):
    in_file = File(
        exists=True,
        position=1,
        argstr="%s",
        mandatory=True,
        desc="neuroimage to deface",
    )
    mask_file = File(
        exists=True, position=2, argstr="%s", desc="brain mask", mandatory=True
    )
    out_file = File(
        name_template="%s_defaced",
        name_source="in_file",
        position=3,
        argstr="%s",
        desc="defaced output image",
        keep_extension=True,
    )
    buff = traits.Int(
        position=4,
        argstr="%d",
        desc="buffer size (in voxels) between shearing " "plane and the brain",
    )


class QuickshearOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="defaced output image")


class Quickshear(CommandLine):
    """
    Quickshear is a simple geometric defacing algorithm

    Given an anatomical image and a reasonable brainmask, Quickshear estimates
    a shearing plane with the brain mask on one side and the face on the other,
    zeroing out the face side.

    >>> from nipype.interfaces.quickshear import Quickshear
    >>> qs = Quickshear(in_file='T1.nii', mask_file='brain_mask.nii')
    >>> qs.cmdline
    'quickshear T1.nii brain_mask.nii T1_defaced.nii'

    In the absence of a precomputed mask, a simple pipeline can be generated
    with any tool that generates brain masks:

    >>> from nipype.pipeline import engine as pe
    >>> from nipype.interfaces import utility as niu
    >>> from nipype.interfaces.fsl import BET
    >>> deface_wf = pe.Workflow('deface_wf')
    >>> inputnode = pe.Node(niu.IdentityInterface(['in_file']),
    ...                     name='inputnode')
    >>> outputnode = pe.Node(niu.IdentityInterface(['out_file']),
    ...                      name='outputnode')
    >>> bet = pe.Node(BET(mask=True), name='bet')
    >>> quickshear = pe.Node(Quickshear(), name='quickshear')
    >>> deface_wf.connect([
    ...     (inputnode, bet, [('in_file', 'in_file')]),
    ...     (inputnode, quickshear, [('in_file', 'in_file')]),
    ...     (bet, quickshear, [('mask_file', 'mask_file')]),
    ...     (quickshear, outputnode, [('out_file', 'out_file')]),
    ...     ])
    >>> inputnode.inputs.in_file = 'T1.nii'
    >>> res = deface_wf.run()  # doctest: +SKIP
    """

    _cmd = "quickshear"
    input_spec = QuickshearInputSpec
    output_spec = QuickshearOutputSpec

    _references = [
        {
            "entry": BibTeX(
                "@inproceedings{Schimke2011,"
                "address = {San Francisco},"
                "author = {Schimke, Nakeisha and Hale, John},"
                "booktitle = {Proceedings of the 2nd USENIX Conference on "
                "Health Security and Privacy},"
                "title = {{Quickshear Defacing for Neuroimages}},"
                "year = {2011},"
                "month = sep}"
            ),
            "tags": ["implementation"],
        }
    ]
