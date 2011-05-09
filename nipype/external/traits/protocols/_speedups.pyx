"""C Speedups for commonly-used operations"""

__all__ = [
    'NO_ADAPTER_NEEDED', 'DOES_NOT_SUPPORT',
    'adapt', 'Protocol__adapt__', 'metamethod', 'classicMRO', 'getMRO',
    'Protocol__call__',
]

cdef extern from "Python.h":
    int PyType_Check(object ob)
    int PyClass_Check(object ob)
    int PyInstance_Check(object ob)
    int PyObject_TypeCheck(object ob, object tp)
    int PyObject_IsInstance(object inst, object cls)
    int PyErr_ExceptionMatches(void *exc)

    void *PyExc_AttributeError
    void *PyObject_GetAttr(object ob, object attr)
    void PyErr_Clear()

    object PyString_InternFromString(char *v)
    object PyMethod_New(object func, object self, object cls)

    ctypedef struct PyTupleObject:
        void *ob_item   # we don't use this, but we can't use 'pass' here

    ctypedef struct PyListObject:
        void *ob_item   # we don't use this, but we can't use 'pass' here

    ctypedef struct PyTypeObject:
        PyTupleObject *tp_mro

    ctypedef struct PyObject:
        PyTypeObject *ob_type

    ctypedef struct PyClassObject:
        PyTupleObject *cl_bases

    ctypedef struct PyInstanceObject:
        PyClassObject *in_class

    int PyObject_IsSubclass(PyClassObject *derived, object cls)
    int PyList_Append(PyListObject *list, object item) except -1
    int PyTuple_GET_SIZE(PyTupleObject *p)
    int PyList_GET_SIZE(PyListObject *p)
    int PyTuple_Check(object op)
    int PyList_Check(object op)

    # These macros return borrowed references, so we make them void *
    # When Pyrex casts them to objects, it will incref them
    void * PyTuple_GET_ITEM(PyTupleObject *p, int pos)
    void * PyList_GET_ITEM(PyListObject *p, int pos)

    PyTypeObject PyInstance_Type
    PyTypeObject PyBaseObject_Type

    void Py_DECREF(PyObject *p)
    object __Pyx_GetExcValue()

cdef object _marker, __conform, __adapt, __mro, __ECType
from sys import exc_info, exc_clear
# Since we can't do "from future import absolute_import", we use __import__
# directly.  Fake the globals dictionary with just the relevant information. In
# an extension module, globals() returns the globals dictionary of the last
# pure Python module that was executing.
AdaptationFailure = __import__(
    'protocols', globals=dict(__name__=__name__, __package__=__package__),
    fromlist=['AdaptationFailure'], level=1
).AdaptationFailure

try:
    from ExtensionClass import ExtensionClass
    __ECType = ExtensionClass
except ImportError:
    __ECType = type

_marker    = object()
__conform  = PyString_InternFromString("__conform__")
__adapt    = PyString_InternFromString("__adapt__")
__class    = PyString_InternFromString("__class__")
__mro      = PyString_InternFromString("__mro__")








# Fundamental Adapters

def NO_ADAPTER_NEEDED(obj, protocol=None):
    """Assume 'obj' implements 'protocol' directly"""
    return obj

def DOES_NOT_SUPPORT(obj, protocol=None):
    """Prevent 'obj' from supporting 'protocol'"""
    return None


cdef class metamethod:
    """Wrapper for metaclass method that might be confused w/instance method"""

    cdef object func

    def __init__(self, func):
        self.func = func

    def __get__(self, ob, typ):
        if ob is None:
            return self
        return PyMethod_New(self.func, ob, typ)

    def __set__(self, ob, value):
        raise AttributeError("Read-only attribute")

    def __delete__(self, ob):
        raise AttributeError("Read-only attribute")












cdef object _adapt(obj, protocol, default, factory):

    # We use nested 'if' blocks here because using 'and' causes Pyrex to
    # convert the return values to Python ints, and then back to booleans!

    cdef object tmp

### This code is superfluous and actually prevents certain old style code (like
### the Python VTK bindings) from working correctly...
###    if PyType_Check(protocol):
###        if PyObject_TypeCheck(obj, protocol):
###            return obj
###
###    if PyClass_Check(protocol):
###        if PyInstance_Check(obj):
###            if PyObject_IsInstance(obj,protocol):
###                return obj

    if PyObject_IsInstance(obj,protocol):
        return obj

    try:
        meth = getattr(obj, __conform)
        try:
            result = meth(protocol)
            if result is not None:
                return result
        except TypeError, e:
            if exc_info()[2].tb_next is not None:
                raise
    except AttributeError, e:
        # Call exc_clear() instead of PyErr_Clear to make sure that the
        # sys.exc_* objects are also removed. This has caused some frames to
        # live too long.
        exc_clear()

    try:
        meth = getattr(protocol, __adapt)
        try:
            result = meth(obj)
            if result is not None:
                return result
        except TypeError:
            if exc_info()[2].tb_next is not None:
                raise
    except AttributeError, e:
        exc_clear()

    if default is _marker:
        if factory is not _marker:
            from warnings import warn
            warn("The 'factory' argument to 'adapt()' will be removed in 1.0",
                DeprecationWarning, 1)
            return factory(obj, protocol)
        raise AdaptationFailure("Can't adapt", obj, protocol)

    return default


