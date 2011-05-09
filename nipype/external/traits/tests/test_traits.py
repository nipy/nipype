#------------------------------------------------------------------------------
# Copyright (c) 2005, Enthought, Inc.
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license included in enthought/LICENSE.txt and may be redistributed only
# under the conditions described in the aforementioned license.  The license
# is also available online at http://www.enthought.com/licenses/BSD.txt
# Thanks for using Enthought open source!
#
# Author: David C. Morrill Date: 03/20/2003 Description: Unit Test Case for the
# Traits Package
# ------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

from __future__ import absolute_import

import unittest

from ..api import (Any, CFloat, CInt, CLong, Float, Delegate, HasTraits, Int,
    Long, Trait, TraitError, TraitList, TraitPrefixList, TraitPrefixMap,
    TraitRange, Tuple)

#-------------------------------------------------------------------------------
#  Base unit test classes:
#-------------------------------------------------------------------------------

class BaseTest(object):

    def assign(self, value):
        self.obj.value = value

    def coerce(self, value):
        return value

    def test_assignment(self):
        obj = self.obj

        # Validate default value
        value = self._default_value
        self.assertEqual(obj.value, value)

        # Validate all legal values
        for i, value in enumerate(self._good_values):
            obj.value = value
            self.assertEqual(obj.value, self.coerce(value))

            # If there's a defined
            if i < len(self._mapped_values):
                self.assertEqual(obj.value_, self._mapped_values[i])

        # NOTE:
        #     There is/was some intercation between nosetests and coverage
        #     which causes problems with raising exceptions in Traits
        #     with Python 2.4.  However, I am no longer able to reproduce
        #     the behavior, see:
        #
        #         https://svn.enthought.com/enthought/ticket/1620
        #
        #if 'coverage' in sys.modules:
        #    raise nose.SkipTest("Skipped because coverage module is loaded")

        # Validate correct behavior for illegal values
        for value in self._bad_values:
            self.assertRaises(TraitError, self.assign, value)

class test_base2(unittest.TestCase):

    def indexed_assign(self, list, index, value):
        list[ index ] = value

    def indexed_range_assign(self, list, index1, index2, value):
        list[ index1: index2 ] = value

    # This avoids using a method name that contains 'test' so that this is not
    # called by the tester directly, as nose looks for all tests, regardless of
    # the handler at the bottom of this file.
    def check_values(self, name, default_value, good_values, bad_values,
                   actual_values = None, mapped_values = None):
        obj = self.obj
        try:
            # Make sure the default value is correct:
            msg   = 'default value'
            value = default_value
            self.assertEqual(getattr(obj, name), value)

            # Iterate over all legal values being tested:
            if actual_values is None:
                actual_values = good_values
            msg = 'legal values'
            i   = 0
            for value in good_values:
                setattr(obj, name, value)
                self.assertEqual(getattr(obj, name), actual_values[i])
                if mapped_values is not None:
                    self.assertEqual(getattr(obj, name + '_'),
                                      mapped_values[i])
                i += 1

            # Iterate over all illegal values being tested:
            msg = 'illegal values'
            for value in bad_values:
                self.assertRaises(TraitError, setattr, obj, name, value)
        except:
            print 'Failed while testing %s for value: %s(%s) in %s' % (
                msg, value, value.__class__.__name__, self.__class__.__name__)
            raise

#-------------------------------------------------------------------------------
#  Trait that can have any value:
#-------------------------------------------------------------------------------

class AnyTrait(HasTraits):

    # Trait definitions:
    value = Any

class AnyTraitTest(BaseTest, unittest.TestCase):

    obj = AnyTrait()

    _default_value = None
    _good_values   = [10.0, 'ten', u'ten', [10], {'ten': 10},(10,), None, 1j]
    _mapped_values = []
    _bad_values    = []

#-------------------------------------------------------------------------------
#  Trait that can only have 'int' values:
#-------------------------------------------------------------------------------

class CoercibleIntTrait(HasTraits):

    # Trait definitions:
    value = CInt(99)

class IntTrait(HasTraits):

    # Trait definitions:
    value = Int(99)

