""" This code was found on http://www.webwareforpython.org/. The only
    modifications are for the explicit purpose of tracking circular
    dependencies.
"""


"""ImportSpy

Keeps track of modules not imported directly by Webware for Python.

This module helps save the filepath of every module which is imported.
This is used by the `AutoReloadingAppServer` (see doc strings for more
information) to restart the server if any source files change.

Other than keeping track of the filepaths, the behaviour of this module
loader is identical to Python's default behaviour.

If the system supports FAM (file alteration monitor) and python-fam is
installed, then the need for reloading can be monitored very effectively
with the use of ImportSpy. Otherwise, ImportSpy will not have much benefit.

Note that ImportSpy is based on the new import hooks of Python 2.3 described in
PEP 302, falling back to the old ihooks module if the new hooks are not available.
In some cases this may become problematic, when other templating systems are
used with Webware which are also using ihook support to load their templates,
or if they are using zipimports. Therefore, it is possible to suppress the use
of ImportSpy by setting `UseImportSpy` in AppServer.config to False.

"""


try: # if possible, use new (PEP 302) import hooks
    from sys import path_hooks, path_importer_cache
except ImportError:
    path_hooks = None

import os.path
import sys

incomplete_imports = []
find_module_chain = []
dependency_map = {}
indent = 0
debug = False

def path_could_be_package(path, package):
   parts = package.split('.')
   parts.reverse()
   for part in parts:
      basename, ext = os.path.splitext(os.path.basename(path))
      if ext == ".so":
         if basename != part:
            part += "module"
      elif basename != part:
         return False
      path = os.path.dirname(path)
   return True

def circular_tester(path, modtime):
   if len(find_module_chain) == 0:
      return
   elif path_could_be_package(path, find_module_chain[-1]):
      return

   for m in incomplete_imports:
      try:
          n,p,d = ImportSpy._imp.find_module(m)
      except ImportError:
          print "  import stack: " + str(incomplete_imports)
          sys.exit(65)



if path_hooks is not None:

    from os.path import isdir


    class ImportSpy(object):
        """New style import tracker."""

        _imp = None

        def __init__(self, path=None):
            """Create importer."""
            assert self._imp
            if path and isdir(path):
                self.path = path
            else:
                raise ImportError

        def find_module(self, fullname):
            """Replaces imp.find_module."""
            global indent
            if debug: print '  '*indent + "Find module(self, %s)" % fullname
            indent += 1

            try:
                self.file, self.filename, self.info = self._imp.find_module(
                    fullname.split('.')[-1], [self.path])
                if (os.path.isdir(self.filename)):
                   find_module_chain.append(fullname)

            except ImportError:
                self.file = None
            if self.file:
                find_module_chain.append(fullname)
                indent -= 1
                return self
            else:
                indent -= 1
                return None

        def load_module(self, fullname):
            """Replaces imp.load_module."""
            global indent
            global find_module_chain
            if debug: print '  '*indent + "Load module %s" % fullname
            indent += 1

            # build the dependency map
            if len(find_module_chain) > 1:
                parent = find_module_chain[-2]
                if dependency_map.has_key(parent):
                    dependency_map[parent].append(fullname)
                else:
                    dependency_map[parent] = [fullname]
            else:
                if len(incomplete_imports) == 0:
                    # this is a top level node
                    pass
                else:
                    parent = incomplete_imports[-1]
                    if dependency_map.has_key(parent):
                        dependency_map[parent].append(fullname)
                    else:
                        dependency_map[parent] = [fullname]

            incomplete_imports.append(fullname)
            mod = self._imp.load_module(fullname, self.file, self.filename, self.info)
            incomplete_imports.remove(fullname)
            find_module_chain = []
            indent -= 1
            if debug: print '  '*indent + "Complete loading %s" % fullname
            if mod:
                mod.__loader__ = self
            return mod

    def activate(imp_manager):
        """Activate ImportSpy."""
        assert not ImportSpy._imp
        ImportSpy._imp = imp_manager
        path_hooks.append(ImportSpy)
        path_importer_cache.clear()
        imp_manager.recordModules()
        return 'new import hooks'


else: # Python < 2.3, fall back to using the old ihooks module

    import ihooks


    class ImportSpy(ihooks.ModuleLoader):
        """Old style import tracker."""

        _imp = None

        def __init__(self):
            """Create import hook."""
            assert self._imp
            ihooks.ModuleLoader.__init__(self)
            self._lock = self._imp._lock
            imp = ihooks.ModuleImporter(loader=self)
            ihooks.install(imp)
            self._imp.recordModules()

        def load_module(self, name, stuff):
            """Replaces imp.load_module."""
            file, filename, info = stuff
            try:
                try:
                    self._lock.acquire()
                    mod = ihooks.ModuleLoader.load_module(self, name, stuff)
                finally:
                    self._lock.release()
                self._imp.recordModule(mod)
            except:
                self._imp.recordFile(filename)
                raise
            return mod

    def activate(imp_manager):
        """Activate ImportSpy."""
        assert not ImportSpy._imp
        ImportSpy._imp = imp_manager
        ImportSpy()
        return 'ihooks'
