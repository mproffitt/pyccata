from unittest import TestCase
from mock     import patch, PropertyMock

from weeklyreport.configuration import Configuration
from weeklyreport.manager       import ProjectManager
from weeklyreport.exceptions    import InvalidModuleError, InvalidClassError

class TestProjectManager(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        if Configuration._instance is not None:
            Configuration._instance = None
        Configuration.NAMESPACE = 'weeklyreport'

    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_raises_invalid_module_error_if_manager_module_does_not_exist(self, mock_load):
        key = 'iwillneverbeamanager'
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            mock_manager.return_value = key
            with self.assertRaisesRegexp(InvalidModuleError, '{0}.*{1}.*'.format(key, Configuration.NAMESPACE)):
                ProjectManager()

    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_raises_invalid_class_error_if_manager_class_does_not_exist(self, mock_load):
        key = 'managermodule'
        Configuration.NAMESPACE = 'tests.mocks'
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            mock_manager.return_value = key
            with self.assertRaisesRegexp(InvalidClassError, 'Managermodule .* {0}.*'.format(Configuration.NAMESPACE)):
                ProjectManager()

    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_raises_import_error_if_manager_class_does_not_exist(self, mock_load):
        key = 'agilemanager'
        Configuration.NAMESPACE = 'tests.mocks'
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            mock_manager.return_value = key
            with self.assertRaises(ImportError):
                a = ProjectManager()


