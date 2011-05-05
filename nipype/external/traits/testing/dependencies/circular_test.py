import ImportSpy
import ImportManager
import sys
import os
import getopt



def usage():
    print "usage: %s [--chart] [-p] input" % sys.argv[0]

def generate_dot(parent, dependents):
    # omit standardy python modules
    import distutils.sysconfig
    dirs_to_omit = [ os.path.realpath(os.path.join(distutils.sysconfig.get_python_lib(), '..')) ]
    if 'win32' == sys.platform:
        for i in range(len(dirs_to_omit)):
            dir = dirs_to_omit[i]
            dirs_to_omit[i] = dir.lower()

    s = ''
    for d in dependents:
        try:
            __import__(d)
            file = sys.modules[d].__file__
            if 'win32' == sys.platform:
                file = file.lower()
            if os.path.dirname(file) not in dirs_to_omit:
                s += '  "' + parent + '" -> "' + d + '";\n'
            else:
                print "omitting " + d
        except Exception, ex:
            print "importing %s failed" % d
    return s

def generate_dot_file(top, dep_map, filename):
   s = 'digraph dependencies {\n'
   s += generate_dot(top, dep_map.keys())
   for key,value in dep_map.items():
      s += generate_dot(key, value)
   s += '}\n'

   f = open(filename, "w")
   f.write(s)
   f.close()

def main():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "p", ["chart"])
    except getopt.GetoptError, ex:
        print ex
        usage()
        sys.exit(65)

    if len(args) != 1:
        usage()
        sys.exit(65)

    package_flag = False
    chart_flag = False
    for opt,arg in opts:
        if opt == "-p":
            package_flag = True
        if opt == "--chart":
            chart_flag = True

    import_manager = ImportManager.ImportManager()
    import_manager.notifyOfNewFiles(ImportSpy.circular_tester)
    ImportSpy.activate(import_manager)

    if package_flag:
        __import__(args[0])
    else:
        #todo: tinker with __name__
        execfile(args[0])

    sys.path_hooks = sys.path_hooks[:-1]

    if chart_flag:
        dot_file = "dependencies.dot"
        generate_dot_file(args[0], ImportSpy.dependency_map, dot_file)

        #try to find 'dot'
        import subprocess
        if 0 == subprocess.call('dot -T svg -o %s %s' % (args[0] + ".svg", dot_file)):
            os.unlink(dot_file)


if __name__ == "__main__":
    main()

