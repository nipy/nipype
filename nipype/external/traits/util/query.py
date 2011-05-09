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
# Author: Enthought, Inc.
# Description: <Enthought util package component>
#------------------------------------------------------------------------------
def query(data, var_names, expression):
    """ Extract all of the items in the dictionary that matches the user
    specified expression.

    data is the dictionary to be queried

    var_names describes the variables in the key that can be used in the
    expression eg (case, marker)

    expression is a python expression eg case == 'oil' and marker = 'top sand'
    """
    matches = {}

    for key in data.keys():
        print key
        ns = _build_namespace(var_names, key)
        print ns

        if eval(expression, ns):
            matches[key] = data[key]

    return matches

def _build_namespace(var_names, key):

    namespace = {}
    for name, value in zip(var_names, key):
        namespace[name] = value

    return namespace


if __name__ == "__main__" or __name__ == 'PyCrust-Shell':

    db = {}
    db[('oil', 'A')] = 1
    db[('oil', 'B')] = 2
    db[('gas', 'A')] = 3
    db[('gas', 'B')] = 4

    result = query(db, ('fluid', 'attribute'), 'fluid == "oil"')

    for name, value in result.iteritems():
        print "%s %s" % (name, value)

    result = query(db, ('fluid', 'attribute'), 'attribute > 2')

    for name, value in result.iteritems():
        print "%s %s" % (name, value)
