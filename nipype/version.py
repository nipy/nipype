version = '0.2'
release  = False

# Return the svn version as a string, raise a ValueError otherwise
# This code was copied from numpy trunk, revision 6873, and modified slightly
def svn_version():
    # Placed imports here (instead of top of module) so they're not
    # imported in released code
    import re
    import subprocess

    try:
        out = subprocess.Popen(['svn', 'info'], 
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        # We only care about stdout
        out = out.communicate()[0]
    except OSError:
        return ""

    # Searh for the 'Revision' tag
    r = re.compile('Revision: ([0-9]+)')
    svnver = ""
    for line in out.split('\n'):
        m = r.match(line)
        if m:
            svnver = m.group(1)
    return svnver

if not release:
    version += '.dev'
    svnver = svn_version()
    version += svnver

