from unittest import TestCase
from mock import patch
from mock import PropertyMock

from releaseessentials.filter import Filter
from releaseessentials.managers.query import QueryManager
from releaseessentials.exceptions import InvalidQueryError
from releaseessentials.managers.project import ProjectManager
from tests.mocks.dataproviders import DataProviders
from releaseessentials.log import Logger

class TestFilter(TestCase):

    @patch('argparse.ArgumentParser.parse_args')
    @patch('releaseessentials.log.Logger.log')
    def setUp(self, mock_log, mock_parser):
        mock_log.return_value = None
        mock_parser.return_value = None
        Logger._instance = mock_log


    def tearDown(self):
        pass

    def test_run_raises_exception_if_manager_is_not_provided(self):
        mock_filter = Filter('issuetype = "Bug"')
        mock_filter.start()
        self.assertTrue(mock_filter.failed)
        self.assertIsInstance(mock_filter.failure, AssertionError)

    @patch('releaseessentials.managers.subjects.jira.Jira._client')
    @patch('releaseessentials.configuration.Configuration._load')
    def test_run_raises_exception_if_query_fails(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = DataProviders._get_client()
        mock_jira_client.search_issues.side_effect = InvalidQueryError('The specified query is invalid')
        with patch('releaseessentials.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('releaseessentials.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter('iamnotavalidquery')
                mock_filter.projectmanager = ProjectManager()
                mock_filter.start()
                self.assertTrue(mock_filter.failed)
                self.assertIsInstance(mock_filter.failure, InvalidQueryError)

    @patch('releaseessentials.managers.subjects.jira.Jira._client')
    @patch('releaseessentials.configuration.Configuration._load')
    def test_run_marks_thread_as_complete_on_success(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = None
        with patch('releaseessentials.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('releaseessentials.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter('assignee = "Bob"')
                mock_filter.projectmanager = ProjectManager()
                mock_filter.projectmanager._client._client = DataProviders._get_client()
                mock_filter.run()
                self.assertTrue(mock_filter.complete)
                self.assertEqual(len(mock_filter.results), len(DataProviders._test_data_for_search_results()))

    @patch('releaseessentials.managers.subjects.jira.Jira._client')
    @patch('releaseessentials.configuration.Configuration._load')
    def test_run_notifies_observers(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = None
        with patch('releaseessentials.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('releaseessentials.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter('assignee = "Bob"')
                mock_filter.projectmanager = ProjectManager()
                mock_filter.projectmanager._client._client = DataProviders._get_client()

                another_filter = Filter('assignee = "Bob"')
                mock_filter.append(another_filter)

                mock_filter.run()
                self.assertEquals(mock_filter.failure, None)
                self.assertTrue(mock_filter.complete)
                self.assertEqual(len(mock_filter.results), len(DataProviders._test_data_for_search_results()))
                self.assertEqual(mock_filter._results, another_filter._results)

    @patch('releaseessentials.managers.subjects.jira.Jira._client')
    @patch('releaseessentials.configuration.Configuration._load')
    def test_run_observer_skips_observer_implementation_if_results_have_been_set(self, mock_load, mock_jira_client):
        mock_jira_client.return_value = None
        with patch('releaseessentials.configuration.Configuration.manager', new_callable=PropertyMock) as mock_manager:
            with patch('releaseessentials.configuration.Configuration._configuration', new_callable=PropertyMock) as mock_config:
                mock_config.return_value = DataProviders._get_config_for_test()
                mock_manager.return_value = 'jira'
                mock_filter = Filter('assignee = "Bob"')
                mock_filter.projectmanager = ProjectManager()
                mock_filter.projectmanager._client._client = DataProviders._get_client()

                another_filter = Filter('assignee = "Bob"')
                another_filter.projectmanager = mock_filter.projectmanager
                mock_filter.append(another_filter)

                mock_filter.run()
                self.assertTrue(mock_filter.complete)
                self.assertEqual(mock_filter._results, another_filter._results)
                another_filter.start()
                self.assertEqual(len(mock_filter.results), len(DataProviders._test_data_for_search_results()))
