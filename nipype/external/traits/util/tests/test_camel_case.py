# Standard library imports.
import unittest

# Local imports.
from traits.util.camel_case import camel_case_to_python, camel_case_to_words


class CamelCaseTestCase(unittest.TestCase):

    def test_python_conversion(self):
        """ Does CamelCase -> Python name work?
        """
        c_names = [ 'GetFooBar', 'GetOBBTree', 'XMLDataReader',
                    'GetFooXML', 'HTMLIsSGML', '_SetMe', '_XYZTest',
                    'Actor2D', 'Actor3D', 'Actor6D', 'PLOT3DReader',
                    'Actor61Dimension', 'GL2PSExporter', 'Volume16Reader' ]
        t_names = [ 'get_foo_bar', 'get_obb_tree', 'xml_data_reader',
                    'get_foo_xml', 'html_is_sgml', '_set_me',
                    '_xyz_test', 'actor2d', 'actor3d', 'actor6_d',
                    'plot3d_reader', 'actor61_dimension',
                    'gl2ps_exporter', 'volume16_reader' ]
        for i, c_name in enumerate(c_names):
            t_name = camel_case_to_python(c_name)
            self.assertEqual(t_name, t_names[i])

    def test_word_conversion(self):
        """ Does CamelCase -> words work?
        """
        self.assertEqual(camel_case_to_words('FooBarBaz'), 'Foo Bar Baz')


if __name__ == "__main__":
    unittest.main()
