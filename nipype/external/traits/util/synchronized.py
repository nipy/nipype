""" A decorator for making methods thread-safe via an object-scope lock. """


def synchronized(lock_attribute='_lk'):
    """ A factory for decorators for making methods thread-safe. """

    def decorator(fn):
        """ A decorator for making methods thread-safe. """

        def wrapper(self, *args, **kw):
            """ The method/function wrapper. """

            lock = getattr(self, lock_attribute)
            try:
                lock.acquire()
                result = fn(self, *args, **kw)

            finally:
                lock.release()

            return result

        wrapper.__doc__  = fn.__doc__
        wrapper.__name__ = fn.__name__

        return wrapper

    return decorator

#### EOF ######################################################################
