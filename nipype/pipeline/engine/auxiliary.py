import pdb
import inspect
from ... import config, logging
logger = logging.getLogger('nipype.workflow')


# dj: might create a new class or move to State

# Function to change user provided mapper to "reverse polish notation" used in State
def mapper2rpn(mapper, wf_mappers=None):
    """ Functions that translate mapper to "reverse polish notation."""
    output_mapper = []
    _ordering(mapper, i=0, output_mapper=output_mapper, wf_mappers=wf_mappers)
    return output_mapper


def _ordering(el, i, output_mapper, current_sign=None, wf_mappers=None):
    """ Used in the mapper2rpn to get a proper order of fields and signs. """
    if type(el) is tuple:
        # checking if the mapper dont contain mapper from previous nodes, i.e. has str "_NA", etc.
        if type(el[0]) is str and el[0].startswith("_"):
            node_nm = el[0][1:]
            if node_nm not in wf_mappers:
                raise Exception("can't ask for mapper from {}".format(node_nm))
            mapper_mod = change_mapper(mapper=wf_mappers[node_nm], name=node_nm)
            el = (mapper_mod, el[1])
        if type(el[1]) is str and el[1].startswith("_"):
            node_nm = el[1][1:]
            if node_nm not in wf_mappers:
                raise Exception("can't ask for mapper from {}".format(node_nm))
            mapper_mod = change_mapper(mapper=wf_mappers[node_nm], name=node_nm)
            el = (el[0], mapper_mod)
        _iterate_list(el, ".", wf_mappers, output_mapper=output_mapper)
    elif type(el) is list:
        if type(el[0]) is str and el[0].startswith("_"):
            node_nm = el[0][1:]
            if node_nm not in wf_mappers:
                raise Exception("can't ask for mapper from {}".format(node_nm))
            mapper_mod = change_mapper(mapper=wf_mappers[node_nm], name=node_nm)
            el[0] = mapper_mod
        if type(el[1]) is str and el[1].startswith("_"):
            node_nm = el[1][1:]
            if node_nm not in wf_mappers:
                raise Exception("can't ask for mapper from {}".format(node_nm))
            mapper_mod = change_mapper(mapper=wf_mappers[node_nm], name=node_nm)
            el[1] = mapper_mod
        _iterate_list(el, "*", wf_mappers, output_mapper=output_mapper)
    elif type(el) is str:
        output_mapper.append(el)
    else:
        raise Exception("mapper has to be a string, a tuple or a list")
    
    if i > 0:
        output_mapper.append(current_sign)


def _iterate_list(element, sign, wf_mappers, output_mapper):
    """ Used in the mapper2rpn to get recursion. """
    for i, el in enumerate(element):
        _ordering(el, i, current_sign=sign, wf_mappers=wf_mappers, output_mapper=output_mapper)


# functions used in State to know which element should be used for a specific axis

def mapping_axis(state_inputs, mapper_rpn):
    """Having inputs and mapper (in rpn notation), functions returns the axes of output for every input."""
    axis_for_input = {}
    stack = []
    current_axis = None
    current_shape = None

    for el in mapper_rpn:
        if el == ".":
            right = stack.pop()
            left = stack.pop()
            if left == "OUT":
                if state_inputs[right].shape == current_shape: #todo:should we allow for one-element array? 
                    axis_for_input[right] = current_axis
                else:
                    raise Exception("arrays for scalar operations should have the same size")

            elif right == "OUT":
                if state_inputs[left].shape == current_shape:
                    axis_for_input[left] = current_axis
                else:
                    raise Exception("arrays for scalar operations should have the same size")

            else:
                if state_inputs[right].shape == state_inputs[left].shape:
                    current_axis = list(range(state_inputs[right].ndim))
                    current_shape = state_inputs[left].shape
                    axis_for_input[left] = current_axis
                    axis_for_input[right] = current_axis
                else:
                    raise Exception("arrays for scalar operations should have the same size")
                
            stack.append("OUT")

        elif el == "*":
            right = stack.pop()
            left = stack.pop()
            if left == "OUT":
                axis_for_input[right] = [i + 1 + current_axis[-1]
                                         for i in range(state_inputs[right].ndim)]
                current_axis = current_axis + axis_for_input[right]
                current_shape = tuple([i for i in current_shape + state_inputs[right].shape])
            elif right == "OUT":
                for key in axis_for_input:
                    axis_for_input[key] = [i + state_inputs[left].ndim
                                           for i in axis_for_input[key]]

                axis_for_input[left] = [i - len(current_shape) + current_axis[-1] + 1
                                        for i in range(state_inputs[left].ndim)]
                current_axis = current_axis + [i + 1 + current_axis[-1]
                                               for i in range(state_inputs[left].ndim)]
                current_shape = tuple([i for i in state_inputs[left].shape + current_shape])
            else:
                axis_for_input[left] = list(range(state_inputs[left].ndim))
                axis_for_input[right] = [i + state_inputs[left].ndim
                                         for i in range(state_inputs[right].ndim)]
                current_axis = axis_for_input[left] + axis_for_input[right]
                current_shape = tuple([i for i in 
                                       state_inputs[left].shape + state_inputs[right].shape])
            stack.append("OUT")

        else:
            stack.append(el)

    if len(stack) == 0:
        pass
    elif len(stack) > 1:
        raise Exception("exception from mapping_axis")
    elif stack[0] != "OUT":
        current_axis = [i for i in range(state_inputs[stack[0]].ndim)]
        axis_for_input[stack[0]] = current_axis

    if current_axis:
        ndim = max(current_axis) + 1
    else:
        ndim = 0
    return axis_for_input, ndim


