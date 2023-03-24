# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
""" Set of interfaces that allow interaction with data. Currently
    available interfaces are:

    DataSource: Generic nifti to named Nifti interface
    DataSink: Generic named output from interfaces to data store
    XNATSource: preliminary interface to XNAT

    To come :
    XNATSink
"""
import glob
import fnmatch
import string
import json
import os
import os.path as op
import shutil
import subprocess
import re
import copy
import tempfile
from os.path import join, dirname
from warnings import warn

from .. import config, logging
from ..utils.filemanip import (
    copyfile,
    simplify_list,
    ensure_list,
    get_related_files,
    split_filename,
)
from ..utils.misc import human_order_sorted, str2bool
from .base import (
    TraitedSpec,
    traits,
    Str,
    File,
    Directory,
    BaseInterface,
    InputMultiPath,
    isdefined,
    OutputMultiPath,
    DynamicTraitedSpec,
    Undefined,
    BaseInterfaceInputSpec,
    LibraryBaseInterface,
    SimpleInterface,
)

iflogger = logging.getLogger("nipype.interface")


def copytree(src, dst, use_hardlink=False):
    """Recursively copy a directory tree using
    nipype.utils.filemanip.copyfile()

    This is not a thread-safe routine. However, in the case of creating new
    directories, it checks to see if a particular directory has already been
    created by another process.
    """
    names = os.listdir(src)
    try:
        os.makedirs(dst)
    except OSError as why:
        if "File exists" in why.strerror:
            pass
        else:
            raise why
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if os.path.isdir(srcname):
                copytree(srcname, dstname, use_hardlink)
            else:
                copyfile(
                    srcname,
                    dstname,
                    True,
                    hashmethod="content",
                    use_hardlink=use_hardlink,
                )
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Exception as err:
            errors.extend(err.args[0])
    if errors:
        raise Exception(errors)


def add_traits(base, names, trait_type=None):
    """Add traits to a traited class.

    All traits are set to Undefined by default
    """
    if trait_type is None:
        trait_type = traits.Any
    undefined_traits = {}
    for key in names:
        base.add_trait(key, trait_type)
        undefined_traits[key] = Undefined
    base.trait_set(trait_change_notify=False, **undefined_traits)
    # access each trait
    for key in names:
        _ = getattr(base, key)
    return base


def _get_head_bucket(s3_resource, bucket_name):
    """Try to get the header info of a bucket, in order to
    check if it exists and its permissions
    """

    import botocore

    # Try fetch the bucket with the name argument
    try:
        s3_resource.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as exc:
        error_code = int(exc.response["Error"]["Code"])
        if error_code == 403:
            err_msg = "Access to bucket: %s is denied; check credentials" % bucket_name
            raise Exception(err_msg)
        elif error_code == 404:
            err_msg = (
                "Bucket: %s does not exist; check spelling and try "
                "again" % bucket_name
            )
            raise Exception(err_msg)
        else:
            err_msg = "Unable to connect to bucket: %s. Error message:\n%s" % (
                bucket_name,
                exc,
            )
    except Exception as exc:
        err_msg = "Unable to connect to bucket: %s. Error message:\n%s" % (
            bucket_name,
            exc,
        )
        raise Exception(err_msg)


class IOBase(BaseInterface):
    def _run_interface(self, runtime):
        return runtime

    def _list_outputs(self):
        raise NotImplementedError

    def _outputs(self):
        return self._add_output_traits(super(IOBase, self)._outputs())

    def _add_output_traits(self, base):
        return base


