#-------------------------------------------------------------------------------
#
#  Unit test case for testing HasTraits 'on_trait_change' support.
#
#  Written by: David C. Morrill
#
#  Date: 4/10/2007
#
#  (c) Copyright 2007 by Enthought, Inc.
#
#  This software is provided without warranty under the terms of the BSD
#  license included in /LICENSE.txt and may be redistributed only
#  under the conditions described in the aforementioned license.  The license
#  is also available online at http://www.enthought.com/licenses/BSD.txt
#
#  Thanks for using Enthought open source!
#
#-------------------------------------------------------------------------------


#-------------------------------------------------------------------------------

""" Unit test case for testing HasTraits 'on_trait_change' support.
"""

#-------------------------------------------------------------------------------
#  Imports:
#-------------------------------------------------------------------------------

from __future__ import absolute_import

import unittest

from nose import SkipTest

from ..api import (HasTraits, List, Dict, Int, Str, Any, Instance, Undefined,
        TraitError, TraitListEvent, TraitDictEvent, push_exception_handler,
        on_trait_change, Property, cached_property)

from ..trait_handlers import TraitListObject, TraitDictObject

#-------------------------------------------------------------------------------
#  Test support classes:
#-------------------------------------------------------------------------------

class ArgCheckBase ( HasTraits ):

    value = Int( 0 )
    int1  = Int( 0, test = True )
    int2  = Int( 0 )
    int3  = Int( 0, test = True )
    tint1 = Int( 0 )
    tint2 = Int( 0, test = True )
    tint3 = Int( 0 )

    calls = Int( 0 )
    tc    = Any

class ArgCheckSimple ( ArgCheckBase ):

    def arg_check0 ( self ):
        self.calls += 1

    def arg_check1 ( self, new ):
        self.calls += 1
        self.tc.assertEqual( new, self.value )

    def arg_check2 ( self, name, new ):
        self.calls += 1
        self.tc.assertEqual( name, 'value' )
        self.tc.assertEqual( new, self.value )

    def arg_check3 ( self, object, name, new ):
        self.calls += 1
        self.tc.assert_( object is self )
        self.tc.assertEqual( name, 'value' )
        self.tc.assertEqual( new, self.value )

    def arg_check4 ( self, object, name, old, new ):
        self.calls += 1
        self.tc.assert_( object is self )
        self.tc.assertEqual( name, 'value' )
        self.tc.assertEqual( old, (self.value - 1) )
        self.tc.assertEqual( new, self.value )

class ArgCheckDecorator ( ArgCheckBase ):

    @on_trait_change( 'value' )
    def arg_check0 ( self ):
        self.calls += 1

    @on_trait_change( 'value' )
    def arg_check1 ( self, new ):
        self.calls += 1
        self.tc.assertEqual( new, self.value )

    @on_trait_change( 'value' )
    def arg_check2 ( self, name, new ):
        self.calls += 1
        self.tc.assertEqual( name, 'value' )
        self.tc.assertEqual( new, self.value )

    @on_trait_change( 'value' )
    def arg_check3 ( self, object, name, new ):
        self.calls += 1
        self.tc.assert_( object is self )
        self.tc.assertEqual( name, 'value' )
        self.tc.assertEqual( new, self.value )

    @on_trait_change( 'value' )
    def arg_check4 ( self, object, name, old, new ):
        self.calls += 1
        self.tc.assert_( object is self )
        self.tc.assertEqual( name, 'value' )
        self.tc.assertEqual( old, (self.value - 1) )
        self.tc.assertEqual( new, self.value )

