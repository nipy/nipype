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
    conn = httplib.HTTPSConnection("api.github.com")
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


def get_file_url(object, hashmap):
    """Returns local or remote url for an object
    """
    filename = inspect.getsourcefile(object)
    lines = inspect.getsourcelines(object)
    uri = 'file://%s#L%d' % (filename, lines[1])
    if is_git_repo():
        o, _ = Popen('git hash-object %s' % filename, shell=True, stdout=PIPE,
                     cwd=os.path.dirname(nipype.__file__)).communicate()
        key = o.strip()
        if key in hashmap:
            uri = 'http://github.com/nipy/nipype/blob/master/' + \
                  hashmap[key] + '#L%d' % lines[1]
    return uri