# Class to track percentage of S3 file upload
class ProgressPercentage(object):
    """
    Callable class instsance (via __call__ method) that displays
    upload percentage of a file to S3
    """

    def __init__(self, filename):
        """ """

        # Import packages
        import threading

        # Initialize data attributes
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        """ """

        # Import packages
        import sys

        # With the lock on, print upload status
        with self._lock:
            self._seen_so_far += bytes_amount
            if self._size != 0:
                percentage = (self._seen_so_far // self._size) * 100
            else:
                percentage = 0
            progress_str = "%d / %d (%.2f%%)\r" % (
                self._seen_so_far,
                self._size,
                percentage,
            )

            # Write to stdout
            sys.stdout.write(progress_str)
            sys.stdout.flush()


# DataSink inputs
class DataSinkInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    """ """

    # Init inputspec data attributes
    base_directory = Str(desc="Path to the base directory for storing data.")
    container = Str(desc="Folder within base directory in which to store output")
    parameterization = traits.Bool(
        True, usedefault=True, desc="store output in parametrized structure"
    )
    strip_dir = Str(desc="path to strip out of filename")
    substitutions = InputMultiPath(
        traits.Tuple(Str, Str),
        desc=(
            "List of 2-tuples reflecting string "
            "to substitute and string to replace "
            "it with"
        ),
    )
    regexp_substitutions = InputMultiPath(
        traits.Tuple(Str, Str),
        desc=(
            "List of 2-tuples reflecting a pair of a "
            "Python regexp pattern and a replacement "
            "string. Invoked after string `substitutions`"
        ),
    )

    _outputs = traits.Dict(Str, value={}, usedefault=True)
    remove_dest_dir = traits.Bool(
        False, usedefault=True, desc="remove dest directory when copying dirs"
    )

    # AWS S3 data attributes
    creds_path = Str(
        desc="Filepath to AWS credentials file for S3 bucket "
        "access; if not specified, the credentials will "
        "be taken from the AWS_ACCESS_KEY_ID and "
        "AWS_SECRET_ACCESS_KEY environment variables"
    )
    encrypt_bucket_keys = traits.Bool(
        desc="Flag indicating whether to use S3 " "server-side AES-256 encryption"
    )
    # Set this if user wishes to override the bucket with their own
    bucket = traits.Any(desc="Boto3 S3 bucket for manual override of bucket")
    # Set this if user wishes to have local copy of files as well
    local_copy = Str(desc="Copy files locally as well as to S3 bucket")

    # Set call-able inputs attributes
    def __setattr__(self, key, value):
        if key not in self.copyable_trait_names():
            if not isdefined(value):
                super(DataSinkInputSpec, self).__setattr__(key, value)
            self._outputs[key] = value
        else:
            if key in self._outputs:
                self._outputs[key] = value
            super(DataSinkInputSpec, self).__setattr__(key, value)


# DataSink outputs
class DataSinkOutputSpec(TraitedSpec):
    # Init out file
    out_file = traits.Any(desc="datasink output")


# Custom DataSink class
class DataSink(IOBase):
    """
    Generic datasink module to store structured outputs.

    Primarily for use within a workflow. This interface allows arbitrary
    creation of input attributes. The names of these attributes define the
    directory structure to create for storage of the files or directories.

    The attributes take the following form::

      string[[.[@]]string[[.[@]]string]] ...

    where parts between ``[]`` are optional.

    An attribute such as contrasts.@con will create a 'contrasts' directory
    to store the results linked to the attribute. If the ``@`` is left out, such
    as in 'contrasts.con', a subdirectory 'con' will be created under
    'contrasts'.

    The general form of the output is::

       'base_directory/container/parameterization/destloc/filename'

    ``destloc = string[[.[@]]string[[.[@]]string]]`` and
    ``filename`` come from the input to the connect statement.

    .. warning::

        This is not a thread-safe node because it can write to a common
        shared location. It will not complain when it overwrites a file.

    .. note::

        If both substitutions and regexp_substitutions are used, then
        substitutions are applied first followed by regexp_substitutions.

        This interface **cannot** be used in a MapNode as the inputs are
        defined only when the connect statement is executed.

    Examples
    --------
    >>> ds = DataSink()
    >>> ds.inputs.base_directory = 'results_dir'
    >>> ds.inputs.container = 'subject'
    >>> ds.inputs.structural = 'structural.nii'
    >>> setattr(ds.inputs, 'contrasts.@con', ['cont1.nii', 'cont2.nii'])
    >>> setattr(ds.inputs, 'contrasts.alt', ['cont1a.nii', 'cont2a.nii'])
    >>> ds.run()  # doctest: +SKIP

    To use DataSink in a MapNode, its inputs have to be defined at the
    time the interface is created.

    >>> ds = DataSink(infields=['contasts.@con'])
    >>> ds.inputs.base_directory = 'results_dir'
    >>> ds.inputs.container = 'subject'
    >>> ds.inputs.structural = 'structural.nii'
    >>> setattr(ds.inputs, 'contrasts.@con', ['cont1.nii', 'cont2.nii'])
    >>> setattr(ds.inputs, 'contrasts.alt', ['cont1a.nii', 'cont2a.nii'])
    >>> ds.run()  # doctest: +SKIP

    """

    # Give obj .inputs and .outputs
    input_spec = DataSinkInputSpec
    output_spec = DataSinkOutputSpec

    # Initialization method to set up datasink
    def __init__(self, infields=None, force_run=True, **kwargs):
        """
        Parameters
        ----------
        infields : list of str
            Indicates the input fields to be dynamically created
        """

        super(DataSink, self).__init__(**kwargs)
        undefined_traits = {}
        # used for mandatory inputs check
        self._infields = infields
        if infields:
            for key in infields:
                self.inputs.add_trait(key, traits.Any)
                self.inputs._outputs[key] = Undefined
                undefined_traits[key] = Undefined
        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)
        if force_run:
            self._always_run = True

    # Get destination paths
    def _get_dst(self, src):
        # If path is directory with trailing os.path.sep,
        # then remove that for a more robust behavior
        src = src.rstrip(os.path.sep)
        path, fname = os.path.split(src)
        if self.inputs.parameterization:
            dst = path
            if isdefined(self.inputs.strip_dir):
                dst = dst.replace(self.inputs.strip_dir, "")
            folders = [
                folder for folder in dst.split(os.path.sep) if folder.startswith("_")
            ]
            dst = os.path.sep.join(folders)
            if fname:
                dst = os.path.join(dst, fname)
        else:
            if fname:
                dst = fname
            else:
                dst = path.split(os.path.sep)[-1]
        if dst[0] == os.path.sep:
            dst = dst[1:]
        return dst

    # Substitute paths in substitutions dictionary parameter
    def _substitute(self, pathstr):
        pathstr_ = pathstr
        if isdefined(self.inputs.substitutions):
            for key, val in self.inputs.substitutions:
                oldpathstr = pathstr
                pathstr = pathstr.replace(key, val)
                if pathstr != oldpathstr:
                    iflogger.debug(
                        "sub.str: %s -> %s using %r -> %r",
                        oldpathstr,
                        pathstr,
                        key,
                        val,
                    )
        if isdefined(self.inputs.regexp_substitutions):
            for key, val in self.inputs.regexp_substitutions:
                oldpathstr = pathstr
                pathstr, _ = re.subn(key, val, pathstr)
                if pathstr != oldpathstr:
                    iflogger.debug(
                        "sub.regexp: %s -> %s using %r -> %r",
                        oldpathstr,
                        pathstr,
                        key,
                        val,
                    )
        if pathstr_ != pathstr:
            iflogger.info("sub: %s -> %s", pathstr_, pathstr)
        return pathstr

    # Check for s3 in base directory
    def _check_s3_base_dir(self):
        """
        Method to see if the datasink's base directory specifies an
        S3 bucket path; if it does, it parses the path for the bucket
        name in the form 's3://bucket_name/...' and returns it

        Parameters
        ----------

        Returns
        -------
        s3_flag : boolean
            flag indicating whether the base_directory contained an
            S3 bucket path
        bucket_name : string
            name of the S3 bucket to connect to; if the base directory
            is not a valid S3 path, defaults to '<N/A>'
        """

        s3_str = "s3://"
        bucket_name = "<N/A>"
        base_directory = self.inputs.base_directory

        if not isdefined(base_directory):
            s3_flag = False
            return s3_flag, bucket_name

        s3_flag = base_directory.lower().startswith(s3_str)
        if s3_flag:
            bucket_name = base_directory[len(s3_str) :].partition("/")[0]

        return s3_flag, bucket_name

    # Function to return AWS secure environment variables
    def _return_aws_keys(self):
        """
        Method to return AWS access key id and secret access key using
        credentials found in a local file.

        Parameters
        ----------
        self : nipype.interfaces.io.DataSink
            self for instance method

        Returns
        -------
        aws_access_key_id : string
            string of the AWS access key ID
        aws_secret_access_key : string
            string of the AWS secret access key
        """

        # Import packages
        import os

        # Init variables
        creds_path = self.inputs.creds_path

        # Check if creds exist
        if creds_path and os.path.exists(creds_path):
            with open(creds_path, "r") as creds_in:
                # Grab csv rows
                row1 = creds_in.readline()
                row2 = creds_in.readline()

            # Are they root or user keys
            if "User Name" in row1:
                # And split out for keys
                aws_access_key_id = row2.split(",")[1]
                aws_secret_access_key = row2.split(",")[2]
            elif "AWSAccessKeyId" in row1:
                # And split out for keys
                aws_access_key_id = row1.split("=")[1]
                aws_secret_access_key = row2.split("=")[1]
            else:
                err_msg = "Credentials file not recognized, check file is correct"
                raise Exception(err_msg)

            # Strip any carriage return/line feeds
            aws_access_key_id = aws_access_key_id.replace("\r", "").replace("\n", "")
            aws_secret_access_key = aws_secret_access_key.replace("\r", "").replace(
                "\n", ""
            )
        else:
            aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        # Return keys
        return aws_access_key_id, aws_secret_access_key

    # Fetch bucket object
    def _fetch_bucket(self, bucket_name):
        """
        Method to return a bucket object which can be used to interact
        with an AWS S3 bucket using credentials found in a local file.

        Parameters
        ----------
        self : nipype.interfaces.io.DataSink
            self for instance method
        bucket_name : string
            string corresponding to the name of the bucket on S3

        Returns
        -------
        bucket : boto3.resources.factory.s3.Bucket
            boto3 s3 Bucket object which is used to interact with files
            in an S3 bucket on AWS
        """

        # Import packages
        try:
            import boto3
            import botocore
        except ImportError as exc:
            err_msg = "Boto3 package is not installed - install boto3 and " "try again."
            raise Exception(err_msg)

        # Init variables
        creds_path = self.inputs.creds_path

        # Get AWS credentials
        try:
            aws_access_key_id, aws_secret_access_key = self._return_aws_keys()
        except Exception as exc:
            err_msg = (
                "There was a problem extracting the AWS credentials "
                "from the credentials file provided: %s. Error:\n%s" % (creds_path, exc)
            )
            raise Exception(err_msg)

        # Try and get AWS credentials if a creds_path is specified
        if aws_access_key_id and aws_secret_access_key:
            # Init connection
            iflogger.info(
                "Connecting to S3 bucket: %s with credentials...", bucket_name
            )
            # Use individual session for each instance of DataSink
            # Better when datasinks are being used in multi-threading, see:
            # http://boto3.readthedocs.org/en/latest/guide/resources.html#multithreading
            session = boto3.session.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )

        else:
            iflogger.info("Connecting to S3 bucket: %s with IAM role...", bucket_name)

            # Lean on AWS environment / IAM role authentication and authorization
            session = boto3.session.Session()

        s3_resource = session.resource("s3", use_ssl=True)

        # And try fetch the bucket with the name argument
        try:
            _get_head_bucket(s3_resource, bucket_name)
        except Exception as exc:
            # Try to connect anonymously
            s3_resource.meta.client.meta.events.register(
                "choose-signer.s3.*", botocore.handlers.disable_signing
            )

            iflogger.info("Connecting to AWS: %s anonymously...", bucket_name)
            _get_head_bucket(s3_resource, bucket_name)

        # Explicitly declare a secure SSL connection for bucket object
        bucket = s3_resource.Bucket(bucket_name)

        # Return the bucket
        return bucket

    # Send up to S3 method
    def _upload_to_s3(self, bucket, src, dst):
        """
        Method to upload outputs to S3 bucket instead of on local disk
        """

        # Import packages
        import hashlib
        import os

        from botocore.exceptions import ClientError

        s3_str = "s3://"
        s3_prefix = s3_str + bucket.name

        # Explicitly lower-case the "s3"
        if dst.lower().startswith(s3_str):
            dst = s3_str + dst[len(s3_str) :]

        # If src is a directory, collect files (this assumes dst is a dir too)
        if os.path.isdir(src):
            src_files = []
            for root, dirs, files in os.walk(src):
                src_files.extend([os.path.join(root, fil) for fil in files])
            # Make the dst files have the dst folder as base dir
            dst_files = [os.path.join(dst, src_f.split(src)[1]) for src_f in src_files]
        else:
            src_files = [src]
            dst_files = [dst]

        # Iterate over src and copy to dst
        for src_idx, src_f in enumerate(src_files):
            # Get destination filename/keyname
            dst_f = dst_files[src_idx]
            dst_k = dst_f.replace(s3_prefix, "").lstrip("/")

            # See if same file is already up there
            try:
                dst_obj = bucket.Object(key=dst_k)
                dst_md5 = dst_obj.e_tag.strip('"')

                # See if same file is already there
                src_read = open(src_f, "rb").read()
                src_md5 = hashlib.md5(src_read).hexdigest()
                # Move to next loop iteration
                if dst_md5 == src_md5:
                    iflogger.info("File %s already exists on S3, skipping...", dst_f)
                    continue
                else:
                    iflogger.info("Overwriting previous S3 file...")

            except ClientError:
                iflogger.info("New file to S3")

            # Copy file up to S3 (either encrypted or not)
            iflogger.info(
                "Uploading %s to S3 bucket, %s, as %s...", src_f, bucket.name, dst_f
            )
            if self.inputs.encrypt_bucket_keys:
                extra_args = {"ServerSideEncryption": "AES256"}
            else:
                extra_args = {}
            bucket.upload_file(
                src_f, dst_k, ExtraArgs=extra_args, Callback=ProgressPercentage(src_f)
            )

    # List outputs, main run routine
    def _list_outputs(self):
        """Execute this module."""

        # Init variables
        outputs = self.output_spec().get()
        out_files = []
        # Use hardlink
        use_hardlink = str2bool(config.get("execution", "try_hard_link_datasink"))

        # Set local output directory if specified
        if isdefined(self.inputs.local_copy):
            outdir = self.inputs.local_copy
        else:
            outdir = self.inputs.base_directory
            # If base directory isn't given, assume current directory
            if not isdefined(outdir):
                outdir = "."

        # Check if base directory reflects S3 bucket upload
        s3_flag, bucket_name = self._check_s3_base_dir()
        if s3_flag:
            s3dir = self.inputs.base_directory
            # If user overrides bucket object, use that
            if self.inputs.bucket:
                bucket = self.inputs.bucket
            # Otherwise fetch bucket object using name
            else:
                try:
                    bucket = self._fetch_bucket(bucket_name)
                # If encountering an exception during bucket access, set output
                # base directory to a local folder
                except Exception as exc:
                    s3dir = "<N/A>"
                    if not isdefined(self.inputs.local_copy):
                        local_out_exception = os.path.join(
                            os.path.expanduser("~"), "s3_datasink_" + bucket_name
                        )
                        outdir = local_out_exception
                    # Log local copying directory
                    iflogger.info(
                        "Access to S3 failed! Storing outputs locally at: "
                        "%s\nError: %s",
                        outdir,
                        exc,
                    )
        else:
            s3dir = "<N/A>"

        # If container input is given, append that to outdir
        if isdefined(self.inputs.container):
            outdir = os.path.join(outdir, self.inputs.container)
            s3dir = os.path.join(s3dir, self.inputs.container)

        # If sinking to local folder
        if outdir != s3dir:
            outdir = os.path.abspath(outdir)
            # Create the directory if it doesn't exist
            if not os.path.exists(outdir):
                try:
                    os.makedirs(outdir)
                except OSError as inst:
                    if "File exists" in inst.strerror:
                        pass
                    else:
                        raise (inst)

        # Iterate through outputs attributes {key : path(s)}
        for key, files in list(self.inputs._outputs.items()):
            if not isdefined(files):
                continue
            iflogger.debug("key: %s files: %s", key, str(files))
            files = ensure_list(files)
            tempoutdir = outdir
            if s3_flag:
                s3tempoutdir = s3dir
            for d in key.split("."):
                if d[0] == "@":
                    continue
                tempoutdir = os.path.join(tempoutdir, d)
                if s3_flag:
                    s3tempoutdir = os.path.join(s3tempoutdir, d)

            # flattening list
            if isinstance(files, list):
                if isinstance(files[0], list):
                    files = [item for sublist in files for item in sublist]

            # Iterate through passed-in source files
            for src in ensure_list(files):
                # Format src and dst files
                src = os.path.abspath(src)
                if not os.path.isfile(src):
                    src = os.path.join(src, "")
                dst = self._get_dst(src)
                if s3_flag:
                    s3dst = os.path.join(s3tempoutdir, dst)
                    s3dst = self._substitute(s3dst)
                dst = os.path.join(tempoutdir, dst)
                dst = self._substitute(dst)
                path, _ = os.path.split(dst)

                # If we're uploading to S3
                if s3_flag:
                    self._upload_to_s3(bucket, src, s3dst)
                    out_files.append(s3dst)
                # Otherwise, copy locally src -> dst
                if not s3_flag or isdefined(self.inputs.local_copy):
                    # Create output directory if it doesn't exist
                    if not os.path.exists(path):
                        try:
                            os.makedirs(path)
                        except OSError as inst:
                            if "File exists" in inst.strerror:
                                pass
                            else:
                                raise (inst)
                    # If src is a file, copy it to dst
                    if os.path.isfile(src):
                        iflogger.debug("copyfile: %s %s", src, dst)
                        copyfile(
                            src,
                            dst,
                            copy=True,
                            hashmethod="content",
                            use_hardlink=use_hardlink,
                        )
                        out_files.append(dst)
                    # If src is a directory, copy entire contents to dst dir
                    elif os.path.isdir(src):
                        if os.path.exists(dst) and self.inputs.remove_dest_dir:
                            iflogger.debug("removing: %s", dst)
                            shutil.rmtree(dst)
                        iflogger.debug("copydir: %s %s", src, dst)
                        copytree(src, dst)
                        out_files.append(dst)

        # Return outputs dictionary
        outputs["out_file"] = out_files

        return outputs


class S3DataGrabberInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    anon = traits.Bool(
        False,
        usedefault=True,
        desc="Use anonymous connection to s3.  If this is set to True, boto may print"
        " a urlopen error, but this does not prevent data from being downloaded.",
    )
    region = Str("us-east-1", usedefault=True, desc="Region of s3 bucket")
    bucket = Str(mandatory=True, desc="Amazon S3 bucket where your data is stored")
    bucket_path = Str(
        "", usedefault=True, desc="Location within your bucket for subject data."
    )
    local_directory = Directory(
        exists=True,
        desc="Path to the local directory for subject data to be downloaded "
        "and accessed. Should be on HDFS for Spark jobs.",
    )
    raise_on_empty = traits.Bool(
        True,
        usedefault=True,
        desc="Generate exception if list is empty for a given field",
    )
    sort_filelist = traits.Bool(
        mandatory=True, desc="Sort the filelist that matches the template"
    )
    template = Str(
        mandatory=True,
        desc="Layout used to get files. Relative to bucket_path if defined."
        "Uses regex rather than glob style formatting.",
    )
    template_args = traits.Dict(
        key_trait=Str,
        value_trait=traits.List(traits.List),
        desc="Information to plug into template",
    )


