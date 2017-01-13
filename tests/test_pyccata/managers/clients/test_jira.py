from unittest import TestCase
from mock import patch, PropertyMock

from pyccata.core.configuration import Configuration
from pyccata.core.managers.project import ProjectManager
from pyccata.core.exceptions import InvalidConnectionError, InvalidQueryError
from pyccata.core.interface import ManagerInterface
from pyccata.core.managers.clients.jira import Jira
from tests.mocks.dataproviders import DataProviders
from jira.client import JIRA
from jira.exceptions import JIRAError
from pyccata.core.log import Logger
from collections import namedtuple

class TestJira(TestCase):

    @patch('argparse.ArgumentParser.parse_args')
    @patch('pyccata.core.log.Logger.log')
    def setUp(self, mock_log, mock_parser):
        mock_log.return_value = None
        mock_parser.return_value = []
        Logger._instance = mock_log

    def tearDown(self):
        Logger._instance = None

    @patch('jira.client.JIRA.__init__')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_manager_raises_exception_on_client_initialisation_failure(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        mock_jira_client.side_effect  = JIRAError(status_code = 500, text='something')
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test(port='')
                mock_manager.return_value = key
                with self.assertRaises(InvalidConnectionError) as cm:
                    manager = ProjectManager()
                    v = manager.client.client

                e = cm.exception
                self.assertEqual(500, e._code)
                self.assertEqual('something', e._error)
                self.assertRegexpMatches(str(e), 'Recieved HTTP\/\d+ whilst establishing connection to .*')


    @patch('pyccata.core.managers.clients.jira.Jira._client')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_manager_loads_client_on_success(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = DataProviders._get_client()
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager, ProjectManager)
                self.assertIsInstance(manager._client, Jira)
                self.assertTrue(ManagerInterface in manager.__implements__)
                self.assertTrue(ManagerInterface in manager._client.__implements__)
                self.assertEquals('http://jira.local:8080', manager.server.server_address)

    @patch('jira.client.JIRA.__init__')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_manager_returns_list_of_projects(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        data = DataProviders._test_data_for_search_results()
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                manager._client._client = DataProviders._get_client()
                self.assertEqual(len(manager.projects()), 3)

    @patch('jira.client.JIRA.__init__')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_manager_returns_search_result_list(self, mock_load, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        data = DataProviders._test_data_for_search_results()
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
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
    @patch('pyccata.core.configuration.Configuration._load')
    def test_manager_raises_invalid_query_exception_if_search_query_fails(self, mock_load, mock_search, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        mock_search.side_effect = JIRAError(status_code=400, text = 'Error in the JQL Query. Unknown field \'bob\'')

        data = DataProviders._test_data_for_search_results()
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                with self.assertRaisesRegexp(InvalidQueryError, '.*Error in the JQL Query.*'):
                    manager.search_issues(search_query='assignee = "bob123"', max_results=2, fields=[])

    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_manager_raises_invalid_connection_exception_if_search_query_fails(self, mock_load, mock_search, mock_jira_client):
        key = 'jira'
        mock_jira_client.return_value = None
        mock_search.side_effect = JIRAError(status_code=500, text = 'Server Error')

        data = DataProviders._test_data_for_search_results()
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = key
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                with self.assertRaisesRegexp(InvalidConnectionError, 'Recieved HTTP/500 whilst establishing.*'):
                    manager.search_issues(search_query='assignee = "bob123"', max_results=2, fields=[])

    @patch('jira.client.JIRA.__init__')
    @patch('jira.client.JIRA.search_issues')
    @patch('pyccata.core.configuration.Configuration._load')
    def test_jira_attachments(self, mock_load, mock_search, mock_jira_client):
        data = DataProviders._test_data_for_attachments()
        mock_jira_client.return_value = None
        mock_search.return_value = data
        with patch('pyccata.core.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('pyccata.core.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                manager = ProjectManager()
                self.assertIsInstance(manager.client.client, JIRA)
                attachments = manager.search_issues(search_query='assignee = "bob123"', max_results=2, fields=['attachments'])


