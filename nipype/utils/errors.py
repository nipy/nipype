# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Errors and exceptions
"""
from __future__ import (print_function, division, unicode_literals,
                        absolute_import)


class MandatoryInputError(ValueError):
    """Raised when one input with the ``mandatory`` metadata set to ``True`` is
    not defined."""
    def __init__(self, inputspec, name):
        classname = inputspec.__class__.__name__
        if classname.endswith('InputSpec'):
            classname = classname[:len('InputSpec')]
        msg = (
            'Interface "{classname}" requires a value for input {name}. '
            'For a list of required inputs, see {classname}.help().').format(
                classname=classname, name=name)
        super(MandatoryInputError, self).__init__(msg)

class MutuallyExclusiveInputError(ValueError):
    """Raised when none or more than one mutually-exclusive inputs are set."""
    def __init__(self, inputspec, name, values_defined=None, name_other=None):
        classname = inputspec.__class__.__name__
        if classname.endswith('InputSpec') and classname != 'InputSpec':
            classname = classname[:-len('InputSpec')]

        if values_defined is not None:
            xor = list(set([name]+ inputspec.traits()[name].xor))
            msg = ('Interface "{classname}" has mutually-exclusive inputs. '
                   'Exactly one of ({xor}) should be set, but {n:d} were set. '
                   'For a list of mutually-exclusive inputs, see '
                   '{classname}.help().').format(classname=classname,
                                                 xor='|'.join(xor),
                                                 n=values_defined)

        else:
            msg = ('Interface "{classname}" has mutually-exclusive inputs. '
                   'Input "{name}" is mutually exclusive with input '
                   '"{name_other}", which is already set').format(
                       classname=classname, name=name, name_other=name_other)
        super(MutuallyExclusiveInputError, self).__init__(msg)

class RequiredInputError(ValueError):
    """Raised when one input requires some other and those or some of
    those are ``Undefined``."""
    def __init__(self, inputspec, name):
        classname = inputspec.__class__.__name__
        if classname.endswith('InputSpec'):
            classname = classname[:-len('InputSpec')]
        requires = inputspec.traits()[name].requires

        msg = ('Interface "{classname}" requires a value for input {name} '
               'because one of ({requires}) is set. For a list of required '
               'inputs, see {classname}.help().').format(
                    classname=classname, name=name,
                    requires=', '.join(requires))
        super(RequiredInputError, self).__init__(msg)
