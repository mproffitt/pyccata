from unittest import TestCase
from mock import patch, PropertyMock

from collections import namedtuple
from weeklyreport.configuration import Configuration
from weeklyreport.managers.project import ProjectManager
from weeklyreport.exceptions import InvalidConnectionError, InvalidQueryError
from weeklyreport.interface import ManagerInterface
from weeklyreport.managers.subjects.jira import Jira
from tests.mocks.dataproviders import DataProviders
from jira.client import JIRA
from jira.exceptions import JIRAError

class TestJira(TestCase):
    @patch('jira.client.JIRA.__init__')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_raises_exception_on_client_initialisation_failure(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        mock_jira_client.side_effect  = JIRAError(status_code = 500, text='something')
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test(port='')
                mock_manager.return_value = key
                with self.assertRaises(InvalidConnectionError) as cm:
                    manager = ProjectManager()
                    v = manager.client.client

                e = cm.exception
                self.assertEqual(500, e._code)
                self.assertEqual('something', e._error)
                self.assertRegexpMatches(str(e), 'Recieved HTTP\/\d+ whilst establishing connection to .*')


    @patch('weeklyreport.managers.subjects.jira.Jira._client')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_loads_client_on_success(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = DataProviders._get_client()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager, ProjectManager)
                self.assertIsInstance(manager._client, Jira)
                self.assertTrue(ManagerInterface in manager.__implements__)
                self.assertTrue(ManagerInterface in manager._client.__implements__)

    @patch('jira.client.JIRA.__init__')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_returns_list_of_projects(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        data = DataProviders._test_data_for_search_results()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                manager._client._client = DataProviders._get_client()
                self.assertEqual(len(manager.projects()), 3)

    @patch('jira.client.JIRA.__init__')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_returns_search_result_list(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        data = DataProviders._test_data_for_search_results()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                manager._client._client = DataProviders._get_client()
                self.assertEqual(
                    len(manager.search_issues(search_query='assignee = "bob123"', max_results=2, fields=[])),
                    len(DataProviders._test_data_for_search_results())
                )

    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_raises_invalid_query_exception_if_search_query_fails(self, mock_load, mock_search, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        mock_search.side_effect = JIRAError(status_code=400, text = 'Error in the JQL Query. Unknown field \'bob\'')

        data = DataProviders._test_data_for_search_results()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                with self.assertRaisesRegexp(InvalidQueryError, '.*Error in the JQL Query.*'):
                    manager.search_issues(search_query='assignee = "bob123"', max_results=2, fields=[])

    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('weeklyreport.configuration.Configuration._load')
    def test_manager_raises_invalid_connection_exception_if_search_query_fails(self, mock_load, mock_search, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        mock_search.side_effect = JIRAError(status_code=500, text = 'Server Error')

        data = DataProviders._test_data_for_search_results()
        with patch('weeklyreport.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('weeklyreport.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                with self.assertRaisesRegexp(InvalidConnectionError, 'Recieved HTTP/500 whilst establishing.*'):
                    manager.search_issues(search_query='assignee = "bob123"', max_results=2, fields=[])