class CoercibleIntTest(AnyTraitTest):

    obj = CoercibleIntTrait()

    _default_value = 99
    _good_values   = [10, -10, 10L, -10L, 10.1, -10.1, '10', '-10', u'10',
                      u'-10']
    _bad_values    = ['10L', '-10L', '10.1', '-10.1', u'10L', u'-10L', u'10.1',
                      u'-10.1', 'ten', u'ten', [10], {'ten': 10},(10,), None,
                      1j]

    def coerce(self, value):
        try:
            return int(value)
        except:
            try:
                return int(float(value))
            except:
                return int(long(value))

class IntTest(AnyTraitTest):

    obj = IntTrait()

    _default_value = 99
    _good_values   = [10, -10]
    _bad_values    = ['ten', u'ten', [10], {'ten': 10},(10,), None, 1j, 10L,
                      -10L, 10.1, -10.1, '10L', '-10L', '10.1', '-10.1', u'10L',
                      u'-10L', u'10.1', u'-10.1',  '10', '-10', u'10', u'-10']

    def coerce(self, value):
        try:
            return int(value)
        except:
            try:
                return int(float(value))
            except:
                return int(long(value))

#-------------------------------------------------------------------------------
#  Trait that can only have 'long' values:
#-------------------------------------------------------------------------------

class CoercibleLongTrait(HasTraits):

    # Trait definitions:
    value = CLong(99L)

class LongTrait(HasTraits):

    # Trait definitions:
    value = Long(99L)

class CoercibleLongTest(AnyTraitTest):

    obj = CoercibleLongTrait()

    _default_value = 99L
    _good_values   = [10, -10, 10L, -10L, 10.1, -10.1, '10', '-10', '10L',
                      '-10L', u'10', u'-10', u'10L', u'-10L']
    _bad_values    = ['10.1', '-10.1', u'10.1', u'-10.1', 'ten', u'ten', [10],
                      [10l], {'ten': 10},(10,),(10L,), None, 1j]

    def coerce(self, value):
        try:
            return long(value)
        except:
            return long(float(value))

class LongTest(AnyTraitTest):

    obj = LongTrait()

    _default_value = 99L
    _good_values   = [10, -10, 10L, -10L]
    _bad_values    = ['ten', u'ten', [10], [10l], {'ten': 10},(10,),(10L,),
                      None, 1j, 10.1, -10.1, '10', '-10', '10L', '-10L', '10.1',
                      '-10.1', u'10', u'-10', u'10L', u'-10L', u'10.1',
                      u'-10.1']

    def coerce(self, value):
        try:
            return long(value)
        except:
            return long(float(value))


#-------------------------------------------------------------------------------
#  Trait that can only have 'float' values:
#-------------------------------------------------------------------------------

class CoercibleFloatTrait(HasTraits):

    # Trait definitions:
    value = CFloat(99.0)

class FloatTrait(HasTraits):

    # Trait definitions:
    value = Float(99.0)

class CoercibleFloatTest(AnyTraitTest):

    obj = CoercibleFloatTrait()

    _default_value = 99.0
    _good_values   = [10, -10, 10L, -10L, 10.1, -10.1, '10', '-10', '10.1',
                      '-10.1', u'10', u'-10', u'10.1', u'-10.1']
    _bad_values    = ['10L', '-10L', u'10L', u'-10L', 'ten', u'ten', [10],
                      {'ten': 10},(10,), None, 1j]

    def coerce(self, value):
        try:
            return float(value)
        except:
            return float(long(value))

class FloatTest(AnyTraitTest):

    obj = FloatTrait()

    _default_value = 99.0
    _good_values   = [10, -10, 10.1, -10.1]
    _bad_values    = [10L, -10L, 'ten', u'ten', [10], {'ten': 10},(10,), None,
                      1j, '10', '-10', '10L', '-10L', '10.1', '-10.1', u'10',
                      u'-10', u'10L', u'-10L', u'10.1', u'-10.1']

    def coerce(self, value):
        try:
            return float(value)
        except:
            return float(long(value))

