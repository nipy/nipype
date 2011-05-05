"""Basic Adapters and Adapter Operations"""

from __future__ import absolute_import, generators

__all__ = [
    'NO_ADAPTER_NEEDED','DOES_NOT_SUPPORT', 'Adapter',
    'minimumAdapter', 'composeAdapters', 'updateWithSimplestAdapter',
    'StickyAdapter', 'AdaptationFailure', 'bindAdapter',
    'adapt', 'declareAdapterForType', 'declareAdapterForProtocol',
    'declareAdapterForObject', 'advise', 'declareImplementation',
    'declareAdapter', 'adviseObject',
    'Protocol', 'InterfaceClass', 'Interface', 'AbstractBase',
    'AbstractBaseMeta', 'IAdapterFactory', 'IProtocol',
    'IAdaptingProtocol', 'IOpenProtocol', 'IOpenProvider',
    'IOpenImplementor', 'IImplicationListener', 'Attribute', 'Variation'
]

from types import FunctionType, ClassType, MethodType

try:
    PendingDeprecationWarning
except NameError:
    class PendingDeprecationWarning(Warning):
        'Base class for warnings about features which will be deprecated in the future.'

class AdaptationFailure(NotImplementedError,TypeError):
    """A suitable implementation/adapter could not be found"""

_marker = object()

# Fundamental Adapters

def NO_ADAPTER_NEEDED(obj, protocol=None):
    """Assume 'obj' implements 'protocol' directly"""
    return obj

def DOES_NOT_SUPPORT(obj, protocol=None):
    """Prevent 'obj' from supporting 'protocol'"""
    return None


try:
    from ._speedups import NO_ADAPTER_NEEDED, DOES_NOT_SUPPORT
except ImportError:
    pass


def _getProto(self):
    from warnings import warn
    warn("The 'protocol' attribute of Adapter subclass %s is being used"
        % (self.__class__,), DeprecationWarning, 2)
    return self.__dict__['protocol']

def _setProto(self,proto):
    self.__dict__['protocol'] = proto


class Adapter(object):
    """Convenient base class for adapters"""

    protocol = property(_getProto,_setProto)

    def __init__(self, ob, proto):
        self.subject = ob
        self.protocol = proto


class StickyAdapter(object):
    """Adapter that attaches itself to its subject for repeated use"""

    attachForProtocols = ()
    protocol = property(_getProto,_setProto)

    def __init__(self, ob, proto):
        self.subject = ob
        self.protocol = proto

        # Declare this instance as a per-instance adaptation for the
        # given protocol

        provides = list(self.attachForProtocols)
        if proto is not None and proto not in provides:
            provides.append(proto)

#        from protocols.api import declareAdapter
        declareAdapter(lambda s: self, provides, forObjects=[ob])


# Adapter "arithmetic"

def minimumAdapter(a1,a2,d1=0,d2=0):

    """Shortest route to implementation, 'a1' @ depth 'd1', or 'a2' @ 'd2'?

    Assuming both a1 and a2 are interchangeable adapters (i.e. have the same
    source and destination protocols), return the one which is preferable; that
    is, the one with the shortest implication depth, or, if the depths are
    equal, then the adapter that is composed of the fewest chained adapters.
    If both are the same, then prefer 'NO_ADAPTER_NEEDED', followed by
    anything but 'DOES_NOT_SUPPORT', with 'DOES_NOT_SUPPORT' being least
    preferable.  If there is no unambiguous choice, and 'not a1 is a2',
    TypeError is raised.
    """

    if d1<d2:
        return a1
    elif d2<d1:
        return a2

    if getattr(a1,'__unbound_adapter__',a1) is getattr(a2,'__unbound_adapter__',a2):
        return a1   # don't care which

    a1ct = getattr(a1,'__adapterCount__',1)
    a2ct = getattr(a2,'__adapterCount__',1)

    if a1ct<a2ct:
        return a1
    elif a2ct<a1ct:
        return a2

    if a1 is NO_ADAPTER_NEEDED or a2 is DOES_NOT_SUPPORT:
        return a1

    if a1 is DOES_NOT_SUPPORT or a2 is NO_ADAPTER_NEEDED:
        return a2

    # it's ambiguous
    raise TypeError("Ambiguous adapter choice", a1, a2, d1, d2)

