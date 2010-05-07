from copy import deepcopy

import numpy as np

from nipype.utils.filemanip import (filename_to_list, list_to_filename)
from nipype.interfaces.base import (traits, TraitedSpec, DynamicTraitedSpec,
                                    Undefined)
from nipype.interfaces.io import IOBase, add_traits

    
class IdentityInterface(IOBase):
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
    input_spec = DynamicTraitedSpec
    output_spec = DynamicTraitedSpec
    
    def __init__(self, fields=None, **inputs):
        super(IdentityInterface, self).__init__(**inputs)
        if fields is None or not fields:
            raise Exception('Identity Interface fields must be a non-empty list')
        self._fields = fields
        add_traits(self.inputs, fields)

    def _add_output_traits(self, base):
        undefined_traits = {}
        for key in self._fields:
            base.add_trait(key, traits.Any)
            undefined_traits[key] = Undefined
        base.trait_set(trait_change_notify=False, **undefined_traits)
        return base

    def _list_outputs(self):
        outputs = self._outputs().get()
        for key in self._fields:
            val = getattr(self.inputs, key)
            if val:
                outputs[key] = val
        return outputs

class MergeOutputSpec(TraitedSpec):
    out = traits.List(desc='Merged output')

class Merge(IOBase):
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
    input_spec = DynamicTraitedSpec
    output_spec = MergeOutputSpec
    
    def __init__(self, numinputs=0, **inputs):
        super(Merge, self).__init__(**inputs)
        add_traits(self.inputs, ['in%d'%(i+1) for i in range(numinputs)])
        
    def _list_outputs(self):
        outputs = self._outputs().get()
        for value in self.inputs.get().values():
            if value:
                if isinstance(value, list):
                    outputs['out'].extend(value)
                else:
                    outputs['out'].append(value)
        return outputs

'''
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

class SubstringMatch(BasicInterface):
    """Basic interface class to match list items containing specific substrings

    Examples
    --------
    
    >>> from nipype.interfaces.utility import SubstringMatch
    >>> match = SubstringMatch()
    >>> match.inputs.update(inlist=['foo', 'goo', 'zoo'], substrings='oo')
    >>> out = match.run()
    >>> out.outputs.out
    ['foo', 'goo', 'zoo']
    >>> match.inputs.update(inlist=['foo', 'goo', 'zoo'], substrings=['foo'])
    >>> out = match.run()
    >>> out.outputs.out
    'foo'
    
    """
    def __init__(self):
        self.inputs = Bunch(inlist=None,
                            substrings=None)
        
    def outputs(self):
        outputs = Bunch(out=None)
        return outputs
    
    def aggregate_outputs(self):
        outputs = self.outputs()
        outputs.out = []
        for val in filename_to_list(self.inputs.inlist):
            match = [val for pat in filename_to_list(self.inputs.substrings) if val.find(pat) >= 0]
            if match:
                outputs.out.append(val)
        if not outputs.out:
            outputs.out = None
        else:
            outputs.out = list_to_filename(outputs.out)
        return outputs
'''