class S3DataGrabber(LibraryBaseInterface, IOBase):
    """
    Pull data from an Amazon S3 Bucket.

    Generic datagrabber module that wraps around glob in an
    intelligent way for neuroimaging tasks to grab files from
    Amazon S3

    Works exactly like DataGrabber, except, you must specify an
    S3 "bucket" and "bucket_path" to search for your data and a
    "local_directory" to store the data. "local_directory"
    should be a location on HDFS for Spark jobs. Additionally,
    "template" uses regex style formatting, rather than the
    glob-style found in the original DataGrabber.

    Examples
    --------
    >>> s3grab = S3DataGrabber(infields=['subj_id'], outfields=["func", "anat"])
    >>> s3grab.inputs.bucket = 'openneuro'
    >>> s3grab.inputs.sort_filelist = True
    >>> s3grab.inputs.template = '*'
    >>> s3grab.inputs.anon = True
    >>> s3grab.inputs.bucket_path = 'ds000101/ds000101_R2.0.0/uncompressed/'
    >>> s3grab.inputs.local_directory = '/tmp'
    >>> s3grab.inputs.field_template = {'anat': '%s/anat/%s_T1w.nii.gz',
    ...                                 'func': '%s/func/%s_task-simon_run-1_bold.nii.gz'}
    >>> s3grab.inputs.template_args = {'anat': [['subj_id', 'subj_id']],
    ...                                'func': [['subj_id', 'subj_id']]}
    >>> s3grab.inputs.subj_id = 'sub-01'
    >>> s3grab.run()  # doctest: +SKIP

    """

    input_spec = S3DataGrabberInputSpec
    output_spec = DynamicTraitedSpec
    _always_run = True
    _pkg = "boto"

    def __init__(self, infields=None, outfields=None, **kwargs):
        """
        Parameters
        ----------
        infields : list of str
            Indicates the input fields to be dynamically created

        outfields: list of str
            Indicates output fields to be dynamically created

        See class examples for usage

        """
        if not outfields:
            outfields = ["outfiles"]
        super(S3DataGrabber, self).__init__(**kwargs)
        undefined_traits = {}
        # used for mandatory inputs check
        self._infields = infields
        self._outfields = outfields
        if infields:
            for key in infields:
                self.inputs.add_trait(key, traits.Any)
                undefined_traits[key] = Undefined
        # add ability to insert field specific templates
        self.inputs.add_trait(
            "field_template",
            traits.Dict(
                traits.Enum(outfields), desc="arguments that fit into template"
            ),
        )
        undefined_traits["field_template"] = Undefined
        if not isdefined(self.inputs.template_args):
            self.inputs.template_args = {}
        for key in outfields:
            if key not in self.inputs.template_args:
                if infields:
                    self.inputs.template_args[key] = [infields]
                else:
                    self.inputs.template_args[key] = []

        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

    def _add_output_traits(self, base):
        """
        S3 specific: Downloads relevant files to a local folder specified

        Using traits.Any instead out OutputMultiPath till add_trait bug
        is fixed.
        """
        return add_traits(base, list(self.inputs.template_args.keys()))

    def _list_outputs(self):
        # infields are mandatory, however I could not figure out how to set 'mandatory' flag dynamically
        # hence manual check
        import boto

        if self._infields:
            for key in self._infields:
                value = getattr(self.inputs, key)
                if not isdefined(value):
                    msg = (
                        "%s requires a value for input '%s' because it was listed in 'infields'"
                        % (self.__class__.__name__, key)
                    )
                    raise ValueError(msg)

        outputs = {}
        # get list of all files in s3 bucket
        conn = boto.connect_s3(anon=self.inputs.anon)
        bkt = conn.get_bucket(self.inputs.bucket)
        bkt_files = list(k.key for k in bkt.list(prefix=self.inputs.bucket_path))

        # keys are outfields, args are template args for the outfield
        for key, args in list(self.inputs.template_args.items()):
            outputs[key] = []
            template = self.inputs.template
            if (
                hasattr(self.inputs, "field_template")
                and isdefined(self.inputs.field_template)
                and key in self.inputs.field_template
            ):
                template = self.inputs.field_template[
                    key
                ]  # template override for multiple outfields
            if isdefined(self.inputs.bucket_path):
                template = os.path.join(self.inputs.bucket_path, template)
            if not args:
                filelist = []
                for fname in bkt_files:
                    if re.match(template, fname):
                        filelist.append(fname)
                if len(filelist) == 0:
                    msg = "Output key: %s Template: %s returned no files" % (
                        key,
                        template,
                    )
                    if self.inputs.raise_on_empty:
                        raise IOError(msg)
                    else:
                        warn(msg)
                else:
                    if self.inputs.sort_filelist:
                        filelist = human_order_sorted(filelist)
                    outputs[key] = simplify_list(filelist)
            for argnum, arglist in enumerate(args):
                maxlen = 1
                for arg in arglist:
                    if isinstance(arg, (str, bytes)) and hasattr(self.inputs, arg):
                        arg = getattr(self.inputs, arg)
                    if isinstance(arg, list):
                        if (maxlen > 1) and (len(arg) != maxlen):
                            raise ValueError(
                                "incompatible number of arguments for %s" % key
                            )
                        if len(arg) > maxlen:
                            maxlen = len(arg)
                outfiles = []
                for i in range(maxlen):
                    argtuple = []
                    for arg in arglist:
                        if isinstance(arg, (str, bytes)) and hasattr(self.inputs, arg):
                            arg = getattr(self.inputs, arg)
                        if isinstance(arg, list):
                            argtuple.append(arg[i])
                        else:
                            argtuple.append(arg)
                    filledtemplate = template
                    if argtuple:
                        try:
                            filledtemplate = template % tuple(argtuple)
                        except TypeError as e:
                            raise TypeError(
                                f"{e}: Template {template} failed to convert "
                                f"with args {tuple(argtuple)}"
                            )
                    outfiles = []
                    for fname in bkt_files:
                        if re.match(filledtemplate, fname):
                            outfiles.append(fname)
                    if len(outfiles) == 0:
                        msg = "Output key: %s Template: %s returned no files" % (
                            key,
                            filledtemplate,
                        )
                        if self.inputs.raise_on_empty:
                            raise IOError(msg)
                        else:
                            warn(msg)
                        outputs[key].append(None)
                    else:
                        if self.inputs.sort_filelist:
                            outfiles = human_order_sorted(outfiles)
                        outputs[key].append(simplify_list(outfiles))
            if any([val is None for val in outputs[key]]):
                outputs[key] = []
            if len(outputs[key]) == 0:
                outputs[key] = None
            elif len(outputs[key]) == 1:
                outputs[key] = outputs[key][0]
        # Outputs are currently stored as locations on S3.
        # We must convert to the local location specified
        # and download the files.
        for key, val in outputs.items():
            # This will basically be either list-like or string-like:
            # if it's an instance of a list, we'll iterate through it.
            # If it isn't, it's string-like (string, unicode), we
            # convert that value directly.
            if isinstance(val, (list, tuple, set)):
                for i, path in enumerate(val):
                    outputs[key][i] = self.s3tolocal(path, bkt)
            else:
                outputs[key] = self.s3tolocal(val, bkt)

        return outputs

    # Takes an s3 address and downloads the file to a local
    # directory, returning the local path.
    def s3tolocal(self, s3path, bkt):
        import boto

        # path formatting
        local_directory = str(self.inputs.local_directory)
        bucket_path = str(self.inputs.bucket_path)
        template = str(self.inputs.template)
        if not os.path.basename(local_directory) == "":
            local_directory += "/"
        if not os.path.basename(bucket_path) == "":
            bucket_path += "/"
        if template[0] == "/":
            template = template[1:]

        localpath = s3path.replace(bucket_path, local_directory)
        localdir = os.path.split(localpath)[0]
        if not os.path.exists(localdir):
            os.makedirs(localdir)
        k = boto.s3.key.Key(bkt)
        k.key = s3path
        k.get_contents_to_filename(localpath)
        return localpath


class DataGrabberInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    base_directory = Directory(
        exists=True, desc="Path to the base directory consisting of subject data."
    )
    raise_on_empty = traits.Bool(
        True,
        usedefault=True,
        desc="Generate exception if list is empty for a given field",
    )
    drop_blank_outputs = traits.Bool(
        False, usedefault=True, desc="Remove ``None`` entries from output lists"
    )
    sort_filelist = traits.Bool(
        mandatory=True, desc="Sort the filelist that matches the template"
    )
    template = Str(
        mandatory=True,
        desc="Layout used to get files. relative to base directory if defined",
    )
    template_args = traits.Dict(
        key_trait=Str,
        value_trait=traits.List(traits.List),
        desc="Information to plug into template",
    )