def composeAdapters(baseAdapter, baseProtocol, extendingAdapter):

    """Return the composition of 'baseAdapter'+'extendingAdapter'"""

    if baseAdapter is DOES_NOT_SUPPORT or extendingAdapter is DOES_NOT_SUPPORT:
        # fuhgeddaboudit
        return DOES_NOT_SUPPORT

    if baseAdapter is NO_ADAPTER_NEEDED:
        return extendingAdapter

    if extendingAdapter is NO_ADAPTER_NEEDED:
        return baseAdapter

    def newAdapter(ob):
        ob = baseAdapter(ob)
        if ob is not None:
            return extendingAdapter(ob)

    newAdapter.__adapterCount__ = (
        getattr(extendingAdapter,'__adapterCount__',1)+
        getattr(baseAdapter,'__adapterCount__',1)
    )

    return newAdapter


def bindAdapter(adapter,proto):
    """Backward compatibility: wrap 'adapter' to support old 2-arg signature"""

    maxargs = 2; f = adapter; tries = 10

    while not isinstance(f,FunctionType) and tries:
        if isinstance(f,MethodType):
            maxargs += (f.im_self is not None)
            f = f.im_func
            tries = 10
        elif isinstance(f,(ClassType,type)):
            maxargs += 1
            f = f.__init__
            tries -=1
        else:
            f = f.__call__
            tries -=1

    if isinstance(f,FunctionType):

        from inspect import getargspec
        args, varargs, varkw, defaults = getargspec(f)

        if defaults:
            args = args[:-len(defaults)]

        if len(args)>=maxargs:
            newAdapter = lambda ob: adapter(ob,proto)
            newAdapter.__adapterCount__ = getattr(
                adapter,'__adapterCount__',1
            )
            newAdapter.__unbound_adapter__ = adapter
            if f not in (Adapter.__init__.im_func, StickyAdapter.__init__.im_func):
                from warnings import warn
                warn("Adapter %r to protocol %r needs multiple arguments"
                    % (adapter,proto), PendingDeprecationWarning, 6)
            return newAdapter

    return adapter


def updateWithSimplestAdapter(mapping, key, adapter, depth):

    """Replace 'mapping[key]' w/'adapter' @ 'depth', return true if changed"""

    new = adapter
    old = mapping.get(key)

    if old is not None:
        old, oldDepth = old
        new = minimumAdapter(old,adapter,oldDepth,depth)
        if old is new and depth>=oldDepth:
            return False

    mapping[key] = new, depth
    return True


"""Implement Interfaces and define the interfaces used by the package"""

#import api

from .advice import metamethod, classicMRO, mkRef

#from adapters \
#    import composeAdapters, updateWithSimplestAdapter, NO_ADAPTER_NEEDED, \
#           DOES_NOT_SUPPORT

from types import InstanceType

# Thread locking support:

try:
    from thread import allocate_lock

except ImportError:
    try:
        from dummy_thread import allocate_lock

    except ImportError:
        class allocate_lock(object):
            __slots__ = ()
            def acquire(*args): pass
            def release(*args): pass

# Trivial interface implementation:

class Protocol:

    """Generic protocol w/type-based adapter registry"""

    def __init__(self):
        self.__adapters = {}
        self.__implies = {}
        self.__listeners = None
        self.__lock = allocate_lock()


    def getImpliedProtocols(self):

        # This is messy so it can clean out weakrefs, but this method is only
        # called for declaration activities and is thus not at all
        # speed-critical.  It's more important that we support weak refs to
        # implied protocols, so that dynamically created subset protocols can
        # be garbage collected.

        out = []
        add = out.append

        self.__lock.acquire()   # we might clean out dead weakrefs

        try:
            for k,v in self.__implies.items():
                proto = k()
                if proto is None:
                    del self.__implies[k]
                else:
                    add((proto,v))

            return out

        finally:
            self.__lock.release()


    def addImpliedProtocol(self,proto,adapter=NO_ADAPTER_NEEDED,depth=1):

        self.__lock.acquire()
        try:
            key = mkRef(proto)
            if not updateWithSimplestAdapter(
                self.__implies, key, adapter, depth
            ):
                return self.__implies[key][0]
        finally:
            self.__lock.release()

        # Always register implied protocol with classes, because they should
        # know if we break the implication link between two protocols
        for klass,(baseAdapter,d) in self.__adapters.items():
