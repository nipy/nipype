

import logging
from StringIO import StringIO
import sys
import unittest

from traits.util.ui.exception_handler import ExceptionHandler


class ExceptionHandlerTestCase(unittest.TestCase):

    def setUp(self):
        # Silence "lack of logger handler" messages.
        f = StringIO()
        logging.basicConfig(stream=f)

    def test_simple(self):
        try:
            ex_handler = None
            raise Exception, 'test exception'

        except:
            ex_handler = ExceptionHandler(message='Your message here!')
            t, v, tb = sys.exc_info()

            self.assertEqual(t, ex_handler.ex_type)
            self.assertEqual(v, ex_handler.ex_value)
            self.assertEqual(tb, ex_handler.ex_traceback)
            self.assert_(str(ex_handler).startswith('Your message here!'))
            self.assert_(str(ex_handler).endswith('Exception: test exception'))

        self.assert_(ex_handler is not None)


    def ui_simple_dialog(self):
        try:
            ex_handler = None
            raise Exception, 'test exception'

        except:
            ex_handler = ExceptionHandler(message=
                                          'Your application message here!')
            ex_handler.configure_traits()


    def ui_file_not_found(self):
        try:
            ex_handler = None
            file('foo.bar', 'rb')

        except:
            ex_handler = ExceptionHandler(message='Unable to find your file.')
            ex_handler.configure_traits()


    def ui_syntax_error(self):
        try:
            ex_handler = None
            eval('import foo')

        except:
            ex_handler = ExceptionHandler(message='Trouble with your source.')
            ex_handler.configure_traits()


if __name__ == "__main__":
    unittest.main()
