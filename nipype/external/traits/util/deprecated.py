""" A decorator for marking methods/functions as deprecated. """


# Standard library imports.
import logging

# Logging.
logger = logging.getLogger(__name__)


# We only warn about each function or method once!
_cache = {}


def deprecated(message):
    """ A factory for decorators for marking methods/functions as deprecated.

    """

    def decorator(fn):
        """ A decorator for marking methods/functions as deprecated. """

        def wrapper(*args, **kw):
            """ The method/function wrapper. """

            global _cache

            module_name = fn.__module__
            function_name = fn.__name__

            if (module_name, function_name) not in _cache:
                logging.warn(
                    'DEPRECATED: %s.%s, %s' % (
                        module_name, function_name, message
                    )
                )

                _cache[(module_name, function_name)] = True

            return fn(*args, **kw)

        wrapper.__doc__  = fn.__doc__
        wrapper.__name__ = fn.__name__

        return wrapper

    return decorator

#### EOF ######################################################################