#            api.declareAdapterForType(
            declareAdapterForType(
                proto,composeAdapters(baseAdapter,self,adapter),klass,depth+d
            )

        if self.__listeners:
            for listener in self.__listeners.keys():    # Must use keys()!
                listener.newProtocolImplied(self, proto, adapter, depth)

        return adapter

    addImpliedProtocol = metamethod(addImpliedProtocol)


    def registerImplementation(self,klass,adapter=NO_ADAPTER_NEEDED,depth=1):

        self.__lock.acquire()
        try:
            if not updateWithSimplestAdapter(
                self.__adapters,klass,adapter,depth
            ):
                return self.__adapters[klass][0]
        finally:
            self.__lock.release()

        if adapter is DOES_NOT_SUPPORT:
            # Don't register non-support with implied protocols, because
            # "X implies Y" and "not X" doesn't imply "not Y".  In effect,
            # explicitly registering DOES_NOT_SUPPORT for a type is just a
            # way to "disinherit" a superclass' claim to support something.
            return adapter

        for proto, (extender,d) in self.getImpliedProtocols():
#            api.declareAdapterForType(
            declareAdapterForType(
                proto, composeAdapters(adapter,self,extender), klass, depth+d
            )

        return adapter

    registerImplementation = metamethod(registerImplementation)

    def registerObject(self, ob, adapter=NO_ADAPTER_NEEDED,depth=1):
        # Object needs to be able to handle registration
#        if api.adapt(ob,IOpenProvider).declareProvides(self,adapter,depth):
        if adapt(ob,IOpenProvider).declareProvides(self,adapter,depth):
            if adapter is DOES_NOT_SUPPORT:
                return  # non-support doesn't imply non-support of implied

            # Handle implied protocols
            for proto, (extender,d) in self.getImpliedProtocols():
#                api.declareAdapterForObject(
                declareAdapterForObject(
                    proto, composeAdapters(adapter,self,extender), ob, depth+d
                )

    registerObject = metamethod(registerObject)

    def __adapt__(self, obj):

        get = self.__adapters.get

        try:
            typ = obj.__class__
        except AttributeError:
            typ = type(obj)

        try:
            mro = typ.__mro__
        except AttributeError:
            # Note: this adds 'InstanceType' and 'object' to end of MRO
            mro = classicMRO(typ,extendedClassic=True)

        for klass in mro:
            factory=get(klass)
            if factory is not None:
                return factory[0](obj)

    try:
        from ._speedups import Protocol__adapt__ as __adapt__
    except ImportError:
        pass
    __adapt__ = metamethod(__adapt__)

    def addImplicationListener(self, listener):
        self.__lock.acquire()

        try:
            if self.__listeners is None:
                from weakref import WeakKeyDictionary
                self.__listeners = WeakKeyDictionary()

            self.__listeners[listener] = 1

        finally:
            self.__lock.release()

    addImplicationListener = metamethod(addImplicationListener)

#    def __call__(self, ob, default=api._marker):
    def __call__(self, ob, default=_marker):
        """Adapt to this protocol"""
#        return api.adapt(ob,self,default)
        return adapt(ob,self,default)


# Use faster __call__ method, if possible
# XXX it could be even faster if the __call__ were in the tp_call slot
# XXX directly, but Pyrex doesn't have a way to do that AFAIK.

try:
    from ._speedups import Protocol__call__
except ImportError:
    pass
else:
    from new import instancemethod
    Protocol.__call__ = instancemethod(Protocol__call__, None, Protocol)


class AbstractBaseMeta(Protocol, type):

    """Metaclass for 'AbstractBase' - a protocol that's also a class

    (Note that this should not be used as an explicit metaclass - always
    subclass from 'AbstractBase' or 'Interface' instead.)
    """

    def __init__(self, __name__, __bases__, __dict__):

        type.__init__(self, __name__, __bases__, __dict__)
        Protocol.__init__(self)

        for b in __bases__:
            if isinstance(b,AbstractBaseMeta) and b.__bases__<>(object,):
                self.addImpliedProtocol(b)


    def __setattr__(self,attr,val):

        # We could probably support changing __bases__, as long as we checked
        # that no bases are *removed*.  But it'd be a pain, since we'd
        # have to do callbacks, remove entries from our __implies registry,
        # etc.  So just punt for now.

        if attr=='__bases__':
            raise TypeError(
                "Can't change interface __bases__", self
            )

        type.__setattr__(self,attr,val)

    __call__ = type.__call__


