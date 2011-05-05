"""Declaration support for Python built-in types"""

from __future__ import absolute_import

__all__ = ['ProviderMixin']

from types import FunctionType, ModuleType, InstanceType, ClassType

from .protocols import (IImplicationListener, IOpenProvider,
    NO_ADAPTER_NEEDED, advise, updateWithSimplestAdapter, composeAdapters,
    declareAdapterForObject)

from new import instancemethod

from .advice import getMRO, metamethod, mkRef


class ProviderMixin:

    """Mixin to support per-instance declarations"""

    advise(
        instancesProvide=[IOpenProvider, IImplicationListener]
    )

    def declareProvides(self,protocol,adapter=NO_ADAPTER_NEEDED,depth=1):
        registry = self.__dict__.get('__protocols_provided__')
        if registry is None:
            self.__protocols_provided__ = registry = {}
        if updateWithSimplestAdapter(registry,protocol,adapter,depth):
            adapt(protocol,IOpenProtocol).addImplicationListener(self)
            return True

    declareProvides = metamethod(declareProvides)

    def newProtocolImplied(self, srcProto, destProto, adapter, depth):
        registry = self.__dict__.get('__protocols_provided__',())
        if srcProto not in registry:
            return

        baseAdapter, d = registry[srcProto]
        adapter = composeAdapters(baseAdapter,srcProto,adapter)

        declareAdapterForObject(
            destProto, adapter, self, depth+d
        )

    newProtocolImplied = metamethod(newProtocolImplied)

    def __conform__(self,protocol):

        for cls in getMRO(self):
            conf = cls.__dict__.get('__protocols_provided__',())
            if protocol in conf:
                return conf[protocol][0](self)

    __conform__ = metamethod(__conform__)

class conformsRegistry(dict):

    """Helper type for objects and classes that need registration support"""

    def __call__(self, protocol):

        # This only gets called for non-class objects

        if protocol in self:

            subject = self.subject()

            if subject is not None:
                return self[protocol][0](subject)


    def findImplementation(self, subject, protocol, checkSelf=True):

        for cls in getMRO(subject):

            conf = cls.__dict__.get('__conform__')

            if conf is None:
                continue

            if not isinstance(conf,conformsRegistry):
                raise TypeError(
                    "Incompatible __conform__ in base class", conf, cls
                )

            if protocol in conf:
                return conf[protocol][0](subject)


    def newProtocolImplied(self, srcProto, destProto, adapter, depth):

        subject = self.subject()

        if subject is None or srcProto not in self:
            return

        baseAdapter, d = self[srcProto]
        adapter = composeAdapters(baseAdapter,srcProto,adapter)

        declareAdapterForObject(
            destProto, adapter, subject, depth+d
        )


    def __hash__(self):
        # Need this because dictionaries aren't hashable, but we need to
        # be referenceable by a weak-key dictionary
        return id(self)


    def __get__(self,ob,typ=None):
        if ob is not None:
            raise AttributeError(
                "__conform__ registry does not pass to instances"
            )
        # Return a bound method that adds the retrieved-from class to the
        return instancemethod(self.findImplementation, typ, type(typ))

    def __getstate__(self):
        return self.subject(), self.items()

    def __setstate__(self,(subject,items)):
        self.clear()
        self.update(dict(items))
        self.subject = mkRef(subject)


class MiscObjectsAsOpenProvider(object):

    """Supply __conform__ registry for funcs, modules, & classic instances"""

    advise(
        instancesProvide=[IOpenProvider],
        asAdapterForTypes=[
            FunctionType, ModuleType, InstanceType, ClassType, type, object
        ]
    )


    def __init__(self,ob):
        obs = list(getMRO(ob))
        for item in obs:
            try:
                reg = item.__dict__.get('__conform__')
                if reg is None and obs==[ob]:
                    # Make sure we don't obscure a method from the class!
                    reg = getattr(item,'__conform__',None)
            except AttributeError:
                raise TypeError(
                    "Only objects with dictionaries can use this adapter",
                    ob
                )
            if reg is not None and not isinstance(reg,conformsRegistry):
                raise TypeError(
                    "Incompatible __conform__ on adapted object", ob, reg
                )

        reg = ob.__dict__.get('__conform__')

        if reg is None:
            reg = ob.__conform__ = self.newRegistry(ob)

        self.ob = ob
        self.reg = reg


    def declareProvides(self, protocol, adapter=NO_ADAPTER_NEEDED, depth=1):
        if updateWithSimplestAdapter(self.reg, protocol, adapter, depth):
            adapt(protocol,IOpenProtocol).addImplicationListener(self.reg)
            return True

    def newRegistry(self,subject):

        # Create a registry that's also set up for inheriting declarations

        reg = conformsRegistry()
        reg.subject = mkRef(subject)

        return reg

