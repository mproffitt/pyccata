# namespace imports
import os

# specific imports
from unittest                   import TestCase
from mock                       import patch, PropertyMock
from ddt                        import ddt, data, unpack
from collections                import namedtuple
from weeklyreport.configuration import Configuration
from weeklyreport.exceptions    import RequiredKeyError, InvalidClassError
from tests.mocks.dataproviders import DataProviders
from weeklyreport.log import Logger

@ddt
class TestConfiguration(TestCase):
    _test_configuration_path = ''
    _required_root_elements = Configuration._required_root_elements

    @patch('weeklyreport.log.Logger.log')
    def setUp(self, mock_log):
        mock_log.return_value = None
        path = os.path.dirname(os.path.realpath(__file__ + '../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))
        self._mock_log = mock_log

    def tearDown(self):
        Configuration.NAMESPACE = 'weeklyreport'
        if Configuration._instance is not None:
            Configuration._instance = None
        if Configuration._configuration is not None:
            Configuration._configuration = None
        Configuration._required_root_elements = self._required_root_elements

    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_configuration_raises_io_exception_if_config_file_cannot_be_found(self, mock_config_list):
        mock_config_list.return_value = ['/i/dont/exist']

        # patching initialises singletons - tear-down to ensure a clean start
        self.tearDown()
        with self.assertRaises(IOError):
            Configuration()

    @patch('weeklyreport.configuration.Configuration._get_locations')
    @patch('weeklyreport.configuration.Configuration.validate_config')
    def test_configuration_calls_validation_once_config_is_loaded(self, mock_validate, mock_config_list):
        mock_config_list.return_value = [self._path]
        mock_validate.return_value = True
        self.tearDown()
        Configuration(filename='config_sections.json')
        mock_validate.assert_called_with(['manager'])

    @patch('weeklyreport.configuration.Configuration._load')
    def test_config_locations_returns_five_paths(self, mock_load):
        """
        Purely for code coverage...
        """
        mock_load.return_value = None
        config = Configuration(filename='')
        self.assertEquals(5, len(config._get_locations()))

    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_configuration_raises_requried_key_error_if_required_value_is_not_defined(self, mock_config_list):
        key = 'idontexist'
        mock_config_list.return_value = [self._path]
        self.tearDown()
        Configuration._required_root_elements = [key]
        required_elements = Configuration._required_root_elements
        with self.assertRaisesRegexp(RequiredKeyError, '.*\'<root>[./]?{0}\'.*'.format(key)):
            config = Configuration(filename='config_sections.json')

    @patch('weeklyreport.configuration.Configuration._load')
    @patch('weeklyreport.configuration.Configuration._get_locations')
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
            'weeklyreport.configuration.Configuration.{0}'.format(data_key),
            new_callable=PropertyMock
        ) as mock_manager:
            mock_manager.return_value = object()
            self.assertTrue(config.validate_config(required_elements))
            mock_manager.assert_called_with(data_driver)

    @patch('weeklyreport.configuration.Configuration._load')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    @data(
        ['manager', 'agilemanager'],
        ['reporting', 'pdf']
    )
    @unpack
    def test_configuration_raises_requried_key_error_if_required_config_is_not_found(self, data_key, data_driver, mock_config_list, mock_load):
        mock_config = DataProviders._get_config_for_test_without_report(manager=data_driver, reporting=data_driver)
        mock_config_list.return_value = [self._path]
        Configuration._configuration = mock_config

        driver = data_driver if data_key != 'reporting' else 'report'
        with self.assertRaisesRegexp(RequiredKeyError, '.*\'<root>[./]?{0}\'.*'.format(driver)):
            config = Configuration(filename='config_missing.json')
            config.validate_config([data_key])
        mock_load.assert_called_once_with()

    @patch('weeklyreport.configuration.Configuration._load')
    @patch('weeklyreport.configuration.Configuration._get_locations')
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

    @patch('weeklyreport.configuration.Configuration._load')
    @patch('weeklyreport.configuration.Configuration._get_locations')
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

    @patch('weeklyreport.configuration.Configuration._load')
    @patch('weeklyreport.configuration.Configuration._get_locations')
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