class Instance1 ( HasTraits ):

    ref        = Instance( ArgCheckBase, () )

    calls      = Int( 0 )
    exp_object = Any
    exp_name   = Any
    dst_name   = Any
    exp_old    = Any
    exp_new    = Any
    dst_new    = Any
    tc         = Any

    @on_trait_change( 'ref.value' )
    def arg_check0 ( self ):
        self.calls += 1

    @on_trait_change( 'ref.value' )
    def arg_check1 ( self, new ):
        self.calls += 1
        self.tc.assertEqual( new, self.dst_new )

    @on_trait_change( 'ref.value' )
    def arg_check2 ( self, name, new ):
        self.calls += 1
        self.tc.assertEqual( name, self.dst_name )
        self.tc.assertEqual( new, self.dst_new )

    @on_trait_change( 'ref.value' )
    def arg_check3 ( self, object, name, new ):
        self.calls += 1
        self.tc.assert_( object is self.exp_object )
        self.tc.assertEqual( name, self.exp_name )
        self.tc.assertEqual( new, self.exp_new )

    @on_trait_change( 'ref.value' )
    def arg_check4 ( self, object, name, old, new ):
        self.calls += 1
        self.tc.assert_( object is self.exp_object )
        self.tc.assertEqual( name, self.exp_name )
        self.tc.assertEqual( old, self.exp_old )
        self.tc.assertEqual( new, self.exp_new )

class List1 ( HasTraits ):

    refs       = List( ArgCheckBase )
    calls      = Int( 0 )

    exp_object = Any
    exp_name   = Any
    type_old   = Any
    exp_old    = Any
    type_new   = Any
    exp_new    = Any
    tc         = Any

    @on_trait_change( 'refs.value' )
    def arg_check0 ( self ):
        self.calls += 1

    @on_trait_change( 'refs.value' )
    def arg_check3 ( self, object, name, new ):
        self.calls += 1
        self.tc.assert_( object is self.exp_object )
        self.tc.assertEqual( name, self.exp_name )
        if self.type_new is None:
            self.tc.assertEqual( new, self.exp_new )
        else:
            self.tc.assert_( isinstance( new, self.type_new ) )

    @on_trait_change( 'refs.value' )
    def arg_check4 ( self, object, name, old, new ):
        self.calls += 1
        self.tc.assert_( object is self.exp_object )
        self.tc.assertEqual( name, self.exp_name )
        if self.type_old is None:
            self.tc.assertEqual( old, self.exp_old )
        else:
            self.tc.assert_( isinstance( old, self.type_old ) )
        if self.type_new is None:
            self.tc.assertEqual( new, self.exp_new )
        else:
            self.tc.assert_( isinstance( new, self.type_new ) )

class List2 ( HasTraits ):

    refs    = List( ArgCheckBase )

    calls   = Int( 0 )
    exp_new = Any
    tc      = Any

    @on_trait_change( 'refs.value' )
    def arg_check1 ( self, new ):
        self.calls += 1
        self.tc.assertEqual( new, self.exp_new )

class List3 ( HasTraits ):

    refs     = List( ArgCheckBase )

    calls    = Int( 0 )
    exp_name = Any
    exp_new  = Any
    tc       = Any

    @on_trait_change( 'refs.value' )
    def arg_check2 ( self, name, new ):
        self.calls += 1
        self.tc.assertEqual( name, self.exp_name )
        self.tc.assertEqual( new, self.exp_new )

class Dict1 ( List1 ):

    refs = Dict( Int, ArgCheckBase )

class Dict2 ( HasTraits ):

    refs    = Dict( Int, ArgCheckBase )

    calls   = Int( 0 )
    exp_new = Any
    tc      = Any

    @on_trait_change( 'refs.value' )
    def arg_check1 ( self, new ):
        self.calls += 1
        self.tc.assertEqual( new, self.exp_new )

class Dict3 ( HasTraits ):

    refs     = Dict( Int, ArgCheckBase )

    calls    = Int( 0 )
    exp_name = Any
    exp_new  = Any
    tc       = Any

    @on_trait_change( 'refs.value' )
    def arg_check2 ( self, name, new ):
        self.calls += 1
        self.tc.assertEqual( name, self.exp_name )
        self.tc.assertEqual( new, self.exp_new )