class AbstractBase(object):
    """Base class for a protocol that's a class"""

    __metaclass__ = AbstractBaseMeta


class InterfaceClass(AbstractBaseMeta):

    """Metaclass for 'Interface' - a non-instantiable protocol

    (Note that this should not be used as an explicit metaclass - always
    subclass from 'AbstractBase' or 'Interface' instead.)
    """

    def __call__(self, *__args, **__kw):
        if self.__init__ is Interface.__init__:
            return Protocol.__call__(self,*__args, **__kw)
        else:
            return type.__call__(self,*__args, **__kw)

    def getBases(self):
        return [
            b for b in self.__bases__
                if isinstance(b,AbstractBaseMeta) and b.__bases__<>(object,)
        ]


class Interface(object):
    __metaclass__ = InterfaceClass


class Variation(Protocol):

    """A variation of a base protocol - "inherits" the base's adapters

    See the 'LocalProtocol' example in the reference manual for more info.
    """


    def __init__(self, baseProtocol, context = None):

        self.baseProtocol = baseProtocol
        self.context = context

        # Note: Protocol is a ``classic'' class, so we don't use super()
        Protocol.__init__(self)

#        api.declareAdapterForProtocol(self,NO_ADAPTER_NEEDED,baseProtocol)
        declareAdapterForProtocol(self,NO_ADAPTER_NEEDED,baseProtocol)


    def __repr__(self):

        if self.context is None:
            return "Variation(%r)" % self.baseProtocol

        return "Variation(%r,%r)" % (self.baseProtocol, self.context)

# Semi-backward compatible 'interface.Attribute'

class Attribute(object):

    """Attribute declaration; should we get rid of this?"""

    def __init__(self,doc,name=None,value=None):
        self.__doc__ = doc
        self.name = name
        self.value = value

    def __get__(self,ob,typ=None):
        if ob is None:
            return self
        if not self.name:
            raise NotImplementedError("Abstract attribute")
        try:
            return ob.__dict__[self.name]
        except KeyError:
            return self.value

    def __set__(self,ob,val):
        if not self.name:
            raise NotImplementedError("Abstract attribute")
        ob.__dict__[self.name] = val

    def __delete__(self,ob):
        if not self.name:
            raise NotImplementedError("Abstract attribute")
        del ob.__dict__[self.name]

    def __repr__(self):
        return "Attribute: %s" % self.__doc__


# Interfaces and adapters for declaring protocol/type/object relationships

class IAdapterFactory(Interface):

    """Callable that can adapt an object to a protocol"""

    def __call__(ob):
        """Return an implementation of protocol for 'ob'"""


class IProtocol(Interface):

    """Object usable as a protocol by 'adapt()'"""

    def __hash__():
        """Protocols must be usable as dictionary keys"""

    def __eq__(other):
        """Protocols must be comparable with == and !="""

    def __ne__(other):
        """Protocols must be comparable with == and !="""


class IAdaptingProtocol(IProtocol):

    """A protocol that potentially knows how to adapt some object to itself"""

    def __adapt__(ob):
        """Return 'ob' adapted to protocol, or 'None'"""


class IConformingObject(Interface):

    """An object that potentially knows how to adapt to a protocol"""

    def __conform__(protocol):
        """Return an implementation of 'protocol' for self, or 'None'"""


class IOpenProvider(Interface):
    """An object that can be told how to adapt to protocols"""

    def declareProvides(protocol, adapter=NO_ADAPTER_NEEDED, depth=1):
        """Register 'adapter' as providing 'protocol' for this object

        Return a true value if the provided adapter is the "shortest path" to
        'protocol' for the object, or false if a shorter path already existed.
        """

class IOpenImplementor(Interface):
    """Object/type that can be told how its instances adapt to protocols"""

    def declareClassImplements(protocol, adapter=NO_ADAPTER_NEEDED, depth=1):
        """Register 'adapter' as implementing 'protocol' for instances"""


