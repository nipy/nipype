.. AUTO-GENERATED FILE -- DO NOT EDIT!

pkg_info
========


.. module:: nipype.pkg_info


.. _nipype.pkg_info.get_pkg_info:

:func:`get_pkg_info`
--------------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/pkg_info.py#L61>`__



Return dict describing the context of this package

Parameters
~~~~~~~~~~
pkg_path : str
   path containing __init__.py for package

Returns
~~~~~~~
context : dict
   with named parameters of interest


.. _nipype.pkg_info.pkg_commit_hash:

:func:`pkg_commit_hash`
-----------------------

`Link to code <http://github.com/nipy/nipype/tree/e63e055194d62d2bdc4665688261c03a42fd0025/nipype/pkg_info.py#L8>`__



Get short form of commit hash given directory `pkg_path`

There should be a file called 'COMMIT_INFO.txt' in `pkg_path`.  This is a
file in INI file format, with at least one section: ``commit hash``, and two
variables ``archive_subst_hash`` and ``install_hash``.  The first has a
substitution pattern in it which may have been filled by the execution of
``git archive`` if this is an archive generated that way.  The second is
filled in by the installation, if the installation is from a git archive.

We get the commit hash from (in order of preference):

* A substituted value in ``archive_subst_hash``
* A written commit hash value in ``install_hash`
* git's output, if we are in a git repository

If all these fail, we return a not-found placeholder tuple

Parameters
~~~~~~~~~~
pkg_path : str
   directory containing package

Returns
~~~~~~~
hash_from : str
   Where we got the hash from - description
hash_str : str
   short form of hash