class Complex ( HasTraits ):

    int1       = Int( 0, test = True )
    int2       = Int( 0 )
    int3       = Int( 0, test = True )
    tint1      = Int( 0 )
    tint2      = Int( 0, test = True )
    tint3      = Int( 0 )
    ref        = Instance( ArgCheckBase, () )

    calls      = Int( 0 )
    exp_object = Any
    exp_name   = Any
    dst_name   = Any
    exp_old    = Any
    exp_new    = Any
    dst_new    = Any
    tc         = Any

    def arg_check0 ( self ):
        self.calls += 1

    def arg_check1 ( self, new ):
        self.calls += 1
        self.tc.assertEqual( new, self.exp_new )

    def arg_check2 ( self, name, new ):
        self.calls += 1
        self.tc.assertEqual( name, self.exp_name )
        self.tc.assertEqual( new, self.exp_new )

    def arg_check3 ( self, object, name, new ):
        self.calls += 1
        self.tc.assert_( object is self.exp_object )
        self.tc.assertEqual( name, self.exp_name )
        self.tc.assertEqual( new, self.exp_new )

    def arg_check4 ( self, object, name, old, new ):
        self.calls += 1
        self.tc.assert_( object is self.exp_object )
        self.tc.assertEqual( name, self.exp_name )
        self.tc.assertEqual( old, self.exp_old )
        self.tc.assertEqual( new, self.exp_new )

class Link ( HasTraits ):

    next  = Any
    prev  = Any
    value = Int( 0 )

class LinkTest ( HasTraits ):

    head = Instance( Link )

    calls      = Int( 0 )
    exp_object = Any
    exp_name   = Any
    dst_name   = Any
    exp_old    = Any
    exp_new    = Any
    dst_new    = Any
    tc         = Any

    def arg_check0 ( self ):
        self.calls += 1

    def arg_check1 ( self, new ):
        self.calls += 1
        self.tc.assertEqual( new, self.exp_new )

    def arg_check2 ( self, name, new ):
        self.calls += 1
        self.tc.assertEqual( name, self.exp_name )
        self.tc.assertEqual( new, self.exp_new )

    def arg_check3 ( self, object, name, new ):
        self.calls += 1
        self.tc.assert_( object is self.exp_object )
        self.tc.assertEqual( name, self.exp_name )
        self.tc.assertEqual( new, self.exp_new )

    def arg_check4 ( self, object, name, old, new ):
        self.calls += 1
        self.tc.assert_( object is self.exp_object )
        self.tc.assertEqual( name, self.exp_name )
        self.tc.assertEqual( old, self.exp_old )
        self.tc.assertEqual( new, self.exp_new )

class PropertyDependsOn ( HasTraits ):

    sum     = Property( depends_on = 'ref.[int1,int2,int3]' )
    ref     = Instance( ArgCheckBase, () )

    pcalls  = Int( 0 )
    calls   = Int( 0 )
    exp_old = Any
    exp_new = Any
    tc      = Any

    @cached_property
    def _get_sum ( self ):
        self.pcalls += 1
        r = self.ref
        return (r.int1 + r.int2 + r.int3)

    def _sum_changed ( self, old, new ):
        self.calls += 1
        self.tc.assertEqual( old, self.exp_old )
        self.tc.assertEqual( new, self.exp_new )

#-------------------------------------------------------------------------------
#  'OnTraitChangeTest' unit test class:
#-------------------------------------------------------------------------------

