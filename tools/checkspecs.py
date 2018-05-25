# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Attempt to check each interface in nipype
"""
from __future__ import print_function, unicode_literals
from builtins import object, str, bytes, open

# Stdlib imports
import os
import re
import sys
import warnings

from nipype.interfaces.base import BaseInterface
from yapf.yapflib.yapf_api import FormatCode


# Functions and classes
class InterfaceChecker(object):
    """Class for checking all interface specifications
    """

    def __init__(self,
                 package_name,
                 package_skip_patterns=None,
                 module_skip_patterns=None,
                 class_skip_patterns=None):
        ''' Initialize package for parsing

        Parameters
        ----------
        package_name : string
            Name of the top-level package.  *package_name* must be the
            name of an importable package
        package_skip_patterns : None or sequence of {strings, regexps}
            Sequence of strings giving URIs of packages to be excluded
            Operates on the package path, starting at (including) the
            first dot in the package path, after *package_name* - so,
            if *package_name* is ``sphinx``, then ``sphinx.util`` will
            result in ``.util`` being passed for earching by these
            regexps.  If is None, gives default. Default is:
            ['\.tests$']
        module_skip_patterns : None or sequence
            Sequence of strings giving URIs of modules to be excluded
            Operates on the module name including preceding URI path,
            back to the first dot after *package_name*.  For example
            ``sphinx.util.console`` results in the string to search of
            ``.util.console``
            If is None, gives default. Default is:
            ['\.setup$', '\._']
        class_skip_patterns : None or sequence
            Sequence of strings giving classes to be excluded
            Default is: None

        '''
        if package_skip_patterns is None:
            package_skip_patterns = ['\\.tests$']
        if module_skip_patterns is None:
            module_skip_patterns = ['\\.setup$', '\\._']
        if class_skip_patterns:
            self.class_skip_patterns = class_skip_patterns
        else:
            self.class_skip_patterns = []
        self.package_name = package_name
        self.package_skip_patterns = package_skip_patterns
        self.module_skip_patterns = module_skip_patterns

    def get_package_name(self):
        return self._package_name

    def set_package_name(self, package_name):
        """Set package_name"""
        # It's also possible to imagine caching the module parsing here
        self._package_name = package_name
        self.root_module = __import__(package_name)
        self.root_path = self.root_module.__path__[0]

    package_name = property(get_package_name, set_package_name, None,
                            'get/set package_name')

    def _get_object_name(self, line):
        name = line.split()[1].split('(')[0].strip()
        # in case we have classes which are not derived from object
        # ie. old style classes
        return name.rstrip(':')

    def _uri2path(self, uri):
        """Convert uri to absolute filepath

        Parameters
        ----------
        uri : string
            URI of python module to return path for

        Returns
        -------
        path : None or string
            Returns None if there is no valid path for this URI
            Otherwise returns absolute file system path for URI

        """
        if uri == self.package_name:
            return os.path.join(self.root_path, '__init__.py')
        path = uri.replace('.', os.path.sep)
        path = path.replace(self.package_name + os.path.sep, '')
        path = os.path.join(self.root_path, path)
        # XXX maybe check for extensions as well?
        if os.path.exists(path + '.py'):  # file
            path += '.py'
        elif os.path.exists(os.path.join(path, '__init__.py')):
            path = os.path.join(path, '__init__.py')
        else:
            return None
        return path

    def _path2uri(self, dirpath):
        ''' Convert directory path to uri '''
        relpath = dirpath.replace(self.root_path, self.package_name)
        if relpath.startswith(os.path.sep):
            relpath = relpath[1:]
        return relpath.replace(os.path.sep, '.')

    def _parse_module(self, uri):
        ''' Parse module defined in *uri* '''
        filename = self._uri2path(uri)
        if filename is None:
            # nothing that we could handle here.
            return ([], [])
        f = open(filename, 'rt')
        functions, classes = self._parse_lines(f, uri)
        f.close()
        return functions, classes

    def _parse_lines(self, linesource, module):
        ''' Parse lines of text for functions and classes '''
        functions = []
        classes = []
        for line in linesource:
            if line.startswith('def ') and line.count('('):
                # exclude private stuff
                name = self._get_object_name(line)
                if not name.startswith('_'):
                    functions.append(name)
            elif line.startswith('class '):
                # exclude private stuff
                name = self._get_object_name(line)
                if not name.startswith('_') and \
                        self._survives_exclude('.'.join((module, name)),
                                               'class'):
                    classes.append(name)
            else:
                pass
        functions.sort()
        classes.sort()
        return functions, classes

    @classmethod
    def _normalize_repr(cls, value):
        if isinstance(value, list):
            return '[{}]'.format(', '.join(map(cls._normalize_repr, value)))
        if isinstance(value, tuple):
            if len(value) == 1:
                return '({},)'.format(cls._normalize_repr(value[0]))
            return '({})'.format(', '.join(map(cls._normalize_repr, value)))
        if isinstance(value, (str, bytes)):
            value = repr(value)
            if value[0] not in ('"', "'"):
                value = value[1:]
        else:
            value = repr(value)
        return value

    def test_specs(self, uri):
        """Check input and output specs in an uri

        Parameters
        ----------
        uri : string
            python location of module - e.g 'sphinx.builder'

        Returns
        -------
        """
        # get the names of all classes and functions
        _, classes = self._parse_module(uri)
        if not classes:
            # print 'WARNING: Empty -',uri  # dbg
            return None

        # Make a shorter version of the uri that omits the package name for
        # titles
        allowed_keys = [
            'desc', 'genfile', 'xor', 'requires', 'desc', 'nohash', 'argstr',
            'position', 'mandatory', 'copyfile', 'usedefault', 'sep',
            'hash_files', 'deprecated', 'new_name', 'min_ver', 'max_ver',
            'name_source', 'name_template', 'keep_extension', 'units',
            'output_name'
        ]
        in_built = [
            'type', 'copy', 'parent', 'instance_handler', 'comparison_mode',
            'array', 'default', 'editor'
        ]
        bad_specs = []
        for c in classes:
            __import__(uri)
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    classinst = sys.modules[uri].__dict__[c]
            except Exception:
                continue

            if not issubclass(classinst, BaseInterface):
                continue
            testdir = os.path.join(*(uri.split('.')[:-1] + ['tests']))
            if not os.path.exists(testdir):
                os.makedirs(testdir)
            nonautotest = os.path.join(testdir, 'test_%s.py' % c)
            testfile = os.path.join(testdir, 'test_auto_%s.py' % c)
            if os.path.exists(testfile):
                os.unlink(testfile)

            if not os.path.exists(nonautotest):
                cmd = [
                    '# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT',
                    'from __future__ import unicode_literals',
                    'from ..%s import %s' % (uri.split('.')[-1], c), ''
                ]
                cmd.append('\ndef test_%s_inputs():' % c)
                input_fields = ''
                for traitname, trait in sorted(
                        classinst.input_spec().traits(transient=None).items()):
                    input_fields += '%s=dict(' % traitname
                    for key, value in sorted(trait.__dict__.items()):
                        if key in in_built or key == 'desc':
                            continue
                        input_fields += "%s=%s,\n    " % (
                            key, self._normalize_repr(value))
                    input_fields += '),\n    '
                cmd += ['    input_map = dict(%s)' % input_fields]
                cmd += ['    inputs = %s.input_spec()' % c]
                cmd += [
                    """
    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value"""
                ]

                fmt_cmd, _ = FormatCode(
                    '\n'.join(cmd) + '\n\n',
                    style_config={
                        'based_on_style': 'pep8',
                        'column_limit': 79
                    })
                with open(testfile, 'wt') as fp:
                    fp.writelines(fmt_cmd)
            else:
                print('%s has nonautotest' % c)

            for traitname, trait in sorted(
                    classinst.input_spec().traits(transient=None).items()):
                for key in sorted(trait.__dict__):
                    if key in in_built:
                        continue
                    parent_metadata = []
                    if 'parent' in trait.__dict__:
                        parent_metadata = list(
                            getattr(trait, 'parent').__dict__.keys())
                    if key not in allowed_keys + classinst._additional_metadata\
                            + parent_metadata:
                        bad_specs.append([uri, c, 'Inputs', traitname, key])
                    if key == 'mandatory' and trait.mandatory is not None and not trait.mandatory:
                        bad_specs.append(
                            [uri, c, 'Inputs', traitname, 'mandatory=False'])
                    if key == "usedefault" and trait.__dict__[key] == False:
                        bad_specs.append(
                            [uri, c, 'Inputs', traitname, 'usedefault=False'])
                # checking if traits that have default_value different that the trits default one
                # also have `usedefault` specified;
                # excluding TraitCompound
                # excluding Enum: always has default value (the first value)
                # excluding Tuple: takes tuple of inner traits default values as default, but doesn't use it
                # for Range assuming that if default == low, it's likely that usedefault should be False
                # (for Range traits takes low as a default default
                if trait.trait_type.__class__.__name__ not in ['TraitCompound', "Tuple", "Enum"]\
                        and trait.default and "usedefault" not in trait.__dict__\
                        and "requires" not in trait.__dict__\
                        and "xor" not in trait.__dict__:
                    if trait.trait_type.__class__.__name__ is "Range"\
                            and trait.default == trait.trait_type._low:
                        continue
                    bad_specs.append(
                        [uri, c, 'Inputs', traitname, 'default value is set, no value for usedefault'])

            if not classinst.output_spec:
                continue

            if not os.path.exists(nonautotest):
                cmd = ['\ndef test_%s_outputs():' % c]
                input_fields = ''
                for traitname, trait in sorted(classinst.output_spec().traits(
                        transient=None).items()):
                    input_fields += '%s=dict(' % traitname
                    for key, value in sorted(trait.__dict__.items()):
                        if key in in_built or key == 'desc':
                            continue
                        input_fields += "%s=%s,\n    " % (
                            key, self._normalize_repr(value))
                    input_fields += '),\n    '
                cmd += ['    output_map = dict(%s)' % input_fields]
                cmd += ['    outputs = %s.output_spec()' % c]
                cmd += [
                    """
    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value"""
                ]
                fmt_cmd, _ = FormatCode(
                    '\n'.join(cmd) + '\n',
                    style_config={
                        'based_on_style': 'pep8',
                        'column_limit': 79
                    })
                with open(testfile, 'at') as fp:
                    fp.writelines(fmt_cmd)

            for traitname, trait in sorted(
                    classinst.output_spec().traits(transient=None).items()):
                for key in sorted(trait.__dict__):
                    if key in in_built:
                        continue
                    parent_metadata = []
                    if 'parent' in trait.__dict__:
                        parent_metadata = list(
                            getattr(trait, 'parent').__dict__.keys())
                    if key not in allowed_keys + classinst._additional_metadata\
                            + parent_metadata:
                        bad_specs.append([uri, c, 'Outputs', traitname, key])
        return bad_specs

    def _survives_exclude(self, matchstr, match_type):
        ''' Returns True if *matchstr* does not match patterns

        ``self.package_name`` removed from front of string if present

        Examples
        --------
        >>> dw = ApiDocWriter('sphinx')
        >>> dw._survives_exclude('sphinx.okpkg', 'package')
        True
        >>> dw.package_skip_patterns.append('^\\.badpkg$')
        >>> dw._survives_exclude('sphinx.badpkg', 'package')
        False
        >>> dw._survives_exclude('sphinx.badpkg', 'module')
        True
        >>> dw._survives_exclude('sphinx.badmod', 'module')
        True
        >>> dw.module_skip_patterns.append('^\\.badmod$')
        >>> dw._survives_exclude('sphinx.badmod', 'module')
        False
        '''
        if match_type == 'module':
            patterns = self.module_skip_patterns
        elif match_type == 'package':
            patterns = self.package_skip_patterns
        elif match_type == 'class':
            patterns = self.class_skip_patterns
        else:
            raise ValueError('Cannot interpret match type "%s"' % match_type)
        # Match to URI without package name
        L = len(self.package_name)
        if matchstr[:L] == self.package_name:
            matchstr = matchstr[L:]
        for pat in patterns:
            try:
                pat.search
            except AttributeError:
                pat = re.compile(pat)
            if pat.search(matchstr):
                return False
        return True

    def discover_modules(self):
        ''' Return module sequence discovered from ``self.package_name``


        Parameters
        ----------
        None

        Returns
        -------
        mods : sequence
            Sequence of module names within ``self.package_name``

        Examples
        --------
        '''
        modules = [self.package_name]
        # raw directory parsing
        for dirpath, dirnames, filenames in os.walk(self.root_path):
            # Check directory names for packages
            root_uri = self._path2uri(os.path.join(self.root_path, dirpath))
            for dirname in dirnames[:]:  # copy list - we modify inplace
                package_uri = '.'.join((root_uri, dirname))
                if (self._uri2path(package_uri)
                        and self._survives_exclude(package_uri, 'package')):
                    modules.append(package_uri)
                else:
                    dirnames.remove(dirname)
            # Check filenames for modules
            for filename in filenames:
                module_name = filename[:-3]
                module_uri = '.'.join((root_uri, module_name))
                if (self._uri2path(module_uri)
                        and self._survives_exclude(module_uri, 'module')):
                    modules.append(module_uri)
        return sorted(modules)

    def check_modules(self):
        # write the list
        modules = self.discover_modules()
        checked_modules = []
        for m in modules:
            bad_specs = self.test_specs(m)
            if bad_specs:
                checked_modules.extend(bad_specs)
        for bad_spec in checked_modules:
            print(':'.join(bad_spec))


if __name__ == "__main__":
    package = 'nipype'
    ic = InterfaceChecker(package)
    # Packages that should not be included in generated API docs.
    ic.package_skip_patterns += [
        '\.external$',
        '\.fixes$',
        '\.utils$',
        '\.pipeline',
        '\.testing',
        '\.caching',
        '\.workflows',
    ]
    """
    # Modules that should not be included in generated API docs.
    ic.module_skip_patterns += ['\.version$',
                                '\.interfaces\.base$',
                                '\.interfaces\.matlab$',
                                '\.interfaces\.rest$',
                                '\.interfaces\.pymvpa$',
                                '\.interfaces\.slicer\.generate_classes$',
                                '\.interfaces\.spm\.base$',
                                '\.interfaces\.traits',
                                '\.pipeline\.alloy$',
                                '\.pipeline\.s3_node_wrapper$',
                                '.\testing',
                                       ]
    ic.class_skip_patterns += ['AFNI',
                               'ANTS',
                               'FSL',
                               'FS',
                               'Info',
                               '^SPM',
                               'Tester',
                               'Spec$',
                               'Numpy',
                               'NipypeTester',
                                      ]
    """
    ic.check_modules()
