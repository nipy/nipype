.. _spmmcr:

====================================
Using SPM with MATLAB Common Runtime
====================================

In order to use the standalone MCR version of spm, you need to ensure that
the following commands are executed at the beginning of your script:

.. testcode::

    from nipype import spm
    matlab_cmd = '/path/to/run_spm8.sh /path/to/Compiler_Runtime/v713/ script'
    spm.SPMCommand.set_mlab_paths(matlab_cmd=matlab_cmd, use_mcr=True)

you can test by calling:

.. testcode::

    spm.SPMCommand().version

If you want to enforce the standalone MCR version of spm for nipype globally,
you can do so by setting the following environment variables:

*SPMMCRCMD*
    Specifies the command to use to run the spm standalone MCR version. You
    may still override the command as described above.

*FORCE_SPMMCR*
    Set this to any value in order to enforce the use of spm standalone MCR
    version in nipype globally. Technically, this sets the `use_mcr` flag of
    the spm interface to True.

Information about the MCR version of SPM8 can be found at:

http://en.wikibooks.org/wiki/SPM/Standalone
