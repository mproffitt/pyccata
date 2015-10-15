# namespace imports
import os

# specific imports
from unittest                   import TestCase
from mock                       import patch, PropertyMock
from ddt                        import ddt, data, unpack
from collections                import namedtuple
from weeklyreport.configuration import Configuration
from weeklyreport.exceptions    import RequiredKeyError, InvalidClassError

@ddt
class TestConfiguration(TestCase):
    _test_configuration_path = ''
    _required_root_elements = Configuration._required_root_elements

    def setUp(self):
        path = os.path.dirname(os.path.realpath(__file__ + '../../../'))
        self._path = os.path.join(path, os.path.join('tests', 'conf'))

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
    def test_configuration_calls_validation_once_config_is_loaded(self, mock_config_list, mock_load):
        Config = namedtuple('Config', 'manager jira server port')
        Jira   = Config(manager = None, jira = None, server = 'http://jira.local', port = '8080')
        mock_config = Config(manager = 'jira', jira = Jira, server = None, port = None)
        mock_config_list.return_value = [self._path]
        mock_load.return_value = None
        self.tearDown()
        Configuration._configuration = mock_config
        required_elements = Configuration._required_root_elements
        config = Configuration(filename='config_sections.json')
        mock_load.assert_called_once_with()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            mock_manager.return_value = object()
            self.assertTrue(config.validate_config(required_elements))
            mock_manager.assert_called_with('jira')

    @patch('weeklyreport.configuration.Configuration._load')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_configuration_raises_requried_key_error_if_manager_config_is_not_found(self, mock_config_list, mock_load):
        key = 'agilemanager'
        Config = namedtuple('Config', 'manager jira server port')
        Jira   = Config(manager = None, jira = None, server = 'http://jira.local', port = '8080')
        mock_config = Config(manager = key, jira = Jira, server = None, port = None)
        mock_load.return_value = None
        self.tearDown()

        mock_config_list.return_value = [self._path]
        Configuration._configuration = mock_config

        with self.assertRaisesRegexp(RequiredKeyError, '.*\'<root>[./]?{0}\'.*'.format(key)):
            config = Configuration(filename='config_sections.json')
            required_elements = Configuration._required_root_elements
            config.validate_config(required_elements)
        mock_load.assert_called_once_with()

    @patch('weeklyreport.configuration.Configuration._load')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_configuration_raises_invalid_class_error_if_manager_class_does_not_exist(self, mock_config_list, mock_load):
        key = 'iwillneverbeamanager'
        Config = namedtuple('Config', 'manager iwillneverbeamanager server port')
        Jira   = Config(manager = None, iwillneverbeamanager = None, server = 'http://jira.local', port = '8080')
        mock_config = Config(manager = key, iwillneverbeamanager = Jira, server = None, port = None)
        mock_load.return_value = None
        self.tearDown()

        mock_config_list.return_value = [self._path]
        Configuration._configuration = mock_config

        with self.assertRaises(InvalidClassError):
            config = Configuration(filename='config_sections.json')
            required_elements = Configuration._required_root_elements
            config.validate_config(required_elements)
        mock_load.assert_called_once_with()

    @patch('weeklyreport.configuration.Configuration._load')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_manager_loading_returns_true_if_manager_is_valid(self, mock_config_list, mock_load):
        key = 'jira'
        Config = namedtuple('Config', 'manager jira server port')
        Jira   = Config(manager = None, jira = None, server = 'http://jira.local', port = '8080')
        mock_config = Config(manager = key, jira = Jira, server = None, port = None)
        mock_load.return_value = None
        self.tearDown()

        mock_config_list.return_value = [self._path]
        Configuration._configuration = mock_config
        Configuration.NAMESPACE = 'tests.mocks'

        config = Configuration(filename='config_sections.json')
        required_elements = Configuration._required_root_elements
        config.validate_config(required_elements)
        mock_load.assert_called_once_with()
        self.assertEquals('jira', config.manager)

    @patch('weeklyreport.configuration.Configuration._load')
    @patch('weeklyreport.configuration.Configuration._get_locations')
    def test_manager_getattr_method(self, mock_config_list, mock_load):
        key = 'jira'
        Config = namedtuple('Config', 'manager jira server port')
        Jira   = Config(manager = None, jira = None, server = 'http://jira.local', port = '8080')
        mock_config = Config(manager = key, jira = Jira, server = None, port = None)
        mock_load.return_value = None
        self.tearDown()

        mock_config_list.return_value = [self._path]
        Configuration._configuration = mock_config
        Configuration.NAMESPACE = 'tests.mocks'

        config = Configuration(filename='config_sections.json')
        config.check = True
        required_elements = Configuration._required_root_elements
        config.validate_config(required_elements)
        mock_load.assert_called_once_with()
        self.assertTrue(config.check)
        with self.assertRaises(AttributeError):
            config.iamnothere

