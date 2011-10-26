"""
Nose test running.

This module implements ``test()`` and ``bench()`` functions for NumPy modules.

"""
import os
import sys

def get_package_name(filepath):
    """
    Given a path where a package is installed, determine its name.

    Parameters
    ----------
    filepath : str
        Path to a file. If the determination fails, "numpy" is returned.

    Examples
    --------
    >>> np.testing.nosetester.get_package_name('nonsense')
    'numpy'

    """

    fullpath = filepath[:]
    pkg_name = []
    while 'site-packages' in filepath or 'dist-packages' in filepath:
        filepath, p2 = os.path.split(filepath)
        if p2 in ('site-packages', 'dist-packages'):
            break
        pkg_name.append(p2)

    # if package name determination failed, just default to numpy/scipy
    if not pkg_name:
        if 'scipy' in fullpath:
            return 'scipy'
        else:
            return 'numpy'

    # otherwise, reverse to get correct order and return
    pkg_name.reverse()

    # don't include the outer egg directory
    if pkg_name[0].endswith('.egg'):
        pkg_name.pop(0)

    return '.'.join(pkg_name)

def import_nose():
    """ Import nose only when needed.
    """
    fine_nose = True
    minimum_nose_version = (0,10,0)
    try:
        import nose
        from nose.tools import raises
    except ImportError:
        fine_nose = False
    else:
        if nose.__versioninfo__ < minimum_nose_version:
            fine_nose = False

    if not fine_nose:
        msg = 'Need nose >= %d.%d.%d for tests - see ' \
              'http://somethingaboutorange.com/mrl/projects/nose' % \
              minimum_nose_version

        raise ImportError(msg)

    return nose

def run_module_suite(file_to_run = None):
    if file_to_run is None:
        f = sys._getframe(1)
        file_to_run = f.f_locals.get('__file__', None)
        if file_to_run is None:
            raise AssertionError

    import_nose().run(argv=['',file_to_run])


