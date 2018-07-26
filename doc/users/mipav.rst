.. _mipav:

================================
Using MIPAV, JIST, and CBS Tools
================================

If you are trying to use MIPAV, JIST or CBS Tools interfaces you need
to configure CLASSPATH environmental variable correctly. It needs to
include extensions shipped with MIPAV, MIPAV itself and MIPAV plugins.
For example:

In order to use the standalone MCR version of spm, you need to ensure that
the following commands are executed at the beginning of your script:

.. testcode::


    # location of additional JAVA libraries to use
    JAVALIB=/Applications/mipav/jre/Contents/Home/lib/ext/

    # location of the MIPAV installation to use
    MIPAV=/Applications/mipav
    # location of the plugin installation to use
    # please replace 'ThisUser' by your user name
    PLUGINS=/Users/ThisUser/mipav/plugins

    export CLASSPATH=$JAVALIB/*:$MIPAV:$MIPAV/lib/*:$PLUGINS