#-------------------------------------------------------------------------------
#  Trait that can only have 'complex'(i.e. imaginary) values:
#-------------------------------------------------------------------------------

class ImaginaryValueTrait(HasTraits):

    # Trait definitions:
    value = Trait(99.0-99.0j)

class ImaginaryValueTest(AnyTraitTest):

    obj = ImaginaryValueTrait()

    _default_value = 99.0-99.0j
    _good_values   = [10, -10, 10L, -10L, 10.1, -10.1, '10', '-10', '10.1',
                      '-10.1', 10j, 10+10j, 10-10j, 10.1j, 10.1+10.1j,
                      10.1-10.1j, '10j', '10+10j', '10-10j']
    _bad_values    = [u'10L', u'-10L', 'ten', [10], {'ten': 10},(10,), None]

    def coerce(self, value):
        try:
            return complex(value)
        except:
            return complex(long(value))

#-------------------------------------------------------------------------------
#  Trait that can only have 'string' values:
#-------------------------------------------------------------------------------

class StringTrait(HasTraits):

    # Trait definitions:
    value = Trait('string')

class StringTest(AnyTraitTest):

    obj = StringTrait()

    _default_value = 'string'
    _good_values   = [10, -10, 10L, -10L, 10.1, -10.1, '10', '-10', '10L',
                      '-10L', '10.1', '-10.1', 'string', u'string', 1j, [10],
                      ['ten'],{'ten': 10},(10,), None]
    _bad_values    = []

    def coerce(self, value):
        return str(value)

#-------------------------------------------------------------------------------
#  Trait that can only have 'unicode' values:
#-------------------------------------------------------------------------------

class UnicodeTrait(HasTraits):

    # Trait definitions:
    value = Trait(u'unicode')

class UnicodeTest(StringTest):

    obj = UnicodeTrait()

    _default_value = u'unicode'
    _good_values   = [10, -10, 10L, -10L, 10.1, -10.1, '10', '-10', '10L',
                      '-10L', '10.1', '-10.1', '', u'', 'string', u'string', 1j,
                       [10], ['ten'], [u'ten'], {'ten': 10},(10,), None]
    _bad_values    = []

    def coerce(self, value):
        return str(value)

#-------------------------------------------------------------------------------
#  Trait that can only have an 'enumerated list' values:
#-------------------------------------------------------------------------------

class EnumTrait(HasTraits):

    # Trait definitions:
    value = Trait([1, 'one', 2, 'two', 3, 'three', 4.4, u'four.four'])

class EnumTest(AnyTraitTest):

    obj = EnumTrait()

    _default_value = 1
    _good_values   = [1, 'one', 2, 'two', 3, 'three', 4.4, u'four.four']
    _bad_values    = [0, 'zero', 4, None]

#-------------------------------------------------------------------------------
#  Trait that can only have a 'mapped' values:
#-------------------------------------------------------------------------------

class MappedTrait(HasTraits):

    # Trait definitions:
    value = Trait('one', {'one': 1, 'two': 2, 'three': 3})

class MappedTest(AnyTraitTest):

    obj = MappedTrait()

    _default_value = 'one'
    _good_values   = ['one', 'two', 'three']
    _mapped_values = [1, 2, 3]
    _bad_values    = ['four', 1, 2, 3, [1],(1,), {1: 1}, None]

#-------------------------------------------------------------------------------
#  Trait that must be a unique prefix of an enumerated list of values:
#-------------------------------------------------------------------------------

class PrefixListTrait(HasTraits):

    # Trait definitions:
    value = Trait('one', TraitPrefixList('one', 'two', 'three'))

class PrefixListTest(AnyTraitTest):

    obj = PrefixListTrait()

    _default_value = 'one'
    _good_values   = ['o', 'on', 'one', 'tw', 'two', 'th', 'thr', 'thre',
                      'three']
    _bad_values    = ['t', 'one ', ' two', 1, None]

    def coerce(self, value):
        return {'o': 'one', 'on': 'one', 'tw': 'two', 'th': 'three'}[value[:2]]

