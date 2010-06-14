# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
'''
Variant of node_wrapper that fetches and stores data on amazon's S3 using boto
'''

import os
from tempfile import mkdtemp
from ConfigParser import RawConfigParser

# Eventually, we'll want to hoist this stuff to something in nipype.utils
# But wait 'til it stabilizes here!
try:
    from boto.s3 import Connection
    import tables
    from boto.s3.key import Key
except ImportError:
    pass

class S3NodeWrapper(object):
    '''
    Wrapper for interface objects, done in a different style than NodeWrapper

    The wrapping is meant to achieve the following:
    1) Quarantine any processing such that original files are not modifiable by
    squirrely analysis programs
    2) Keep copies of things in such a way that it's easy to tell if something
    has already been done

    In particular, S3NodeWrapper introduces the notion of a URI to the
    identification of data resources
    Note that the logic here assumes that files in S3 do not change. This is
    somewhat redundant with the notion of URI.

    I'm also not implementing features until they are actually useful

    Parameters
    ----------
    interface : Interface instance
        e.g., fsl.Bet(frac=0.34), spm.Coregister()
    s3_storage : string
        root directory for s3 files
    base_directory : string
        root directory where working directories will be created
        two S3NodeWrappers using the same base_directory will share cached
        files already downloaded from s3.
        default=None, which results in the use of mkdtemp
    '''
    @property
    def inputs(self):
        return self.interface.inputs

    def __init__(self, interface, s3_directory, working_directory=None):
        self.interface = interface
        self.s3_directory = s3_directory
        self.base_directory = base_directory

# Candidate for hoisting
class S3Transporter(object):
    '''Connect one working directory with one URI root

    If you want more than one mapping, make more than one class

    Currently, only s3:// syntax is supported. It should be trivial to
    implement other formats, e.g. http, ftp, scp...
    
    There is also no error checking anywhere at this point. This should clearly
    be added at some point'''

    def __init__(self, working_directory, s3_root, s3env='shell'):
        '''Set up the environment for dealing with S3'''
        if s3env == 'shell':
            self.access_key = os.environ['AWS_ACCESS_KEY']
            self.secret_key = os.environ['AWS_SECRET_KEY']
        if s3env == 's3cfg':
            rcfg = RawConfigParser()
            rcfg.read(os.environ['HOME'] + '/.s3cfg')
            config = dict(rcfg.items('default'))
            self.access_key = config['access_key']
            self.secret_key = config['secret_key']
            # This stuff still needs to be done
            gpg_command = config['gpg_command']


        if self.access_key is None:
            raise Exception('AWS_ACCESS_KEY is not defined')
        if self.secret_key is None:
            raise Exception('AWS_SECRET_KEY is not defined')

        self.working_directory = working_directory
        try:
            self.s3_bucket, self.s3_key_prefix = \
                    s3_root.strip('/').split('/', 1)
        except ValueError:
            self.s3_bucket = s3_bucket.strip('/')
            self.s3_key_prefix = ''

        self.conn = Connection(aws_access_key_id=self.access_key, 
                       aws_secret_access_key=self.secret_key)
        self.bucket = self.conn.get_bucket(self.s3_bucket)
                
    def get(self, s3_path, local_path=None):
        '''Get a file corresponding to uri 

        Currently, authentication is handled by the standard amazon S3 environment
        variables for public and private keys.
        
        Parameters
        ----------
        s3_path : string
            path relative to the s3_root specified at __init__ time
        local_path : string
            Where to put the downloaded file
        '''
        if local_path is None:
            local_path = s3_path
        full_key = os.path.join(self.s3_key_prefix, s3_path)
        key = self.bucket.get_key(full_key)
        full_fname = os.path.join(self.working_directory, local_path)
        self.make_dirs(os.path.dirname(full_fname))
        f = open(full_fname, 'w')
        key.get_file(f)
        f.close()

    def put(self, s3_path, local_path):
        '''Put file from local path to s3 path'''
        if s3_path is None:
            s3_path = ''
        full_key = os.path.join(self.s3_key_prefix, s3_path)
        key = Key(self.bucket)
        key.key = full_key
        f = open(local_path, 'r')
        key.send_file(f)
        f.close()

    def make_dirs(self, path):
        '''Create intervening subdirectories as needed

        This should probably be a util function'''
        if not os.path.exists(path):
            self.make_dirs(os.path.dirname(path))
            os.mkdir(path)
        
