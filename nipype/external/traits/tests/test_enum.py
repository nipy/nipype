import unittest

from traits.api import Enum, HasTraits, List, Property, TraitError

class ExampleModel(HasTraits):
    valid_models = Property(List)
    root = Enum(values='valid_models')

    def _get_valid_models(self):
        return ['model1', 'model2', 'model3']

class EnumTestCase(unittest.TestCase):
    def test_valid_enum(self):
        example_model = ExampleModel(root='model1')
        example_model.root = 'model2'

    def test_invalid_enum(self):
        example_model = ExampleModel(root='model1')

        def assign_invalid():
            example_model.root = 'not_valid_model'

        self.assertRaises(TraitError, assign_invalid)