#-------------------------------------------------------------------------------
#  Trait that must be a unique prefix of a mapped set of values:
#-------------------------------------------------------------------------------

class PrefixMapTrait(HasTraits):

    # Trait definitions:
    value = Trait('one', TraitPrefixMap({'one': 1, 'two': 2, 'three': 3}))

class PrefixMapTest(AnyTraitTest):

    obj = PrefixMapTrait()

    _default_value = 'one'
    _good_values   = ['o', 'on', 'one', 'tw', 'two', 'th', 'thr', 'thre',
                      'three']
    _mapped_values = [1, 1, 1, 2, 2, 3, 3, 3]
    _bad_values    = ['t', 'one ', ' two', 1, None]

    def coerce(self, value):
        return {'o': 'one', 'on': 'one', 'tw': 'two', 'th': 'three'}[value[:2]]

#-------------------------------------------------------------------------------
#  Trait that must be within a specified integer range:
#-------------------------------------------------------------------------------

class IntRangeTrait(HasTraits):

    # Trait definitions:
    value = Trait(3, TraitRange(2, 5))

class IntRangeTest(AnyTraitTest):

    obj = IntRangeTrait()

    _default_value = 3
    _good_values   = [2, 3, 4, 5]
    _bad_values    = [0, 1, 6, 0.999, 6.01, 'two', '0.999', '6.01', None]

    def coerce(self, value):
        try:
            return int(value)
        except:
            try:
                return int(float(value))
            except:
                return int(long(value))

#-------------------------------------------------------------------------------
#  Trait that must be within a specified float range:
#-------------------------------------------------------------------------------

class FloatRangeTrait(HasTraits):

    # Trait definitions:
    value = Trait(3.0, TraitRange(2.0, 5.0))

class FloatRangeTest(AnyTraitTest):

    obj = FloatRangeTrait()

    _default_value = 3.0
    _good_values   = [2.0, 3.0, 4.0, 5.0, 2.001, 4.999]
    _bad_values    = [0, 1, 6, 0L, 1L, 6L, 1.999, 6.01, 'two', '0.999', '6.01',
                      None]

    def coerce(self, value):
        try:
            return float(value)
        except:
            return float(long(value))

#-------------------------------------------------------------------------------
#  Trait that must be an instance of a particular class(or subclass):
#-------------------------------------------------------------------------------

# Old style class version:
class OTraitTest1:                pass
class OTraitTest2(OTraitTest1): pass
class OTraitTest3(OTraitTest2): pass
class OBadTraitTest:              pass

otrait_test1 = OTraitTest1()

class OldInstanceTrait(HasTraits):

    # Trait definitions:
    value = Trait(otrait_test1)

class OldInstanceTest(AnyTraitTest):

    # Trait definitions:
    obj = OldInstanceTrait()

    _default_value = otrait_test1
    _good_values   = [otrait_test1, OTraitTest1(), OTraitTest2(),
                      OTraitTest3(), None]
    _bad_values    = [0, 0L, 0.0, 0j, OTraitTest1, OTraitTest2, OBadTraitTest(),
                      'string', u'string', [otrait_test1],(otrait_test1,),
                      {'data': otrait_test1}]

# New style class version:
class NTraitTest1(object):      pass
class NTraitTest2(NTraitTest1): pass
class NTraitTest3(NTraitTest2): pass
class NBadTraitTest:            pass

ntrait_test1 = NTraitTest1()

class NewInstanceTrait(HasTraits):

    # Trait definitions:
    value = Trait(ntrait_test1)

class NewInstanceTest(AnyTraitTest):

    obj = NewInstanceTrait()

    _default_value = ntrait_test1
    _good_values   = [ntrait_test1, NTraitTest1(), NTraitTest2(), NTraitTest3(),
                      None]
    _bad_values    = [0, 0L, 0.0, 0j, NTraitTest1, NTraitTest2, NBadTraitTest(),
                      'string', u'string', [ntrait_test1],(ntrait_test1,),
                      {'data': ntrait_test1}]

#-------------------------------------------------------------------------------
#  Trait(using a function) that must be an odd integer:
#-------------------------------------------------------------------------------

