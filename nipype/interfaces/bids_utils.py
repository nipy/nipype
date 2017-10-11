# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" Set of interfaces that allow interaction with BIDS data. Currently
available interfaces are:

BIDSDataGrabber: Query data from BIDS dataset using pybids grabbids.

Change directory to provide relative paths for doctests
>>> import os
>>> import bids
>>> filepath = os.path.realpath(os.path.dirname(bids.__file__))
>>> datadir = os.path.realpath(os.path.join(filepath, 'grabbids/tests/data/'))
>>> os.chdir(datadir)

"""
from os.path import join, dirname
from .. import logging
from .base import (traits,
                   DynamicTraitedSpec,
                   Directory,
                   BaseInterface,
                   isdefined,
                   Str,
                   Undefined)

try:
    from bids import grabbids as gb
    import json
except ImportError:
    have_pybids = False
else:
    have_pybids = True

LOGGER = logging.getLogger('workflows')

class BIDSDataGrabberInputSpec(DynamicTraitedSpec):
    base_dir = Directory(exists=True,
                         desc='Path to BIDS Directory.',
                         mandatory=True)
    output_query = traits.Dict(key_trait=Str,
                               value_trait=traits.Dict,
                               desc='Queries for outfield outputs')
    raise_on_empty = traits.Bool(True, usedefault=True,
                                 desc='Generate exception if list is empty '
                                 'for a given field')
    return_type = traits.Enum('file', 'namedtuple', usedefault=True)


class BIDSDataGrabber(BaseInterface):

    """ BIDS datagrabber module that wraps around pybids to allow arbitrary
    querying of BIDS datasets.

    Examples
    --------

    >>> from nipype.interfaces.bids_utils import BIDSDataGrabber
    >>> from os.path import basename

    By default, the BIDSDataGrabber fetches anatomical and functional images
    from a project, and makes BIDS entities (e.g. subject) available for
    filtering outputs.

    >>> bg = BIDSDataGrabber()
    >>> bg.inputs.base_dir = 'ds005/'
    >>> bg.inputs.subject = '01'
    >>> results = bg.run()
    >>> basename(results.outputs.anat[0]) # doctest: +ALLOW_UNICODE
    'sub-01_T1w.nii.gz'

    >>> basename(results.outputs.func[0]) # doctest: +ALLOW_UNICODE
    'sub-01_task-mixedgamblestask_run-01_bold.nii.gz'


    Dynamically created, user-defined output fields can also be defined to
    return different types of outputs from the same project. All outputs
    are filtered on common entities, which can be explicitly defined as
    infields.

    >>> bg = BIDSDataGrabber(infields = ['subject'], outfields = ['dwi'])
    >>> bg.inputs.base_dir = 'ds005/'
    >>> bg.inputs.subject = '01'
    >>> bg.inputs.output_query['dwi'] = dict(modality='dwi')
    >>> results = bg.run()
    >>> basename(results.outputs.dwi[0]) # doctest: +ALLOW_UNICODE
    'sub-01_dwi.nii.gz'

    """
    input_spec = BIDSDataGrabberInputSpec
    output_spec = DynamicTraitedSpec
    _always_run = True

    def __init__(self, infields=None, outfields=None, **kwargs):
        """
        Parameters
        ----------
        infields : list of str
            Indicates the input fields to be dynamically created

        outfields: list of str
            Indicates output fields to be dynamically created.
            If no matching items, returns Undefined.
        """
        super(BIDSDataGrabber, self).__init__(**kwargs)
        if not have_pybids:
            raise ImportError("The BIDSEventsGrabber interface requires pybids."
                              " Please make sure it is installed.")

        # If outfields is None use anat and func as default
        if outfields is None:
            outfields = ['func', 'anat']
            self.inputs.output_query = {
                "func": {"modality": "func"},
                "anat": {"modality": "anat"}}
        else:
            self.inputs.output_query = {}

        # If infields is None, use all BIDS entities
        if infields is None:
            bids_config = join(dirname(gb.__file__), 'config', 'bids.json')
            bids_config = json.load(open(bids_config, 'r'))
            infields = [i['name'] for i in bids_config['entities']]

        self._infields = infields
        self._outfields = outfields

        # used for mandatory inputs check
        undefined_traits = {}
        for key in infields:
            self.inputs.add_trait(key, traits.Any)
            undefined_traits[key] = Undefined

        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

    def _run_interface(self, runtime):
        return runtime

    def _list_outputs(self):
        layout = gb.BIDSLayout(self.inputs.base_dir)

        for key in self._outfields:
            if key not in self.inputs.output_query:
                raise ValueError("Define query for all outputs")

        # If infield is not given nm input value, silently ignore
        filters = {}
        for key in self._infields:
            value = getattr(self.inputs, key)
            if isdefined(value):
                filters[key] = value

        outputs = {}
        for key, query in self.inputs.output_query.items():
            args = query.copy()
            args.update(filters)
            filelist = layout.get(return_type=self.inputs.return_type,
                                      **args)
            if len(filelist) == 0:
                msg = 'Output key: %s returned no files' % (
                    key)
                if self.inputs.raise_on_empty:
                    raise IOError(msg)
                else:
                    LOGGER.warning(msg)
                    filelist = Undefined

            outputs[key] = filelist
        return outputs
