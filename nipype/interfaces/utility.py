from copy import deepcopy

import numpy as np

from nipype.interfaces.base import (Bunch, CommandLine, Interface,
                                    load_template, InterfaceResult)

class BasicInterface(Interface):
    """Basic interface class to merge inputs into a single list
    """
    def __init__(self):
        self.inputs = Bunch()
        
    def get_input_info(self):
        return []

    def outputs(self):
        return Bunch()
    
    def run(self):
        """Execute this module.
        """
        runtime = Bunch(returncode=0,
                        stdout=None,
                        stderr=None)
        outputs=self.aggregate_outputs()
        return InterfaceResult(deepcopy(self), runtime, outputs=outputs)

class IdentityInterface(BasicInterface):
    """Basic interface class generates identity mappings

    Examples
    --------
    
    >>> from nipype.interfaces.utility import IdentityInterface
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
        self.inputs = Bunch()
        if fields:
            for f in fields:
                setattr(self.inputs, f, None)
    
    def outputs(self):
        outputs = Bunch()
        for k,v in self.inputs.items():
            setattr(outputs, k, None)
        return outputs
    
    def aggregate_outputs(self):
        outputs = self.outputs()
        for k,v in self.inputs.items():
            setattr(outputs, k, v)
        return outputs

class Merge(BasicInterface):
    """Basic interface class to merge inputs into a single list

    Examples
    --------
    
    >>> from nipype.interfaces.utility import Merge
    >>> mi = Merge(3)
    >>> mi.inputs.in1 = 1
    >>> mi.inputs.in2 = [2,5]
    >>> mi.inputs.in3 = 3
    >>> out = mi.run()
    >>> out.outputs.out
    [1, 2, 5, 3]
    
    """
    def __init__(self, numinputs=0):
        self.inputs = Bunch()
        for i in range(numinputs):
            setattr(self.inputs, 'in%d'%(i+1), None)
        
    def outputs(self):
        return Bunch(out=[])
    
    def aggregate_outputs(self):
        outputs = self.outputs()
        for k,v in self.inputs.items():
            if v:
                if isinstance(v, list):
                    outputs.out.extend(v)
                else:
                    outputs.out.append(v)
        return outputs

class Split(BasicInterface):
    """Basic interface class to split lists into multiple outputs

    Examples
    --------
    
    >>> from nipype.interfaces.utility import Split
    >>> sp = Split()
    >>> sp.inputs.update(inlist=[1,2,3],splits=[2,1])
    >>> out = sp.run()
    >>> out.outputs.out1
    [1, 2]
    
    """
    def __init__(self):
        self.inputs = Bunch(inlist=None,
                            splits=None)
        
    def outputs(self):
        outputs = Bunch()
        if self.inputs.splits:
            for i in range(len(self.inputs.splits)):
                setattr(outputs, 'out%d'%(i+1), [])
        return outputs
    
    def aggregate_outputs(self):
        outputs = self.outputs()
        if self.inputs.splits:
            if sum(self.inputs.splits) != len(self.inputs.inlist):
                raise RuntimeError('sum of splits != num of list elements')
            splits = [0]
            splits.extend(self.inputs.splits)
            splits = np.cumsum(splits)
            for i in range(len(splits)-1):
                setattr(outputs, 'out%d'%(i+1), np.array(self.inputs.inlist)[splits[i]:splits[i+1]].tolist())
        return outputs

class Select(BasicInterface):
    """Basic interface class to select specific elements from a list

    Examples
    --------
    
    >>> from nipype.interfaces.utility import Select
    >>> sl = Select()
    >>> sl.inputs.update(inlist=[1,2,3,4,5],index=[3])
    >>> out = sl.run()
    >>> out.outputs.out
    4
    >>> sl.inputs.update(inlist=[1,2,3,4,5],index=[3,4])
    >>> out = sl.run()
    >>> out.outputs.out
    [4, 5]
    
    """
    def __init__(self):
        self.inputs = Bunch(inlist=None,
                            index=None)
        
    def outputs(self):
        outputs = Bunch(out=None)
        return outputs
    
    def aggregate_outputs(self):
        outputs = self.outputs()
        out = np.array(self.inputs.inlist)[np.array(self.inputs.index)].tolist()
        if len(out) == 1:
            out = out[0]
        outputs.out = out
        return outputs