class DataGrabber(IOBase):
    """
    Find files on a filesystem.

    Generic datagrabber module that wraps around glob in an
    intelligent way for neuroimaging tasks to grab files

    .. important::

       Doesn't support directories currently

    Examples
    --------
    >>> from nipype.interfaces.io import DataGrabber

    Pick all files from current directory

    >>> dg = DataGrabber()
    >>> dg.inputs.template = '*'

    Pick file foo/foo.nii from current directory

    >>> dg.inputs.template = '%s/%s.dcm'
    >>> dg.inputs.template_args['outfiles']=[['dicomdir','123456-1-1.dcm']]

    Same thing but with dynamically created fields

    >>> dg = DataGrabber(infields=['arg1','arg2'])
    >>> dg.inputs.template = '%s/%s.nii'
    >>> dg.inputs.arg1 = 'foo'
    >>> dg.inputs.arg2 = 'foo'

    however this latter form can be used with iterables and iterfield in a
    pipeline.

    Dynamically created, user-defined input and output fields

    >>> dg = DataGrabber(infields=['sid'], outfields=['func','struct','ref'])
    >>> dg.inputs.base_directory = '.'
    >>> dg.inputs.template = '%s/%s.nii'
    >>> dg.inputs.template_args['func'] = [['sid',['f3','f5']]]
    >>> dg.inputs.template_args['struct'] = [['sid',['struct']]]
    >>> dg.inputs.template_args['ref'] = [['sid','ref']]
    >>> dg.inputs.sid = 's1'

    Change the template only for output field struct. The rest use the
    general template

    >>> dg.inputs.field_template = dict(struct='%s/struct.nii')
    >>> dg.inputs.template_args['struct'] = [['sid']]

    """

    input_spec = DataGrabberInputSpec
    output_spec = DynamicTraitedSpec
    _always_run = True

    def __init__(self, infields=None, outfields=None, **kwargs):
        """
        Parameters
        ----------
        infields : list of str
            Indicates the input fields to be dynamically created

        outfields: list of str
            Indicates output fields to be dynamically created

        See class examples for usage

        """
        if not outfields:
            outfields = ["outfiles"]
        super(DataGrabber, self).__init__(**kwargs)
        undefined_traits = {}
        # used for mandatory inputs check
        self._infields = infields
        self._outfields = outfields
        if infields:
            for key in infields:
                self.inputs.add_trait(key, traits.Any)
                undefined_traits[key] = Undefined
        # add ability to insert field specific templates
        self.inputs.add_trait(
            "field_template",
            traits.Dict(
                traits.Enum(outfields), desc="arguments that fit into template"
            ),
        )
        undefined_traits["field_template"] = Undefined
        if not isdefined(self.inputs.template_args):
            self.inputs.template_args = {}
        for key in outfields:
            if key not in self.inputs.template_args:
                if infields:
                    self.inputs.template_args[key] = [infields]
                else:
                    self.inputs.template_args[key] = []

        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

    def _add_output_traits(self, base):
        """

        Using traits.Any instead out OutputMultiPath till add_trait bug
        is fixed.
        """
        return add_traits(base, list(self.inputs.template_args.keys()))

    def _list_outputs(self):
        # infields are mandatory, however I could not figure out how to set 'mandatory' flag dynamically
        # hence manual check
        if self._infields:
            for key in self._infields:
                value = getattr(self.inputs, key)
                if not isdefined(value):
                    msg = (
                        "%s requires a value for input '%s' because it was listed in 'infields'"
                        % (self.__class__.__name__, key)
                    )
                    raise ValueError(msg)

        outputs = {}
        for key, args in list(self.inputs.template_args.items()):
            outputs[key] = []
            template = self.inputs.template
            if (
                hasattr(self.inputs, "field_template")
                and isdefined(self.inputs.field_template)
                and key in self.inputs.field_template
            ):
                template = self.inputs.field_template[key]
            if isdefined(self.inputs.base_directory):
                template = os.path.join(
                    os.path.abspath(self.inputs.base_directory), template
                )
            else:
                template = os.path.abspath(template)
            if not args:
                filelist = glob.glob(template)
                if len(filelist) == 0:
                    msg = "Output key: %s Template: %s returned no files" % (
                        key,
                        template,
                    )
                    if self.inputs.raise_on_empty:
                        raise IOError(msg)
                    else:
                        warn(msg)
                else:
                    if self.inputs.sort_filelist:
                        filelist = human_order_sorted(filelist)
                    outputs[key] = simplify_list(filelist)
            for argnum, arglist in enumerate(args):
                maxlen = 1
                for arg in arglist:
                    if isinstance(arg, (str, bytes)) and hasattr(self.inputs, arg):
                        arg = getattr(self.inputs, arg)
                    if isinstance(arg, list):
                        if (maxlen > 1) and (len(arg) != maxlen):
                            raise ValueError(
                                "incompatible number of arguments for %s" % key
                            )
                        if len(arg) > maxlen:
                            maxlen = len(arg)
                outfiles = []
                for i in range(maxlen):
                    argtuple = []
                    for arg in arglist:
                        if isinstance(arg, (str, bytes)) and hasattr(self.inputs, arg):
                            arg = getattr(self.inputs, arg)
                        if isinstance(arg, list):
                            argtuple.append(arg[i])
                        else:
                            argtuple.append(arg)
                    filledtemplate = template
                    if argtuple:
                        try:
                            filledtemplate = template % tuple(argtuple)
                        except TypeError as e:
                            raise TypeError(
                                f"{e}: Template {template} failed to convert "
                                f"with args {tuple(argtuple)}"
                            )
                    outfiles = glob.glob(filledtemplate)
                    if len(outfiles) == 0:
                        msg = "Output key: %s Template: %s returned no files" % (
                            key,
                            filledtemplate,
                        )
                        if self.inputs.raise_on_empty:
                            raise IOError(msg)
                        else:
                            warn(msg)
                        outputs[key].append(None)
                    else:
                        if self.inputs.sort_filelist:
                            outfiles = human_order_sorted(outfiles)
                        outputs[key].append(simplify_list(outfiles))
            if self.inputs.drop_blank_outputs:
                outputs[key] = [x for x in outputs[key] if x is not None]
            else:
                if any([val is None for val in outputs[key]]):
                    outputs[key] = []
            if len(outputs[key]) == 0:
                outputs[key] = None
            elif len(outputs[key]) == 1:
                outputs[key] = outputs[key][0]
        return outputs


class SelectFilesInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    base_directory = Directory(exists=True, desc="Root path common to templates.")
    sort_filelist = traits.Bool(
        True,
        usedefault=True,
        desc="When matching multiple files, return them" " in sorted order.",
    )
    raise_on_empty = traits.Bool(
        True,
        usedefault=True,
        desc="Raise an exception if a template pattern " "matches no files.",
    )
    force_lists = traits.Either(
        traits.Bool(),
        traits.List(Str()),
        default=False,
        usedefault=True,
        desc=(
            "Whether to return outputs as a list even"
            " when only one file matches the template. "
            "Either a boolean that applies to all output "
            "fields or a list of output field names to "
            "coerce to a list"
        ),
    )


class SelectFiles(IOBase):
    """
    Flexibly collect data from disk to feed into workflows.

    This interface uses Python's {}-based string formatting syntax to plug
    values (possibly known only at workflow execution time) into string
    templates and collect files from persistent storage. These templates can
    also be combined with glob wildcards (``*``, ``?``) and character ranges (``[...]``).
    The field names in the formatting template (i.e. the terms in braces) will
    become inputs fields on the interface, and the keys in the templates
    dictionary will form the output fields.

    Examples
    --------
    >>> import pprint
    >>> from nipype import SelectFiles, Node
    >>> templates={"T1": "{subject_id}/struct/T1.nii",
    ...            "epi": "{subject_id}/func/f[0,1].nii"}
    >>> dg = Node(SelectFiles(templates), "selectfiles")
    >>> dg.inputs.subject_id = "subj1"
    >>> pprint.pprint(dg.outputs.get())  # doctest:
    {'T1': <undefined>, 'epi': <undefined>}

    Note that SelectFiles does not support lists as inputs for the dynamic
    fields. Attempts to do so may lead to unexpected results because brackets
    also express glob character ranges. For example,

    >>> templates["epi"] = "{subject_id}/func/f{run}.nii"
    >>> dg = Node(SelectFiles(templates), "selectfiles")
    >>> dg.inputs.subject_id = "subj1"
    >>> dg.inputs.run = [10, 11]

    would match f0.nii or f1.nii, not f10.nii or f11.nii.

    """

    input_spec = SelectFilesInputSpec
    output_spec = DynamicTraitedSpec
    _always_run = True

    def __init__(self, templates, **kwargs):
        """Create an instance with specific input fields.

        Parameters
        ----------
        templates : dictionary
            Mapping from string keys to string template values.
            The keys become output fields on the interface.
            The templates should use {}-formatting syntax, where
            the names in curly braces become inputs fields on the interface.
            Format strings can also use glob wildcards to match multiple
            files. At runtime, the values of the interface inputs will be
            plugged into these templates, and the resulting strings will be
            used to select files.

        """
        super(SelectFiles, self).__init__(**kwargs)

        # Infer the infields and outfields from the template
        infields = []
        for name, template in list(templates.items()):
            for _, field_name, _, _ in string.Formatter().parse(template):
                if field_name is not None:
                    field_name = re.match("\w+", field_name).group()
                    if field_name not in infields:
                        infields.append(field_name)

        self._infields = infields
        self._outfields = list(templates)
        self._templates = templates

        # Add the dynamic input fields
        undefined_traits = {}
        for field in infields:
            self.inputs.add_trait(field, traits.Any)
            undefined_traits[field] = Undefined
        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

    def _add_output_traits(self, base):
        """Add the dynamic output fields"""
        return add_traits(base, list(self._templates.keys()))

    def _list_outputs(self):
        """Find the files and expose them as interface outputs."""
        outputs = {}
        info = dict(
            [
                (k, v)
                for k, v in list(self.inputs.__dict__.items())
                if k in self._infields
            ]
        )

        force_lists = self.inputs.force_lists
        if isinstance(force_lists, bool):
            force_lists = self._outfields if force_lists else []
        bad_fields = set(force_lists) - set(self._outfields)
        if bad_fields:
            bad_fields = ", ".join(list(bad_fields))
            plural = "s" if len(bad_fields) > 1 else ""
            verb = "were" if len(bad_fields) > 1 else "was"
            msg = (
                "The field%s '%s' %s set in 'force_lists' and not in " "'templates'."
            ) % (plural, bad_fields, verb)
            raise ValueError(msg)

        for field, template in list(self._templates.items()):
            find_dirs = template[-1] == os.sep

            # Build the full template path
            if isdefined(self.inputs.base_directory):
                template = op.abspath(op.join(self.inputs.base_directory, template))
            else:
                template = op.abspath(template)

            # re-add separator if searching exclusively for directories
            if find_dirs:
                template += os.sep

            # Fill in the template and glob for files
            filled_template = template.format(**info)
            filelist = glob.glob(filled_template)

            # Handle the case where nothing matched
            if not filelist:
                msg = "No files were found matching %s template: %s" % (
                    field,
                    filled_template,
                )
                if self.inputs.raise_on_empty:
                    raise IOError(msg)
                else:
                    warn(msg)

            # Possibly sort the list
            if self.inputs.sort_filelist:
                filelist = human_order_sorted(filelist)

            # Handle whether this must be a list or not
            if field not in force_lists:
                filelist = simplify_list(filelist)

            outputs[field] = filelist

        return outputs


class DataFinderInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    root_paths = traits.Either(traits.List(), Str(), mandatory=True)
    match_regex = Str(
        "(.+)", usedefault=True, desc=("Regular expression for matching paths.")
    )
    ignore_regexes = traits.List(
        desc=(
            "List of regular expressions, "
            "if any match the path it will be "
            "ignored."
        )
    )
    max_depth = traits.Int(desc="The maximum depth to search beneath " "the root_paths")
    min_depth = traits.Int(desc="The minimum depth to search beneath " "the root paths")
    unpack_single = traits.Bool(
        False, usedefault=True, desc="Unpack single results from list"
    )