class IOpenProtocol(IAdaptingProtocol):
    """A protocol that be told what it implies, and what supports it

    Note that these methods are for the use of the declaration APIs only,
    and you should NEVER call them directly."""

    def addImpliedProtocol(proto, adapter=NO_ADAPTER_NEEDED, depth=1):
        """'adapter' provides conversion from this protocol to 'proto'"""

    def registerImplementation(klass, adapter=NO_ADAPTER_NEEDED, depth=1):
        """'adapter' provides protocol for instances of klass"""

    def registerObject(ob, adapter=NO_ADAPTER_NEEDED, depth=1):
        """'adapter' provides protocol for 'ob' directly"""

    def addImplicationListener(listener):
        """Notify 'listener' whenever protocol has new implied protocol"""


class IImplicationListener(Interface):

    def newProtocolImplied(srcProto, destProto, adapter, depth):
        """'srcProto' now implies 'destProto' via 'adapter' at 'depth'"""


"""Adapter and Declaration API"""

from sys import _getframe, exc_info, modules

from types import ClassType

ClassTypes = ( ClassType, type )

#from adapters \
#    import NO_ADAPTER_NEEDED, DOES_NOT_SUPPORT, AdaptationFailure
#
#from adapters \
#    import bindAdapter

from .advice import addClassAdvisor, getFrameInfo

#from interfaces \
#    import IOpenProtocol, IOpenProvider, IOpenImplementor, Protocol, \
#           InterfaceClass, Interface


def adapt(obj, protocol, default=_marker, factory=_marker):

    """PEP 246-alike: Adapt 'obj' to 'protocol', return 'default'

    If 'default' is not supplied and no implementation is found,
    the result of 'factory(obj,protocol)' is returned.  If 'factory'
    is also not supplied, 'NotImplementedError' is then raised."""

    if isinstance(protocol,ClassTypes) and isinstance(obj,protocol):
        return obj

    try:
        _conform = obj.__conform__
    except AttributeError:
        pass
    else:
        try:
            result = _conform(protocol)
            if result is not None:
                return result
        except TypeError:
            if exc_info()[2].tb_next is not None:
                raise

    try:
        _adapt = protocol.__adapt__
    except AttributeError:
        pass
    else:
        try:
            result = _adapt(obj)
            if result is not None:
                return result
        except TypeError:
            if exc_info()[2].tb_next is not None:
                raise

    if default is _marker:
        if factory is not _marker:
            from warnings import warn
            warn("The 'factory' argument to 'adapt()' will be removed in 1.0",
                DeprecationWarning, 2)
            return factory(obj, protocol)

        raise AdaptationFailure("Can't adapt", obj, protocol)

    return default

try:
    from ._speedups import adapt
except ImportError:
    pass


# Fundamental, explicit interface/adapter declaration API:
#   All declarations should end up passing through these three routines.

def declareAdapterForType(protocol, adapter, typ, depth=1):
    """Declare that 'adapter' adapts instances of 'typ' to 'protocol'"""
    adapter = bindAdapter(adapter,protocol)
    adapter = adapt(protocol, IOpenProtocol).registerImplementation(
        typ, adapter, depth
    )

    oi = adapt(typ, IOpenImplementor, None)

    if oi is not None:
        oi.declareClassImplements(protocol,adapter,depth)


def declareAdapterForProtocol(protocol, adapter, proto, depth=1):
    """Declare that 'adapter' adapts 'proto' to 'protocol'"""
    adapt(protocol, IOpenProtocol)  # src and dest must support IOpenProtocol
    adapt(proto, IOpenProtocol).addImpliedProtocol(protocol, bindAdapter(adapter,protocol), depth)


def declareAdapterForObject(protocol, adapter, ob, depth=1):
    """Declare that 'adapter' adapts 'ob' to 'protocol'"""
    adapt(protocol,IOpenProtocol).registerObject(ob,bindAdapter(adapter,protocol),depth)

# Bootstrap APIs to work with Protocol and InterfaceClass, without needing to
# give Protocol a '__conform__' method that's hardwired to IOpenProtocol.
# Note that InterfaceClass has to be registered first, so that when the
# registration propagates to IAdaptingProtocol and IProtocol, InterfaceClass
# will already be recognized as an IOpenProtocol, preventing infinite regress.

IOpenProtocol.registerImplementation(InterfaceClass)    # VERY BAD!!
IOpenProtocol.registerImplementation(Protocol)          # NEVER DO THIS!!
# From this line forward, the declaration APIs can work.  Use them instead!

# Interface and adapter declarations - convenience forms, explicit targets

