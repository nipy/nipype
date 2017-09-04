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

from .base import (traits,
                   DynamicTraitedSpec,
                   BaseInterface,
                   isdefined,
                   Str,
                   Undefined)

try:
    from bids.grabbids import BIDSLayout
except ImportError:
    have_pybids = False
else:
    have_pybids = True


class BIDSDataGrabberInputSpec(DynamicTraitedSpec):
    base_dir = traits.Directory(exists=True,
                                desc='Path to BIDS Directory.',
                                mandatory=True)
    output_query = traits.Dict(key_trait=Str,
                               value_trait=traits.Dict,
                               desc='Queries for outfield outputs')
    return_type = traits.Enum('filename', 'namedtuple', usedefault=True)


class BIDSDataGrabber(BaseInterface):

    """ BIDS datagrabber module that wraps around pybids to allow arbitrary
        querying of BIDS datasets.

        Examples
        --------

        >>> from nipype.interfaces.bids import BIDSDataGrabber
        >>> from os.path import basename
        >>> import pprint

        Select all files from a BIDS project

        >>> bg = BIDSDataGrabber()
        >>> bg.inputs.base_dir = 'ds005/'
        >>> results = bg.run()
        >>> len(results.outputs.outfield) # doctest: +ALLOW_UNICODE
        116

        Using dynamically created, user-defined input fields,
        filter files based on BIDS entities.

        >>> bg = BIDSDataGrabber(infields = ['subject', 'run'])
        >>> bg.inputs.base_dir = 'ds005/'
        >>> bg.inputs.subject = '01'
        >>> bg.inputs.run = '01'
        >>> results = bg.run()
        >>> basename(results.outputs.outfield[0]) # doctest: +ALLOW_UNICODE
        'sub-01_task-mixedgamblestask_run-01_bold.nii.gz'

        Using user-defined output fields, return different types of outputs,
        filtered on common entities
        filter files based on BIDS entities.

        >>> bg = BIDSDataGrabber(infields = ['subject'], outfields = ['func', 'anat'])
        >>> bg.inputs.base_dir = 'ds005/'
        >>> bg.inputs.subject = '01'
        >>> bg.inputs.output_query['func'] = dict(modality='func')
        >>> bg.inputs.output_query['anat'] = dict(modality='anat')
        >>> results = bg.run()
        >>> basename(results.outputs.func[0]) # doctest: +ALLOW_UNICODE
        'sub-01_task-mixedgamblestask_run-01_bold.nii.gz'

        >>> basename(results.outputs.anat[0]) # doctest: +ALLOW_UNICODE
        'sub-01_T1w.nii.gz'
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
            Indicates output fields to be dynamically created

        """
        if not outfields:
            outfields = []
        if not infields:
            infields = []

        super(BIDSDataGrabber, self).__init__(**kwargs)
        undefined_traits = {}
        # used for mandatory inputs check
        self._infields = infields
        self._outfields = outfields
        for key in infields:
            self.inputs.add_trait(key, traits.Any)
            undefined_traits[key] = Undefined

        if not isdefined(self.inputs.output_query):
            self.inputs.output_query = {}

        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

    def _run_interface(self, runtime):
        if not have_pybids:
            raise ImportError("The BIDSEventsGrabber interface requires pybids."
                              " Please make sure it is installed.")
        return runtime

    def _list_outputs(self):
        if not self._outfields:
            self._outfields = ['outfield']
            self.inputs.output_query = {'outfield' : {}}
        else:
            for key in self._outfields:
                if key not in self.inputs.output_query:
                    raise ValueError("Define query for all outputs")

        for key in self._infields:
            value = getattr(self.inputs, key)
            if not isdefined(value):
                msg = "%s requires a value for input '%s' because" \
                      " it was listed in 'infields'" % \
                    (self.__class__.__name__, key)
                raise ValueError(msg)

        layout = BIDSLayout(self.inputs.base_dir)

        filters = {i: getattr(self.inputs, i) for i in self._infields}

        outputs = {}
        for key, query in self.inputs.output_query.items():
            outputs[key] = layout.get(
                **dict(query.items() | filters.items()),
                return_type='file')
        return outputs
