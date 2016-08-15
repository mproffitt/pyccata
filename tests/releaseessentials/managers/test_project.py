from unittest import TestCase
from mock     import patch, PropertyMock
from collections import namedtuple
from releaseessentials.configuration import Configuration
from releaseessentials.interface import ManagerInterface
from releaseessentials.exceptions import InvalidModuleError
from releaseessentials.exceptions import InvalidClassError
from releaseessentials.exceptions import RequiredKeyError
from releaseessentials.managers.project import ProjectManager
from tests.mocks.dataproviders import InvalidRequires
from releaseessentials.log import Logger

class TestProjectManager(TestCase):

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.log.Logger.log')
    def setUp(self, mock_log, mock_parser):
        mock_log.return_value = None
        mock_parser.return_value = None
        Logger._instance = mock_log

    def tearDown(self):
        if Configuration._instance is not None:
            Configuration._instance = None
        Configuration.NAMESPACE = 'releaseessentials'

    @patch('releaseessentials.configuration.Configuration._load')
    def test_manager_raises_invalid_module_error_if_manager_module_does_not_exist(self, mock_load):
        key = 'iwillneverbeamanager'
        with patch('releaseessentials.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            mock_manager.return_value = key
            with self.assertRaisesRegexp(InvalidModuleError, '{0}.*{1}.*'.format(key, Configuration.NAMESPACE)):
                ProjectManager()

    @patch('releaseessentials.configuration.Configuration._load')
    def test_manager_raises_invalid_class_error_if_manager_class_does_not_exist(self, mock_load):
        key = 'managermodule'
        Configuration.NAMESPACE = 'tests.mocks'
        with patch('releaseessentials.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            mock_manager.return_value = key
            with self.assertRaisesRegexp(InvalidClassError, 'Managermodule .* {0}.*'.format(Configuration.NAMESPACE)):
                ProjectManager()

    @patch('releaseessentials.configuration.Configuration._load')
    def test_manager_raises_import_error_if_manager_class_does_not_exist(self, mock_load):
        key = 'agilemanager'
        Configuration.NAMESPACE = 'tests.mocks'
        with patch('releaseessentials.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            mock_manager.return_value = key
            with self.assertRaises(ImportError):
                a = ProjectManager()

    @patch('releaseessentials.configuration.Configuration._load')
    def test_manager_raises_not_implemented_error_if_manager_class_has_no_requires(self, mock_load):
        key = 'jira'
        Configuration.NAMESPACE = 'tests.mocks'
        with patch('releaseessentials.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            mock_manager.return_value = key
            with self.assertRaises(NotImplementedError):
                a = InvalidRequires()

    @patch('releaseessentials.configuration.Configuration._load')
    def test_manager_raises_required_key_error_if_config_has_invalid_requires(self, mock_load):
        key = 'jira'
        Configuration.NAMESPACE = 'tests.mocks'
        Config = namedtuple('Config', 'manager jira server port')
        Jira   = Config(manager = None, jira = None, server = 'http://jira.local', port = '8080')
        mock_config = Config(manager = 'jira', jira = Jira, server = None, port = None)
        self.tearDown()
        Configuration._configuration = mock_config
        with patch('releaseessentials.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            mock_manager.return_value = key
            InvalidRequires.REQUIRED = ['bob']
            with self.assertRaises(RequiredKeyError):
                a = InvalidRequires()
