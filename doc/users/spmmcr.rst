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

Information about the MCR version of SPM8 can be found at:

http://en.wikibooks.org/wiki/SPM/Standalone
