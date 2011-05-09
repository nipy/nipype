The files contained in this directory are from the pyprotocols project
(http://peak.telecommunity.com/PyProtocols.html).

Copyright (C) 2003, Phillip J. Eby

This project's original licensing terms (as stated in the upstream
README.txt) are compatible with the enthought software licensing
terms.

+++++++++ Upstream README.txt ++++++++++++++++++++++++++++++++++++++++++++++++++

PyProtocols Release 0.9.3 (release candidate 1)

 Copyright (C) 2003 by Phillip J. Eby.  All rights reserved.  This software may
 be used under the same terms as Zope or Python.  THERE ARE ABSOLUTELY NO
 WARRANTIES OF ANY KIND.

 Package Description

    Do you hate having to write lots of if-then logic to test what type
    something is?  Wouldn't it be nice if you could just declare "I want this
    object to have this behavior" and magically convert whatever value you
    have, to the type you need?  PyProtocols lets you do just that, cleanly,
    quickly, and robustly -- even with built-in types or other people's
    classes.

    PyProtocols extends the PEP 246 adapt() function with a new "declaration
    API" that lets you easily define your own interfaces and adapters, and
    declare what adapters should be used to adapt what types, objects, or
    interfaces.  In addition to its own Interface type, PyProtocols can also
    use Twisted and Zope's Interface types.  (Of course, since Twisted and
    Zope interfaces aren't as flexible, only a subset of the PyProtocols API
    works with them.  Specific limitations are listed in the documentation.)

    If you're familiar with Interface objects in Zope, Twisted, or PEAK, the
    Interface objects in PyProtocols are very similar.  But, they can also do
    many things that no other Python interface types can do.  For example,
    PyProtocols supports "subsetting" of interfaces, where you can declare that
    one interface is a subset of another existing interface.  This is like
    declaring that somebody else's existing interface is actually a subclass
    of the new interface.  Twisted and Zope don't allow this, which
    makes them very hard to use if you're trying to define interfaces like
    "Read-only Mapping" as a subset of "Mapping Object".

    Unlike Zope and Twisted, PyProtocols also doesn't force you to use a
    particular interface coding style or even a specific interface type.  You
    can use its built-in interface types, or define your own.  If there's
    another Python package out there with interface types that you'd like to
    use (CORBA? COM?), you can even create your own adapters to make them
    work with the PyProtocols API.


    PyProtocols is also the only interface package that supports automatic
    "transitive adaptation".  That is, if you define an adapter from interface
    A to interface B, and another from B to C, PyProtocols automatically
    creates and registers a new adapter from A to C for you.  If you later
    declare an explicit adapter from A to C, it silently replaces the
    automatically created one.

    PyProtocols may be used, modified, and distributed under the same terms
    and conditions as Python or Zope.


 Version 0.9.3 Release Notes

    For **important** notes on upgrading from previous releases, and
    information about changes coming in 1.0, please see the UPGRADING.txt file.
    For the complete list of changes from 0.9.2, please see the CHANGES.txt
    file.

    Note that the 0.9.x release series is now in "maintenance mode", and no
    new features will be added in future 0.9.x releases.  From now on, new
    features will only be added to the 1.x releases, beginning with 1.0a1
    later this year.

    If you'd like to use Zope interfaces with PyProtocols, you must
    use Zope X3 beta 1 or later, as PyProtocols' Zope support uses
    the latest Zope interface declaration API.

    If you'd like to use Twisted interfaces with PyProtocols, you must use
    Twisted 1.0.5 or later.


 Obtaining the Package and Documentation

    Please see the "PyProtocols Home Page":http://peak.telecommunity.com/PyProtocols.html
    for download links, CVS links, reference manuals, etc.










 Installation Instructions

  Python 2.2.2 or better is required.  To install, just unpack the archive,
  go to the directory containing 'setup.py', and run::

    python setup.py install

  PyProtocols will be installed in the 'site-packages' directory of your Python
  installation.  (Unless directed elsewhere; see the "Installing Python
  Modules" section of the Python manuals for details on customizing
  installation locations, etc.).

  (Note: for the Win32 installer release, just run the .exe file.)

  If you wish to run the associated test suite, you can also run::

    python setup.py test

  which will verify the correct installation and functioning of the package.

  PyProtocols includes an optional speed-enhancing module written in Pyrex and
  C.  If you do not have a C compiler available, you can disable installation
  of the C module by invoking 'setup.py' with '--without-speedups', e.g.::

    python setup.py --without-speedups install

  or::

    python setup.py --without-speedups test

  You do not need to worry about this if you are using the Win32 binary
  installer, since it includes a pre-compiled speedups module.

  Note: if you have installed Pyrex on your Python path, be sure it is Pyrex
  version 0.7.2.  You do *not* have to have Pyrex installed, even to build the
  C extension, but if you do have it installed, make sure it's up to date
  before building the C extension.



