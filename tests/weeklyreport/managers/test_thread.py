from unittest import TestCase
from mock     import patch, PropertyMock

from weeklyreport.configuration import Configuration
from weeklyreport.managers.project import ProjectManager
from weeklyreport.managers.thread import ThreadManager
from weeklyreport.exceptions import InvalidModuleError
from weeklyreport.exceptions import InvalidClassError
from tests.mocks.dataproviders import DataProviders
from weeklyreport.filter import Filter

class TestThreadManager(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('weeklyreport.managers.subjects.jira.Jira._client')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_adding_filter_adds_project_manager(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = DataProviders._get_client()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                manager = ThreadManager()
                mock_filter = Filter('assignee = "Foo"')
                manager.append(mock_filter)
                self.assertIsInstance(mock_filter.projectmanager, ProjectManager)