class NoseTester(object):
    """
    Nose test runner.

    This class is made available as numpy.testing.Tester, and a test function
    is typically added to a package's __init__.py like so::

      from numpy.testing import Tester
      test = Tester().test

    Calling this test function finds and runs all tests associated with the
    package and all its sub-packages.

    Attributes
    ----------
    package_path : str
        Full path to the package to test.
    package_name : str
        Name of the package to test.

    Parameters
    ----------
    package : module, str or None
        The package to test. If a string, this should be the full path to
        the package. If None (default), `package` is set to the module from
        which `NoseTester` is initialized.

    """
    # Stuff to exclude from tests. These are from numpy.distutils
    excludes = ['f2py_ext',
                'f2py_f90_ext',
                'gen_ext',
                'pyrex_ext',
                'swig_ext']

    def __init__(self, package=None):
        ''' Test class init

        Parameters
        ----------
        package : string or module
            If string, gives full path to package
            If None, extract calling module path
            Default is None
        '''
        package_name = None
        if package is None:
            f = sys._getframe(1)
            package_path = f.f_locals.get('__file__', None)
            if package_path is None:
                raise AssertionError
            package_path = os.path.dirname(package_path)
            package_name = f.f_locals.get('__name__', None)
        elif isinstance(package, type(os)):
            package_path = os.path.dirname(package.__file__)
            package_name = getattr(package, '__name__', None)
        else:
            package_path = str(package)

        self.package_path = package_path

        # find the package name under test; this name is used to limit coverage
        # reporting (if enabled)
        if package_name is None:
            package_name = get_package_name(package_path)
        self.package_name = package_name

    def _test_argv(self, label, verbose, extra_argv):
        ''' Generate argv for nosetest command

        Parameters
        ----------
        label : {'fast', 'full', '', attribute identifier}, optional
            see ``test`` docstring
        verbose : int, optional
            Verbosity value for test outputs, in the range 1-10. Default is 1.
        extra_argv : list, optional
            List with any extra arguments to pass to nosetests.

        Returns
        -------
        argv : list
            command line arguments that will be passed to nose
        '''
        argv = [__file__, self.package_path, '-s']
        if label and label != 'full':
            if not isinstance(label, basestring):
                raise TypeError('Selection label should be a string')
            if label == 'fast':
                label = 'not slow'
            argv += ['-A', label]
        argv += ['--verbosity', str(verbose)]
        if extra_argv:
            argv += extra_argv
        return argv

    def _show_system_info(self):
        nose = import_nose()

        import numpy
        print "NumPy version %s" % numpy.__version__
        npdir = os.path.dirname(numpy.__file__)
        print "NumPy is installed in %s" % npdir

        if 'scipy' in self.package_name:
            import scipy
            print "SciPy version %s" % scipy.__version__
            spdir = os.path.dirname(scipy.__file__)
            print "SciPy is installed in %s" % spdir

        pyversion = sys.version.replace('\n','')
        print "Python version %s" % pyversion
        print "nose version %d.%d.%d" % nose.__versioninfo__

    def _get_custom_doctester(self):
        """ Return instantiated plugin for doctests

        Allows subclassing of this class to override doctester

        A return value of None means use the nose builtin doctest plugin
        """
        from noseclasses import NumpyDoctest
        return NumpyDoctest()

    def prepare_test_args(self, label='fast', verbose=1, extra_argv=None,
                          doctests=False, coverage=False):
        """
        Run tests for module using nose.

        This method does the heavy lifting for the `test` method. It takes all
        the same arguments, for details see `test`.

        See Also
        --------
        test

        """
        # fail with nice error message if nose is not present
        import_nose()
        # compile argv
        argv = self._test_argv(label, verbose, extra_argv)
        # bypass tests noted for exclude
        for ename in self.excludes:
            argv += ['--exclude', ename]
        # our way of doing coverage
        if coverage:
            argv+=['--cover-package=%s' % self.package_name, '--with-coverage',
                   '--cover-tests', '--cover-inclusive', '--cover-erase']
        # construct list of plugins
        import nose.plugins.builtin
        from noseclasses import KnownFailure, Unplugger
        plugins = [KnownFailure()]
        plugins += [p() for p in nose.plugins.builtin.plugins]
        # add doctesting if required
        doctest_argv = '--with-doctest' in argv
        if doctests == False and doctest_argv:
            doctests = True
        plug = self._get_custom_doctester()
        if plug is None:
            # use standard doctesting
            if doctests and not doctest_argv:
                argv += ['--with-doctest']
        else: # custom doctesting
            if doctest_argv: # in fact the unplugger would take care of this
                argv.remove('--with-doctest')
            plugins += [Unplugger('doctest'), plug]
            if doctests:
                argv += ['--with-' + plug.name]
        return argv, plugins

    def test(self, label='fast', verbose=1, extra_argv=None, doctests=False,
             coverage=False):
        """
        Run tests for module using nose.

        Parameters
        ----------
        label : {'fast', 'full', '', attribute identifier}, optional
            Identifies the tests to run. This can be a string to pass to
            the nosetests executable with the '-A' option, or one of several
            special values.  Special values are:
            * 'fast' - the default - which corresponds to the ``nosetests -A``
              option of 'not slow'.
            * 'full' - fast (as above) and slow tests as in the
              'no -A' option to nosetests - this is the same as ''.
            * None or '' - run all tests.
            attribute_identifier - string passed directly to nosetests as '-A'.
        verbose : int, optional
            Verbosity value for test outputs, in the range 1-10. Default is 1.
        extra_argv : list, optional
            List with any extra arguments to pass to nosetests.
        doctests : bool, optional
            If True, run doctests in module. Default is False.
        coverage : bool, optional
            If True, report coverage of NumPy code. Default is False.
            (This requires the `coverage module:
             <http://nedbatchelder.com/code/modules/coverage.html>`_).

        Returns
        -------
        result : object
            Returns the result of running the tests as a
            ``nose.result.TextTestResult`` object.

        Notes
        -----
        Each NumPy module exposes `test` in its namespace to run all tests for it.
        For example, to run all tests for numpy.lib:

        >>> np.lib.test() #doctest: +SKIP

        Examples
        --------
        >>> result = np.lib.test() #doctest: +SKIP
        Running unit tests for numpy.lib
        ...
        Ran 976 tests in 3.933s

        OK

        >>> result.errors #doctest: +SKIP
        []
        >>> result.knownfail #doctest: +SKIP
        []
        """

        # cap verbosity at 3 because nose becomes *very* verbose beyond that
        verbose = min(verbose, 3)

        import utils
        utils.verbose = verbose

        if doctests:
            print "Running unit tests and doctests for %s" % self.package_name
        else:
            print "Running unit tests for %s" % self.package_name

        self._show_system_info()

        # reset doctest state on every run
        import doctest
        doctest.master = None

        argv, plugins = self.prepare_test_args(label, verbose, extra_argv,
                                               doctests, coverage)
        from noseclasses import NumpyTestProgram
        t = NumpyTestProgram(argv=argv, exit=False, plugins=plugins)
        return t.result

    def bench(self, label='fast', verbose=1, extra_argv=None):
        """
        Run benchmarks for module using nose.

        Parameters
        ----------
        label : {'fast', 'full', '', attribute identifier}, optional
            Identifies the benchmarks to run. This can be a string to pass to
            the nosetests executable with the '-A' option, or one of several
            special values.  Special values are:
            * 'fast' - the default - which corresponds to the ``nosetests -A``
              option of 'not slow'.
            * 'full' - fast (as above) and slow benchmarks as in the
              'no -A' option to nosetests - this is the same as ''.
            * None or '' - run all tests.
            attribute_identifier - string passed directly to nosetests as '-A'.
        verbose : int, optional
            Verbosity value for benchmark outputs, in the range 1-10. Default is 1.
        extra_argv : list, optional
            List with any extra arguments to pass to nosetests.

        Returns
        -------
        success : bool
            Returns True if running the benchmarks works, False if an error
            occurred.

        Notes
        -----
        Benchmarks are like tests, but have names starting with "bench" instead
        of "test", and can be found under the "benchmarks" sub-directory of the
        module.

        Each NumPy module exposes `bench` in its namespace to run all benchmarks
        for it.

        Examples
        --------
        >>> success = np.lib.bench() #doctest: +SKIP
        Running benchmarks for numpy.lib
        ...
        using 562341 items:
        unique:
        0.11
        unique1d:
        0.11
        ratio: 1.0
        nUnique: 56230 == 56230
        ...
        OK

        >>> success #doctest: +SKIP
        True

        """

        print "Running benchmarks for %s" % self.package_name
        self._show_system_info()

        argv = self._test_argv(label, verbose, extra_argv)
        argv += ['--match', r'(?:^|[\\b_\\.%s-])[Bb]ench' % os.sep]

        # import nose or make informative error
        nose = import_nose()

        # get plugin to disable doctests
        from noseclasses import Unplugger
        add_plugins = [Unplugger('doctest')]

        return nose.run(argv=argv, addplugins=add_plugins)