class DataFinder(IOBase):
    r"""Search for paths that match a given regular expression. Allows a less
    proscriptive approach to gathering input files compared to DataGrabber.
    Will recursively search any subdirectories by default. This can be limited
    with the min/max depth options.
    Matched paths are available in the output 'out_paths'. Any named groups of
    captured text from the regular expression are also available as outputs of
    the same name.

    Examples
    --------
    >>> from nipype.interfaces.io import DataFinder
    >>> df = DataFinder()
    >>> df.inputs.root_paths = '.'
    >>> df.inputs.match_regex = r'.+/(?P<series_dir>.+(qT1|ep2d_fid_T1).+)/(?P<basename>.+)\.nii.gz'
    >>> result = df.run() # doctest: +SKIP
    >>> result.outputs.out_paths  # doctest: +SKIP
    ['./027-ep2d_fid_T1_Gd4/acquisition.nii.gz',
     './018-ep2d_fid_T1_Gd2/acquisition.nii.gz',
     './016-ep2d_fid_T1_Gd1/acquisition.nii.gz',
     './013-ep2d_fid_T1_pre/acquisition.nii.gz']
    >>> result.outputs.series_dir  # doctest: +SKIP
    ['027-ep2d_fid_T1_Gd4',
     '018-ep2d_fid_T1_Gd2',
     '016-ep2d_fid_T1_Gd1',
     '013-ep2d_fid_T1_pre']
    >>> result.outputs.basename  # doctest: +SKIP
    ['acquisition',
     'acquisition'
     'acquisition',
     'acquisition']

    """

    input_spec = DataFinderInputSpec
    output_spec = DynamicTraitedSpec
    _always_run = True

    def _match_path(self, target_path):
        # Check if we should ignore the path
        for ignore_re in self.ignore_regexes:
            if ignore_re.search(target_path):
                return
        # Check if we can match the path
        match = self.match_regex.search(target_path)
        if match is not None:
            match_dict = match.groupdict()
            if self.result is None:
                self.result = {"out_paths": []}
                for key in list(match_dict.keys()):
                    self.result[key] = []
            self.result["out_paths"].append(target_path)
            for key, val in list(match_dict.items()):
                self.result[key].append(val)

    def _run_interface(self, runtime):
        # Prepare some of the inputs
        if isinstance(self.inputs.root_paths, (str, bytes)):
            self.inputs.root_paths = [self.inputs.root_paths]
        self.match_regex = re.compile(self.inputs.match_regex)
        if self.inputs.max_depth is Undefined:
            max_depth = None
        else:
            max_depth = self.inputs.max_depth
        if self.inputs.min_depth is Undefined:
            min_depth = 0
        else:
            min_depth = self.inputs.min_depth
        if self.inputs.ignore_regexes is Undefined:
            self.ignore_regexes = []
        else:
            self.ignore_regexes = [
                re.compile(regex) for regex in self.inputs.ignore_regexes
            ]
        self.result = None
        for root_path in self.inputs.root_paths:
            # Handle tilda/env variables and remove extra separators
            root_path = os.path.normpath(
                os.path.expandvars(os.path.expanduser(root_path))
            )
            # Check if the root_path is a file
            if os.path.isfile(root_path):
                if min_depth == 0:
                    self._match_path(root_path)
                continue
            # Walk through directory structure checking paths
            for curr_dir, sub_dirs, files in os.walk(root_path):
                # Determine the current depth from the root_path
                curr_depth = curr_dir.count(os.sep) - root_path.count(os.sep)
                # If the max path depth has been reached, clear sub_dirs
                # and files
                if max_depth is not None and curr_depth >= max_depth:
                    sub_dirs[:] = []
                    files = []
                # Test the path for the curr_dir and all files
                if curr_depth >= min_depth:
                    self._match_path(curr_dir)
                if curr_depth >= (min_depth - 1):
                    for infile in files:
                        full_path = os.path.join(curr_dir, infile)
                        self._match_path(full_path)
        if self.inputs.unpack_single and len(self.result["out_paths"]) == 1:
            for key, vals in list(self.result.items()):
                self.result[key] = vals[0]
        else:
            # sort all keys according to out_paths
            for key in list(self.result.keys()):
                if key == "out_paths":
                    continue
                sort_tuples = human_order_sorted(
                    list(zip(self.result["out_paths"], self.result[key]))
                )
                self.result[key] = [x for (_, x) in sort_tuples]
            self.result["out_paths"] = human_order_sorted(self.result["out_paths"])

        if not self.result:
            raise RuntimeError("Regular expression did not match any files!")

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs.update(self.result)
        return outputs


class FSSourceInputSpec(BaseInterfaceInputSpec):
    subjects_dir = Directory(
        exists=True, mandatory=True, desc="Freesurfer subjects directory."
    )
    subject_id = Str(mandatory=True, desc="Subject name for whom to retrieve data")
    hemi = traits.Enum(
        "both", "lh", "rh", usedefault=True, desc="Selects hemisphere specific outputs"
    )


class FSSourceOutputSpec(TraitedSpec):
    T1 = File(exists=True, desc="Intensity normalized whole-head volume", loc="mri")
    aseg = File(
        exists=True,
        loc="mri",
        desc="Volumetric map of regions from automatic segmentation",
    )
    brain = File(exists=True, desc="Intensity normalized brain-only volume", loc="mri")
    brainmask = File(exists=True, desc="Skull-stripped (brain-only) volume", loc="mri")
    filled = File(exists=True, desc="Subcortical mass volume", loc="mri")
    norm = File(exists=True, desc="Normalized skull-stripped volume", loc="mri")
    nu = File(exists=True, desc="Non-uniformity corrected whole-head volume", loc="mri")
    orig = File(exists=True, desc="Base image conformed to Freesurfer space", loc="mri")
    rawavg = File(
        exists=True, desc="Volume formed by averaging input images", loc="mri"
    )
    ribbon = OutputMultiPath(
        File(exists=True),
        desc="Volumetric maps of cortical ribbons",
        loc="mri",
        altkey="*ribbon",
    )
    wm = File(exists=True, desc="Segmented white-matter volume", loc="mri")
    wmparc = File(
        exists=True,
        loc="mri",
        desc="Aparc parcellation projected into subcortical white matter",
    )
    curv = OutputMultiPath(
        File(exists=True), desc="Maps of surface curvature", loc="surf"
    )
    avg_curv = OutputMultiPath(
        File(exists=True),
        desc="Average atlas curvature, sampled to subject",
        loc="surf",
    )
    inflated = OutputMultiPath(
        File(exists=True), desc="Inflated surface meshes", loc="surf"
    )
    pial = OutputMultiPath(
        File(exists=True), desc="Gray matter/pia mater surface meshes", loc="surf"
    )
    area_pial = OutputMultiPath(
        File(exists=True),
        desc="Mean area of triangles each vertex on the pial surface is "
        "associated with",
        loc="surf",
        altkey="area.pial",
    )
    curv_pial = OutputMultiPath(
        File(exists=True),
        desc="Curvature of pial surface",
        loc="surf",
        altkey="curv.pial",
    )
    smoothwm = OutputMultiPath(
        File(exists=True), loc="surf", desc="Smoothed original surface meshes"
    )
    sphere = OutputMultiPath(
        File(exists=True), desc="Spherical surface meshes", loc="surf"
    )
    sulc = OutputMultiPath(
        File(exists=True), desc="Surface maps of sulcal depth", loc="surf"
    )
    thickness = OutputMultiPath(
        File(exists=True), loc="surf", desc="Surface maps of cortical thickness"
    )
    volume = OutputMultiPath(
        File(exists=True), desc="Surface maps of cortical volume", loc="surf"
    )
    white = OutputMultiPath(
        File(exists=True), desc="White/gray matter surface meshes", loc="surf"
    )
    jacobian_white = OutputMultiPath(
        File(exists=True),
        desc="Distortion required to register to spherical atlas",
        loc="surf",
    )
    graymid = OutputMultiPath(
        File(exists=True),
        desc="Graymid/midthickness surface meshes",
        loc="surf",
        altkey=["graymid", "midthickness"],
    )
    label = OutputMultiPath(
        File(exists=True),
        desc="Volume and surface label files",
        loc="label",
        altkey="*label",
    )
    annot = OutputMultiPath(
        File(exists=True), desc="Surface annotation files", loc="label", altkey="*annot"
    )
    aparc_aseg = OutputMultiPath(
        File(exists=True),
        loc="mri",
        altkey="aparc*aseg",
        desc="Aparc parcellation projected into aseg volume",
    )
    sphere_reg = OutputMultiPath(
        File(exists=True),
        loc="surf",
        altkey="sphere.reg",
        desc="Spherical registration file",
    )
    aseg_stats = OutputMultiPath(
        File(exists=True),
        loc="stats",
        altkey="aseg",
        desc="Automated segmentation statistics file",
    )
    wmparc_stats = OutputMultiPath(
        File(exists=True),
        loc="stats",
        altkey="wmparc",
        desc="White matter parcellation statistics file",
    )
    aparc_stats = OutputMultiPath(
        File(exists=True),
        loc="stats",
        altkey="aparc",
        desc="Aparc parcellation statistics files",
    )
    BA_stats = OutputMultiPath(
        File(exists=True),
        loc="stats",
        altkey="BA",
        desc="Brodmann Area statistics files",
    )
    aparc_a2009s_stats = OutputMultiPath(
        File(exists=True),
        loc="stats",
        altkey="aparc.a2009s",
        desc="Aparc a2009s parcellation statistics files",
    )
    curv_stats = OutputMultiPath(
        File(exists=True), loc="stats", altkey="curv", desc="Curvature statistics files"
    )
    entorhinal_exvivo_stats = OutputMultiPath(
        File(exists=True),
        loc="stats",
        altkey="entorhinal_exvivo",
        desc="Entorhinal exvivo statistics files",
    )


class FreeSurferSource(IOBase):
    """Generates freesurfer subject info from their directories.

    Examples
    --------
    >>> from nipype.interfaces.io import FreeSurferSource
    >>> fs = FreeSurferSource()
    >>> #fs.inputs.subjects_dir = '.'
    >>> fs.inputs.subject_id = 'PWS04'
    >>> res = fs.run() # doctest: +SKIP

    >>> fs.inputs.hemi = 'lh'
    >>> res = fs.run() # doctest: +SKIP

    """

    input_spec = FSSourceInputSpec
    output_spec = FSSourceOutputSpec
    _always_run = True
    _additional_metadata = ["loc", "altkey"]

    def _get_files(self, path, key, dirval, altkey=None):
        globsuffix = ""
        if dirval == "mri":
            globsuffix = ".mgz"
        elif dirval == "stats":
            globsuffix = ".stats"
        globprefix = ""
        if dirval in ("surf", "label", "stats"):
            if self.inputs.hemi != "both":
                globprefix = self.inputs.hemi + "."
            else:
                globprefix = "?h."
            if key in ("aseg_stats", "wmparc_stats"):
                globprefix = ""
        elif key == "ribbon":
            if self.inputs.hemi != "both":
                globprefix = self.inputs.hemi + "."
            else:
                globprefix = "*"
        keys = ensure_list(altkey) if altkey else [key]
        globfmt = os.path.join(path, dirval, "".join((globprefix, "{}", globsuffix)))
        return [
            os.path.abspath(f) for key in keys for f in glob.glob(globfmt.format(key))
        ]

    def _list_outputs(self):
        subjects_dir = self.inputs.subjects_dir
        subject_path = os.path.join(subjects_dir, self.inputs.subject_id)
        output_traits = self._outputs()
        outputs = output_traits.get()
        for k in list(outputs.keys()):
            val = self._get_files(
                subject_path,
                k,
                output_traits.traits()[k].loc,
                output_traits.traits()[k].altkey,
            )
            if val:
                outputs[k] = simplify_list(val)
        return outputs


class XNATSourceInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    query_template = Str(
        mandatory=True,
        desc=("Layout used to get files. Relative to base " "directory if defined"),
    )

    query_template_args = traits.Dict(
        Str,
        traits.List(traits.List),
        value=dict(outfiles=[]),
        usedefault=True,
        desc="Information to plug into template",
    )

    server = Str(mandatory=True, requires=["user", "pwd"], xor=["config"])

    user = Str()
    pwd = traits.Password()
    config = File(mandatory=True, xor=["server"])

    cache_dir = Directory(desc="Cache directory")


