.. _cli:

=============================
Nipype Command Line Interface
=============================

The Nipype Command Line Interface allows a variety of operations::

    $ nipypecli
    Usage: nipypecli [OPTIONS] COMMAND [ARGS]...

    Options:
      -h, --help  Show this message and exit.

    Commands:
      convert  Export nipype interfaces to other formats.
      crash    Display Nipype crash files.
      run      Run a Nipype Interface.
      search   Search for tracebacks content.
      show     Print the content of Nipype node .pklz file.

These have replaced previous nipype command line tools such as
`nipype_display_crash`, `nipype_crash_search`, `nipype2boutiques`,
`nipype_cmd` and `nipype_display_pklz`.
