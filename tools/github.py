import httplib
import inspect
import json
import os
from subprocess import Popen, PIPE

import nipype


def is_git_repo():
    """Does the current nipype module have a git folder
    """
    sourcepath = os.path.realpath(os.path.join(os.path.dirname(nipype.__file__),
                                               os.path.pardir))
    gitpathgit = os.path.join(sourcepath, '.git')
    if os.path.exists(gitpathgit):
        return True
    else:
        return False


def get_local_branch():
    """Determine current branch
    """
    if is_git_repo():
        o, _ = Popen('git branch | grep "\* "', shell=True, stdout=PIPE,
                     cwd=os.path.dirname(nipype.__file__)).communicate()
        return o.strip()[2:]
    else:
        return None


def get_remote_branch():
    """Get remote branch for current branch
    """

    pass


def create_hash_map():
    """Create a hash map for all objects
    """

    hashmap = {}
    from base64 import encodestring as base64
    import pwd
    login_name = pwd.getpwuid(os.geteuid())[0]
    conn = httplib.HTTPSConnection("api.github.com")
    conn.request("GET", "/repos/nipy/nipype",
                 headers={'Authorization': 'Basic %s' % base64(login_name)})
    try:
        conn.request("GET", "/repos/nipy/nipype/git/trees/master?recursive=1")
    except:
        pass
    else:
        r1 = conn.getresponse()
        if r1.reason != 'OK':
            raise Exception('HTTP Response  %s:%s' % (r1.status, r1.reason))
        payload = json.loads(r1.read())
        for infodict in payload['tree']:
            if infodict['type'] == "blob":
                hashmap[infodict['sha']] = infodict['path']
    return hashmap


def get_repo_url(force_github=False):
    """Returns github url or local url

    Returns
    -------
    URI: str
       filesystem path or github repo url
    """
    sourcepath = os.path.realpath(os.path.join(os.path.dirname(nipype.__file__),
                                               os.path.pardir))
    gitpathgit = os.path.join(sourcepath, '.git')
    if not os.path.exists(gitpathgit) and not force_github:
        uri = 'file://%s' % sourcepath
    else:
        uri = 'http://github.com/nipy/nipype/blob/master'
    return uri


def get_file_url(object):
    """Returns local or remote url for an object
    """
    filename = inspect.getsourcefile(object)
    lines = inspect.getsourcelines(object)
    uri = 'file://%s#L%d' % (filename, lines[1])
    if is_git_repo():
        info = nipype.get_info()
        shortfile = os.path.join('nipype', filename.split('nipype/')[-1])
        uri = 'http://github.com/nipy/nipype/tree/%s/%s#L%d' % \
                                                           (info['commit_hash'],
                                                            shortfile, lines[1])
    return uri