class OnTraitChangeTest ( unittest.TestCase ):

    #-- Unit Test Methods ------------------------------------------------------

    def test_arg_check_simple ( self ):
        ac = ArgCheckSimple( tc = self )
        ac.on_trait_change( ac.arg_check0, 'value' )
        ac.on_trait_change( ac.arg_check1, 'value' )
        ac.on_trait_change( ac.arg_check2, 'value' )
        ac.on_trait_change( ac.arg_check3, 'value' )
        ac.on_trait_change( ac.arg_check4, 'value' )
        for i in range( 3 ):
            ac.value += 1
        self.assert_( ac.calls == (3 * 5) )
        ac.on_trait_change( ac.arg_check0, 'value', remove = True )
        ac.on_trait_change( ac.arg_check1, 'value', remove = True )
        ac.on_trait_change( ac.arg_check2, 'value', remove = True )
        ac.on_trait_change( ac.arg_check3, 'value', remove = True )
        ac.on_trait_change( ac.arg_check4, 'value', remove = True )
        for i in range( 3 ):
            ac.value += 1
        self.assertEqual( ac.calls, (3 * 5) )
        self.assertEqual( ac.value, (2 * 3) )

    def test_arg_check_decorator ( self ):
        ac = ArgCheckDecorator( tc = self )
        for i in range( 3 ):
            ac.value += 1
        self.assertEqual( ac.calls, (3 * 5) )
        self.assertEqual( ac.value, 3 )

    def test_instance1 ( self ):
        i1 = Instance1( tc = self )
        for i in range( 3 ):
            i1.set( exp_object = i1.ref, exp_name = 'value', dst_name = 'value',
                    exp_old = i, exp_new = (i + 1), dst_new = (i + 1) )
            i1.ref.value = (i + 1)
        self.assertEqual( i1.calls, (3 * 5) )
        self.assertEqual( i1.ref.value, 3 )
        ref = ArgCheckBase()
        i1.set( exp_object = i1,     exp_name = 'ref', dst_name = 'value',
                exp_old    = i1.ref, exp_new  = ref,   dst_new  = 0 )
        i1.ref = ref
        self.assertEqual( i1.calls, (4 * 5) )
        self.assertEqual( i1.ref.value, 0 )
        for i in range( 3 ):
            i1.set( exp_object = i1.ref, exp_name = 'value', dst_name = 'value',
                    exp_old = i, exp_new = (i + 1), dst_new = (i + 1) )
            i1.ref.value = (i + 1)
        self.assertEqual( i1.calls, (7 * 5) )
        self.assertEqual( i1.ref.value, 3 )

    def test_list1 ( self ):
        l1 = List1( tc = self )
        for i in range( 3 ):
            ac = ArgCheckBase()
            l1.set( exp_object = l1, exp_name = 'refs_items', type_old = None,
                    exp_old = Undefined, type_new = TraitListEvent )
            l1.refs.append( ac )
        #self.assertEqual( l1.calls, (3 * 3) )  # FIXME
        for i in range( 3 ):
            self.assertEqual( l1.refs[i].value, 0 )
        refs = [ ArgCheckBase(), ArgCheckBase(), ArgCheckBase() ]
        l1.set( exp_object = l1, exp_name = 'refs', type_old = None,
                exp_old = l1.refs, type_new = TraitListObject )
        l1.refs = refs
        #self.assertEqual( l1.calls, (4 * 3) )
        for i in range( 3 ):
            self.assertEqual( l1.refs[i].value, 0 )
        for i in range( 3 ):
            for j in range( 3 ):
                l1.set( exp_object = l1.refs[j], exp_name = 'value',
                    type_old = None, exp_old = i,
                    type_new = None, exp_new = (i + 1) )
                l1.refs[j].value = (i + 1)
        #self.assertEqual( l1.calls, (13 * 3) )
        for i in range( 3 ):
            self.assertEqual( l1.refs[i].value, 3 )

    def test_list2 ( self ):
        self.check_list( List2( tc = self ) )

    def test_list3 ( self ):
        self.check_list( List3( tc = self ) )

    def test_dict1 ( self ):
        d1 = Dict1( tc = self )
        for i in range( 3 ):
            ac = ArgCheckBase()
            d1.set( exp_object = d1, exp_name = 'refs_items', type_old = None,
                    exp_old = Undefined, type_new = TraitDictEvent )
            d1.refs[i] = ac
        #self.assertEqual( d1.calls, (3 * 3) )  # FIXME
        for i in range( 3 ):
            self.assertEqual( d1.refs[i].value, 0 )
        refs = { 0: ArgCheckBase(), 1: ArgCheckBase(), 2: ArgCheckBase() }
        d1.set( exp_object = d1, exp_name = 'refs', type_old = None,
                exp_old = d1.refs, type_new = TraitDictObject )
        d1.refs = refs
        #self.assertEqual( d1.calls, (4 * 3) )
        for i in range( 3 ):
            self.assertEqual( d1.refs[i].value, 0 )
        for i in range( 3 ):
            for j in range( 3 ):
                d1.set( exp_object = d1.refs[j], exp_name = 'value',
                    type_old = None, exp_old = i,
                    type_new = None, exp_new = (i + 1) )
                d1.refs[j].value = (i + 1)
        #self.assertEqual( d1.calls, (13 * 3) )
        for i in range( 3 ):
            self.assertEqual( d1.refs[i].value, 3 )

    def test_dict2 ( self ):
        self.check_dict( Dict2( tc = self ) )

    def test_dict3 ( self ):
        self.check_dict( Dict3( tc = self ) )

    def test_pattern_list1 ( self ):
        c = Complex( tc = self )
        self.check_complex( c, c, 'int1, int2, int3',
                     [ 'int1', 'int2', 'int3' ], [ 'tint1', 'tint2', 'tint3' ] )

    def test_pattern_list2 ( self ):
        c = Complex( tc = self )
        self.check_complex( c, c, [ 'int1', 'int2', 'int3' ],
                     [ 'int1', 'int2', 'int3' ], [ 'tint1', 'tint2', 'tint3' ] )

    def test_pattern_list3 ( self ):
        c = Complex( tc = self )
        self.check_complex( c, c.ref, 'ref.[int1, int2, int3]',
                     [ 'int1', 'int2', 'int3' ], [ 'tint1', 'tint2', 'tint3' ] )

    def test_pattern_list4 ( self ):
        c = Complex( tc = self )
        handlers = [ c.arg_check0, c.arg_check3, c.arg_check4 ]
        n        = len( handlers )
        pattern  = 'ref.[int1,int2,int3]'
        self.multi_register( c, handlers, pattern )
        r0 = c.ref
        r1 = ArgCheckBase()
        c.set( exp_object = c, exp_name = 'ref', exp_old = r0, exp_new = r1 )
        c.ref = r1
        c.set( exp_old = r1, exp_new = r0 )
        c.ref = r0
        self.assertEqual( c.calls, 2 * n )
        self.multi_register( c, handlers, pattern, remove = True )
        c.ref = r1
        c.ref = r0
        self.assertEqual( c.calls, 2 * n )

    def test_pattern_list5 ( self ):
        c = Complex( tc = self )
        c.on_trait_change( c.arg_check1, 'ref.[int1,int2,int3]' )
        self.assertRaises( TraitError, c.set, ref = ArgCheckBase() )

    def test_pattern_list6 ( self ):
        c = Complex( tc = self )
        c.on_trait_change( c.arg_check2, 'ref.[int1,int2,int3]' )
        self.assertRaises( TraitError, c.set, ref = ArgCheckBase() )

    def test_pattern_list7 ( self ):
        c = Complex( tc = self )
        self.check_complex( c, c, '+test', [ 'int1', 'int3', 'tint2' ],
                            [ 'int2', 'tint1', 'tint3' ] )

    def test_pattern_list8 ( self ):
        c = Complex( tc = self )
        self.check_complex( c, c, 'int+test',
                     [ 'int1', 'int3' ], [ 'int2', 'tint1', 'tint2', 'tint3' ] )

    def test_pattern_list9 ( self ):
        c = Complex( tc = self )
        self.check_complex( c, c, 'int-test', [ 'int2' ],
                            [ 'int1', 'int3', 'tint4', 'tint5', 'tint6' ] )

    def test_pattern_list10 ( self ):
        c = Complex( tc = self )
        self.check_complex( c, c, 'int+',
                     [ 'int1', 'int2', 'int3' ], [ 'tint1', 'tint2', 'tint3' ] )

    def test_pattern_list11 ( self ):
        c = Complex( tc = self )
        self.check_complex( c, c, 'int-',
                     [ 'int1', 'int2', 'int3' ], [ 'tint1', 'tint2', 'tint3' ] )

    def test_pattern_list12 ( self ):
        c = Complex( tc = self )
        self.check_complex( c, c, 'int+test,tint-test',
                     [ 'int1', 'int3', 'tint1', 'tint3' ], [ 'int2', 'tint2' ] )

    def test_pattern_list13 ( self ):
        c = Complex( tc = self )
        self.check_complex( c, c.ref, 'ref.[int+test,tint-test]',
                     [ 'int1', 'int3', 'tint1', 'tint3' ], [ 'int2', 'tint2' ] )

    def test_cycle1 ( self ):
        lt = LinkTest( tc = self, head = self.build_list() )
        handlers = [ lt.arg_check0, lt.arg_check1, lt.arg_check2, lt.arg_check3,
                     lt.arg_check4 ]
        nh       = len( handlers )
        self.multi_register( lt, handlers, 'head.next*.value' )
        cur = lt.head
        for i in range( 4 ):
            lt.set( exp_object = cur, exp_name = 'value', exp_old = 10 * i,
                    exp_new = (10 * i) + 1 )
            cur.value = (10 * i) + 1
            cur = cur.next
        self.assertEqual( lt.calls, 4 * nh )
        self.multi_register( lt, handlers, 'head.next*.value', remove = True )
        cur = lt.head
        for i in range( 4 ):
            cur.value = (10 * i) + 2
            cur = cur.next
        self.assertEqual( lt.calls, 4 * nh )

    def test_cycle2 ( self ):
        lt = LinkTest( tc = self, head = self.build_list() )
        handlers = [ lt.arg_check0, lt.arg_check1, lt.arg_check2, lt.arg_check3,
                     lt.arg_check4 ]
        nh       = len( handlers )
        self.multi_register( lt, handlers, 'head.[next,prev]*.value' )
        cur = lt.head
        for i in range( 4 ):
            lt.set( exp_object = cur, exp_name = 'value', exp_old = 10 * i,
                    exp_new = (10 * i) + 1 )
            cur.value = (10 * i) + 1
            cur = cur.next
        self.assertEqual( lt.calls, 4 * nh )
        self.multi_register( lt, handlers, 'head.[next,prev]*.value', remove = True )
        cur = lt.head
        for i in range( 4 ):
            cur.value = (10 * i) + 2
            cur = cur.next
        self.assertEqual( lt.calls, 4 * nh )

    def test_cycle3 ( self ):
        lt = LinkTest( tc = self, head = self.build_list() )
        handlers = [ lt.arg_check0, lt.arg_check3, lt.arg_check4 ]
        nh       = len( handlers )
        self.multi_register( lt, handlers, 'head.next*.value' )
        link = self.new_link( lt, lt.head, 1 )
        self.assertEqual( lt.calls, nh )
        link = self.new_link( lt, link, 2 )
        self.assertEqual( lt.calls, 2 * nh )
        self.multi_register( lt, handlers, 'head.next*.value', remove = True )
        link = self.new_link( lt, link, 3 )
        self.assertEqual( lt.calls, 2 * nh )

    def test_property ( self ):
        pdo = PropertyDependsOn( tc = self )
        sum = pdo.sum
        self.assertEqual( sum, 0 )
        for n in [ 'int1', 'int2', 'int3' ]:
            for i in range( 3 ):
                pdo.set( exp_old = sum, exp_new = sum + 1 )
                setattr( pdo.ref, n, i + 1 )
                sum += 1
        self.assertEqual( pdo.pcalls, (3 * 3) + 1 )
        self.assertEqual( pdo.calls,  3 * 3 )
        for i in range( 10 ):
            x = pdo.sum
        self.assertEqual( pdo.pcalls, (3 * 3) + 1 )
        pdo.set( exp_old = sum, exp_new = 60 )
        old_ref = pdo.ref
        pdo.ref = ArgCheckBase( int1 = 10, int2 = 20, int3 = 30 )
        self.assertEqual( pdo.pcalls, (3 * 3) + 2 )
        self.assertEqual( pdo.calls,  (3 * 3) + 1 )
        sum = 60
        for n in [ 'int1', 'int2', 'int3' ]:
            for i in range( 3 ):
                pdo.set( exp_old = sum, exp_new = sum + 1 )
                setattr( pdo.ref, n, getattr( pdo.ref, n ) + 1 )
                sum += 1
        self.assertEqual( pdo.pcalls, (2 * 3 * 3) + 2 )
        self.assertEqual( pdo.calls,  (2 * 3 * 3) + 1 )
        for n in [ 'int1', 'int2', 'int3' ]:
            for i in range( 3 ):
                setattr( old_ref, n, getattr( old_ref, n ) + 1 )
        self.assertEqual( pdo.pcalls, (2 * 3 * 3) + 2 )
        self.assertEqual( pdo.calls,  (2 * 3 * 3) + 1 )
        self.assertEqual( pdo.sum, sum )
        self.assertEqual( pdo.pcalls, (2 * 3 * 3) + 2 )

    #-- Helper methods ---------------------------------------------------------

    def check_list ( self, l ):
        for i in range( 3 ):
            ac = ArgCheckBase()
            self.assertRaises( TraitError, l.refs.append, ac)
        self.assertEqual( l.calls, 0 )
        for i in range( 3 ):
            self.assertEqual( l.refs[i].value, 0 )
        refs = [ ArgCheckBase(), ArgCheckBase(), ArgCheckBase() ]
        self.assertRaises( TraitError, l.set, refs = refs )
        self.assertEqual( l.calls, 0 )
        for i in range( 3 ):
            self.assertEqual( l.refs[i].value, 0 )
        for i in range( 3 ):
            for j in range( 3 ):
                l.exp_new = (i + 1)
                l.refs[j].value = (i + 1)
        self.assertEqual( l.calls, 0 )
        for i in range( 3 ):
            self.assertEqual( l.refs[i].value, 3 )

    def check_dict ( self, d ):
        for i in range( 3 ):
            ac = ArgCheckBase()
            self.assertRaises( TraitError, d.refs.setdefault, i, ac )
        self.assertEqual( d.calls, 0 )
        for i in range( 3 ):
            self.assertEqual( d.refs[i].value, 0 )
        refs = { 0: ArgCheckBase(), 1: ArgCheckBase(), 2: ArgCheckBase() }
        self.assertRaises( TraitError, d.set, refs = refs )
        self.assertEqual( d.calls, 0 )
        for i in range( 3 ):
            self.assertEqual( d.refs[i].value, 0 )
        for i in range( 3 ):
            for j in range( 3 ):
                d.exp_new = (i + 1)
                d.refs[j].value = (i + 1)
        self.assertEqual( d.calls, 0 )
        for i in range( 3 ):
            self.assertEqual( d.refs[i].value, 3 )

    def check_complex ( self, c, r, pattern, names, other = [] ):
        handlers = [ c.arg_check0, c.arg_check1, c.arg_check2, c.arg_check3,
                     c.arg_check4 ]
        nh       = len( handlers )
        nn       = len( names )
        self.multi_register( c, handlers, pattern )
        for i in range( 3 ):
            for n in names:
                c.set( exp_object = r, exp_name = n, exp_old = i,
                       exp_new = (i + 1) )
                setattr( r, n, i + 1 )
            for n in other:
                c.set( exp_object = r, exp_name = n, exp_old = i,
                       exp_new = (i + 1) )
                setattr( r, n, i + 1 )
        self.assertEqual( c.calls, 3 * nn * nh )
        self.multi_register( c, handlers, pattern, remove = True )
        for i in range( 3 ):
            for n in names:
                setattr( r, n, i + 1 )
            for n in other:
                setattr( r, n, i + 1 )
        self.assertEqual( c.calls, 3 * nn * nh )

    def multi_register ( self, object, handlers, pattern, remove = False ):
        for handler in handlers:
            print object, handler, pattern, remove
            object.on_trait_change( handler, pattern, remove = remove )

    def build_list ( self ):
        l1 = Link( value = 00 )
        l2 = Link( value = 10 )
        l3 = Link( value = 20 )
        l4 = Link( value = 30 )
        l1.set( next = l2, prev = l4 )
        l2.set( next = l3, prev = l1 )
        l3.set( next = l4, prev = l2 )
        l4.set( next = l1, prev = l3 )
        return l1

    def new_link ( self, lt, cur, value ):
        link = Link( value = value, next = cur.next, prev = cur )
        cur.next.prev = link
        lt.set( exp_object = cur, exp_name = 'next', exp_old = cur.next,
                exp_new = link )
        cur.next = link
        return link

# Run the unit tests (if invoked from the command line):
def ignore ( *args ):
    pass

push_exception_handler( handler = ignore, reraise_exceptions = True )
if __name__ == '__main__':
    unittest.main()