def converting_axis2input(state_inputs, axis_for_input, ndim):
    """ Having axes for all the input fields, the function returns fields for each axis. """
    input_for_axis = []
    shape = []
    for i in range(ndim):
        input_for_axis.append([])
        shape.append(0)
        
    for inp, axis in axis_for_input.items():
        for (i, ax) in enumerate(axis):
            input_for_axis[ax].append(inp)
            shape[ax] = state_inputs[inp].shape[i]
            
    return input_for_axis, shape


# used in the Node to change names in a mapper

def change_mapper(mapper, name):
    """changing names of mapper: adding names of the node"""
    if isinstance(mapper, str):
        if "." in mapper or mapper.startswith("_"):
            return mapper
        else:
            return "{}.{}".format(name, mapper)
    elif isinstance(mapper, list):
        return _add_name(mapper, name)
    elif isinstance(mapper, tuple):
        mapper_l = list(mapper)
        return tuple(_add_name(mapper_l, name))


def _add_name(mlist, name):
    for i, elem in enumerate(mlist):
        if isinstance(elem, str):
            if "." in elem or elem.startswith("_"):
                pass
            else:
                mlist[i] = "{}.{}".format(name, mlist[i])
        elif isinstance(elem, list):
            mlist[i] = _add_name(elem, name)
        elif isinstance(elem, tuple):
            mlist[i] = list(elem)
            mlist[i] = _add_name(mlist[i], name)
            mlist[i] = tuple(mlist[i])
    return mlist


#Function interface

class Function_Interface(object):
    """ A new function interface """
    def __init__(self, function, output_nm, input_map=None):
        self.function = function
        if type(output_nm) is list:
            self._output_nm = output_nm
        else:
            raise Exception("output_nm should be a list")
        if not input_map:
            self.input_map = {}
        # TODO use signature
        for key in inspect.getargspec(function)[0]:
            if key not in self.input_map.keys():
                self.input_map[key] = key


    def run(self, input):
        self.output = {}
        if self.input_map:
            for (key_fun, key_inp) in self.input_map.items():
                try:
                    input[key_fun] = input.pop(key_inp)
                except KeyError:
                    raise Exception("no {} in the input dictionary".format(key_inp))
        fun_output = self.function(**input)
        logger.debug("Function Interf, input={}, fun_out={}".format(input, fun_output))
        if type(fun_output) is tuple:
            if len(self._output_nm) == len(fun_output):
                for i, out in enumerate(fun_output):
                    self.output[self._output_nm[i]] = out
            else:
                raise Exception("length of output_nm doesnt match length of the function output")
        elif len(self._output_nm)==1:
            self.output[self._output_nm[0]] = fun_output
        else:
            raise Exception("output_nm doesnt match length of the function output")

        return fun_output


# want to use to access input as dot,
# but it doesnt work since im using "." within names (using my old syntax with - also cant work)
# https://stackoverflow.com/questions/2352181/how-to-use-a-dot-to-access-members-of-dictionary
class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    def __getattr__(self, attr):
        return self.get(attr)
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)
        self.__dict__ = self