def adapt(obj, protocol, default=_marker, factory=_marker):
    """PEP 246-alike: Adapt 'obj' to 'protocol', return 'default'

    If 'default' is not supplied and no implementation is found,
    raise 'AdaptationFailure'."""

    return _adapt(obj,protocol,default,factory)

def Protocol__call__(self, ob, default=_marker):
    """Adapt to this protocol"""
    return _adapt(ob,self,default,_marker)


cdef buildClassicMRO(PyClassObject *cls, PyListObject *list):

    cdef PyTupleObject *bases
    cdef int i

    PyList_Append(list, <object> cls)
    bases = cls.cl_bases

    if bases:
        for i from 0 <= i < PyTuple_GET_SIZE(bases):
            tmp = <object> PyTuple_GET_ITEM(bases, i)
            buildClassicMRO(<PyClassObject *>tmp, list)


def classicMRO(ob, extendedClassic=False):

    if PyClass_Check(ob):
        mro = []
        buildClassicMRO(<PyClassObject *>ob, <PyListObject *>mro)
        if extendedClassic:
            PyList_Append(<PyListObject *>mro, <object> &PyInstance_Type)
            PyList_Append(<PyListObject *>mro, <object> &PyBaseObject_Type)
        return mro

    raise TypeError("Not a classic class", ob)
















cdef buildECMRO(object cls, PyListObject *list):
    PyList_Append(list, cls)
    for i in cls.__bases__:
        buildECMRO(i, list)


def extClassMRO(ob, extendedClassic=False):
    mro = []
    buildECMRO(ob, <PyListObject *>mro)
    if extendedClassic:
        PyList_Append(<PyListObject *>mro, <object> &PyInstance_Type)
        PyList_Append(<PyListObject *>mro, <object> &PyBaseObject_Type)
    return mro



def getMRO(ob, extendedClassic=False):

    if PyClass_Check(ob):
        return classicMRO(ob,extendedClassic)

    elif PyType_Check(ob):
        return ob.__mro__

    elif PyObject_TypeCheck(ob,__ECType):
        return extClassMRO(ob, extendedClassic)

    return ob,













def Protocol__adapt__(self, obj):

    cdef void *tmp
    cdef int i

    if PyInstance_Check(obj):
        cls = <object> ((<PyInstanceObject *>obj).in_class)
    else:
        # We use __class__ instead of type to support proxies
        try:
            cls = getattr(obj, __class)
        except AttributeError:
            # Some object have no __class__; use their type
            cls = <object> (<PyObject *>obj).ob_type

    mro = None
    if PyType_Check(cls):
        # It's a type, we can use its mro directly
        tmp = <void*>((<PyTypeObject *>cls).tp_mro)
        if tmp != NULL:
            mro = <object>tmp

    if mro is None:
        if PyClass_Check(cls):
            # It's a classic class, build up its MRO
            mro = []
            buildClassicMRO(<PyClassObject *>cls, <PyListObject *>mro)
            PyList_Append(<PyListObject *>mro, <object> &PyInstance_Type)
            PyList_Append(<PyListObject *>mro, <object> &PyBaseObject_Type)

        else:
            # Fallback to getting __mro__ (for e.g. security proxies/ExtensionClass)
            try:
                mro = getattr(cls, __mro)
            except Exception:
                # No __mro__?  Is it an ExtensionClass?
                if PyObject_TypeCheck(cls,__ECType):
                    # Yep, toss out the error and compute a reasonable MRO
                    mro = extClassMRO(cls, 1)
                else:
                    raise










    get = self._Protocol__adapters.get

    if PyTuple_Check(mro):
        #print "tuple",mro
        for i from 0 <= i < PyTuple_GET_SIZE(<PyTupleObject *>mro):
            cls = <object> PyTuple_GET_ITEM(<PyTupleObject *>mro, i)
            factory=get(cls)
            if factory is not None:
                return factory[0](obj)

    elif PyList_Check(mro):
        #print "list",mro
        for i from 0 <= i < PyList_GET_SIZE(<PyListObject *>mro):
            cls = <object> PyList_GET_ITEM(<PyListObject *>mro, i)
            factory=get(cls)
            if factory is not None:
                return factory[0](obj)

    else:
        #print "other",mro

        for cls in mro:
            factory=get(cls)
            if factory is not None:
                return factory[0](obj)
