class XNATSource(LibraryBaseInterface, IOBase):
    """
    Pull data from an XNAT server.

    Generic XNATSource module that wraps around the pyxnat module in
    an intelligent way for neuroimaging tasks to grab files and data
    from an XNAT server.

    Examples
    --------
    Pick all files from current directory

    >>> dg = XNATSource()
    >>> dg.inputs.template = '*'

    >>> dg = XNATSource(infields=['project','subject','experiment','assessor','inout'])
    >>> dg.inputs.query_template = '/projects/%s/subjects/%s/experiments/%s' \
               '/assessors/%s/%s_resources/files'
    >>> dg.inputs.project = 'IMAGEN'
    >>> dg.inputs.subject = 'IMAGEN_000000001274'
    >>> dg.inputs.experiment = '*SessionA*'
    >>> dg.inputs.assessor = '*ADNI_MPRAGE_nii'
    >>> dg.inputs.inout = 'out'

    >>> dg = XNATSource(infields=['sid'],outfields=['struct','func'])
    >>> dg.inputs.query_template = '/projects/IMAGEN/subjects/%s/experiments/*SessionA*' \
               '/assessors/*%s_nii/out_resources/files'
    >>> dg.inputs.query_template_args['struct'] = [['sid','ADNI_MPRAGE']]
    >>> dg.inputs.query_template_args['func'] = [['sid','EPI_faces']]
    >>> dg.inputs.sid = 'IMAGEN_000000001274'

    """

    input_spec = XNATSourceInputSpec
    output_spec = DynamicTraitedSpec
    _pkg = "pyxnat"

    def __init__(self, infields=None, outfields=None, **kwargs):
        """
        Parameters
        ----------
        infields : list of str
            Indicates the input fields to be dynamically created

        outfields: list of str
            Indicates output fields to be dynamically created

        See class examples for usage

        """
        super(XNATSource, self).__init__(**kwargs)
        undefined_traits = {}
        # used for mandatory inputs check
        self._infields = infields
        if infields:
            for key in infields:
                self.inputs.add_trait(key, traits.Any)
                undefined_traits[key] = Undefined
            self.inputs.query_template_args["outfiles"] = [infields]
        if outfields:
            # add ability to insert field specific templates
            self.inputs.add_trait(
                "field_template",
                traits.Dict(
                    traits.Enum(outfields),
                    desc="arguments that fit into query_template",
                ),
            )
            undefined_traits["field_template"] = Undefined
            # self.inputs.remove_trait('query_template_args')
            outdict = {}
            for key in outfields:
                outdict[key] = []
            self.inputs.query_template_args = outdict
        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

    def _add_output_traits(self, base):
        """

        Using traits.Any instead out OutputMultiPath till add_trait bug
        is fixed.
        """
        return add_traits(base, list(self.inputs.query_template_args.keys()))

    def _list_outputs(self):
        # infields are mandatory, however I could not figure out
        # how to set 'mandatory' flag dynamically, hence manual check
        import pyxnat

        cache_dir = self.inputs.cache_dir or tempfile.gettempdir()

        if self.inputs.config:
            xnat = pyxnat.Interface(config=self.inputs.config)
        else:
            xnat = pyxnat.Interface(
                self.inputs.server, self.inputs.user, self.inputs.pwd, cache_dir
            )

        if self._infields:
            for key in self._infields:
                value = getattr(self.inputs, key)
                if not isdefined(value):
                    msg = (
                        "%s requires a value for input '%s' "
                        "because it was listed in 'infields'"
                        % (self.__class__.__name__, key)
                    )
                    raise ValueError(msg)

        outputs = {}
        for key, args in list(self.inputs.query_template_args.items()):
            outputs[key] = []
            template = self.inputs.query_template
            if (
                hasattr(self.inputs, "field_template")
                and isdefined(self.inputs.field_template)
                and key in self.inputs.field_template
            ):
                template = self.inputs.field_template[key]
            if not args:
                file_objects = xnat.select(template).get("obj")
                if file_objects == []:
                    raise IOError("Template %s returned no files" % template)
                outputs[key] = simplify_list(
                    [
                        str(file_object.get())
                        for file_object in file_objects
                        if file_object.exists()
                    ]
                )
            for argnum, arglist in enumerate(args):
                maxlen = 1
                for arg in arglist:
                    if isinstance(arg, (str, bytes)) and hasattr(self.inputs, arg):
                        arg = getattr(self.inputs, arg)
                    if isinstance(arg, list):
                        if (maxlen > 1) and (len(arg) != maxlen):
                            raise ValueError(
                                "incompatible number " "of arguments for %s" % key
                            )
                        if len(arg) > maxlen:
                            maxlen = len(arg)
                outfiles = []
                for i in range(maxlen):
                    argtuple = []
                    for arg in arglist:
                        if isinstance(arg, (str, bytes)) and hasattr(self.inputs, arg):
                            arg = getattr(self.inputs, arg)
                        if isinstance(arg, list):
                            argtuple.append(arg[i])
                        else:
                            argtuple.append(arg)
                    if argtuple:
                        target = template % tuple(argtuple)
                        file_objects = xnat.select(target).get("obj")

                        if file_objects == []:
                            raise IOError("Template %s " "returned no files" % target)

                        outfiles = simplify_list(
                            [
                                str(file_object.get())
                                for file_object in file_objects
                                if file_object.exists()
                            ]
                        )
                    else:
                        file_objects = xnat.select(template).get("obj")

                        if file_objects == []:
                            raise IOError("Template %s " "returned no files" % template)

                        outfiles = simplify_list(
                            [
                                str(file_object.get())
                                for file_object in file_objects
                                if file_object.exists()
                            ]
                        )

                    outputs[key].insert(i, outfiles)
            if len(outputs[key]) == 0:
                outputs[key] = None
            elif len(outputs[key]) == 1:
                outputs[key] = outputs[key][0]
        return outputs


class XNATSinkInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    _outputs = traits.Dict(Str, value={}, usedefault=True)

    server = Str(mandatory=True, requires=["user", "pwd"], xor=["config"])

    user = Str()
    pwd = traits.Password()
    config = File(mandatory=True, xor=["server"])
    cache_dir = Directory(desc="")

    project_id = Str(desc="Project in which to store the outputs", mandatory=True)

    subject_id = Str(desc="Set to subject id", mandatory=True)

    experiment_id = Str(desc="Set to workflow name", mandatory=True)

    assessor_id = Str(
        desc=(
            "Option to customize outputs representation in XNAT - "
            "assessor level will be used with specified id"
        ),
        xor=["reconstruction_id"],
    )

    reconstruction_id = Str(
        desc=(
            "Option to customize outputs representation in XNAT - "
            "reconstruction level will be used with specified id"
        ),
        xor=["assessor_id"],
    )

    share = traits.Bool(
        False,
        desc=(
            "Option to share the subjects from the original project"
            "instead of creating new ones when possible - the created "
            "experiments are then shared back to the original project"
        ),
        usedefault=True,
    )

    def __setattr__(self, key, value):
        if key not in self.copyable_trait_names():
            self._outputs[key] = value
        else:
            super(XNATSinkInputSpec, self).__setattr__(key, value)


class XNATSink(LibraryBaseInterface, IOBase):
    """Generic datasink module that takes a directory containing a
    list of nifti files and provides a set of structured output
    fields.
    """

    input_spec = XNATSinkInputSpec
    _pkg = "pyxnat"

    def _list_outputs(self):
        """Execute this module."""
        import pyxnat

        # setup XNAT connection
        cache_dir = self.inputs.cache_dir or tempfile.gettempdir()

        if self.inputs.config:
            xnat = pyxnat.Interface(config=self.inputs.config)
        else:
            xnat = pyxnat.Interface(
                self.inputs.server, self.inputs.user, self.inputs.pwd, cache_dir
            )

        # if possible share the subject from the original project
        if self.inputs.share:
            subject_id = self.inputs.subject_id
            result = xnat.select(
                "xnat:subjectData",
                ["xnat:subjectData/PROJECT", "xnat:subjectData/SUBJECT_ID"],
            ).where("xnat:subjectData/SUBJECT_ID = %s AND" % subject_id)

            # subject containing raw data exists on the server
            if result.data and isinstance(result.data[0], dict):
                result = result.data[0]
                shared = xnat.select(
                    "/project/%s/subject/%s"
                    % (self.inputs.project_id, self.inputs.subject_id)
                )

                if not shared.exists():  # subject not in share project
                    share_project = xnat.select("/project/%s" % self.inputs.project_id)

                    if not share_project.exists():  # check project exists
                        share_project.insert()

                    subject = xnat.select(
                        "/project/%(project)s" "/subject/%(subject_id)s" % result
                    )

                    subject.share(str(self.inputs.project_id))

        # setup XNAT resource
        uri_template_args = dict(
            project_id=quote_id(self.inputs.project_id),
            subject_id=self.inputs.subject_id,
            experiment_id=quote_id(self.inputs.experiment_id),
        )

        if self.inputs.share:
            uri_template_args["original_project"] = result["project"]

        if self.inputs.assessor_id:
            uri_template_args["assessor_id"] = quote_id(self.inputs.assessor_id)
        elif self.inputs.reconstruction_id:
            uri_template_args["reconstruction_id"] = quote_id(
                self.inputs.reconstruction_id
            )

        # gather outputs and upload them
        for key, files in list(self.inputs._outputs.items()):
            for name in ensure_list(files):
                if isinstance(name, list):
                    for i, file_name in enumerate(name):
                        push_file(
                            self, xnat, file_name, "%s_" % i + key, uri_template_args
                        )
                else:
                    push_file(self, xnat, name, key, uri_template_args)


def quote_id(string):
    return str(string).replace("_", "---")


def unquote_id(string):
    return str(string).replace("---", "_")


def push_file(self, xnat, file_name, out_key, uri_template_args):
    # grab info from output file names
    val_list = [
        unquote_id(val)
        for part in os.path.split(file_name)[0].split(os.sep)
        for val in part.split("_")[1:]
        if part.startswith("_") and len(part.split("_")) % 2
    ]

    keymap = dict(list(zip(val_list[1::2], val_list[2::2])))

    _label = []
    for key, val in sorted(keymap.items()):
        if str(self.inputs.subject_id) not in val:
            _label.extend([key, val])

    # select and define container level
    uri_template_args["container_type"] = None

    for container in ["assessor_id", "reconstruction_id"]:
        if getattr(self.inputs, container):
            uri_template_args["container_type"] = container.split("_id")[0]
            uri_template_args["container_id"] = uri_template_args[container]

    if uri_template_args["container_type"] is None:
        uri_template_args["container_type"] = "reconstruction"

        uri_template_args["container_id"] = unquote_id(
            uri_template_args["experiment_id"]
        )

        if _label:
            uri_template_args["container_id"] += "_results_%s" % "_".join(_label)
        else:
            uri_template_args["container_id"] += "_results"

    # define resource level
    uri_template_args["resource_label"] = "%s_%s" % (
        uri_template_args["container_id"],
        out_key.split(".")[0],
    )

    # define file level
    uri_template_args["file_name"] = os.path.split(
        os.path.abspath(unquote_id(file_name))
    )[1]

    uri_template = (
        "/project/%(project_id)s/subject/%(subject_id)s"
        "/experiment/%(experiment_id)s/%(container_type)s/%(container_id)s"
        "/out/resource/%(resource_label)s/file/%(file_name)s"
    )

    # unquote values before uploading
    for key in list(uri_template_args.keys()):
        uri_template_args[key] = unquote_id(uri_template_args[key])

    # upload file
    remote_file = xnat.select(uri_template % uri_template_args)
    remote_file.insert(file_name, experiments="xnat:imageSessionData", use_label=True)

    # shares the experiment back to the original project if relevant
    if "original_project" in uri_template_args:
        experiment_template = (
            "/project/%(original_project)s"
            "/subject/%(subject_id)s/experiment/%(experiment_id)s"
        )

        xnat.select(experiment_template % uri_template_args).share(
            uri_template_args["original_project"]
        )


def capture_provenance():
    pass


def push_provenance():
    pass


class SQLiteSinkInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    database_file = File(exists=True, mandatory=True)
    table_name = Str(mandatory=True)


