# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" class mixin and utilities for enabling reports for nipype interfaces """
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import os
from abc import abstractmethod

from ... import logging
from ..base import (
    File, traits, BaseInterface, BaseInterfaceInputSpec, TraitedSpec)

iflogger = logging.getLogger('interface')


class ReportCapableInputSpec(BaseInterfaceInputSpec):
    generate_report = traits.Bool(False, usedefault=True,
                                  desc="Enable report generation")
    out_report = File('report', usedefault=True, hash_files=False,
                      desc='filename for the visual report')


class ReportCapableOutputSpec(TraitedSpec):
    out_report = File(desc='filename for the visual report')


class ReportCapableInterface(BaseInterface):
    """Mixin to enable reporting for Nipype interfaces"""
    _out_report = None

    def _post_run_hook(self, runtime):
        runtime = super(ReportCapableInterface, self)._post_run_hook(runtime)

        # leave early if there's nothing to do
        if not self.inputs.generate_report:
            return runtime

        self._out_report = os.path.abspath(self.inputs.out_report)
        self._generate_report()

        return runtime

    def _list_outputs(self):
        try:
            outputs = super(ReportCapableInterface, self)._list_outputs()
        except NotImplementedError:
            outputs = {}
        if self._out_report is not None:
            outputs['out_report'] = self._out_report
        return outputs

    @abstractmethod
    def _generate_report(self):
        """
        Saves report to file identified by _out_report instance variable
        """
        raise NotImplementedError