def declareAdapter(factory, provides,
    forTypes=(),
    forProtocols=(),
    forObjects=()
):
    """'factory' is an IAdapterFactory providing 'provides' protocols"""

    for protocol in provides:

        for typ in forTypes:
            declareAdapterForType(protocol, factory, typ)

        for proto in forProtocols:
            declareAdapterForProtocol(protocol, factory, proto)

        for ob in forObjects:
            declareAdapterForObject(protocol, factory, ob)


def declareImplementation(typ, instancesProvide=(), instancesDoNotProvide=()):
    """Declare information about a class, type, or 'IOpenImplementor'"""

    for proto in instancesProvide:
        declareAdapterForType(proto, NO_ADAPTER_NEEDED, typ)

    for proto in instancesDoNotProvide:
        declareAdapterForType(proto, DOES_NOT_SUPPORT, typ)


def adviseObject(ob, provides=(), doesNotProvide=()):
    """Tell an object what it does or doesn't provide"""

    for proto in provides:
        declareAdapterForObject(proto, NO_ADAPTER_NEEDED, ob)

    for proto in doesNotProvide:
        declareAdapterForObject(proto, DOES_NOT_SUPPORT, ob)


# And now for the magic function...

def advise(**kw):
    kw = kw.copy()
    frame = _getframe(1)
    kind, module, caller_locals, caller_globals = getFrameInfo(frame)

    if kind=="module":
        moduleProvides = kw.setdefault('moduleProvides',())
        del kw['moduleProvides']

        for k in kw:
            raise TypeError(
                "Invalid keyword argument for advising modules: %s" % k
            )

        adviseObject(module,
            provides=moduleProvides
        )
        return

    elif kind!="class":
        raise SyntaxError(
            "protocols.advise() must be called directly in a class or"
            " module body, not in a function or exec."
        )

    classProvides         = kw.setdefault('classProvides',())
    classDoesNotProvide   = kw.setdefault('classDoesNotProvide',())
    instancesProvide      = kw.setdefault('instancesProvide',())
    instancesDoNotProvide = kw.setdefault('instancesDoNotProvide',())
    asAdapterForTypes     = kw.setdefault('asAdapterForTypes',())
    asAdapterForProtocols = kw.setdefault('asAdapterForProtocols',())
    protocolExtends       = kw.setdefault('protocolExtends',())
    protocolIsSubsetOf    = kw.setdefault('protocolIsSubsetOf',())
    factoryMethod         = kw.setdefault('factoryMethod',None)
    equivalentProtocols   = kw.setdefault('equivalentProtocols',())

    map(kw.__delitem__,"classProvides classDoesNotProvide instancesProvide"
        " instancesDoNotProvide asAdapterForTypes asAdapterForProtocols"
        " protocolExtends protocolIsSubsetOf factoryMethod equivalentProtocols"
        .split())

    for k in kw:
        raise TypeError(
            "Invalid keyword argument for advising classes: %s" % k
        )

    def callback(klass):
        if classProvides or classDoesNotProvide:
            adviseObject(klass,
                provides=classProvides, doesNotProvide=classDoesNotProvide
            )

        if instancesProvide or instancesDoNotProvide:
            declareImplementation(klass,
                instancesProvide=instancesProvide,
                instancesDoNotProvide=instancesDoNotProvide
            )

        if asAdapterForTypes or asAdapterForProtocols:
            if not instancesProvide:
                raise TypeError(
                    "When declaring an adapter, you must specify what"
                    " its instances will provide."
                )
            if factoryMethod:
                factory = getattr(klass,factoryMethod)
            else:
                factory = klass

            declareAdapter(factory, instancesProvide,
                forTypes=asAdapterForTypes, forProtocols=asAdapterForProtocols
            )
        elif factoryMethod:
            raise TypeError(
                "'factoryMethod' is only used when declaring an adapter type"
            )

        if protocolExtends:
            declareAdapter(NO_ADAPTER_NEEDED, protocolExtends,
                forProtocols=[klass]
            )

        if protocolIsSubsetOf:
            declareAdapter(NO_ADAPTER_NEEDED, [klass],
                forProtocols=protocolIsSubsetOf
            )

        if equivalentProtocols:
            declareAdapter(
                NO_ADAPTER_NEEDED, equivalentProtocols, forProtocols=[klass]
            )
            declareAdapter(
                NO_ADAPTER_NEEDED, [klass], forProtocols=equivalentProtocols
            )

        return klass

    addClassAdvisor(callback)