def odd_integer(object, name, value):
    try:
       float(value)
       if(value % 2) == 1:
          return int(value)
    except:
        pass
    raise TraitError

class OddIntegerTrait(HasTraits):

    # Trait definitions:
    value = Trait(99, odd_integer)

class OddIntegerTest(AnyTraitTest):

    obj = OddIntegerTrait()

    _default_value = 99
    _good_values   = [  1,   3,   5,   7,   9,  999999999,
                        1L,  3L,  5L,  7L,  9L,  999999999L,
                        1.0, 3.0, 5.0, 7.0, 9.0, 999999999.0,
                       -1,  -3,  -5,  -7,  -9, -999999999,
                       -1L, -3L, -5L, -7L, -9L, -999999999L,
                        -1.0, -3.0, -5.0, -7.0, -9.0, -999999999.0 ]
    _bad_values    = [0, 2, -2, 1j, None, '1', [1],(1,), {1: 1}]

#-------------------------------------------------------------------------------
#  Trait that has various notifiers attached:
#-------------------------------------------------------------------------------

class NotifierTraits(HasTraits):

    # Trait definitions:
    value1       = Int
    value2       = Int
    value1_count = Int
    value2_count = Int

    def _anytrait_changed(self, trait_name, old, new):
        if trait_name == 'value1':
            self.value1_count += 1
        elif trait_name == 'value2':
            self.value2_count += 1

    def _value1_changed(self, old, new):
        self.value1_count += 1

    def _value2_changed(self, old, new):
        self.value2_count += 1

class NotifierTests(unittest.TestCase):

    obj = NotifierTraits()

    def __init__(self, value):
        unittest.TestCase.__init__(self, value)

    def setUp(self):
        obj = self.obj
        obj.value1       = 0
        obj.value2       = 0
        obj.value1_count = 0
        obj.value2_count = 0

    def tearDown(self):
        obj = self.obj
        obj.on_trait_change(self.on_value1_changed, 'value1', remove = True)
        obj.on_trait_change(self.on_value2_changed, 'value2', remove = True)
        obj.on_trait_change(self.on_anytrait_changed,         remove = True)

    def on_anytrait_changed(self, object, trait_name, old, new):
        if trait_name == 'value1':
           self.obj.value1_count += 1
        elif trait_name == 'value2':
           self.obj.value2_count += 1

    def on_value1_changed(self):
        self.obj.value1_count += 1

    def on_value2_changed(self):
        self.obj.value2_count += 1

    def test_simple(self):
        obj = self.obj

        obj.value1 = 1
        self.assertEqual(obj.value1_count, 2)
        self.assertEqual(obj.value2_count, 0)

        obj.value2 = 1
        self.assertEqual(obj.value1_count, 2)
        self.assertEqual(obj.value2_count, 2)

    def test_complex(self):
        obj = self.obj

        obj.on_trait_change(self.on_value1_changed, 'value1')
        obj.value1 = 1
        self.assertEqual(obj.value1_count, 3)
        self.assertEqual(obj.value2_count, 0)

        obj.on_trait_change(self.on_value2_changed, 'value2')
        obj.value2 = 1
        self.assertEqual(obj.value1_count, 3)
        self.assertEqual(obj.value2_count, 3)

        obj.on_trait_change(self.on_anytrait_changed)

        obj.value1 = 2
        self.assertEqual(obj.value1_count, 7)
        self.assertEqual(obj.value2_count, 3)

        obj.value1 = 2
        self.assertEqual(obj.value1_count, 7)
        self.assertEqual(obj.value2_count, 3)

        obj.value2 = 2
        self.assertEqual(obj.value1_count, 7)
        self.assertEqual(obj.value2_count, 7)

        obj.on_trait_change(self.on_value1_changed, 'value1', remove = True)
        obj.value1 = 3
        self.assertEqual(obj.value1_count, 10)
        self.assertEqual(obj.value2_count, 7)

        obj.on_trait_change(self.on_value2_changed, 'value2', remove = True)
        obj.value2 = 3
        self.assertEqual(obj.value1_count, 10)
        self.assertEqual(obj.value2_count, 10)

        obj.on_trait_change(self.on_anytrait_changed, remove = True)

        obj.value1 = 4
        self.assertEqual(obj.value1_count, 12)
        self.assertEqual(obj.value2_count, 10)

        obj.value2 = 4
        self.assertEqual(obj.value1_count, 12)
        self.assertEqual(obj.value2_count, 12)