class SQLiteSink(LibraryBaseInterface, IOBase):
    """
    Very simple frontend for storing values into SQLite database.

    .. warning::

        This is not a thread-safe node because it can write to a common
        shared location. It will not complain when it overwrites a file.

    Examples
    --------

    >>> sql = SQLiteSink(input_names=['subject_id', 'some_measurement'])
    >>> sql.inputs.database_file = 'my_database.db'
    >>> sql.inputs.table_name = 'experiment_results'
    >>> sql.inputs.subject_id = 's1'
    >>> sql.inputs.some_measurement = 11.4
    >>> sql.run() # doctest: +SKIP

    """

    input_spec = SQLiteSinkInputSpec
    _pkg = "sqlite3"

    def __init__(self, input_names, **inputs):
        super(SQLiteSink, self).__init__(**inputs)

        self._input_names = ensure_list(input_names)
        add_traits(self.inputs, [name for name in self._input_names])

    def _list_outputs(self):
        """Execute this module."""
        import sqlite3

        conn = sqlite3.connect(self.inputs.database_file, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO %s (" % self.inputs.table_name
            + ",".join(self._input_names)
            + ") VALUES ("
            + ",".join(["?"] * len(self._input_names))
            + ")",
            [getattr(self.inputs, name) for name in self._input_names],
        )
        conn.commit()
        c.close()
        return None


class MySQLSinkInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    host = Str(
        "localhost",
        mandatory=True,
        requires=["username", "password"],
        xor=["config"],
        usedefault=True,
    )
    config = File(
        mandatory=True, xor=["host"], desc="MySQL Options File (same format as my.cnf)"
    )
    database_name = Str(mandatory=True, desc="Otherwise known as the schema name")
    table_name = Str(mandatory=True)
    username = Str()
    password = Str()


class MySQLSink(IOBase):
    """
    Very simple frontend for storing values into MySQL database.

    Examples
    --------

    >>> sql = MySQLSink(input_names=['subject_id', 'some_measurement'])
    >>> sql.inputs.database_name = 'my_database'
    >>> sql.inputs.table_name = 'experiment_results'
    >>> sql.inputs.username = 'root'
    >>> sql.inputs.password = 'secret'
    >>> sql.inputs.subject_id = 's1'
    >>> sql.inputs.some_measurement = 11.4
    >>> sql.run() # doctest: +SKIP

    """

    input_spec = MySQLSinkInputSpec

    def __init__(self, input_names, **inputs):
        super(MySQLSink, self).__init__(**inputs)

        self._input_names = ensure_list(input_names)
        add_traits(self.inputs, [name for name in self._input_names])

    def _list_outputs(self):
        """Execute this module."""
        import MySQLdb

        if isdefined(self.inputs.config):
            conn = MySQLdb.connect(
                db=self.inputs.database_name, read_default_file=self.inputs.config
            )
        else:
            conn = MySQLdb.connect(
                host=self.inputs.host,
                user=self.inputs.username,
                passwd=self.inputs.password,
                db=self.inputs.database_name,
            )
        c = conn.cursor()
        c.execute(
            "REPLACE INTO %s (" % self.inputs.table_name
            + ",".join(self._input_names)
            + ") VALUES ("
            + ",".join(["%s"] * len(self._input_names))
            + ")",
            [getattr(self.inputs, name) for name in self._input_names],
        )
        conn.commit()
        c.close()
        return None


class SSHDataGrabberInputSpec(DataGrabberInputSpec):
    hostname = Str(mandatory=True, desc="Server hostname.")
    username = Str(desc="Server username.")
    password = traits.Password(desc="Server password.")
    download_files = traits.Bool(
        True,
        usedefault=True,
        desc="If false it will return the file names without downloading them",
    )
    base_directory = Str(
        mandatory=True, desc="Path to the base directory consisting of subject data."
    )
    template_expression = traits.Enum(
        ["fnmatch", "regexp"],
        usedefault=True,
        desc="Use either fnmatch or regexp to express templates",
    )
    ssh_log_to_file = Str(
        "", usedefault=True, desc="If set SSH commands will be logged to the given file"
    )


class SSHDataGrabber(LibraryBaseInterface, DataGrabber):
    """
    Extension of DataGrabber module that downloads the file list and
    optionally the files from a SSH server. The SSH operation must
    not need user and password so an SSH agent must be active in
    where this module is being run.


    .. attention::

       Doesn't support directories currently

    Examples
    --------
    >>> from nipype.interfaces.io import SSHDataGrabber
    >>> dg = SSHDataGrabber()
    >>> dg.inputs.hostname = 'test.rebex.net'
    >>> dg.inputs.user = 'demo'
    >>> dg.inputs.password = 'password'
    >>> dg.inputs.base_directory = 'pub/example'

    Pick all files from the base directory

    >>> dg.inputs.template = '*'

    Pick all files starting with "s" and a number from current directory

    >>> dg.inputs.template_expression = 'regexp'
    >>> dg.inputs.template = 'pop[0-9].*'

    Same thing but with dynamically created fields

    >>> dg = SSHDataGrabber(infields=['arg1','arg2'])
    >>> dg.inputs.hostname = 'test.rebex.net'
    >>> dg.inputs.user = 'demo'
    >>> dg.inputs.password = 'password'
    >>> dg.inputs.base_directory = 'pub'
    >>> dg.inputs.template = '%s/%s.txt'
    >>> dg.inputs.arg1 = 'example'
    >>> dg.inputs.arg2 = 'foo'

    however this latter form can be used with iterables and iterfield in a
    pipeline.

    Dynamically created, user-defined input and output fields

    >>> dg = SSHDataGrabber(infields=['sid'], outfields=['func','struct','ref'])
    >>> dg.inputs.hostname = 'myhost.com'
    >>> dg.inputs.base_directory = '/main_folder/my_remote_dir'
    >>> dg.inputs.template_args['func'] = [['sid',['f3','f5']]]
    >>> dg.inputs.template_args['struct'] = [['sid',['struct']]]
    >>> dg.inputs.template_args['ref'] = [['sid','ref']]
    >>> dg.inputs.sid = 's1'

    Change the template only for output field struct. The rest use the
    general template

    >>> dg.inputs.field_template = dict(struct='%s/struct.nii')
    >>> dg.inputs.template_args['struct'] = [['sid']]

    """

    input_spec = SSHDataGrabberInputSpec
    output_spec = DynamicTraitedSpec
    _always_run = False
    _pkg = "paramiko"

    def __init__(self, infields=None, outfields=None, **kwargs):
        """
        Parameters
        ----------
        infields : list of str
            Indicates the input fields to be dynamically created

        outfields: list of str
            Indicates output fields to be dynamically created

        See class examples for usage

        """
        if not outfields:
            outfields = ["outfiles"]
        kwargs = kwargs.copy()
        kwargs["infields"] = infields
        kwargs["outfields"] = outfields
        super(SSHDataGrabber, self).__init__(**kwargs)
        if None in (self.inputs.username, self.inputs.password):
            raise ValueError(
                "either both username and password " "are provided or none of them"
            )

        if (
            self.inputs.template_expression == "regexp"
            and self.inputs.template[-1] != "$"
        ):
            self.inputs.template += "$"

    def _get_files_over_ssh(self, template):
        """Get the files matching template over an SSH connection."""
        # Connect over SSH
        client = self._get_ssh_client()
        sftp = client.open_sftp()
        sftp.chdir(self.inputs.base_directory)

        # Get all files in the dir, and filter for desired files
        template_dir = os.path.dirname(template)
        template_base = os.path.basename(template)
        every_file_in_dir = sftp.listdir(template_dir)
        if self.inputs.template_expression == "fnmatch":
            outfiles = fnmatch.filter(every_file_in_dir, template_base)
        elif self.inputs.template_expression == "regexp":
            regexp = re.compile(template_base)
            outfiles = list(filter(regexp.match, every_file_in_dir))
        else:
            raise ValueError("template_expression value invalid")

        if len(outfiles) == 0:
            # no files
            msg = "Output template: %s returned no files" % template
            if self.inputs.raise_on_empty:
                raise IOError(msg)
            else:
                warn(msg)

            # return value
            outfiles = None

        else:
            # found files, sort and save to outputs
            if self.inputs.sort_filelist:
                outfiles = human_order_sorted(outfiles)

            # actually download the files, if desired
            if self.inputs.download_files:
                files_to_download = copy.copy(outfiles)  # make sure new list!

                # check to see if there are any related files to download
                for file_to_download in files_to_download:
                    related_to_current = get_related_files(
                        file_to_download, include_this_file=False
                    )
                    existing_related_not_downloading = [
                        f
                        for f in related_to_current
                        if f in every_file_in_dir and f not in files_to_download
                    ]
                    files_to_download.extend(existing_related_not_downloading)

                for f in files_to_download:
                    try:
                        sftp.get(os.path.join(template_dir, f), f)
                    except IOError:
                        iflogger.info("remote file %s not found" % f)

            # return value
            outfiles = simplify_list(outfiles)

        return outfiles

    def _list_outputs(self):
        import paramiko

        if len(self.inputs.ssh_log_to_file) > 0:
            paramiko.util.log_to_file(self.inputs.ssh_log_to_file)
        # infields are mandatory, however I could not figure out how to set 'mandatory' flag dynamically
        # hence manual check
        if self._infields:
            for key in self._infields:
                value = getattr(self.inputs, key)
                if not isdefined(value):
                    msg = (
                        "%s requires a value for input '%s' because it was listed in 'infields'"
                        % (self.__class__.__name__, key)
                    )
                    raise ValueError(msg)

        outputs = {}
        for key, args in list(self.inputs.template_args.items()):
            outputs[key] = []
            template = self.inputs.template
            if (
                hasattr(self.inputs, "field_template")
                and isdefined(self.inputs.field_template)
                and key in self.inputs.field_template
            ):
                template = self.inputs.field_template[key]

            if not args:
                outputs[key] = self._get_files_over_ssh(template)

            for argnum, arglist in enumerate(args):
                maxlen = 1
                for arg in arglist:
                    if isinstance(arg, (str, bytes)) and hasattr(self.inputs, arg):
                        arg = getattr(self.inputs, arg)
                    if isinstance(arg, list):
                        if (maxlen > 1) and (len(arg) != maxlen):
                            raise ValueError(
                                "incompatible number of arguments for %s" % key
                            )
                        if len(arg) > maxlen:
                            maxlen = len(arg)
                outfiles = []
                for i in range(maxlen):
                    argtuple = []
                    for arg in arglist:
                        if isinstance(arg, (str, bytes)) and hasattr(self.inputs, arg):
                            arg = getattr(self.inputs, arg)
                        if isinstance(arg, list):
                            argtuple.append(arg[i])
                        else:
                            argtuple.append(arg)
                    filledtemplate = template
                    if argtuple:
                        try:
                            filledtemplate = template % tuple(argtuple)
                        except TypeError as e:
                            raise TypeError(
                                f"{e}: Template {template} failed to convert "
                                f"with args {tuple(argtuple)}"
                            )

                    outputs[key].append(self._get_files_over_ssh(filledtemplate))

            # disclude where there was any invalid matches
            if any([val is None for val in outputs[key]]):
                outputs[key] = []

            # no outputs is None, not empty list
            if len(outputs[key]) == 0:
                outputs[key] = None

            # one output is the item, not a list
            elif len(outputs[key]) == 1:
                outputs[key] = outputs[key][0]

        for k, v in list(outputs.items()):
            outputs[k] = os.path.join(os.getcwd(), v)

        return outputs

    def _get_ssh_client(self):
        import paramiko

        config = paramiko.SSHConfig()
        config.parse(open(os.path.expanduser("~/.ssh/config")))
        host = config.lookup(self.inputs.hostname)
        if "proxycommand" in host:
            proxy = paramiko.ProxyCommand(
                subprocess.check_output(
                    [os.environ["SHELL"], "-c", "echo %s" % host["proxycommand"]]
                ).strip()
            )
        else:
            proxy = None
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host["hostname"], username=host["user"], sock=proxy)
        return client


class JSONFileGrabberInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    in_file = File(exists=True, desc="JSON source file")
    defaults = traits.Dict(
        desc=(
            "JSON dictionary that sets default output"
            "values, overridden by values found in in_file"
        )
    )


class JSONFileGrabber(IOBase):
    """
    Datagrabber interface that loads a json file and generates an output for
    every first-level object

    Example
    -------

    >>> import pprint
    >>> from nipype.interfaces.io import JSONFileGrabber
    >>> jsonSource = JSONFileGrabber()
    >>> jsonSource.inputs.defaults = {'param1': 'overrideMe', 'param3': 1.0}
    >>> res = jsonSource.run()
    >>> pprint.pprint(res.outputs.get())
    {'param1': 'overrideMe', 'param3': 1.0}
    >>> jsonSource.inputs.in_file = os.path.join(datadir, 'jsongrabber.txt')
    >>> res = jsonSource.run()
    >>> pprint.pprint(res.outputs.get())  # doctest:, +ELLIPSIS
    {'param1': 'exampleStr', 'param2': 4, 'param3': 1.0}
    """

    input_spec = JSONFileGrabberInputSpec
    output_spec = DynamicTraitedSpec
    _always_run = True

    def _list_outputs(self):
        import simplejson

        outputs = {}
        if isdefined(self.inputs.in_file):
            with open(self.inputs.in_file, "r") as f:
                data = simplejson.load(f)

            if not isinstance(data, dict):
                raise RuntimeError("JSON input has no dictionary structure")

            for key, value in list(data.items()):
                outputs[key] = value

        if isdefined(self.inputs.defaults):
            defaults = self.inputs.defaults
            for key, value in list(defaults.items()):
                if key not in list(outputs.keys()):
                    outputs[key] = value

        return outputs


class JSONFileSinkInputSpec(DynamicTraitedSpec, BaseInterfaceInputSpec):
    out_file = File(desc="JSON sink file")
    in_dict = traits.Dict(value={}, usedefault=True, desc="input JSON dictionary")
    _outputs = traits.Dict(value={}, usedefault=True)

    def __setattr__(self, key, value):
        if key not in self.copyable_trait_names():
            if not isdefined(value):
                super(JSONFileSinkInputSpec, self).__setattr__(key, value)
            self._outputs[key] = value
        else:
            if key in self._outputs:
                self._outputs[key] = value
            super(JSONFileSinkInputSpec, self).__setattr__(key, value)


class JSONFileSinkOutputSpec(TraitedSpec):
    out_file = File(desc="JSON sink file")


class JSONFileSink(IOBase):
    """
    Very simple frontend for storing values into a JSON file.
    Entries already existing in in_dict will be overridden by matching
    entries dynamically added as inputs.

    .. warning::

        This is not a thread-safe node because it can write to a common
        shared location. It will not complain when it overwrites a file.

    Examples
    --------
    >>> jsonsink = JSONFileSink(input_names=['subject_id',
    ...                         'some_measurement'])
    >>> jsonsink.inputs.subject_id = 's1'
    >>> jsonsink.inputs.some_measurement = 11.4
    >>> jsonsink.run() # doctest: +SKIP

    Using a dictionary as input:

    >>> dictsink = JSONFileSink()
    >>> dictsink.inputs.in_dict = {'subject_id': 's1',
    ...                            'some_measurement': 11.4}
    >>> dictsink.run() # doctest: +SKIP

    """

    input_spec = JSONFileSinkInputSpec
    output_spec = JSONFileSinkOutputSpec

    def __init__(self, infields=[], force_run=True, **inputs):
        super(JSONFileSink, self).__init__(**inputs)
        self._input_names = infields

        undefined_traits = {}
        for key in infields:
            self.inputs.add_trait(key, traits.Any)
            self.inputs._outputs[key] = Undefined
            undefined_traits[key] = Undefined
        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

        if force_run:
            self._always_run = True

    def _process_name(self, name, val):
        if "." in name:
            newkeys = name.split(".")
            name = newkeys.pop(0)
            nested_dict = {newkeys.pop(): val}

            for nk in reversed(newkeys):
                nested_dict = {nk: nested_dict}
            val = nested_dict

        return name, val

    def _list_outputs(self):
        import simplejson
        import os.path as op

        if not isdefined(self.inputs.out_file):
            out_file = op.abspath("datasink.json")
        else:
            out_file = op.abspath(self.inputs.out_file)

        out_dict = self.inputs.in_dict

        # Overwrite in_dict entries automatically
        for key, val in list(self.inputs._outputs.items()):
            if not isdefined(val) or key == "trait_added":
                continue
            key, val = self._process_name(key, val)
            out_dict[key] = val

        with open(out_file, "w") as f:
            f.write(str(simplejson.dumps(out_dict, ensure_ascii=False)))

        outputs = self.output_spec().get()
        outputs["out_file"] = out_file
        return outputs


class BIDSDataGrabberInputSpec(DynamicTraitedSpec):
    base_dir = Directory(exists=True, desc="Path to BIDS Directory.", mandatory=True)
    output_query = traits.Dict(
        key_trait=Str, value_trait=traits.Dict, desc="Queries for outfield outputs"
    )
    load_layout = Directory(
        exists=True, desc="Path to load already saved Bidslayout.", mandatory=False
    )
    raise_on_empty = traits.Bool(
        True,
        usedefault=True,
        desc="Generate exception if list is empty for a given field",
    )
    index_derivatives = traits.Bool(
        False, mandatory=True, usedefault=True, desc="Index derivatives/ sub-directory"
    )
    extra_derivatives = traits.List(
        Directory(exists=True), desc="Additional derivative directories to index"
    )


class BIDSDataGrabber(LibraryBaseInterface, IOBase):
    """BIDS datagrabber module that wraps around pybids to allow arbitrary
    querying of BIDS datasets.

    Examples
    --------

    .. setup::

        >>> try:
        ...     import bids
        ... except ImportError:
        ...     pytest.skip()

    By default, the BIDSDataGrabber fetches anatomical and functional images
    from a project, and makes BIDS entities (e.g. subject) available for
    filtering outputs.

    >>> bg = BIDSDataGrabber()
    >>> bg.inputs.base_dir = 'ds005/'
    >>> bg.inputs.subject = '01'
    >>> results = bg.run() # doctest: +SKIP


    Dynamically created, user-defined output fields can also be defined to
    return different types of outputs from the same project. All outputs
    are filtered on common entities, which can be explicitly defined as
    infields.

    >>> bg = BIDSDataGrabber(infields = ['subject'])
    >>> bg.inputs.base_dir = 'ds005/'
    >>> bg.inputs.subject = '01'
    >>> bg.inputs.output_query['dwi'] = dict(datatype='dwi')
    >>> results = bg.run() # doctest: +SKIP

    """

    input_spec = BIDSDataGrabberInputSpec
    output_spec = DynamicTraitedSpec
    _always_run = True
    _pkg = "bids"

    def __init__(self, infields=None, **kwargs):
        """
        Parameters
        ----------
        infields : list of str
            Indicates the input fields to be dynamically created
        """
        super(BIDSDataGrabber, self).__init__(**kwargs)

        if not isdefined(self.inputs.output_query):
            self.inputs.output_query = {
                "bold": {
                    "datatype": "func",
                    "suffix": "bold",
                    "extension": ["nii", ".nii.gz"],
                },
                "T1w": {
                    "datatype": "anat",
                    "suffix": "T1w",
                    "extension": ["nii", ".nii.gz"],
                },
            }

        # If infields is empty, use all BIDS entities
        if infields is None:
            from bids import layout as bidslayout

            bids_config = join(dirname(bidslayout.__file__), "config", "bids.json")
            bids_config = json.load(open(bids_config, "r"))
            infields = [i["name"] for i in bids_config["entities"]]

        self._infields = infields or []

        # used for mandatory inputs check
        undefined_traits = {}
        for key in self._infields:
            self.inputs.add_trait(key, traits.Any)
            undefined_traits[key] = kwargs[key] if key in kwargs else Undefined

        self.inputs.trait_set(trait_change_notify=False, **undefined_traits)

    def _list_outputs(self):
        from bids import BIDSLayout

        # if load_layout is given load layout which is on some datasets much faster
        if isdefined(self.inputs.load_layout):
            layout = BIDSLayout.load(self.inputs.load_layout)
        else:
            layout = BIDSLayout(
                self.inputs.base_dir, derivatives=self.inputs.index_derivatives
            )

        if isdefined(self.inputs.extra_derivatives):
            layout.add_derivatives(self.inputs.extra_derivatives)

        # If infield is not given nm input value, silently ignore
        filters = {}
        for key in self._infields:
            value = getattr(self.inputs, key)
            if isdefined(value):
                filters[key] = value

        outputs = {}
        for key, query in self.inputs.output_query.items():
            args = query.copy()
            args.update(filters)
            filelist = layout.get(return_type="file", **args)
            if len(filelist) == 0:
                msg = "Output key: %s returned no files" % key
                if self.inputs.raise_on_empty:
                    raise IOError(msg)
                else:
                    iflogger.warning(msg)
                    filelist = Undefined

            outputs[key] = filelist
        return outputs

    def _add_output_traits(self, base):
        return add_traits(base, list(self.inputs.output_query.keys()))


class ExportFileInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc="Input file name")
    out_file = File(mandatory=True, desc="Output file name")
    check_extension = traits.Bool(
        True,
        usedefault=True,
        desc="Ensure that the input and output file extensions match",
    )
    clobber = traits.Bool(desc="Permit overwriting existing files")


class ExportFileOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc="Output file name")


class ExportFile(SimpleInterface):
    """Export a file to an absolute path.

    This interface copies an input file to a named output file.
    This is useful to save individual files to a specific location,
    instead of more flexible interfaces like DataSink.

    Examples
    --------
    >>> from nipype.interfaces.io import ExportFile
    >>> import os.path as op
    >>> ef = ExportFile()
    >>> ef.inputs.in_file = "T1.nii.gz"
    >>> os.mkdir("output_folder")
    >>> ef.inputs.out_file = op.abspath("output_folder/sub1_out.nii.gz")
    >>> res = ef.run()
    >>> os.path.exists(res.outputs.out_file)
    True

    """

    input_spec = ExportFileInputSpec
    output_spec = ExportFileOutputSpec

    def _run_interface(self, runtime):
        if not self.inputs.clobber and op.exists(self.inputs.out_file):
            raise FileExistsError(self.inputs.out_file)
        if not op.isabs(self.inputs.out_file):
            raise ValueError("Out_file must be an absolute path.")
        if (
            self.inputs.check_extension
            and split_filename(self.inputs.in_file)[2]
            != split_filename(self.inputs.out_file)[2]
        ):
            raise RuntimeError(
                "%s and %s have different extensions"
                % (self.inputs.in_file, self.inputs.out_file)
            )
        shutil.copy(str(self.inputs.in_file), str(self.inputs.out_file))
        self._results["out_file"] = self.inputs.out_file
        return runtime
