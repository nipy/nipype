import os
import sys
import subprocess
import pickle
import operator

dependent_pickle_name = "dependents.pickle"

def get_dependent(module_name):
   if os.path.exists(dependent_pickle_name):
      dep_map = pickle.load(open(dependent_pickle_name, "r"))
      if dep_map.has_key(module_name):
         return dep_map[module_name]

   return None

def store_dependent(module_name, module):
   if os.path.exists(dependent_pickle_name):
      dep_map = pickle.load(open(dependent_pickle_name, "r"))
   else:
      dep_map = {}
   dep_map[module_name] = module
   pickle.dump(dep_map, open(dependent_pickle_name, "w"))

def print_dependencies(module_name):
   dep_map = pickle.load(open(dependent_pickle_name, "r"))
   print dep_map[module_name].pretty_print(0)

def generate_dot_file(filename):
   s = 'digraph dependencies {\n'
   dep_map = pickle.load(open(dependent_pickle_name, "r"))
   for key,value in dep_map.items():
      s += value.generate_dot()
   s += '}\n'

   f = open(filename, "w")
   f.write(s)
   f.close()


class Dependent(object):
   def __init__(self, name, path, script=False):
      self.name = name
      self.path = path
      if script:
         self.dependents = self._exec_script()
      else:
         self.dependents = self._find_dependencies_subprocess()
         store_dependent(self.name, self)

   def _exec_script(self):
      global_dict = globals()
      global_dict['__name__'] = self.name
      global_dict['__file__'] = self.path
      global_dict['sys.argv'] = self.path

      before = sys.modules.keys()
      sys.path.append(os.path.dirname(self.path))
      execfile(self.path, global_dict)

      after = sys.modules.keys()

      dependents = []
      for key in after:
         if key not in before:
            m = sys.modules[key]
            if (m is not None) and ('__path__' in dir(m)):
               dependent = get_dependent(m.__name__)
               if (dependent is None):
                  new_dependent = Dependent(m.__name__, m.__path__)
                  dependents.append(new_dependent)
                  store_dependent(m.__name__, new_dependent)

      return dependents


   def _find_dependencies_subprocess(self):
      dependent = get_dependent(self.name)
      if dependent is None:

         # put something in the map now & pickle it so
         # subprocesses wont get stuck in a loop
         store_dependent(self.name, '')

         subprocess.call([sys.executable, sys.argv[0], "-m", self.name])

         store_dependent(self.name, self)

         f = open(self.name + ".pickle", "r")
         return pickle.load(f)
      else:
         return d.dependents

   def __str__(self):
      return self.__format_str__(0)

   def pretty_print(self, indent):
      s = operator.repeat(' ', indent) + self.name + "\n"
      indent = indent + 2
      for d in self.dependents:
         s += operator.repeat(' ', indent) + d.name + "\n"

      for d in self.dependents:
         s += d.pretty_print(indent) + "\n"

      #trim the last newline off
      return s[:-1]

   def generate_dot(self):
      s = ''
      for d in self.dependents:
         s += '  "' + self.name + '" -> "' + d.name + '";\n'
      return s

def find_dependencies_script(filename):
   script = Dependent(os.path.basename(filename).split(".")[0], filename, script=True)
   store_dependent(script.name, script)

   return

def find_dependencies_module(module):
   dependents = []
   before = sys.modules.keys()
   try:
      __import__(module)
   except:
      print "[ERROR] importing %s failed" % module
   after = sys.modules.keys()

   for key in after:
      if key not in before:
         m = sys.modules[key]
         if (m is not None) and ('__path__' in dir(m)):
            dependent = get_dependent(m.__name__)
            if (dependent is None):
               new_dependent = Dependent(m.__name__, m.__path__)
               dependents.append(new_dependent)
               store_dependent(m.__name__, new_dependent)

   f = open(module + ".pickle", "w")
   pickle.dump(dependents, f)

   return dependents

def clean_pickles():
   import glob
   pickles = glob.glob("*.pickle")
   for pickle in pickles:
      os.unlink(pickle)

def usage():
   print "usage:"
   print "  %s: <-m|-s> <module|script> [[-o] [filename]]" % sys.argv[0]
   sys.exit(65)


if __name__ == "__main__":
   if len(sys.argv) < 3:
      usage()

   if "-m" == sys.argv[1]:
      dependencies = find_dependencies_module(sys.argv[2])
   elif "-s" == sys.argv[1]:
      clean_pickles()
      find_dependencies_script(sys.argv[2])
   else:
      usage()

   if len(sys.argv) > 3:
      if sys.argv[3] == '-o':
         if len(sys.argv) > 4:
            generate_dot_file(sys.argv[4])
         else:
            name,ext = os.path.splitext(sys.argv[2])
            print_dependencies(name)
      else:
         usage()

   # only clean the pickles up if its a script, so the module subprocesses can find
   # them later
   #
   # TODO: add a command line flag for keeping the pickles
   #
   elif "-s" == sys.argv[1]:
      clean_pickles()
