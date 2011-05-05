#------------------------------------------------------------------------------
#
#  Copyright (c) 2005, Enthought, Inc.
#  All rights reserved.
#
#  This software is provided without warranty under the terms of the BSD
#  license included in enthought/LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#
#  Author: David C. Morrill
#  Date:   12/06/2005
#
#------------------------------------------------------------------------------

""" Pseudo-package for all of the core symbols from Traits and TraitsUI.
Use this module for importing Traits names into your namespace. For example::

    from traits.api import HasTraits
"""

from __future__ import absolute_import

from .trait_base import Uninitialized, Undefined, Missing, Self, python_version

from .trait_errors import TraitError, TraitNotificationError, DelegationError

from .trait_notifiers import (push_exception_handler, pop_exception_handler,
        TraitChangeNotifyWrapper)

from .category import Category

from .traits import (CTrait, Trait, Property, TraitFactory, Default, Color,
        RGBColor, Font)

from .trait_types import (Any, Generic, Int, Long, Float, Complex, Str, Title,
        Unicode, Bool, CInt, CLong, CFloat, CComplex, CStr, CUnicode, CBool,
        String, Regex, Code, HTML, Password, Callable, This, self, Function,
        Method, Class, Module, Python, ReadOnly, Disallow, missing, Constant,
        Delegate, DelegatesTo, PrototypedFrom, Expression, PythonValue, File,
        Directory, Range, Enum, Tuple, List, CList, Set, CSet, Dict, Instance,
        AdaptedTo, AdaptsTo, Event, Button, ToolbarButton, Either, Type,
        Symbol, WeakRef, Date, Time, false, true, undefined)

from .trait_types import (ListInt, ListFloat, ListStr, ListUnicode,
        ListComplex, ListBool, ListFunction, ListMethod, ListClass,
        ListInstance, ListThis, DictStrAny, DictStrStr, DictStrInt,
        DictStrLong, DictStrFloat, DictStrBool, DictStrList)

from .trait_types import (BaseInt, BaseLong, BaseFloat, BaseComplex, BaseStr,
        BaseUnicode, BaseBool, BaseCInt, BaseCLong, BaseCFloat, BaseCComplex,
        BaseCStr, BaseCUnicode, BaseCBool, BaseFile, BaseDirectory, BaseRange,
        BaseEnum, BaseTuple, BaseInstance)

from .trait_types import UUID

from .has_traits import (method, HasTraits, HasStrictTraits, HasPrivateTraits,
        Interface, SingletonHasTraits, SingletonHasStrictTraits,
        SingletonHasPrivateTraits, MetaHasTraits, Vetoable, VetoableEvent,
        implements, traits_super, on_trait_change, cached_property,
        property_depends_on)

from .trait_handlers import (BaseTraitHandler, TraitType, TraitHandler,
        TraitRange, TraitString, TraitCoerceType, TraitCastType, TraitInstance,
        ThisClass, TraitClass, TraitFunction, TraitEnum, TraitPrefixList,
        TraitMap, TraitPrefixMap, TraitCompound, TraitList, TraitListObject,
        TraitListEvent, TraitSetObject, TraitSetEvent, TraitDict,
        TraitDictObject, TraitDictEvent, TraitTuple, NO_COMPARE,
        OBJECT_IDENTITY_COMPARE, RICH_COMPARE)

from .trait_value import (BaseTraitValue, TraitValue, SyncValue,
        TypeValue, DefaultValue)

from .adapter import Adapter, adapts

from .trait_numeric import Array, CArray

try:
    from . import has_traits as has_traits
    #---------------------------------------------------------------------------
    #  Patch the main traits module with the correct definition for the
    #  ViewElements class:
    #  NOTE: We do this in a try..except block because traits.ui depends on
    #  the pyface module (part of the TraitsGUI package) which may not
    #  necessarily be installed. Not having TraitsGUI means that the 'ui'
    #  features of traits will not work.
    #---------------------------------------------------------------------------

    from traitsui import view_elements
    has_traits.ViewElements = view_elements.ViewElements

    #-------------------------------------------------------------------------------
    #  Patch the main traits module with the correct definition for the
    #  ViewElement and ViewSubElement class:
    #-------------------------------------------------------------------------------

    has_traits.ViewElement = view_elements.ViewElement
except ImportError:
    pass
