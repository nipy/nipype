

import logging
import sys
import traceback
import types

from traits.api import Any, Bool, HasTraits, Instance, Str


#Setup a logger for this module.
logger = logging.getLogger(__name__)


#starting with python 2.5 exceptions are no longer instances of types.ClassType
EXCEPTION_BASE_TYPE = types.ClassType
try:
    import exceptions
    if not isinstance(exceptions.Exception, types.ClassType):
        EXCEPTION_BASE_TYPE = types.ObjectType
except:
    pass

class ExceptionHandler(HasTraits):
    """ Provides standardized exception handling.

    Instantiate immediately after 'except:' to capture the exception and
    stack frame information.
    """

    # Application message.
    message = Str

    # Initialized form rom sys.exc_info on object creation.
    ex_type = Instance(EXCEPTION_BASE_TYPE)

    # Initialized form rom sys.exc_info on object creation.
    ex_value = Any # Instance(Exception)

    # Initialized form rom sys.exc_info on object creation.
    ex_traceback = Instance(types.TracebackType)

    # Formatted text for the exception.
    exception_text = Str

    # Formatted text for the exception only. I.e. without stack trace.
    exception_only_text = Str

    # Enter message in the log using traits.logger; default is True.
    use_logger = Bool(True)

    def __init__(self, **traits):
        """ Creates an ExceptionHandler initialized with the most recent
        traceback information.
        Optionally logs the exception using traits.logger.
        """
        super(ExceptionHandler,self).__init__(**traits)
        self.ex_type, self.ex_value, self.ex_traceback = sys.exc_info()
        if self.use_logger:
            logger.error( str(self) )
        return

    def __str__(self):
        """ Returns string representation of self. """
        text = self.message + '\n' + self.exception_text
        return text

    def _exception_text_default(self):
        """ Returns formatted exception. """
        list_o_lines = traceback.format_exception( self.ex_type,
                                                   self.ex_value,
                                                   self.ex_traceback)

        lines = ''.join(list_o_lines)

        # remove trailing \n
        return lines.strip()


    def _exception_only_text_default(self):
        """ Returns formatted exception only (see traceback).
        I.e. without stack trace.
        """
        list_o_lines = traceback.format_exception_only( self.ex_type,
                                                        self.ex_value)

        lines = ''.join(list_o_lines)

        # remove trailing \n
        return lines.strip()

    def trait_view(self, name=None, view_element=None):
        """ Returns a View """
        if (name or view_element) != None:
            return super(ExceptionHandler, self).trait_view( name=name,
                                                view_element=view_element )

        from exception_handler_view import ExceptionHandlerView
        return ExceptionHandlerView()

### EOF
