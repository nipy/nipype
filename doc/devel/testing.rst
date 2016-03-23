=======
Testing
=======

The best way to test nipype is to run the test suite.  If you have
nose_ installed, then do the following::

    python -c "import nipype; nipype.test()"

you can also test with nosetests::

    nosetests --with-doctest /software/nipy-repo/masternipype/nipype
    --exclude=external --exclude=testing

All tests should pass (unless you're missing a dependency). If SUBJECTS_DIR
variable is not set some FreeSurfer related tests will fail.

On Debian systems, set the following environment variable before running
tests::

       export MATLABCMD=$pathtomatlabdir/bin/$platform/MATLAB

where, $pathtomatlabdir is the path to your matlab installation and
$platform is the directory referring to x86 or x64 installations
(typically glnxa64 on 64-bit installations).

Avoiding any MATLAB calls from testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On unix systems, set an empty environment variable::

    export NIPYPE_NO_MATLAB=

This will skip any tests that require matlab.