#-------------------------------------------------------------------------------
#  Trait that uses delegation:
#-------------------------------------------------------------------------------

class DelegatedFloatTrait(HasTraits):

    # Trait definitions:
    value = Trait(99.0)

class DelegateTrait(HasTraits):

    # Trait definitions:
    value    = Delegate('delegate')
    delegate = Trait(DelegatedFloatTrait())

class DelegateTrait2(DelegateTrait):

    # Trait definitions:
    delegate = Trait(DelegateTrait())

class DelegateTrait3(DelegateTrait):

    # Trait definitions:
    delegate = Trait(DelegateTrait2())

class DelegateTests(unittest.TestCase):

    def test_delegation(self):
        obj = DelegateTrait3()

        self.assertEqual(obj.value, 99.0)
        parent1 = obj.delegate
        parent2 = parent1.delegate
        parent3 = parent2.delegate
        parent3.value = 3.0
        self.assertEqual(obj.value,     3.0)
        parent2.value = 2.0
        self.assertEqual(obj.value,     2.0)
        self.assertEqual(parent3.value, 3.0)
        parent1.value = 1.0
        self.assertEqual(obj.value,     1.0)
        self.assertEqual(parent2.value, 2.0)
        self.assertEqual(parent3.value, 3.0)
        obj.value = 0.0
        self.assertEqual(obj.value,     0.0)
        self.assertEqual(parent1.value, 1.0)
        self.assertEqual(parent2.value, 2.0)
        self.assertEqual(parent3.value, 3.0)
        del obj.value
        self.assertEqual(obj.value,     1.0)
        del parent1.value
        self.assertEqual(obj.value,     2.0)
        self.assertEqual(parent1.value, 2.0)
        del parent2.value
        self.assertEqual(obj.value,     3.0)
        self.assertEqual(parent1.value, 3.0)
        self.assertEqual(parent2.value, 3.0)
        del parent3.value
        # Uncommenting the following line allows
        # the last assertions to pass. However, this
        # may not be intended behavior, so keeping
        # the line commented.
        #del parent2.value
        self.assertEqual(obj.value,     99.0)
        self.assertEqual(parent1.value, 99.0)
        self.assertEqual(parent2.value, 99.0)
        self.assertEqual(parent3.value, 99.0)

#-------------------------------------------------------------------------------
#  Complex(i.e. 'composite') Traits tests:
#-------------------------------------------------------------------------------

# Make a TraitCompound handler that does not have a fast_validate so we can
# check for a particular regression.
slow = Trait(1, TraitRange(1, 3), TraitRange(-3, -1))
del slow.handler.fast_validate

class complex_value(HasTraits):

    # Trait definitions:
    num1 = Trait(1, TraitRange(1, 5), TraitRange(-5, -1))
    num2 = Trait(1, TraitRange(1, 5),
                     TraitPrefixList('one', 'two', 'three', 'four', 'five'))
    num3 = Trait(1, TraitRange(1, 5),
                     TraitPrefixMap({ 'one':   1, 'two':  2, 'three': 3,
                                       'four': 4, 'five': 5 }))
    num4 = Trait(1, Trait(1, Tuple, slow), 10)
    num5 = Trait(1, 10, Trait(1, Tuple, slow))

