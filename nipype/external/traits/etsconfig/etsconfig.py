""" Enthought Tool Suite configuration information. """


# Standard library imports.
import sys
import os
from os import path


class ETSConfig(object):
    """
    Enthought Tool Suite configuration information.

    This class should not use ANY other package in the tool suite so that it
    will always work no matter which other packages are present.

    """

    ###########################################################################
    # 'object' interface.
    ###########################################################################

    #### operator methods #####################################################

    def __init__(self):
        """
        Constructor.

        Note that this constructor can only ever be called from within this
        module, since we don't expose the class.

        """

        # Shadow attributes for properties.
        self._application_data = None
        self._application_home = None
        self._company          = None
        self._toolkit          = None
        self._kiva_backend     = None
        self._user_data        = None

        return


    ###########################################################################
    # 'ETSConfig' interface.
    ###########################################################################

    #### properties ###########################################################

    def get_application_data(self, create=False):
        """ Return the application data directory path.

            **Parameters**

            create: create the corresponding directory or not

            **Notes**

            This is a directory that applications and packages can safely
            write non-user accessible data to i.e. configuration
            information, preferences etc.

            Do not put anything in here that the user might want to navigate to
            e.g. projects, user data files etc.

            The actual location differs between operating systems.
       """
        if self._application_data is None:
            self._application_data = \
                    self._initialize_application_data(create=create)

        return self._application_data


    def _get_application_data(self):
        """ Property getter, see get_application_data's docstring.
        """
        return self.get_application_data(create=True)


    def _set_application_data(self, application_data):
        """
        Property setter.

        """

        self._application_data = application_data

        return

    def get_application_home(self, create=False):
        """ Return the application home directory path.

            **Parameters**

            create: create the corresponding directory or not

            **Notes**

            This is a directory named after the current, running
            application that imported this module that applications and
            packages can safely write non-user accessible data to i.e.
            configuration information, preferences etc.  It is a
            sub-directory of self.application_data, named after the
            directory that contains the "main" python script that started
            the process.  For example, if application foo is started with
            a script named "run.py" in a directory named "foo", then the
            application home would be: <ETSConfig.application_data>/foo,
            regardless of if it was launched with "python
            <path_to_foo>/run.py" or "cd <path_to_foo>; python run.py"

            This is useful for library modules used in apps that need to
            store state, preferences, etc. for the specific app only, and
            not for all apps which use that library module.  If the
            library module uses ETSConfig.application_home, they can
            store prefs for the app all in one place and do not need to
            know the details of where each app might reside.

            Do not put anything in here that the user might want to
            navigate to e.g. projects, user home files etc.

            The actual location differs between operating systems.

       """
        if self._application_home is None:
            self._application_home = path.join(
                                self.get_application_data(create=create),
                                self._get_application_dirname())

        return self._application_home



    application_data = property(_get_application_data, _set_application_data)


    def _get_application_home(self):
        """ Property getter, see get_application_home's docstring.
        """
        return self.get_application_home(create=True)


    def _set_application_home(self, application_home):
        """
        Property setter.

        """

        self._application_home = application_home

        return


    application_home = property(_get_application_home, _set_application_home)


    def _get_company(self):
        """
        Property getter.

        """

        if self._company is None:
            self._company = self._initialize_company()

        return self._company


    def _set_company(self, company):
        """
        Property setter for the company name.

        """

        self._company = company

        return


    company = property(_get_company, _set_company)


    def _get_toolkit(self):
        """
        Property getter for the GUI toolkit.  The value returned is, in order
        of preference: the value set by the application; the value passed on
        the command line using the '-toolkit' option; the value specified by
        the 'ETS_TOOLKIT' environment variable; otherwise the empty string.

        """

        if self._toolkit is None:
            self._toolkit = self._initialize_toolkit()

        return self._toolkit.split('.')[0]


    def _set_toolkit(self, toolkit):
        """
        Property setter for the GUI toolkit.  The toolkit can be set more than
        once, but only if it is the same one each time.  An application that is
        written for a particular toolkit can explicitly set it before any other
        module that gets the value is imported.

        """

        if self._toolkit and self._toolkit != toolkit:
            raise ValueError, "cannot set toolkit to %s because it has "\
                            "already been set to %s" % (toolkit, self._toolkit)

        self._toolkit = toolkit

        return


    toolkit = property(_get_toolkit, _set_toolkit)

    def _get_enable_toolkit(self):
        """
        Deprecated: This property is no longer used.

        Property getter for the Enable backend.  The value returned is, in order
        of preference: the value set by the application; the value passed on
        the command line using the '-toolkit' option; the value specified by
        the 'ENABLE_TOOLKIT' environment variable; otherwise the empty string.
        """
        from warnings import warn
        warn('Use of the enable_toolkit attribute is deprecated.')

        return self.toolkit


    def _set_enable_toolkit(self, toolkit):
        """
        Deprecated.

        Property setter for the Enable toolkit.  The toolkit can be set more than
        once, but only if it is the same one each time.  An application that is
        written for a particular toolkit can explicitly set it before any other
        module that gets the value is imported.
        """
        from warnings import warn
        warn('Use of the enable_toolkit attribute is deprecated.')

        return


    enable_toolkit = property(_get_enable_toolkit, _set_enable_toolkit)

    def _get_kiva_backend(self):
        """
        Property getter for the Kiva backend. The value returned is dependent
        on the value of the toolkit property. If toolkit specifies a kiva backend
        using the extended syntax: <enable toolkit>[.<kiva backend>] then the
        value of the property will be whatever was specified. Otherwise the
        value will be a reasonable default for the given enable backend.
        """
        if self._toolkit is None:
            raise AttributeError, "The kiva_backend attribute is dependent on toolkit, which has not been set."

        if self._kiva_backend is None:
            try:
                self._kiva_backend = self._toolkit.split('.')[1]
            except IndexError:
                # Pick a reasonable default based on the toolkit
                if self.toolkit == "wx":
                    self._kiva_backend = "quartz" if sys.platform == "darwin" else "image"
                elif self.toolkit == "qt4":
                    self._kiva_backend = "image"
                elif self.toolkit == "pyglet":
                    self._kiva_backend = "gl"
                else:
                    self._kiva_backend = "image"

        return self._kiva_backend

    kiva_backend = property(_get_kiva_backend)

    def _get_user_data(self):
        """
        Property getter.

        This is a directory that users can safely write user accessible data
        to i.e. user-defined functions, edited functions, etc.

        The actual location differs between operating systems.

        """

        if self._user_data is None:
            self._user_data = self._initialize_user_data()

        return self._user_data


    def _set_user_data(self, user_data):
        """
        Property setter.

        """

        self._user_data = user_data

        return


    user_data = property(_get_user_data, _set_user_data)


    #### private methods #####################################################

    # fixme: In future, these methods could allow the properties to be set
    # via the (as yet non-existent) preference/configuration mechanism. This
    # would allow configuration via (in order of precedence):-
    #
    # - a configuration file
    # - environment variables
    # - the command line

    def _get_application_dirname(self):
        """
        Return the name of the directory (not a path) that the "main"
        Python script which started this process resides in, or "" if it could
        not be determined or is not appropriate.

        For example, if the script that started the current process was named
        "run.py" in a directory named "foo", and was launched with "python
        run.py", the name "foo" would be returned (this assumes the directory
        name is the name of the app, which seems to be as good of an assumption
        as any).

        """

        dirname = ""

        main_mod = sys.modules.get('__main__', None)
        if main_mod is not None:
            if hasattr(main_mod, '__file__'):
                main_mod_file = path.abspath(main_mod.__file__)
                dirname = path.basename(path.dirname(main_mod_file))

        return dirname


    def _initialize_application_data(self, create=True):
        """
        Initializes the (default) application data directory.

        """

        if sys.platform == 'win32':
            environment_variable = 'APPDATA'
            directory_name       = self.company

        else:
            environment_variable = 'HOME'
            directory_name       = '.' + self.company.lower()

        # Lookup the environment variable.
        parent_directory = os.environ.get(environment_variable, None)
        if parent_directory is None or parent_directory == '/root':
            import tempfile
            from warnings import warn
            parent_directory = tempfile.gettempdir()
            user = os.environ.get('USER', None)
            if user is not None:
                directory_name += "_%s" % user
            warn('Environment variable "%s" not set, setting home directory to %s' % \
                (environment_variable, parent_directory))

        application_data = os.path.join(parent_directory, directory_name)

        if create:
            # If a file already exists with this name then make sure that it is
            # a directory!
            if os.path.exists(application_data):
                if not os.path.isdir(application_data):
                    raise ValueError('File "%s" already exists'
                                                    % application_data)

            # Otherwise, create the directory.
            else:
                os.makedirs(application_data)

        return application_data


    def _initialize_company(self):
        """
        Initializes the (default) company.

        """

        return 'Enthought'


    def _initialize_toolkit(self):
        """
        Initializes the toolkit.

        """
        # We handle the command line option even though it doesn't have the
        # highest precedence because we always want to remove it from the
        # command line.
        if '-toolkit' in sys.argv:
            opt_idx = sys.argv.index('-toolkit')

            try:
                opt_toolkit = sys.argv[opt_idx + 1]
            except IndexError:
                raise ValueError, "the -toolkit command line argument must be followed by a toolkit name"

            # Remove the option.
            del sys.argv[opt_idx:opt_idx + 1]
        else:
            opt_toolkit = None

        if self._toolkit is not None:
            toolkit = self._toolkit
        elif opt_toolkit is not None:
            toolkit = opt_toolkit
        else:
            toolkit = os.environ.get('ETS_TOOLKIT', '')

        return toolkit


    def _initialize_user_data(self):
        """
        Initializes the (default) user data directory.

        """

        # We check what the os.path.expanduser returns
        parent_directory = os.path.expanduser('~')
        directory_name = self.company


        if sys.platform == 'win32':
            # Check if the usr_dir is C:\\John Doe\\Documents and Settings.
            # If yes, then we should modify the usr_dir to be 'My Documents'.
            # If no, then the user must have modified the os.environ
            # variables and the directory chosen is a desirable one.
            desired_dir = os.path.join(parent_directory, 'My Documents')

            if os.path.exists(desired_dir):
                parent_directory = desired_dir

        else:
            directory_name = directory_name.lower()

        # The final directory.
        usr_dir = os.path.join(parent_directory, directory_name)

        # If a file already exists with this name then make sure that it is
        # a directory!
        if os.path.exists(usr_dir):
            if not os.path.isdir(usr_dir):
                raise ValueError('File "%s" already exists' % usr_dir)

        # Otherwise, create the directory.
        else:
            os.makedirs(usr_dir)

        return usr_dir



# We very purposefully only have one object and do not export the class. We
# could have just made everything class methods, but that always seems a bit
# gorpy, especially with properties etc.
ETSConfig = ETSConfig()


#### EOF ######################################################################
