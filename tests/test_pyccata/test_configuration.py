# namespace imports
import os

# specific imports
from unittest                   import TestCase
from mock                       import patch, PropertyMock
from ddt                        import ddt, data, unpack
from collections                import namedtuple
from pyccata.core.configuration import Configuration
from pyccata.core.exceptions    import RequiredKeyError, InvalidClassError
from tests.mocks.dataproviders import DataProviders
from pyccata.core.log import Logger
from pyccata.core.resources import Replacements

@ddt
class TestConfiguration(TestCase):
    _test_configuration_path = ''
    _required_root_elements = Configuration._required_root_elements

    @patch('argparse.ArgumentParser.parse_args')
    @patch('pyccata.core.log.Logger.log')
    def setUp(self, mock_log, mock_parser):
        self.tearDown()
        mock_log.return_value = None
        mock_parser.return_value = []
        self.mock_parser = mock_parser
        path = os.path.dirname(os.path.realpath(__file__ + '../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        Logger._instance = mock_log

    def tearDown(self):
        Configuration.NAMESPACE = 'pyccata.core'
        if Configuration._instance is not None:
            del Configuration._instance
            Configuration._instance = None
        if Configuration._configuration is not None:
            del Configuration._configuration
            Configuration._configuration = None
        Configuration._required_root_elements = self._required_root_elements
        if Replacements._instance is not None:
            del Replacements._instance
            Replacements._instance = None

    @patch('pyccata.core.configuration.Configuration._get_locations')
    def test_configuration_raises_io_exception_if_config_file_cannot_be_found(self, mock_config_list):
        mock_config_list.return_value = ['/i/dont/exist']

        # patching initialises singletons - tear-down to ensure a clean start
        self.tearDown()
        with self.assertRaises(IOError):
            Configuration()

    @patch('pyccata.core.configuration.Configuration._get_locations')
    @patch('pyccata.core.configuration.Configuration.validate_config')
    def test_configuration_calls_validation_once_config_is_loaded(self, mock_validate, mock_config_list):
        mock_config_list.return_value = [self._path]
        mock_validate.return_value = True
        self.tearDown()
        Configuration(filename='config_sections.json')
        mock_validate.assert_called_with(['manager'])

    @patch('pyccata.core.configuration.Configuration._load')
    def test_config_locations_returns_five_paths(self, mock_load):
        """
        Purely for code coverage...
        """
        mock_load.return_value = None
        config = Configuration(filename='')
        self.assertEquals(5, len(config._get_locations()))

    @patch('pyccata.core.configuration.Configuration._get_locations')
    def test_configuration_raises_requried_key_error_if_required_value_is_not_defined(self, mock_config_list):
        key = 'idontexist'
        mock_config_list.return_value = [self._path]
        self.tearDown()
        Configuration._required_root_elements = [key]
        required_elements = Configuration._required_root_elements
        with self.assertRaisesRegexp(RequiredKeyError, '.*\'<root>[./]?{0}\'.*'.format(key)):
            config = Configuration(filename='config_sections.json')

    @patch('pyccata.core.configuration.Configuration._load')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    @data(
        ['manager', 'jira'],
        ['reporting', 'docx']
    )
    @unpack
    def test_configuration_calls_validation_once_config_is_loaded(self, data_key, data_driver, mock_config_list, mock_load):
        mock_config = DataProviders._get_config_for_test()
        mock_config_list.return_value = [self._path]
        mock_load.return_value = None
        self.tearDown()
        Configuration._configuration = mock_config
        required_elements = [data_key]
        config = Configuration(filename='config_sections.json')
        mock_load.assert_called_once_with()
        with patch(
            'pyccata.core.configuration.Configuration.{0}'.format(data_key),
            new_callable=PropertyMock
        ) as mock_manager:
            mock_manager.return_value = object()
            self.assertTrue(config.validate_config(required_elements))
            mock_manager.assert_called_with(data_driver)

    @patch('pyccata.core.configuration.Configuration._parse_flags')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    def test_configuration_doesnt_assign_required_if_property_doesnt_exist(self, mock_config_list, mock_parser):
        mock_config = DataProviders._get_config_for_test()
        mock_config_list.return_value = [self._path]
        required_elements = ['manager', 'iamrequiredandexistinconfigbutdonothaveaproperty']
        self.tearDown()
        Configuration._configuration = mock_config
        Configuration._required_root_elements = required_elements
        config = Configuration(filename='config_no_property.json')

    @patch('pyccata.core.configuration.Configuration._parse_flags')
    @patch('pyccata.core.configuration.Configuration._load')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    @data(
        ['manager', 'agilemanager'],
        ['reporting', 'pdf']
    )
    @unpack
    def test_configuration_raises_requried_key_error_if_required_config_is_not_found(self, data_key, data_driver, mock_config_list, mock_load, mock_parser):
        mock_config = DataProviders._get_config_for_test_without_report(manager=data_driver, reporting=data_driver)
        mock_config_list.return_value = [self._path]
        Configuration._configuration = mock_config

        driver = data_driver if data_key != 'reporting' else 'report'
        with self.assertRaisesRegexp(RequiredKeyError, '.*\'<root>[./]?{0}\'.*'.format(driver)):
            config = Configuration(filename='config_missing.json')
            config.validate_config([data_key])
        mock_load.assert_called_once_with()

    @patch('pyccata.core.configuration.Configuration._load')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    @data(
        ['manager', 'willneverbeamanager'],
        ['reporting', 'iwillneverexist']
    )
    @unpack
    def test_configuration_raises_invalid_class_error_if_required_class_does_not_exist(self, data_key, data_driver, mock_config_list, mock_load):
        mock_config = DataProviders._get_config_for_test_with_invalid_classes()
        mock_load.return_value = None
        self.tearDown()

        mock_config_list.return_value = [self._path]
        Configuration._configuration = mock_config

        with self.assertRaises(InvalidClassError):
            config = Configuration(filename='config_sections.json')
            config.validate_config([data_key])
        mock_load.assert_called_once_with()

    @patch('pyccata.core.configuration.Configuration._load')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    @data(
        ['manager', 'jira'],
        ['reporting', 'docx']
    )
    @unpack
    def test_manager_loading_returns_true_if_required_is_valid(self, data_key, data_driver, mock_config_list, mock_load):
        mock_config = DataProviders._get_config_for_test(manager=data_driver, reporting=data_driver)
        mock_load.return_value = None
        self.tearDown()

        mock_config_list.return_value = [self._path]
        Configuration._configuration = mock_config
        Configuration.NAMESPACE = 'tests.mocks'

        config = Configuration(filename='config_sections.json')
        config.validate_config([data_key])
        mock_load.assert_called_once_with()
        self.assertEquals(data_driver, getattr(config, data_key))

    @patch('pyccata.core.configuration.Configuration._load')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    @data(
        ['manager', 'jira'],
        ['reporting', 'docx']
    )
    @unpack
    def test_config_getattr_method(self, data_key, data_driver, mock_config_list, mock_load):
        mock_config = DataProviders._get_config_for_test(manager=data_driver, reporting=data_driver)
        mock_load.return_value = None
        self.tearDown()

        mock_config_list.return_value = [self._path]
        Configuration._configuration = mock_config
        Configuration.NAMESPACE = 'tests.mocks'

        config = Configuration(filename='config_sections.json')
        config.check = True
        required_elements = [data_key]
        config.validate_config(required_elements)
        mock_load.assert_called_once_with()
        self.assertTrue(config.check)
        with self.assertRaises(AttributeError):
            config.iamnothere

    @patch('argparse.ArgumentParser.parse_args')
    @patch('argparse.ArgumentParser.add_argument')
    @patch('pyccata.core.configuration.Configuration._get_locations')
    def test_config_parse_flags(self, mock_config_list, mock_arguments, mock_parser):
        mock_config_list.return_value = [self._path]
        Configuration.NAMESPACE = 'tests.mocks'
        mock_parser.return_value = []
        config = Configuration(filename='valid_config.json')
        self.assertGreater(mock_parser.call_count, 0)
        config.check = True
        self.assertTrue(config.check)
        self.assertIsInstance(config.replacements, Replacements)