class test_complex_value(test_base2):

    # Trait definitions:
    obj = complex_value()

    def test_num1(self):
        self.check_values('num1', 1,
            [ 1, 2, 3, 4, 5, -1, -2, -3, -4, -5 ],
            [ 0, 6, -6, '0', '6', '-6', 0.0, 6.0, -6.0, [ 1 ],(1,),
              { 1: 1 }, None ],
            [ 1, 2, 3, 4, 5, -1, -2, -3, -4, -5 ])

    def test_enum_exceptions(self):
        """ Check that enumerated values can be combined with nested TraitCompound handlers.
        """
        self.check_values('num4', 1,
            [1,2,3,-3,-2,-1, 10, ()],
            [0, 4, 5, -5, -4, 11],
        )
        self.check_values('num5', 1,
            [1,2,3,-3,-2,-1, 10, ()],
            [0, 4, 5, -5, -4, 11],
        )

##     def check_num2(self):
##         self.check_values('num2', 1,
##             [ 1, 2, 3, 4, 5,
##               'one', 'two', 'three', 'four', 'five', 'o', 'on', 'tw',
##               'th', 'thr', 'thre', 'fo', 'fou', 'fi', 'fiv' ],
##             [ 0, 6, '0', '6', 0.0, 6.0, 't', 'f', 'six', [ 1 ],(1,),
##               { 1: 1 }, None ],
##             [ 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 'one', 'two',
##               'three', 'four', 'five', 'one', 'one', 'two', 'three', 'three',
##               'three', 'four', 'four', 'five', 'five' ])

##     def check_num3(self):
##         self.check_values('num3', 1,
##             [ 1, 2, 3, 4, 5,
##               'one', 'two', 'three', 'four', 'five', 'o', 'on', 'tw',
##               'th', 'thr', 'thre', 'fo', 'fou', 'fi', 'fiv' ],
##             [ 0, 6, '0', '6', 0.0, 6.0, 't', 'f', 'six', [ 1 ],(1,),
##               { 1: 1 }, None ],
##             [ 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 'one', 'two',
##               'three', 'four', 'five', 'one', 'one', 'two', 'three', 'three',
##               'three', 'four', 'four', 'five', 'five' ],
##             [ 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5,
##               1, 1, 2, 3, 3, 3, 4, 4, 5, 5 ])

#-------------------------------------------------------------------------------
#  Test traits which are lists:
#-------------------------------------------------------------------------------

class list_value(HasTraits):

    # Trait definitions:
    list1 = Trait([ 2 ], TraitList(Trait([ 1, 2, 3, 4 ]),
                          maxlen = 4))
    list2 = Trait([ 2 ], TraitList(Trait([ 1, 2, 3, 4 ]),
                          minlen = 1, maxlen = 4))

class test_list_value(test_base2):

    obj = list_value()

    def del_range(self, list, index1, index2):
        del list[ index1: index2 ]

    def check_list(self, list):
        self.assertEqual(list, [ 2 ])
        self.assertEqual(len(list), 1)
        list.append(3)
        self.assertEqual(len(list), 2)
        list[1] = 2
        self.assertEqual(list[1], 2)
        self.assertEqual(len(list), 2)
        list[0] = 1
        self.assertEqual(list[0], 1)
        self.assertEqual(len(list), 2)
        self.assertRaises(TraitError, self.indexed_assign, list, 0, 5)
        self.assertRaises(TraitError, list.append, 5)
        self.assertRaises(TraitError, list.extend, [ 1, 2, 3 ])
        list.extend([ 3, 4 ])
        self.assertEqual(list, [ 1 ,2, 3, 4 ])
        self.assertRaises(TraitError, list.append, 1)
        del list[1]
        self.assertEqual(list, [ 1, 3, 4 ])
        del list[0]
        self.assertEqual(list, [ 3, 4 ])
        list[:0] = [ 1, 2 ]
        self.assertEqual(list, [ 1 ,2, 3, 4 ])
        self.assertRaises(TraitError,
                   self.indexed_range_assign, list, 0, 0, [ 1 ])
        del list[0:3]
        self.assertEqual(list, [ 4 ])
        self.assertRaises(TraitError,
                   self.indexed_range_assign, list, 0, 0, [ 4, 5 ])

    def test_list1(self):
        self.check_list(self.obj.list1)

    def test_list2(self):
        self.check_list(self.obj.list2)
        self.assertRaises(TraitError, self.del_range, self.obj.list2, 0, 1)
