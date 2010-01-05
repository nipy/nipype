from copy import deepcopy

from nipype.interfaces.base import (Bunch, CommandLine, Interface,
                                    load_template, InterfaceResult)

class IdentityInterface(Interface):
    """Basic interface class generates identity mappings

    Examples
    --------
    
    >>> from nipype.interfaces.base import IdentityInterface
    >>> ii = IdentityInterface(fields=['a','b'])
    >>> ii.inputs.a

    >>> ii.inputs.a = 'foo'
    >>> out = ii.outputs()
    >>> out.a

    >>> out = ii.run()
    >>> out.outputs.a
    'foo'
    
    """
    def __init__(self, fields=None, **inputs):
        """
        """
        self._populate_inputs()
        if fields:
            for f in fields:
                setattr(self.inputs, f, None)
        
    def _populate_inputs(self):
        self.inputs = Bunch()
    
    def get_input_info(self):
        return []

    def outputs(self):
        outputs = Bunch()
        for k,v in self.inputs.iteritems():
            setattr(outputs, k, None)
        return outputs
    
    def aggregate_outputs(self):
        outputs = self.outputs()
        for k,v in self.inputs.iteritems():
            setattr(outputs, k, v)
        return outputs
    
    def run(self, cwd=None):
        """Execute this module.
        """
        runtime = Bunch(returncode=0,
                        stdout=None,
                        stderr=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)
