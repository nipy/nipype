# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Define custom errors
"""

class InterfaceError(Exception):
    """Error raised in nipype interfaces"""
    def __init__(self, value):
        self.value = value
        super(InterfaceError, self).__init__(value)

    def __str__(self):
        return repr(self.value)

class InterfaceInputsError(InterfaceError):
    """Error raised in nipype interfaces"""
    def __init__(self, value):
        self.value = value
        super(InterfaceInputsError, self).__init__(value)

    def __str__(self):
        return repr(self.value)
