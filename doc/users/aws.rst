.. _aws:

============================================
Using Nipype with Amazon Web Services (AWS)
============================================
Several groups have been successfully using Nipype on AWS. This procedure
involves setting a temporary cluster using StarCluster and potentially
transferring files to/from S3. The latter is supported by Nipype through
DataSink and S3DataGrabber.


Using DataSink with S3
======================
The DataSink class now supports sending output data directly to an AWS S3
bucket. It does this through the introduction of several input attributes to the
DataSink interface and by parsing the `base_directory` attribute. This class
uses the `boto3 <https://boto3.readthedocs.org/en/latest/>`_ and
`botocore <https://botocore.readthedocs.org/en/latest/>`_ Python packages to
interact with AWS. To configure the DataSink to write data to S3, the user must
set the ``base_directory`` property to an S3-style filepath. For example:

::

	import nipype.interfaces.io as nio
	ds = nio.DataSink()
	ds.inputs.base_directory = 's3://mybucket/path/to/output/dir'

With the "s3://" prefix in the path, the DataSink knows that the output
directory to send files is on S3 in the bucket "mybucket". "path/to/output/dir"
is the relative directory path within the bucket "mybucket" where output data
will be uploaded to (NOTE: if the relative path specified contains folders that
don’t exist in the bucket, the DataSink will create them). The DataSink treats
the S3 base directory exactly as it would a local directory, maintaining support
for containers, substitutions, subfolders, "." notation, etc to route output
data appropriately.

There are four new attributes introduced with S3-compatibility: ``creds_path``,
``encrypt_bucket_keys``, ``local_copy``, and ``bucket``.

::

	ds.inputs.creds_path = '/home/user/aws_creds/credentials.csv'
	ds.inputs.encrypt_bucket_keys = True
	ds.local_copy = '/home/user/workflow_outputs/local_backup'

``creds_path`` is a file path where the user's AWS credentials file (typically
a csv) is stored. This credentials file should contain the AWS access key id and
secret access key and should be formatted as one of the following (these formats
are how Amazon provides the credentials file by default when first downloaded).

Root-account user:

::

	AWSAccessKeyID=ABCDEFGHIJKLMNOP
	AWSSecretKey=zyx123wvu456/ABC890+gHiJk

IAM-user:

::

	User Name,Access Key Id,Secret Access Key
	"username",ABCDEFGHIJKLMNOP,zyx123wvu456/ABC890+gHiJk

The ``creds_path`` is necessary when writing files to a bucket that has
restricted access (almost no buckets are publicly writable). If ``creds_path``
is not specified, the DataSink will check the ``AWS_ACCESS_KEY_ID`` and
``AWS_SECRET_ACCESS_KEY`` environment variables and use those values for bucket
access.

``encrypt_bucket_keys`` is a boolean flag that indicates whether to encrypt the
output data on S3, using server-side AES-256 encryption. This is useful if the
data being output is sensitive and one desires an extra layer of security on the
data. By default, this is turned off.

``local_copy`` is a string of the filepath where local copies of the output data
are stored in addition to those sent to S3. This is useful if one wants to keep
a backup version of the data stored on their local computer. By default, this is
turned off.

``bucket`` is a boto3 Bucket object that the user can use to overwrite the
bucket specified in their ``base_directory``. This can be useful if one has to
manually create a bucket instance on their own using special credentials (or
using a mock server like `fakes3 <https://github.com/jubos/fake-s3>`_). This is
typically used for developers unit-testing the DataSink class. Most users do not
need to use this attribute for actual workflows. This is an optional argument.

Finally, the user needs only to specify the input attributes for any incoming
data to the node, and the outputs will be written to their S3 bucket.

::

	workflow.connect(inputnode, 'subject_id', ds, 'container')
	workflow.connect(realigner, 'realigned_files', ds, 'motion')

So, for example, outputs for sub001’s realigned_file1.nii.gz will be in:
s3://mybucket/path/to/output/dir/sub001/motion/realigned_file1.nii.gz


Using S3DataGrabber
======================
Coming soon...
